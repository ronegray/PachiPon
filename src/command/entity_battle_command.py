"""
バトルコマンドモジュール
"""

import logging
from typing import Generator
from abc import abstractmethod
from dataclasses import dataclass
from random import choice
import pyxel as px
from const import SoundID
from gameutils.lib import Window

# from helper import diceroll, upper_int
from helper import upper_int, diceroll
from entity import EntityContext, Enemy, EntityBase, WeakType, Character
from skill import SkillTargetType, DebuffType, SkillDef, SkillID
from item import ItemTargetType  # , StackPool  # , ItemState  # , WeaponType
import service_locater as di

# from . import CommandPhase
from .entity_command import CommandBaseEntity
from .effect_command import (
    efx_diceroll,
    efx_physical_attack,
    efx_damage_shake,
    efx_monster_dead,
    efx_skill_attack,
)


# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseBattle(CommandBaseEntity):
    """エンティティが実行者となるバトルシーン専用コマンドの基底クラス"""

    def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        super().__init__(ctx, wnd, *args, **kwargs)
        self.allies: list[EntityBase] = []
        self.targets: list[EntityBase] = []
        self.target: EntityBase = ctx.target
        self.living_targets: list[EntityBase] = []

    def _bind_ctx_for_local(self) -> None:
        """コンテキスト書換影響の局所化"""
        self.allies = list(self._ctx.allies)
        self.targets = list(self._ctx.targets)
        self.target = self._ctx.target

    def _check_living_targets(self) -> list[EntityBase]:
        """攻撃対象生存チェック"""
        return [t for t in self.targets if t.is_alive]

    def _check_actor_status(self) -> tuple[bool, str]:
        """行動前の状態チェック"""
        actor = self._ctx.actor
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
            if self.target in self.allies:
                ctarget = choice(self.targets)
            else:
                ctarget = choice(self.allies)
            self.target = ctarget
            # ローカルコンテキストのターゲットを入替
            callies = list(self.allies)
            ctargets = list(self.targets)
            self.allies = ctargets
            self.targets = callies
            return True, f"{actor.param.name}は　敵にメロメロだ"
        return True, ""

    @abstractmethod
    def _sequence_action(self) -> Generator[list[str], None, None]:
        """バトルコマンドの本体処理"""
        ...

    def _after_action(self) -> Generator[list[str], None, None]:
        """行動後の共通処理"""
        if not self._ctx.actor.is_alive:
            return
        actor = self._ctx.actor

        # 毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]
            damage = max(1, poisoned - actor.bonus_end)
            yield from self._apply_damage(actor, damage)

    def _sequence(self) -> Generator[list[str], None, None]:
        """メイン処理フロー
        ターン内の各エンティティの１行動に関する処理の流れ
        敵全滅時は
        """
        # コンテキスト情報のローカルコピー
        self._bind_ctx_for_local()
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

    def _resolve_singletarget(self) -> None:  # EntityBase:
        """現在のターゲットが生存していればそれ、いなければ生存者の先頭"""
        if not self.target.is_alive:
            self.target = [t for t in self.targets if t.is_alive][0]

    def _apply_damage(self, target: EntityBase, damage: int) -> Generator[list[str], None, None]:
        """ダメージの演出・適用・撃破判定（攻撃演出の後に呼ぶ）"""
        yield from efx_damage_shake(self.display_info, target)  # type: ignore
        yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]
        target.decrease_hp(damage)

        if target.is_alive:
            return
        if isinstance(target, Enemy):
            yield from efx_monster_dead(self.display_info, target)  # type: ignore
            yield [f"{target.param.name}は 力尽きて ころがった"]


@dataclass
class CommandPackage:
    """Command選択結果のメニュー⇔シーン間受け渡し用パッケージ"""

    selected_action: type[CommandBaseBattle] | None = None
    target_type: SkillTargetType | ItemTargetType | None = None
    selected_args: dict | None = None


class Attack(CommandBaseBattle):
    """エンティティ共通行動：物理攻撃"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        # ファーストメッセージ
        yield [f"{actor.param.name}は {self.target.param.name} に 襲い掛かる！", ""]

        # 命中ロール
        hit = actor.attackroll_offence()
        dodge = self.target.attackroll_defence()
        judge = hit - dodge
        logger.debug(f"actor={actor.param.name},hit={hit}, dodge={dodge}")
        if judge <= 0:
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield ["だけど、攻撃は かすりもしなかった・・・"]
            return  # ここで終了

        # ダメージロール
        crit_rate = actor.get_critical_rate(judge)
        dice, damage = actor.damageroll_melee()
        yield from efx_diceroll(self.display_info, dice)  # type: ignore
        damage = (damage * crit_rate) - self.target.suppress_damage_melee()
        weapon_type = actor.get_weapon_type()
        damage = int(damage * self.target.calc_guard_rate(weapon_type))

        if damage <= 0:
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [f"{self.target.param.name}の かたい防御に はばまれた"]
            return

        yield from efx_physical_attack(self.display_info, self.target, weapon_type)  # type: ignore
        yield from self._apply_damage(self.target, damage)


# class UseSkill(CommandBaseBattle):
#     """ユーザ行動：スキル使用"""

#     def _sequence_action(self) -> Generator[list[str], None, None]:
#         actor = self._ctx.actor
#         # ファーストメッセージ
#         yield [f"{actor.param.name}は、 スキルを使いたがった", ""]


class DefenceMode(CommandBaseBattle):
    """ユーザ行動：防御体勢"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        # ファーストメッセージ
        yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]
        actor.defend()
        yield [f"{actor.param.name}の 受けるダメージが 減少する"]


class EnemyEscape(CommandBaseBattle):
    """エネミー専用行動：撤退"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        # ファーストメッセージ
        yield [f"{actor.param.name}は、 逃げ出した！", ""]

        dice = diceroll(actor.bonus_spd) + actor.bonus_lck - actor.reduce_dice
        dc = di.ref.pt.get_party_speed()
        if dice > dc:
            di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_ESCAPE)
            actor.decrease_hp(actor.max_hp)
            # 死亡＆報酬０扱いにする（モンスターリストの中から削除しない）
            actor.param.exp = actor.eparam.gold = 0  # type: ignore
        else:
            # 逃走失敗時はイニシアチブが0
            yield ["スッ転がって　逃げそびれた・・・"]
            actor.activate_debuff(DebuffType.INITIATIVE_ZERO, 1)


class EnemySpecial(CommandBaseBattle):
    """エネミー専用行動：特殊攻撃"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        # ファーストメッセージ
        yield [f"{actor.param.name}の 特殊攻撃！", ""]


class CommandBaseSpell(CommandBaseBattle):
    """MP消費型スキル用共通クラス"""

    def _cast_spell(self, skill_def: SkillDef) -> Generator[list[str], None, bool]:
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return False

        # 詠唱ロール
        if self._ctx.situation == "battle" and not actor.castroll(skill_def.dc):
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return False

        return True

    def _damage_spell(
        self, actor: EntityBase, skill_def: SkillDef, target: EntityBase
    ) -> Generator[list[str], None, bool]:
        """スペルダメージ関連共通処理"""
        damage = int(
            (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
            * target.calc_weak_rate(skill_def.skill_type)
        )

        if damage <= 0:
            px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [f"{target.param.name}の守りを 貫けない！"]
            return False

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        yield from self._apply_damage(self.target, damage)
        return True

    def _recover_spell(
        self, actor: EntityBase, skill_def: SkillDef, target: EntityBase
    ) -> Generator[list[str], None, None]:
        """スペル回復関連共通処理"""
        healing = actor.damageroll_skill(skill_def)

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore

        real_heal = target.increase_hp(healing)
        di.ref.sndmgr.play_se_instant(SoundID.RECOVER)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


class AttackSpellSingle(CommandBaseSpell):
    """単体攻撃魔法"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        # ダメージロール
        yield from self._damage_spell(actor, skill_def, target)


class AttackSpellArea(CommandBaseSpell):
    """全体攻撃魔法"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        for target in self._check_living_targets():
            # ダメージロール
            yield from self._damage_spell(actor, skill_def, target)


class RecoverSpellSingle(CommandBaseSpell):
    """単体回復呪文"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        # 回復ロール
        self._recover_spell(actor, skill_def, target)


class RecoverSpellArea(CommandBaseSpell):
    """全体回復呪文"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        # 回復ロール
        for target in self.allies:
            if target.is_alive:
                self._recover_spell(actor, skill_def, target)


class AttackDisruptUndead(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        for target in self._check_living_targets():
            # ダメージロール
            yield from self._damage_spell(actor, skill_def, target)

            # 混乱時味方にキャストしたらダメージのみで終了
            if isinstance(target, Enemy):
                # 抵抗ロール（アンデッド＝霊光属性弱点の場合のみ）
                if (target.eparam.weaktype & WeakType.LIGHT) >= 1 and target.registroll(
                    DebuffType.DISRUPT_UNDEAD, skill_def.dc + actor.bonus_arc
                ) is False:
                    target.instant_kill()
                    yield [f"{target.param.name}は　灰となって　崩れ落ちた！"]
                    continue


class DebuffDiceValue(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.REDUCE_DICEVALUE, skill_def.dc + actor.bonus_arc)
            is False
        ):
            target.activate_debuff(DebuffType.REDUCE_DICEVALUE, skill_def.dc + actor.bonus_arc)
            yield [f"{target.param.name}は　苦痛の呪いを受けた・・・"]
        else:
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [f"{target.param.name}は　効果をはねのけた！"]


class DebuffContinualDamage(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        for target in self._check_living_targets():
            yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
            # 抵抗ロール（弱点属性の場合は必中）
            if (
                target.calc_weak_rate(skill_def.skill_type) > 1.0
                or target.registroll(DebuffType.POISON_DAMAGE, skill_def.dc + actor.bonus_arc)
                is False
            ):
                target.activate_debuff(DebuffType.POISON_DAMAGE, skill_def.dc + actor.bonus_arc)
                yield [f"{target.param.name}は　毒を浴びてしまった・・・"]
            else:
                di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
                yield [f"{target.param.name}は　効果をはねのけた！"]


class DebuffStoneStatue(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.STONE_HOLD, skill_def.dc + actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.STONE_HOLD, skill_def.dc + actor.bonus_arc)
            yield [f"{target.param.name}は　石の像になった・・・"]
        else:
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [f"{target.param.name}は　効果をはねのけた！"]


class DebuffSleep(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        for target in self._check_living_targets():
            yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
            # 抵抗ロール（弱点属性の場合は必中）
            if (
                target.calc_weak_rate(skill_def.skill_type) > 1.0
                or target.registroll(DebuffType.FALL_ASLEEP, skill_def.dc + actor.bonus_arc)
                is False
            ):
                target.activate_debuff(DebuffType.FALL_ASLEEP, skill_def.dc + actor.bonus_arc)
                yield [f"{target.param.name}は　眠りにおちた・・・"]
            else:
                di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
                yield [f"{target.param.name}は　効果をはねのけた！"]


class DebuffCastPenalty(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.DISTURB_MIND, skill_def.dc + actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.DISTURB_MIND, skill_def.dc + actor.bonus_arc)
            yield [f"{target.param.name}は　集中を乱された・・・"]
        else:
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [f"{target.param.name}は　効果をはねのけた！"]


class DebuffCharm(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.CHARM_PERSON, skill_def.dc + actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.CHARM_PERSON, skill_def.dc + actor.bonus_arc)
            yield [f"{target.param.name}は　魅了された・・・"]
        else:
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [f"{target.param.name}は　効果をはねのけた！"]


class AttackInitiativeZero(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        # ダメージロール
        result2 = yield from self._damage_spell(actor, skill_def, target)
        if result2:
            # 抵抗ロール（弱点属性の場合は必中）
            if (
                target.calc_weak_rate(skill_def.skill_type) > 1.0
                or target.registroll(DebuffType.INITIATIVE_ZERO, skill_def.dc + actor.bonus_arc)
                is False
            ):
                target.activate_debuff(DebuffType.INITIATIVE_ZERO, skill_def.dc + actor.bonus_arc)
                yield [f"{target.param.name}は　吹っ飛ばされた！"]


class DispellDebuff(CommandBaseSpell):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # actor = self._ctx.actor
        self._resolve_singletarget()
        target = self.target

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # スキル共通処理
        result = yield from self._cast_spell(skill_def)
        if result is False:
            return

        target.clear_all_debuff()
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        yield [f"{target.param.name}の状態異常は　消え去った！"]
