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
from random import choice
from const import SoundID
from helper import upper_int, diceroll
from entity import Enemy, EntityBase, Character
from skill import DebuffType, SkillDef, SkillID
from item import ItemDef
import service_locater as di
from . import SeqSubCmd, CommandBaseAction
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
            yield [SeqSubCmd.SE_INSTANT, SoundID.ATTACK_MISS]
            yield [f"{self.local_target.param.name}の かたい防御に はばまれた"]
            return

        yield from efx_physical_attack(self.display_info, self.local_target, weapon_type)  # type: ignore
        yield from self.apply_damage(self.local_target, damage)


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
        # 引き回されたアイテムデータの取得
        self.item_def: ItemDef = self.kwargs["sel_cmd_dict"]["item_def"]
        equip = cast(Character, self.ctx.actor).equipments
        slot = self.kwargs["sel_cmd_dict"]["source"]

        from .item_ import item_info_package, use_item

        yield from use_item(
            item_info_package(
                command=self,
                item_def=self.item_def,
                consume=lambda: equip.use_consume(slot),
                pre_effects=[self.send_blank],
            )
        )

        return

    def send_blank(self) -> Generator[list, None, None]:
        yield [""]
        return


class CastSpellBattle(CommandBaseBattle):
    """MP消費型スキル用バトルシーン向け共通クラス※エネミー特殊スキルは別途"""

    def _sequence_action(self) -> Generator[list, None, None]:
        """バトル内スキル利用の殻。効果関数へのフックを持つ。"""
        # 引き回されたスキルデータの取得
        self.skill_def: SkillDef = self.kwargs["sel_cmd_dict"]["skillinfo"]

        from .skill_ import skill_info_package, use_skill

        yield from use_skill(
            skill_info_package(
                command=self,
                skill_def=self.skill_def,
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
            yield [SeqSubCmd.SE_INSTANT, SoundID.MAGIC_FAIL]
            yield ["呪文は　失敗に終わった・・・"]
            return False

        return True

    def damage_spell(self, actor: EntityBase, skill_def: SkillDef, target: EntityBase) -> Generator[list, None, bool]:
        """スペルダメージ関連共通処理"""
        damage = int(
            (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
            * target.calc_weak_rate(skill_def.skill_type)
        )

        if damage <= 0:
            yield [SeqSubCmd.SE_INSTANT, SoundID.ATTACK_MISS]
            yield [f"{target.param.name}の守りを 貫けない！"]
            return False

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        yield from self.apply_damage(target, damage)
        return True

    def recover_spell(self, actor: EntityBase, skill_def: SkillDef, target: EntityBase) -> Generator[list, None, None]:
        """スペル回復関連共通処理"""
        healing = actor.damageroll_skill(skill_def)

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore

        real_heal = target.increase_hp(healing)
        yield [SeqSubCmd.SE_INSTANT, SoundID.RECOVER]
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]
