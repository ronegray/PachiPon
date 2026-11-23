"""
バトルコマンドモジュール
CommandProtocol
└CommandBaseSequence
 └CommandBaseEntity
  └CommandBaseActionを継承した、CommandBaseBattleによるコマンド群
内部でアイテムおよびスキル用ラッパーへの継承もあり
CommandBaseBattle
└CastSpellBattle
└UseItemBattle
"""

import logging
from typing import Generator, cast

# from abc import abstractmethod
# from dataclasses import dataclass
from random import choice

# import pyxel as px
from const import SoundID
# from gameutils.lib import Window

# from helper import diceroll, upper_int
from helper import upper_int, diceroll

# from entity import EntityContext, Enemy, EntityBase, WeakType, Character, EquipSlot, Equips
# from skill import SkillTargetType, DebuffType, SkillDef, SkillID
from entity import Enemy, EntityBase, Character
from skill import DebuffType, SkillDef, SkillID
from item import ItemDef  # , ItemTargetType  # , StackPool  # , ItemState  # , WeaponType
import service_locater as di

# from . import CommandPhase
from . import SeqSubCmd, CommandBaseAction

# from .entity_command import CommandBaseEntity
from .effect_command import (
    efx_diceroll,
    efx_physical_attack,
    efx_damage_shake,
    efx_monster_dead,
    efx_skill_attack,
)


# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseBattle(CommandBaseAction):
    """エンティティが実行者となるバトルシーン専用コマンドの基底クラス"""

    # def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
    #     """初期化：コンテキストの引継"""
    #     super().__init__(ctx, wnd, *args, **kwargs)
    # self.allies: list[EntityBase] = []
    # self.targets: list[EntityBase] = []
    # self.target: EntityBase = ctx.target
    # self.living_targets: list[EntityBase] = []

    # def _bind_ctx_for_local(self) -> None:
    #     """コンテキスト書換影響の局所化"""
    #     self.allies = list(self._ctx.allies)
    #     self.targets = list(self._ctx.targets)
    #     self.target = self._ctx.target

    def _check_living_targets(self) -> list[EntityBase]:
        """攻撃対象生存チェック"""
        return [t for t in self.local_targets if t.is_alive]

    def _check_actor_status(self) -> tuple[bool, str]:
        """行動前の状態チェック"""
        actor = self.ctx.actor
        if not actor.is_alive:
            if isinstance(actor, Character):
                return False, f"{actor.param.name}は　意識がトンでいる"
            return False, ""
        elif actor.debuff_list.get(DebuffType.STONE_HOLD, None):
            return False, f"{actor.param.name}は　石の体を　動かせない"
        elif actor.debuff_list.get(DebuffType.FALL_ASLEEP, None):
            return False, f"{actor.param.name}は　ねむりこけている"
        elif actor.debuff_list.get(DebuffType.CHARM_PERSON, None):
            # ターゲットの変更
            if self.local_target in self.local_allies:
                ctarget = choice(self.local_targets)
            else:
                ctarget = choice(self.local_allies)
            self.local_target = ctarget
            # ローカルコンテキストのターゲットを入替
            callies = list(self.local_allies)
            ctargets = list(self.local_targets)
            self.local_allies = ctargets
            self.local_targets = callies
            return True, f"{actor.param.name}は　敵にメロメロだ"
        return True, ""

    # @abstractmethod
    # def _sequence_action(self) -> Generator[list, None, None]:
    #     """バトルコマンドの本体処理"""
    #     ...

    def _after_action(self) -> Generator[list, None, None]:
        """行動後の共通処理"""
        if not self.ctx.actor.is_alive:
            return
        actor = self.ctx.actor

        # 毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]
            damage = max(1, poisoned - actor.bonus_end)
            yield from self.apply_damage(actor, damage)

    def _sequence(self) -> Generator[list, None, None]:
        """メイン処理フロー
        ターン内の各エンティティの１行動に関する処理の流れ
        敵全滅時は
        """
        # # コンテキスト情報のローカルコピー
        # self._bind_ctx_for_local()
        # 0. 戦闘継続チェック(攻撃対象が居る？)
        if not self._check_living_targets():
            return
        # 1. 行動事前チェックと状態メッセージ出力
        is_can_act, message = self._check_actor_status()
        if message:
            yield [message]
        if is_can_act is False:
            return
        # 2. 行動の実体
        yield from self._sequence_action()
        if not self._check_living_targets():
            # 行動によって対象全滅時は即時戦闘終了（デバフ処理なし）
            return
        # 3. 行動後の処理
        yield from self._after_action()

    def resolve_singletarget(self, action_targets: list[EntityBase]) -> None:  # EntityBase:
        """現在のターゲットが生存していればそれ、いなければ生存者の先頭"""
        if not self.local_target.is_alive:
            # self.target = [t for t in self.targets if t.is_alive][0]
            self.local_target = next(t for t in action_targets if t.is_alive)

    def apply_damage(self, target: EntityBase, damage: int) -> Generator[list, None, None]:
        """ダメージの演出・適用・撃破判定（攻撃演出の後に呼ぶ）"""
        yield from efx_damage_shake(self.display_info, target)  # type: ignore
        yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]
        target.decrease_hp(damage)

        if target.is_alive:
            return
        if isinstance(target, Enemy):
            yield from efx_monster_dead(self.display_info, target)  # type: ignore
            yield [f"{target.param.name}は 力尽きて ころがった"]


# @dataclass
# class CommandPackage:
#     """Command選択結果のメニュー⇔シーン間受け渡し用パッケージ"""

#     selected_action: type[CommandBaseBattle] | None = None
#     target_type: SkillTargetType | ItemTargetType | None = None
#     selected_args: dict | None = None


class Attack(CommandBaseBattle):
    """エンティティ共通行動：物理攻撃"""

    def _sequence_action(self) -> Generator[list, None, None]:
        actor = self.ctx.actor
        self.resolve_singletarget(self.local_targets)
        # ファーストメッセージ
        yield [f"{actor.param.name}は {self.local_target.param.name} に 襲い掛かる！", ""]

        # 命中ロール
        hit = actor.attackroll_offence()
        dodge = self.local_target.attackroll_defence()
        judge = hit - dodge
        logger.debug(f"actor={actor.param.name},hit={hit}, dodge={dodge}")
        if judge <= 0:
            # di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [SeqSubCmd.SE_INSTANT, SoundID.ATTACK_MISS]
            yield ["だけど、攻撃は かすりもしなかった・・・"]
            return  # ここで終了

        # ダメージロール
        crit_rate = actor.get_critical_rate(judge)
        dice, damage = actor.damageroll_melee()
        yield from efx_diceroll(self.display_info, dice)  # type: ignore
        damage = (damage * crit_rate) - self.local_target.suppress_damage_melee()
        weapon_type = actor.get_weapon_type()
        damage = int(damage * self.local_target.calc_guard_rate(weapon_type))

        if damage <= 0:
            # di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [SeqSubCmd.SE_INSTANT, SoundID.ATTACK_MISS]
            yield [f"{self.local_target.param.name}の かたい防御に はばまれた"]
            return

        yield from efx_physical_attack(self.display_info, self.local_target, weapon_type)  # type: ignore
        yield from self.apply_damage(self.local_target, damage)


# class UseSkill(CommandBaseBattle):
#     """ユーザ行動：スキル使用"""

#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         # ファーストメッセージ
#         yield [f"{actor.param.name}は、 スキルを使いたがった", ""]


class DefenceMode(CommandBaseBattle):
    """ユーザ行動：防御体勢"""

    def _sequence_action(self) -> Generator[list, None, None]:
        actor = self.ctx.actor
        # ファーストメッセージ
        yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]
        actor.defend()
        yield [f"{actor.param.name}の 受けるダメージが 減少する"]


class EnemyEscape(CommandBaseBattle):
    """エネミー専用行動：撤退"""

    def _sequence_action(self) -> Generator[list, None, None]:
        actor = self.ctx.actor
        # ファーストメッセージ
        yield [f"{actor.param.name}は、 逃げ出した！", ""]

        dice = diceroll(actor.bonus_spd) + actor.bonus_lck - actor.reduce_dice
        dc = di.ref.pt.get_party_speed()
        if dice > dc:
            # di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_ESCAPE)
            yield [SeqSubCmd.SE_SUSTAIN, SoundID.ENEMY_ESCAPE]
            actor.decrease_hp(actor.max_hp)
            # 死亡＆報酬０扱いにする（モンスターリストの中から削除しない）
            actor.param.exp = actor.eparam.gold = 0  # type: ignore
        else:
            # 逃走失敗時はイニシアチブが0
            yield ["スッ転がって　逃げそびれた・・・"]
            actor.activate_debuff(DebuffType.INITIATIVE_ZERO, 1)


class EnemySpecial(CommandBaseBattle):
    """エネミー専用行動：特殊攻撃"""

    def _sequence_action(self) -> Generator[list, None, None]:
        actor = self.ctx.actor
        # ファーストメッセージ
        yield [f"{actor.param.name}の 特殊攻撃！", ""]


class UseItemBattle(CommandBaseBattle):
    """消費アイテム用バトルシーン向け共通クラス"""

    def _sequence_action(self) -> Generator[list, None, None]:
        """アイテム利用の殻"""
        # # # 引き回されたアイテムデータの取得
        # # # self.item_def = cast(ItemDef, self.args[0]["item_def"])
        # # self.item_def = cast(ItemDef, self.args[0]["item_def"])
        # self.item_def = self.args[0]["item_def"]
        self.item_def: ItemDef = self.kwargs["sel_cmd_dict"]["item_def"]
        equip = cast(Character, self.ctx.actor).equipments
        slot = self.kwargs["sel_cmd_dict"]["source"]

        from .item_ import item_info_package, use_item

        yield from use_item(
            item_info_package(
                command=self,
                item_def=self.item_def,
                # consume=lambda: equip.use_consume(self.args[0]["slot"]),
                consume=lambda: equip.use_consume(slot),
                pre_effects=[self.send_blank],
            )
        )

        # yield []
        return

    def send_blank(self) -> Generator[list, None, None]:
        yield [""]
        return


class CastSpellBattle(CommandBaseBattle):
    """MP消費型スキル用バトルシーン向け共通クラス※エネミー特殊スキルは別途"""

    def _sequence_action(self) -> Generator[list, None, None]:
        """バトル内スキル利用の殻。効果関数へのフックを持つ。"""
        # # 引き回されたアイテムデータの取得
        # # self.item_def = cast(ItemDef, self.args[0]["item_def"])
        # self._parse_args_spell()
        self.skill_def: SkillDef = self.kwargs["sel_cmd_dict"]["skillinfo"]

        from .skill_ import skill_info_package, use_skill

        yield from use_skill(
            skill_info_package(
                command=self,
                skill_def=self.skill_def,
                # consume=lambda: equip.use_consume(self.args[0]["slot"]),
                # consume=lambda: equip.use_consume(slot),
                # pre_effects=[self.send_blank],
            )
        )
        return

    def cast_spell(self, skill_def: SkillDef) -> Generator[list, None, bool]:
        actor = self.ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return False

        # 詠唱ロール
        if self.ctx.situation == "battle" and not actor.castroll(skill_def.dc):
            # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
            yield ["呪文は　失敗に終わった・・・"]
            return False

        return True

    def damage_spell(
        self, actor: EntityBase, skill_def: SkillDef, target: EntityBase
    ) -> Generator[list, None, bool]:
        """スペルダメージ関連共通処理"""
        damage = int(
            (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
            * target.calc_weak_rate(skill_def.skill_type)
        )

        if damage <= 0:
            # di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [SeqSubCmd.SE_INSTANT, SoundID.ATTACK_MISS]
            yield [f"{target.param.name}の守りを 貫けない！"]
            return False

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        yield from self.apply_damage(target, damage)
        return True

    def recover_spell(
        self, actor: EntityBase, skill_def: SkillDef, target: EntityBase
    ) -> Generator[list, None, None]:
        """スペル回復関連共通処理"""
        healing = actor.damageroll_skill(skill_def)

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore

        real_heal = target.increase_hp(healing)
        # di.ref.sndmgr.play_se_instant(SoundID.RECOVER)
        yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


# class attack_spell_single(CastSpellBattle):
#     """単体攻撃魔法"""

#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.targets)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         # ダメージロール
#         yield from self._damage_spell(actor, skill_def, target)


# class attack_spell_area(CastSpellBattle):
#     """全体攻撃魔法"""

#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         for target in self._check_living_targets():
#             # ダメージロール
#             yield from self._damage_spell(actor, skill_def, target)


# class recover_spell_single(CastSpellBattle):
#     """単体回復呪文"""

#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.allies)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         # 回復ロール
#         yield from self._recover_spell(actor, skill_def, target)


# class recover_spell_area(CastSpellBattle):
#     """全体回復呪文"""

#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         # self._resolve_singletarget(self.allies)

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         # 回復ロール
#         for target in self.allies:
#             if target.is_alive:
#                 yield from self._recover_spell(actor, skill_def, target)


# class attack_disrupt_undead(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         for target in self._check_living_targets():
#             # ダメージロール
#             dmg = yield from self._damage_spell(actor, skill_def, target)

#             # 混乱時味方にキャストしたらダメージのみで終了
#             if isinstance(target, Enemy) and dmg and target.is_alive:
#                 # 抵抗ロール（アンデッド＝霊光属性弱点の場合のみ）
#                 if (target.eparam.weaktype & WeakType.LIGHT) >= 1 and target.registroll(
#                     DebuffType.DISRUPT_UNDEAD, skill_def.dc + actor.bonus_arc
#                 ) is False:
#                     target.instant_kill()
#                     yield [f"{target.param.name}は　灰となって　崩れ落ちた！"]
#                     continue


# class debuff_dice_value(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.targets)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#         # 抵抗ロール（弱点属性の場合は必中）
#         if (
#             target.calc_weak_rate(skill_def.skill_type) > 1.0
#             or target.registroll(DebuffType.REDUCE_DICEVALUE, skill_def.dc + actor.bonus_arc)
#             is False
#         ):
#             target.activate_debuff(DebuffType.REDUCE_DICEVALUE, skill_def.dc + actor.bonus_arc)
#             yield [f"{target.param.name}は　苦痛の呪いを受けた・・・"]
#         else:
#             # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
#             yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
#             yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_continual_damage(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         for target in self._check_living_targets():
#             yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#             # 抵抗ロール（弱点属性の場合は必中）
#             if (
#                 target.calc_weak_rate(skill_def.skill_type) > 1.0
#                 or target.registroll(DebuffType.POISON_DAMAGE, skill_def.dc + actor.bonus_arc)
#                 is False
#             ):
#                 target.activate_debuff(DebuffType.POISON_DAMAGE, skill_def.dc + actor.bonus_arc)
#                 yield [f"{target.param.name}は　毒を浴びてしまった・・・"]
#             else:
#                 # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
#                 yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
#                 yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_stone_statue(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.targets)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#         # 抵抗ロール（弱点属性の場合は必中）
#         if (
#             target.calc_weak_rate(skill_def.skill_type) > 1.0
#             or target.registroll(DebuffType.STONE_HOLD, skill_def.dc + actor.bonus_arc) is False
#         ):
#             target.activate_debuff(DebuffType.STONE_HOLD, skill_def.dc + actor.bonus_arc)
#             yield [f"{target.param.name}は　石の像になった・・・"]
#         else:
#             # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
#             yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
#             yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_sleep(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         for target in self._check_living_targets():
#             yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#             # 抵抗ロール（弱点属性の場合は必中）
#             if (
#                 target.calc_weak_rate(skill_def.skill_type) > 1.0
#                 or target.registroll(DebuffType.FALL_ASLEEP, skill_def.dc + actor.bonus_arc)
#                 is False
#             ):
#                 target.activate_debuff(DebuffType.FALL_ASLEEP, skill_def.dc + actor.bonus_arc)
#                 yield [f"{target.param.name}は　眠りにおちた・・・"]
#             else:
#                 # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
#                 yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
#                 yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_cast_penalty(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.targets)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
#         yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#         # 抵抗ロール（弱点属性の場合は必中）
#         if (
#             target.calc_weak_rate(skill_def.skill_type) > 1.0
#             or target.registroll(DebuffType.DISTURB_MIND, skill_def.dc + actor.bonus_arc) is False
#         ):
#             target.activate_debuff(DebuffType.DISTURB_MIND, skill_def.dc + actor.bonus_arc)
#             yield [f"{target.param.name}は　集中を乱された・・・"]
#         else:
#             # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
#             yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
#             yield [f"{target.param.name}は　効果をはねのけた！"]


# class debuff_charm(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.targets)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
#         yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#         # 抵抗ロール（弱点属性の場合は必中）
#         if (
#             target.calc_weak_rate(skill_def.skill_type) > 1.0
#             or target.registroll(DebuffType.CHARM_PERSON, skill_def.dc + actor.bonus_arc) is False
#         ):
#             target.activate_debuff(DebuffType.CHARM_PERSON, skill_def.dc + actor.bonus_arc)
#             yield [f"{target.param.name}は　魅了された・・・"]
#         else:
#             # di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
#             yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
#             yield [f"{target.param.name}は　効果をはねのけた！"]


# class attack_initiative_zero(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         actor = self._ctx.actor
#         self._resolve_singletarget(self.targets)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         # ダメージロール
#         result2 = yield from self._damage_spell(actor, skill_def, target)
#         if result2:
#             # 抵抗ロール（弱点属性の場合は必中）
#             if (
#                 target.calc_weak_rate(skill_def.skill_type) > 1.0
#                 or target.registroll(DebuffType.INITIATIVE_ZERO, skill_def.dc + actor.bonus_arc)
#                 is False
#             ):
#                 target.activate_debuff(DebuffType.INITIATIVE_ZERO, skill_def.dc + actor.bonus_arc)
#                 yield [f"{target.param.name}は　吹っ飛ばされた！"]


# class dispell_debuff(CastSpellBattle):
#     def _sequence_action(self) -> Generator[list, None, None]:
#         # actor = self._ctx.actor
#         self._resolve_singletarget(self.allies)
#         target = self.target

#         # コマンドパッケージから取得するスキル情報
#         skill_def = self.args[0]["skillinfo"]

#         # スキル共通処理
#         result = yield from self._cast_spell(skill_def)
#         if result is False:
#             return

#         target.clear_all_debuff()
#         yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
#         yield [f"{target.param.name}の状態異常は　消え去った！"]
