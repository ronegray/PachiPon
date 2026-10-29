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
from helper import upper_int
from entity import EntityContext, Enemy, EntityBase, WeakType, Character
from skill import SkillTargetType, DebuffType, SkillID
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

    def _resolve_target(self) -> None:  # EntityBase:
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
        self._resolve_target()
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


class UseSkill(CommandBaseBattle):
    """ユーザ行動：スキル使用"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # # 最初に必ず生死チェック
        # # if self._check_actor_alive():
        # #     actor = self._ctx.actor
        # # else:
        # #     return
        # # 行動可否チェック
        # result = self._check_actor_status()
        # if len(result):
        #     yield [result]
        #     return
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}は、 スキルを使いたがった", ""]

        # # 行動後毒ダメージチェック
        # poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        # if poisoned:
        #     yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
        #     actor.decrease_hp(poisoned - actor.bonus_end)
        #     di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
        #     yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DefenceMode(CommandBaseBattle):
    """ユーザ行動：防御体勢"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # if self._check_actor_alive():
        # #     actor = self._ctx.actor
        # # else:
        # #     return
        # # 行動可否チェック
        # result = self._check_actor_status()
        # if len(result):
        #     yield [result]
        #     return
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]

        actor.defend()
        yield [f"{actor.param.name}の 受けるダメージが 減少する"]

        # # 行動後毒ダメージチェック
        # poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        # if poisoned:
        #     yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
        #     actor.decrease_hp(poisoned - actor.bonus_end)
        #     di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
        #     yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class AttackSpellSingle(CommandBaseBattle):
    """単体攻撃魔法"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_BOLT)
        # ダメージロール
        damage = int(
            (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
            * target.calc_weak_rate(skill_def.skill_type)
        )

        if damage <= 0:
            # px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [f"{target.param.name}の守りを 貫けない！"]
            return

        # px.play(self.se_ch, SoundID.DAMAGE_GIVEN, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        yield from efx_damage_shake(self.display_info, target)  # type: ignore
        yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]

        # run_effectに相当：メッセージ表示後にダメージ適用
        target.decrease_hp(damage)

        if not target.is_alive:
            # cleanupに相当：撃破メッセージ
            # px.play(self.se_ch, SoundID.ENEMY_DEATH, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_DEATH)
            yield [f"{target.param.name}は 力尽きて ころがった"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class AttackSpellArea(CommandBaseBattle):
    """全体攻撃魔法"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # # 生存ターゲットチェック
        # living_targets = self._check_living_targets()
        # if not living_targets:
        #     return
        # # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        # current = self._ctx.target
        # target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if actor.castroll(skill_def.dc) is False:
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        for target in self._check_living_targets():
            di.ref.sndmgr.play_se_sustain(SoundID.CAST_BOLT)
            # ダメージロール
            damage = int(
                (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
                * target.calc_weak_rate(skill_def.skill_type)
            )

            if damage <= 0:
                px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
                yield [f"{target.param.name}の守りを 貫けない！"]
                return

            # px.play(self.se_ch, SoundID.DAMAGE_GIVEN, resume=True)
            # di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
            yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
            yield from efx_damage_shake(self.display_info, target)  # type: ignore
            yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]

            # run_effectに相当：メッセージ表示後にダメージ適用
            target.decrease_hp(damage)

            if not target.is_alive:
                # cleanupに相当：撃破メッセージ
                # px.play(self.se_ch, SoundID.ENEMY_DEATH, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_DEATH)
                yield [f"{target.param.name}は 力尽きて ころがった"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class RecoverSpellSingle(CommandBaseBattle):
    """単体回復呪文"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]

        if self._ctx.situation == "battle":
            yield [""]

            # 戦闘中のＭＰ減少による使用の可否チェック
            if not actor.use_mp(skill_def.cost):
                yield ["しかし　ＭＰが不足している・・・"]
                return

            # 詠唱ロール
            if actor.castroll(skill_def.dc) is False:
                # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
                yield ["呪文は　失敗に終わった・・・"]
                return  # ここで終了
        # else:
        #     # px.play(self.se_ch, SoundID.CAST_LIGHT, resume=True)
        #     di.ref.sndmgr.play_se_sustain(SoundID.CAST_LIGHT)
        #     actor.use_mp(skill_def.cost)
        di.ref.sndmgr.play_se_sustain(SoundID.CAST_LIGHT)
        # actor.use_mp(skill_def.cost)

        # ダメージロール
        healing = actor.damageroll_skill(skill_def)
        # yield [""]

        # real_heal = target.increase_hp(healing)
        # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        real_heal = target.increase_hp(healing)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class RecoverSpellArea(CommandBaseBattle):
    """全体回復呪文"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]

        if self._ctx.situation == "battle":
            yield [""]

            # 戦闘中のＭＰ減少による使用の可否チェック
            if not actor.use_mp(skill_def.cost):
                yield ["しかし　ＭＰが不足している・・・"]
                return

            # 詠唱ロール
            if actor.castroll(skill_def.dc) is False:
                # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
                yield ["呪文は　失敗に終わった・・・"]
                return  # ここで終了

        # px.play(self.se_ch, SoundID.CAST_LIGHT, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.CAST_LIGHT)
        # actor.use_mp(skill_def.cost)

        for target in self._ctx.allies:
            # ダメージロール
            healing = actor.damageroll_skill(skill_def)
            # yield [""]

            # real_heal = target.increase_hp(healing)
            # px.play(self.se_ch, SoundID.RECOVER, resume=True)
            # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
            yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
            real_heal = target.increase_hp(healing)
            yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class AttackDisruptUndead(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if actor.castroll(skill_def.dc) is False:
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        for target in self._check_living_targets():
            di.ref.sndmgr.play_se_sustain(SoundID.CAST_SACRED)
            # ダメージロール
            damage = int(
                (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
                * target.calc_weak_rate(skill_def.skill_type)
            )

            if damage <= 0:
                px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
                yield [f"{target.param.name}の守りを 貫けない！"]
                return

            # px.play(self.se_ch, SoundID.DAMAGE_GIVEN, resume=True)
            # di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
            yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
            yield from efx_damage_shake(self.display_info, target)  # type: ignore
            yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]

            # 抵抗ロール（アンデッド＝霊光属性弱点の場合のみ）
            if (target.weaktype & WeakType.LIGHT) >= 1 and target.registroll(
                DebuffType.DISRUPT_UNDEAD, skill_def.dc + actor.bonus_arc
            ) is False:
                target.instant_kill()
                yield [f"{target.param.name}は　灰となって　崩れ落ちた！"]
                continue

            # run_effectに相当：メッセージ表示後にダメージ適用
            target.decrease_hp(damage)

            if not target.is_alive:
                # cleanupに相当：撃破メッセージ
                # px.play(self.se_ch, SoundID.ENEMY_DEATH, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_DEATH)
                yield [f"{target.param.name}は 力尽きて ころがった"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DebuffDiceValue(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_CURSE)
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

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DebuffContinualDamage(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_CURSE)
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.POISON_DAMAGE, skill_def.dc + actor.bonus_arc) is False
        ):
            target.activate_debuff(DebuffType.POISON_DAMAGE, skill_def.dc + actor.bonus_arc)
            yield [f"{target.param.name}は　毒を浴びてしまった・・・"]
        else:
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield [f"{target.param.name}は　効果をはねのけた！"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DebuffStoneStatue(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_CURSE)
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

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DebuffSleep(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # # 全体効果スキルのターゲット処理見直し
        # # 生存ターゲットチェック
        # living_targets = self._check_living_targets()
        # if not living_targets:
        #     return
        # # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        # current = self._ctx.target
        # target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        for target in self._check_living_targets():
            # di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
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

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DebuffCastPenalty(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

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

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DebuffCharm(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

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

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class AttackInitiativeZero(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]
        yield [""]

        # 戦闘中のＭＰ減少による使用の可否チェック
        if not actor.use_mp(skill_def.cost):
            yield ["しかし　ＭＰが不足している・・・"]
            return

        # 詠唱ロール
        if not actor.castroll(skill_def.dc):
            # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_SHOCK)
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        # ダメージロール
        damage = int(
            (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
            * target.calc_weak_rate(skill_def.skill_type)
        )

        if damage <= 0:
            # px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [f"{target.param.name}の守りを 貫けない！"]
            return

        # 抵抗ロール（弱点属性の場合は必中）
        if (
            target.calc_weak_rate(skill_def.skill_type) > 1.0
            or target.registroll(DebuffType.INITIATIVE_ZERO, skill_def.dc + actor.bonus_arc)
            is False
        ):
            target.activate_debuff(DebuffType.INITIATIVE_ZERO, skill_def.dc + actor.bonus_arc)
            yield [f"{target.param.name}は　吹っ飛ばされた！"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class DispellDebuff(CommandBaseBattle):
    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        skill_def = self.args[0]["skillinfo"]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {skill_def.name} を 詠唱する", "　　・・・・・"]

        if self._ctx.situation == "battle":
            yield [""]

            # 戦闘中のＭＰ減少による使用の可否チェック
            if not actor.use_mp(skill_def.cost):
                yield ["しかし　ＭＰが不足している・・・"]
                return

            # 詠唱ロール
            if actor.castroll(skill_def.dc) is False:
                # px.play(self.se_ch, SoundID.MAGIC_FAIL, resume=True)
                di.ref.sndmgr.play_se_sustain(SoundID.MAGIC_FAIL)
                yield ["呪文は　失敗に終わった・・・"]
                return  # ここで終了
        # else:
        #     # px.play(self.se_ch, SoundID.CAST_LIGHT, resume=True)
        #     di.ref.sndmgr.play_se_sustain(SoundID.CAST_LIGHT)
        #     actor.use_mp(skill_def.cost)
        # di.ref.sndmgr.play_se_sustain(SoundID.CAST_LIGHT)

        actor.use_mp(skill_def.cost)

        # # ダメージロール
        # healing = actor.damageroll_skill(skill_def)
        # # yield [""]

        # real_heal = target.increase_hp(healing)
        # # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        # yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]
        target.clear_all_debuff()
        yield from efx_skill_attack(self.display_info, target, skill_def.def_id)  # type: ignore
        yield [f"{target.param.name}の状態異常は　消え去った！"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned - actor.bonus_end)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒がまわってきた・・・"]


class EnemyEscape(CommandBaseBattle):
    """エネミー専用行動：撤退"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # # triggerに相当：計算はここで完結、yieldでメッセージを渡す

        # # アクターが生存していない場合は終了
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # ファーストメッセージ
        # px.play(self.se_ch, SoundID.ENEMY_ESCAPE, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_ESCAPE)
        yield [f"{actor.param.name}は、 逃げ出したい！", ""]


class EnemySpecial(CommandBaseBattle):
    """エネミー専用行動：特殊攻撃"""

    def _sequence_action(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_status()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}の 特殊攻撃！", ""]


# class DebuffRecoverCheck(CommandBaseBattle):
#     """ターン終了時のデバフ回復チェック"""

#     def _sequence_action(self) -> Generator[list[str], None, None]:
#         yield [self.WAIT, "0"]
#         self.step_wait = -1
#         debuff_name = {
#             DebuffType.REDUCE_DICEVALUE: "呪詛",
#             DebuffType.POISON_DAMAGE: "中毒",
#             DebuffType.STONE_HOLD: "石化",
#             DebuffType.FALL_ASLEEP: "睡眠",
#             DebuffType.DISTURB_MIND: "混乱",
#             DebuffType.CHARM_PERSON: "魅了",
#             DebuffType.INITIATIVE_ZERO: "転倒",
#         }
#         for member in self.allies:
#             recover = member.recoverroll()
#             if len(recover) > 0:
#                 for debuff_id in recover:
#                     yield [f"{member.param.name}は {debuff_name[debuff_id]}状態から回復した"]
#                 self.display_info.target.update_indicator(True)
#                 while self.display_info.target.update() == WindowAction.CONTINUE:
#                     yield [self.WAIT, "0"]
#                 self.display_info.target.update_indicator(False)
#         return
