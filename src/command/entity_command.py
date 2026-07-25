"""
エンティティコマンドモジュール
"""
import logging

# from collections import deque
# from abc import abstractmethod
from typing import Generator, cast  # , Any
from dataclasses import dataclass
import pyxel as px
from const import COMMAND_STEPWAIT_FRAME, SoundID
from gameutils.lib import Window  # , WindowAction
from helper import diceroll, upper_int
from entity import EntityContext, Enemy, Party, Character
from skill import SkillTargetType
from item import ItemTargetType, StackPool, ItemState, WeaponType

# from . import CommandBase, CommandPhase, DisplayInfo
from . import CommandBaseSequence, CommandPhase, DisplayInfo
from .effect_command import efx_diceroll

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseEntity(CommandBaseSequence):
    """エンティティが実行者となるコマンドの基底クラス"""

    # WAIT = "wait"  # 待機を示すリターンコマンド

    def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        self._ctx: EntityContext = ctx
        self.display_info: DisplayInfo = DisplayInfo(wnd)
        self.step_wait = COMMAND_STEPWAIT_FRAME  # メッセージ待ち間隔
        self.se_no = 0  # サウンドエフェクトの番号
        self.args = args
        self.kwargs = kwargs
        self.phase = CommandPhase.SYN

    def _check_actor_alive(self) -> bool:
        """行動前の行動可否チェック"""
        if self._ctx.actor.is_alive:
            return True
        else:
            self.step_wait = 0  # COMMAND_STEPWAIT_FRAME//2
            return False

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

    # @abstractmethod
    # def _sequence(self) -> Generator[list[str], None, None]:
    #     ...
    #     # """サブクラスが実装すべき処理シーケンス"""

    # def update(self) -> CommandPhase:
    #     match self.phase:
    #         case CommandPhase.SYN:
    #             self.display_info.target.message_list.clear()
    #             self._gen = self._sequence()
    #             self._advance()
    #             self.phase = CommandPhase.ACK
    #         case CommandPhase.ACK:
    #             if (
    #                 self.display_info.target.update() == WindowAction.DISCARD
    #                 or self.step_wait < 0
    #             ):
    #                 self._advance()
    #             self.step_wait -= 1
    #     return self.phase

    # def _advance(self):
    #     try:
    #         result = next(self._gen)
    #         if result:
    #             if result[0] == self.WAIT:
    #                 self.step_wait = int(result[1]) * COMMAND_STEPWAIT_FRAME
    #             else:
    #                 self.display_info.message = result
    #                 self.display_info.is_change = True
    #                 self.step_wait = COMMAND_STEPWAIT_FRAME
    #         else:
    #             self.step_wait = 0
    #     except StopIteration:
    #         self.phase = CommandPhase.FIN

    # def draw(self) -> DisplayInfo:
    #     """コマンド描画情報送信"""
    #     return self.display_info


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
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

        # # 生存しているターゲットだけをリストアップ
        # living_targets = [t for t in self._ctx.targets if t.is_alive]
        # # ターゲットが全て生存していない場合は終了
        # if not living_targets:
        #     self.phase = CommandPhase.FIN
        #     self.step_wait = 0
        #     return
        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        # current = self._ctx.targets[self._ctx.target_index]
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # ファーストメッセージ
        yield [f"{actor.param.name}は {target.param.name} に 襲い掛かる！", ""]

        # 命中ロール
        judge = actor.hitroll_offence() - target.hitroll_defence()
        if judge <= 0:
            px.play(3, SoundID.ATTACK_MISS, resume=True)
            yield ["だけど、攻撃は かすりもしなかった・・・"]
            return  # ここで終了

        # ダメージロール
        crit_rate = actor.get_critical_rate(judge)
        dice, damage = actor.damageroll_melee()
        yield from efx_diceroll(self.display_info, dice)
        damage = (damage * crit_rate) - target.suppress_damage_melee()
        weapon_type = actor.get_weapon_type()
        if not weapon_type:
            damage = int(damage * target.calc_guard_rate(weapon_type))

        if damage <= 0:
            px.play(3, SoundID.ATTACK_MISS, resume=True)
            yield [f"{target.param.name}の かたい防御に はばまれた"]
            return

        match weapon_type:
            case WeaponType.NONE | WeaponType.BASH:
                attackse_id = SoundID.BASH
            case WeaponType.CHOP | WeaponType.FULL:
                attackse_id = SoundID.CHOP
            case WeaponType.STUB:
                attackse_id = SoundID.STUB
        px.play(3, attackse_id, resume=True)
        yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]

        # run_effectに相当：メッセージ表示後にダメージ適用
        px.play(3, SoundID.DAMAGE_GIVEN, resume=True)
        target.decrease_hp(damage)

        if not target.is_alive:
            # cleanupに相当：撃破メッセージ
            px.play(3, SoundID.ENEMY_DEATH, resume=True)
            yield [f"{target.param.name}は 力尽きて ころがった"]


# class UseItem(CommandBaseEntity):

#     """ユーザ行動：防御体勢"""

#     def _sequence(self) -> Generator[list[str], None, None]:
#         if self._check_actor_alive():
#             actor = self._ctx.actor
#         else:
#             return

#         # ファーストメッセージ
#         yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]

#         actor.defend()
#         yield [f"{actor.param.name}の 受けるダメージが 減少する"]


class UseSkill(CommandBaseEntity):

    """ユーザ行動：スキル使用"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

        # ファーストメッセージ
        yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]

        actor.defend()
        yield [f"{actor.param.name}の 受けるダメージが 減少する"]


class DefenceMode(CommandBaseEntity):

    """ユーザ行動：防御体勢"""

    def _sequence(self) -> Generator[list[str], None, None]:
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

        # ファーストメッセージ
        yield [f"{actor.param.name}は、 防御の体勢をとっている", ""]

        actor.defend()
        yield [f"{actor.param.name}の 受けるダメージが 減少する"]


class AttackSpellSingle(CommandBaseEntity):
    """単体攻撃魔法"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

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
            px.play(3, SoundID.MAGIC_FAIL, resume=True)
            yield ["呪文は　失敗に終わった・・・"]
            return  # ここで終了

        # ダメージロール
        damage = int(
            (actor.damageroll_skill(skill_def) - target.suppress_damage_skill())
            * target.calc_weak_rate(skill_def.def_id)
        )

        if damage <= 0:
            px.play(3, SoundID.ATTACK_MISS, resume=True)
            yield [f"{target.param.name}の守りを 貫けない！"]
            return

        px.play(3, SoundID.DAMAGE_GIVEN, resume=True)
        yield [f"{target.param.name}に {upper_int(damage)} ポイントの ダメージ！"]

        # run_effectに相当：メッセージ表示後にダメージ適用
        target.decrease_hp(damage)

        if not target.is_alive:
            # cleanupに相当：撃破メッセージ
            px.play(3, SoundID.ENEMY_DEATH, resume=True)
            yield [f"{target.param.name}は 力尽きて ころがった"]


class RecoverSpellSingle(CommandBaseEntity):
    """単体回復呪文"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

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
            if not actor.castroll(skill_def.dc):
                px.play(3, SoundID.MAGIC_FAIL, resume=True)
                yield ["呪文は　失敗に終わった・・・"]
                return  # ここで終了
        else:
            px.play(3, SoundID.CAST_LIGHT, resume=True)
            actor.use_mp(skill_def.cost)

        # ダメージロール
        healing = actor.damageroll_skill(skill_def)
        # yield [""]

        real_heal = target.increase_hp(healing)
        px.play(3, SoundID.RECOVER, resume=True)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]

        # if not target.is_alive:
        #     # cleanupに相当：撃破メッセージ
        #     yield [f"{target.param.name}は 力尽きて ころがった"]


class EnemyEscape(CommandBaseEntity):
    """エネミー専用行動：撤退"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # triggerに相当：計算はここで完結、yieldでメッセージを渡す

        # アクターが生存していない場合は終了
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

        # ファーストメッセージ
        px.play(3, SoundID.ENEMY_ESCAPE, resume=True)
        yield [f"{actor.param.name}は、 逃げ出したい！", ""]


class EnemySpecial(CommandBaseEntity):
    """エネミー専用行動：特殊攻撃"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # triggerに相当：計算はここで完結、yieldでメッセージを渡す

        # アクターが生存していない場合は終了
        if self._check_actor_alive():
            actor = self._ctx.actor
        else:
            return

        # ファーストメッセージ
        yield [f"{actor.param.name}の 特殊攻撃！", ""]


class GrantReward(CommandBaseEntity):
    """戦闘報酬獲得イベント（エンティティ関連）"""

    def _sequence(self) -> Generator[list[str], None, None]:
        enemy_list = cast(list[Enemy], self._ctx.targets)
        pt: Party = self.args[0]

        # ここで勝利SEとBGMロード
        px.play(3, SoundID.BATTLE_VICTORY, resume=True)
        yield ["敵との戦闘に　勝利した！！"]
        yield [""]
        yield [self.WAIT, "1"]  # 勝利SEの長さを文字で返す

        # お金
        reward_gold = sum([enemy.eparam.gold for enemy in enemy_list])
        pt.earn_gold(reward_gold)
        yield [f"パーティーは　{reward_gold}ゴールド　の儲け"]

        # 経験値はメンバー人数割りで死亡者も全員獲得
        reward_exp = sum([enemy.param.exp for enemy in enemy_list])
        num = pt.get_member_count()
        for member in pt.get_allmember():
            getexp = px.ceil(reward_exp / num)
            member.gain_exp(getexp)
            yield [f"{member.param.name}は　経験値{getexp}　を稼いだ！"]

        return


class heal_hp(CommandBaseEntity):
    """HP回復アイテム"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = cast(Character, self._ctx.actor)
        else:
            return

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        item_def = self.args[0]["item_def"]

        # ファーストメッセージ
        yield [
            f"{actor.param.name}は　{target.param.name}に",
            f"　{item_def.name} を 使用した",
        ]

        # アイテム消費
        if self._ctx.situation == "battle":
            slot = self.args[0]["slot"]
            actor.equipments.use_consume(slot)
        else:
            pl_stack = cast(StackPool, self.args[0]["pl_stack"])
            pl_stack.remove(item_def.def_id, ItemState.BAG, 1)

        # 回復ロール
        if item_def.effect_value:
            healing = target.param.max_hp
        else:
            healing = diceroll(actor.param.level)

        if self._ctx.situation == "battle":
            yield [""]

        # run_effectに相当：メッセージ表示後にダメージ適用
        real_heal = target.increase_hp(healing)
        px.play(3, SoundID.RECOVER, resume=True)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


class heal_mp(CommandBaseEntity):
    """MP回復アイテム"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = cast(Character, self._ctx.actor)
        else:
            return

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        item_def = self.args[0]["item_def"]

        # ファーストメッセージ
        yield [
            f"{actor.param.name}は　{target.param.name}に",
            f"　{item_def.name} を 使用した",
        ]

        # アイテム消費
        if self._ctx.situation == "battle":
            slot = self.args[0]["slot"]
            actor.equipments.use_consume(slot)
        else:
            pl_stack = cast(StackPool, self.args[0]["pl_stack"])
            pl_stack.remove(item_def.def_id, ItemState.BAG, 1)

        # 回復ロール
        if item_def.effect_value:
            healing = target.param.max_hp
        else:
            healing = diceroll(actor.param.level)

        if self._ctx.situation == "battle":
            yield [""]

        # run_effectに相当：メッセージ表示後にダメージ適用
        real_heal = target.increase_mp(healing)
        px.play(3, SoundID.RECOVER, resume=True)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＭＰが　回復した"]
