"""
エンティティコマンドモジュール
"""

import logging
from typing import Generator, cast
from dataclasses import dataclass
import pyxel as px
from const import SoundID
from gameutils.lib import Window, WindowAction

# from helper import diceroll, upper_int
from helper import upper_int
from entity import EntityContext, Enemy, Party, WeakType  # , Character
from skill import SkillTargetType, DebuffType, SkillID
from item import ItemTargetType  # , StackPool  # , ItemState  # , WeaponType
import service_locater as di
from . import CommandBaseSequence, CommandPhase
from .effect_command import (
    efx_diceroll,
    efx_physical_attack,
    efx_damage_shake,
    efx_monster_dead,
    efx_skill_attack,
)


# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseEntity(CommandBaseSequence):
    """エンティティが実行者となるコマンドの基底クラス"""

    def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        super().__init__(wnd, *args, **kwargs)
        self._ctx: EntityContext = ctx

    # def _check_actor_alive(self) -> bool:
    #     """行動前の行動可否チェック"""
    #     if self._ctx.actor.is_alive:
    #         return True
    #     else:
    #         self.step_wait = 0
    #         return False
    def _check_actor_alive(self) -> str:
        """行動前の状態チェック"""
        if not self._ctx.actor.is_alive:
            # self.step_wait = 0
            return f"{self._ctx.actor.param.name}は　意識がトンでいる"
        elif self._ctx.actor.debuff_list.get(DebuffType.STONE_HOLD, None):
            return f"{self._ctx.actor.param.name}は　石の体を　動かせない"
        elif self._ctx.actor.debuff_list.get(DebuffType.FALL_ASLEEP, None):
            return f"{self._ctx.actor.param.name}は　ねむりこけている"
        elif self._ctx.actor.debuff_list.get(DebuffType.CHARM_PERSON, None):
            # ターゲットの変更
            if self._ctx.target in self._ctx.allies:
                ctarget = self._ctx.targets[px.rndi(0, len(self._ctx.targets) - 1)]
            else:
                ctarget = self._ctx.allies[px.rndi(0, len(self._ctx.allies) - 1)]
            callies = self._ctx.allies[:]
            ctargets = self._ctx.targets[:]
            # コンテキストのターゲットを入替
            self._ctx.target = ctarget
            self._ctx.allies = ctargets
            self._ctx.targets = callies
            # return f"{self._ctx.actor.param.name}は　敵にメロメロだ"
        return ""

    def _check_living_targets(self) -> list:
        """行動前の対象生存チェック"""
        # 生存しているターゲットだけをリストアップ
        living_targets = [t for t in self._ctx.targets if t.is_alive]
        # ターゲットが全て生存していない場合は終了
        if not living_targets:
            self.phase = CommandPhase.FIN
            self.step_wait = 0
            return []
        return living_targets


@dataclass
class CommandPackage:
    """Command選択結果のメニュー⇔シーン間受け渡し用パッケージ"""

    selected_action: type[CommandBaseEntity] | None = None
    target_type: SkillTargetType | ItemTargetType | None = None
    selected_args: dict | None = None


class Attack(CommandBaseEntity):
    """エンティティ共通行動：物理攻撃"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return

        # 行動可否チェック
        result = self._check_actor_alive()
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

        # ファーストメッセージ
        yield [f"{actor.param.name}は {target.param.name} に 襲い掛かる！", ""]

        # 命中ロール
        hit = actor.attackroll_offence()
        dodge = target.attackroll_defence()
        judge = hit - dodge
        logger.debug(f"actor={actor.param.name},hit={hit}, dodge={dodge}")
        if judge <= 0:
            # px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield ["だけど、攻撃は かすりもしなかった・・・"]
            return  # ここで終了

        # ダメージロール
        crit_rate = actor.get_critical_rate(judge)
        dice, damage = actor.damageroll_melee()
        yield from efx_diceroll(self.display_info, dice)  # type: ignore
        damage = (damage * crit_rate) - target.suppress_damage_melee()
        weapon_type = actor.get_weapon_type()
        if not weapon_type:
            damage = int(damage * target.calc_guard_rate(weapon_type))

        if damage <= 0:
            # px.play(self.se_ch, SoundID.ATTACK_MISS, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.ATTACK_MISS)
            yield [f"{target.param.name}の かたい防御に はばまれた"]
            return

        # match weapon_type:
        #     case WeaponType.NONE | WeaponType.BASH:
        #         attackse_id = SoundID.BASH
        #     case WeaponType.CHOP | WeaponType.FULL:
        #         attackse_id = SoundID.CHOP
        #     case WeaponType.STUB:
        #         attackse_id = SoundID.STUB
        # # px.play(self.se_ch, attackse_id, resume=True)
        # di.ref.sndmgr.play_se_sustain(attackse_id)
        yield from efx_physical_attack(self.display_info, target, weapon_type)  # type: ignore
        yield from efx_damage_shake(self.display_info, target)  # type: ignore
        yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]

        # run_effectに相当：メッセージ表示後にダメージ適用
        # px.play(self.se_ch, SoundID.DAMAGE_GIVEN, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
        target.decrease_hp(damage)

        if not target.is_alive:
            # cleanupに相当：撃破メッセージ
            # px.play(self.se_ch, SoundID.ENEMY_DEATH, resume=True)
            # di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_DEATH)
            # yield [f"{target.param.name}は 力尽きて ころがった"]
            # while True:
            #     if di.ref.sndmgr.wait_se_fin():
            #         break
            #     yield [self.WAIT, "0"]
            # yield [f"{target.param.name}は 力尽きて ころがった"]
            if isinstance(target, Enemy):
                yield from efx_monster_dead(self.display_info, target)  # type: ignore
                yield [f"{target.param.name}は 力尽きて ころがった"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class UseSkill(CommandBaseEntity):
    """ユーザ行動：スキル使用"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}は、 スキルを使いたがった", ""]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DefenceMode(CommandBaseEntity):
    """ユーザ行動：防御体勢"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]

        actor.defend()
        yield [f"{actor.param.name}の 受けるダメージが 減少する"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class AttackSpellSingle(CommandBaseEntity):
    """単体攻撃魔法"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_BOLT)
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
        di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class AttackSpellArea(CommandBaseEntity):
    """全体攻撃魔法"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
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

            px.play(self.se_ch, SoundID.DAMAGE_GIVEN, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class RecoverSpellSingle(CommandBaseEntity):
    """単体回復呪文"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
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

        real_heal = target.increase_hp(healing)
        # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class RecoverSpellArea(CommandBaseEntity):
    """全体回復呪文"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # 最初に必ず生死チェック
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
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

            real_heal = target.increase_hp(healing)
            # px.play(self.se_ch, SoundID.RECOVER, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
            yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class AttackDisruptUndead(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

            px.play(self.se_ch, SoundID.DAMAGE_GIVEN, resume=True)
            di.ref.sndmgr.play_se_sustain(SoundID.DAMAGE_GIVEN)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DebuffDiceValue(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_CURSE)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DebuffContinualDamage(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_CURSE)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DebuffStoneStatue(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_CURSE)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DebuffSleep(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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
            di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DebuffCastPenalty(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DebuffCharm(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_MIND)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class AttackInitiativeZero(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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

        di.ref.sndmgr.play_se_sustain(SoundID.CAST_SHOCK)
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
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class DispellDebuff(CommandBaseEntity):
    def _sequence(self) -> Generator[list[str], None, None]:
        # 行動可否チェック
        result = self._check_actor_alive()
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
        actor.use_mp(skill_def.cost)

        # # ダメージロール
        # healing = actor.damageroll_skill(skill_def)
        # # yield [""]

        # real_heal = target.increase_hp(healing)
        # # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        # yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]
        target.clear_all_debuff()
        yield [f"{target.param.name}の状態異常は　消え去った！"]

        # 行動後毒ダメージチェック
        poisoned = actor.debuff_list.get(DebuffType.POISON_DAMAGE, None)
        if poisoned:
            yield from efx_skill_attack(self.display_info, actor, SkillID.POISON_CLOUD)  # type: ignore
            actor.decrease_hp(poisoned)
            di.ref.sndmgr.play_se_instant(SoundID.DAMAGE_TAKEN)
            yield [f"{actor.param.name}は 毒で消耗している・・・"]


class EnemyEscape(CommandBaseEntity):
    """エネミー専用行動：撤退"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # triggerに相当：計算はここで完結、yieldでメッセージを渡す

        # # アクターが生存していない場合は終了
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # ファーストメッセージ
        # px.play(self.se_ch, SoundID.ENEMY_ESCAPE, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.ENEMY_ESCAPE)
        yield [f"{actor.param.name}は、 逃げ出したい！", ""]


class EnemySpecial(CommandBaseEntity):
    """エネミー専用行動：特殊攻撃"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # # triggerに相当：計算はここで完結、yieldでメッセージを渡す

        # # アクターが生存していない場合は終了
        # if self._check_actor_alive():
        #     actor = self._ctx.actor
        # else:
        #     return
        # 行動可否チェック
        result = self._check_actor_alive()
        if len(result):
            yield [result]
            return
        actor = self._ctx.actor

        # ファーストメッセージ
        yield [f"{actor.param.name}の 特殊攻撃！", ""]


class GrantReward(CommandBaseEntity):
    """戦闘報酬獲得イベント（エンティティ関連）"""

    def _sequence(self) -> Generator[list[str], None, None]:
        enemy_list = cast(list[Enemy], self._ctx.targets)
        pt: Party = self.args[0]

        # ここで勝利SEとBGMロード
        px.stop()
        # px.play(self.se_ch, SoundID.BATTLE_VICTORY, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.BATTLE_VICTORY)
        yield ["敵との戦闘に　勝利した！！"]
        yield [""]
        # yield [self.WAIT, "1"]  # 勝利SEの長さを文字で返す

        # お金
        reward_gold = sum([enemy.eparam.gold for enemy in enemy_list])
        pt.earn_gold(reward_gold)
        yield [f"パーティーは　{upper_int(reward_gold)}ゴールド　の儲け"]

        # 経験値はメンバー人数割りで死亡者も全員獲得
        reward_exp = sum([enemy.param.exp for enemy in enemy_list])
        num = pt.get_member_count()
        for member in pt.get_allmember():
            getexp = px.ceil(reward_exp / num)
            member.gain_exp(getexp)
            yield [f"{member.param.name}は　経験値{upper_int(getexp)}　を稼いだ！"]

        return


class CharacterInitialHPMP(CommandBaseEntity):
    """キャラメイク時の初期HPとMPの決定"""

    def _sequence(self) -> Generator[list[str], None, None]:
        effect = di.ref.efxdice
        roll_frames = 60
        yield ["初期ＨＰとＭＰを決めるため", "サイコロを２回転がします"]
        yield ["ＨＰサイコロの数は、１＋耐久ボーナス値"]
        dices = 1 + self._ctx.actor.bonus_end
        effect.start(dices, roll_frames)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
            # self.display_info.graphic_command = effect.get_draw_commands()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield ["wait", "0"]
        max_hp = effect.total + self._ctx.actor.endurance
        yield [f"最大ＨＰは {max_hp} になりました"]
        self._ctx.actor.param.max_hp = max_hp
        self._ctx.actor.param.hp = max_hp

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

        yield ["ＭＰサイコロの数は、１＋魔力ボーナス値"]
        dices = 1 + self._ctx.actor.bonus_arc
        effect.start(dices, roll_frames)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
            # self.display_info.graphic_command = effect.get_draw_commands()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield ["wait", "0"]
        max_mp = effect.total + self._ctx.actor.bonus_arc
        yield [f"最大ＭＰは {max_mp} になりました"]
        self._ctx.actor.param.max_mp = max_mp
        self._ctx.actor.param.mp = max_mp

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class CharacterLevelup(CommandBaseEntity):
    """レベルアップメッセージと効果音"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # px.play(self.se_ch, SoundID.LEVEL_UP, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.LEVEL_UP)
        yield [f"{self._ctx.actor.param.name}は　レベルアップ！！", ""]
        return


class CharacterGainHPMP(CommandBaseEntity):
    """レベルアップによるHPとMPの上昇"""

    def _sequence(self) -> Generator[list[str], None, None]:
        yield ["ＨＰの上昇値を決定します", "Ｌｅｔ’ｓ　ｄｉｃｅｒｏｌｌ！"]
        val = yield from efx_diceroll(self.display_info, 1)  # type: ignore
        yield [f"ＨＰが{val} 増えました！"]
        gain = val + self._ctx.actor.bonus_end
        self._ctx.actor.param.max_hp += gain
        self._ctx.actor.param.hp += gain

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

        yield ["ＭＰの上昇値を決定します"]
        val = yield from efx_diceroll(self.display_info, 1)  # type: ignore
        yield [f"ＭＰが{val} 増えました！"]
        gain = val + self._ctx.actor.bonus_arc
        self._ctx.actor.param.max_mp += gain
        self._ctx.actor.param.mp += gain

        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

        return


class DebuffRecoverCheck(CommandBaseEntity):
    """ターン終了時のデバフ回復チェック"""

    def _sequence(self) -> Generator[list[str], None, None]:
        yield [self.WAIT, "0"]
        self.step_wait = -1
        debuff_name = {
            DebuffType.REDUCE_DICEVALUE: "呪詛",
            DebuffType.POISON_DAMAGE: "中毒",
            DebuffType.STONE_HOLD: "石化",
            DebuffType.FALL_ASLEEP: "睡眠",
            DebuffType.DISTURB_MIND: "混乱",
            DebuffType.CHARM_PERSON: "魅了",
            DebuffType.INITIATIVE_ZERO: "転倒",
        }
        for member in self._ctx.allies:
            recover = member.recoverroll()
            if len(recover) > 0:
                for debuff_id in recover:
                    yield [f"{member.param.name}は {debuff_name[debuff_id]}状態から回復した"]
                self.display_info.target.update_indicator(True)
                while self.display_info.target.update() == WindowAction.CONTINUE:
                    yield [self.WAIT, "0"]
                self.display_info.target.update_indicator(False)
        return


# class heal_hp(CommandBaseEntity):
#     """HP回復アイテム"""

#     def _sequence(self) -> Generator[list[str], None, None]:
#         # 最初に必ず生死チェック
#         if self._check_actor_alive():
#             actor = cast(Character, self._ctx.actor)
#         else:
#             return

#         # 生存ターゲットチェック
#         living_targets = self._check_living_targets()
#         if not living_targets:
#             return
#         # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
#         current = self._ctx.target
#         target = current if current.is_alive else living_targets[0]

#         # コマンドパッケージから取得するスキル情報
#         item_def = self.args[0]["item_def"]

#         # ファーストメッセージ
#         yield [
#             f"{actor.param.name}は　{target.param.name}に",
#             f"　{item_def.name} を 使用した",
#         ]

#         # アイテム消費
#         if self._ctx.situation == "battle":
#             slot = self.args[0]["slot"]
#             actor.equipments.use_consume(slot)
#         else:
#             pl_stack = cast(StackPool, self.args[0]["pl_stack"])
#             # pl_stack.remove(item_def.def_id, ItemState.BAG, 1)
#             pl_stack.remove(item_def.def_id)

#         # 回復ロール
#         if item_def.effect_value:
#             healing = target.param.max_hp
#         else:
#             healing = diceroll(actor.param.level)

#         if self._ctx.situation == "battle":
#             yield [""]

#         # run_effectに相当：メッセージ表示後にダメージ適用
#         real_heal = target.increase_hp(healing)
#         # px.play(self.se_ch, SoundID.RECOVER, resume=True)
#         di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
#         yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


# class heal_mp(CommandBaseEntity):
#     """MP回復アイテム"""

#     def _sequence(self) -> Generator[list[str], None, None]:
#         # 最初に必ず生死チェック
#         if self._check_actor_alive():
#             actor = cast(Character, self._ctx.actor)
#         else:
#             return

#         # 生存ターゲットチェック
#         living_targets = self._check_living_targets()
#         if not living_targets:
#             return
#         # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
#         current = self._ctx.target
#         target = current if current.is_alive else living_targets[0]

#         # コマンドパッケージから取得するスキル情報
#         item_def = self.args[0]["item_def"]

#         # ファーストメッセージ
#         yield [
#             f"{actor.param.name}は　{target.param.name}に",
#             f"　{item_def.name} を 使用した",
#         ]

#         # アイテム消費
#         if self._ctx.situation == "battle":
#             slot = self.args[0]["slot"]
#             actor.equipments.use_consume(slot)
#         else:
#             pl_stack = cast(StackPool, self.args[0]["pl_stack"])
#             # pl_stack.remove(item_def.def_id, ItemState.BAG, 1)
#             pl_stack.remove(item_def.def_id)

#         # 回復ロール
#         if item_def.effect_value:
#             healing = target.param.max_hp
#         else:
#             healing = diceroll(actor.param.level)

#         if self._ctx.situation == "battle":
#             yield [""]

#         # run_effectに相当：メッセージ表示後にダメージ適用
#         real_heal = target.increase_mp(healing)
#         # px.play(self.se_ch, SoundID.RECOVER, resume=True)
#         di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
#         yield [f"{target.param.name}は {upper_int(real_heal)} のＭＰが　回復した"]
