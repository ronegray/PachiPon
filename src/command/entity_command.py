"""
エンティティコマンドモジュール
"""
import logging
from collections import deque
import pyxel as px
from gameutils.lib import Window, WindowAction
from helper import diceroll, upper_int
from const import BATTLE_MESSAGE_FRAME
from entity import EntityContext
from . import CommandBase, CommandPhase, DisplayInfo

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseEntity(CommandBase):
    """エンティティが実行者となるコマンドの基底クラス"""

    def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        self._ctx: EntityContext = ctx
        self.display_info: DisplayInfo = DisplayInfo(wnd)
        self.message_queue: deque[str] = deque()  # メッセージキュー
        self.message_wait = BATTLE_MESSAGE_FRAME  # メッセージ待ち間隔
        self.se_no = 0  # サウンドエフェクトの番号
        self.args = args
        self.kwargs = kwargs
        self.phase = CommandPhase.SYN
        self.params: dict = {}  # コマンド毎に自由に使うパラメタ格納変数
        # self.trigger()

    def trigger(self):
        """エンティティの行動で最初に一度だけ処理するもの"""
        raise NotImplementedError("trigger関数が未定義です")

    def run_effect(self):
        """エンティティの行動で一度だけ効果を発揮するもの"""
        pass

    def cleanup(self):
        """コマンド自体の処理完了後に行う処理"""
        pass

    def check_actor_state(self) -> bool:
        """行動前の行動可否チェック"""
        if self._ctx.actor.is_alive:
            return True
        else:
            self.message_queue.append(f"{self._ctx.actor.param.name}は　倒れ伏している")
            # self.message_queue.append(" ")
            return False

    def update(self) -> CommandPhase:
        """コマンド状況推移"""

        def step_check() -> bool:
            return (
                self.display_info.target.update() == WindowAction.DISCARD
            ) or self.message_wait < 0

        try:
            match self.phase:
                case CommandPhase.SYN:
                    # logger.info(f"\n{self._ctx.actor} {self.phase} {self.display_info.message}")
                    self.display_info.target.text_list.clear()
                    self.trigger()
                    if self.phase == CommandPhase.FINACK:
                        return CommandPhase.FINACK
                    self.display_info.message = [
                        self.message_queue.popleft(),
                        #  self.message_queue.popleft()]
                        " ",
                    ]
                    # px.play(3, self.se_no, resume=True)
                    self.display_info.is_change = True
                    self.phase = CommandPhase.SYNACK
                case CommandPhase.SYNACK:
                    self.phase = CommandPhase.ACK
                case CommandPhase.ACK:
                    if step_check():
                        if not self.message_queue:
                            self.run_effect()
                            self.phase = CommandPhase.FINACK
                            # self.display_info.target.text_list.clear()
                        else:
                            self.display_info.message = [self.message_queue.popleft()]
                            self.display_info.is_change = True
                            self.message_wait = BATTLE_MESSAGE_FRAME
                case CommandPhase.FINACK:
                    self.cleanup()
                    if step_check():
                        self.phase = CommandPhase.FIN
                        # self.display_info.target.text_list.clear()
                case CommandPhase.FIN:
                    if step_check():
                        self.display_info.message = [self.message_queue.popleft()]
                    pass
        except Exception as e:
            print(f"\n{self._ctx}\n{e}")

        self.message_wait -= 1
        return self.phase

    def draw(self) -> DisplayInfo:
        """コマンド描画情報送信"""
        return self.display_info


class Attack(CommandBaseEntity):

    """エンティティ共通行動：物理攻撃"""

    """コマンドの流れ（「」内はメッセージ表示）
    - 「actorがtargetに攻撃！」
      - actorとtargetの設定
    - 攻撃の命中判定（計算）
      - 失敗の場合、「攻撃は外れた」
      - 成功の場合
        - ダメージ値の計算
        - actorはtargetに〇のダメージ」
    """

    def trigger(self) -> None:
        actor = self._ctx.actor
        if not self.check_actor_state():
            return
        if self._ctx.targets[self._ctx.target_index].is_alive:
            target = self._ctx.targets[self._ctx.target_index]
        else:
            is_alive = False
            for i, candidate in enumerate(self._ctx.targets):
                if candidate.is_alive:
                    target = self._ctx.targets[i]
                    is_alive = True
                    break
            if not is_alive:
                # logger.info(f"\nアクター{self._ctx.actor.param.name}のターゲットは全滅")
                self.phase = CommandPhase.FINACK
                return
        # 命中ロール
        offence = actor.hitroll_offence()
        defence = target.hitroll_defence()
        judge = offence - defence
        self.message_queue.append(
            f"{actor.param.name}は　{target.param.name}　に　襲い掛かる！"
        )
        # self.message_queue.append(" ")
        if judge <= 0:
            # 攻撃はずれ
            self.message_queue.append("だけど、　攻撃は　失敗した")
        else:
            # ダメージロール
            crit_rate = actor.get_critical_rate(judge)
            damage = (
                actor.damageroll_melee() * crit_rate
            ) - target.suppress_damage_melee()
            try:
                weapon_type = actor.get_weapon_type()
                damage *= target.calc_guard_rate(weapon_type)
            except AttributeError:
                pass

            damage = int(damage)
            if damage > 0:
                self.message_queue.append(
                    f"{target.param.name}に　{upper_int(damage)}　ポイントの　ダメージ！"
                )
                # target.decrease_hp(damage)
                # run_effectへ実ダメージ処理を引き渡す為のパラメタ
                self.params["target"] = target
                self.params["damage"] = damage
            else:
                self.message_queue.append(
                    f"{target.param.name}に　ダメージを　与えられなかった"
                )
        # self.phase = CommandPhase.ACK

    def run_effect(self):
        """ダメージ値があれば減算処理"""
        damage = self.params.get("damage", 0)
        if damage > 0:
            self.params["target"].decrease_hp(damage)
            if not self.params["target"].is_alive:
                #     self.display_info.is_change = True
                #     self.message_queue.append(f"{self.params["target"].param.name}は　倒れ伏した")
                #     self.display_info.message = [self.message_queue.popleft()]
                self.params["dead"] = True

    def cleanup(self):
        if self.params.get("dead", False):
            self.params["dead"] = False
            self.display_info.is_change = True
            self.message_queue.append(
                f"{self.params["target"].param.name}は　倒れ伏した"
            )
            self.display_info.message = [self.message_queue.popleft()]
            self.message_wait = BATTLE_MESSAGE_FRAME

    # def cleanup(self):
    #     """全滅チェック"""
    #     if self.params.get("wipeout", None) is None:
    #         for target in self._ctx.targets:
    #             if target.is_alive:
    #                 # 攻撃処理なので味方側増減は無い想定
    #                 return
    #         if self._ctx.actor.id < ENEMY_ID_BASE:
    #             self.message_queue.append("全ての敵を　ぶっころした！")
    #             self.display_info.message = [self.message_queue.popleft()]
    #             self.params["wipeout"] = 0
    #         else:
    #             self.message_queue.append("パーティは　全滅した・・・")
    #             self.display_info.message = [self.message_queue.popleft()]
    #             self.params["wipeout"] = 1
    #         self.display_info.is_change = True
    #         self.message_wait = BATTLE_MESSAGE_FRAME


class UseItem(CommandBaseEntity):
    ...


class UseSkill(CommandBaseEntity):
    ...


class DefenceMode(CommandBaseEntity):

    """ユーザ行動：防御体勢"""

    def trigger(self) -> None:
        actor = self._ctx.actor
        if not self.check_actor_state():
            return
        # 実際の防御効果
        actor.defend()
        self.message_queue.append(f"{actor.param.name}は、　防御の体勢をとった")
        self.message_queue.append(" ")
        # self.message_queue.append(f"{actor.param.name}の受けるダメージが減少する")
        self.se_no = 50

        # self.phase = CommandPhase.SYN

    def run_effect(self):
        """防御効果メッセージを追加"""
        self.message_queue.append("受けるダメージが　減少する")


class AttackSpellSingle(CommandBaseEntity):
    def update(self) -> CommandPhase:
        ...

    def draw(self) -> DisplayInfo:
        ...


class RecoverSpellSingle(CommandBaseEntity):
    """単体回復呪文"""

    def trigger(self) -> None:
        """コマンド起動時一回性処理"""
        self.skill_def = self.args[0]
        self.message_window: Window = Window("basic", 0, 116, 240, 32, "once")
        self.display_info = DisplayInfo(self.message_window)
        # MP残量チェック
        if self._ctx.actor.use_mp(self.skill_def.cost):
            heal_val = diceroll(int(self.skill_def.effect_value))
            real_val = self._ctx.allies[0].increase_hp(heal_val)
            self.message_window.set_message([f"ＨＰが{real_val}回復しました"])
            px.play(3, 63)
        else:
            self.message_window.set_message(["ＭＰが足りません"])

        # self.phase = CommandPhase.SYN

    def update(self) -> CommandPhase:
        """コマンド応答待ち"""
        if self.phase == CommandPhase.ACK:
            if self.display_info.target.update() == WindowAction.DISCARD:
                return CommandPhase.FIN
        else:
            self.phase = CommandPhase.ACK
        return self.phase

    def draw(self) -> DisplayInfo:
        """コマンド描画情報送信"""
        return self.display_info


# class EnemyAttack(CommandBaseEntity):

#     """エネミー行動：物理攻撃"""
#     def trigger(self) -> None:
#         # self.countdown_timer = 60
#         actor = self._ctx.actor
#         if self._ctx.targets[self._ctx.target_index].is_alive:
#             target = self._ctx.targets[0]
#         else:
#             for i, candidate in enumerate(self._ctx.targets):
#                 if candidate.is_alive:
#                     target = self._ctx.targets[i]
#                     break
#             return
#         # self.display_info = DisplayInfo(self.args[0])
#         # 命中ロール
#         offence = actor.hitroll_offence()
#         defence = target.hitroll_defence()
#         judge = offence - defence
#         # self.display_info.message = [f"{actor.param.name}は　{target.param.name}　に　襲い掛かる！"]
#         self.message_queue.append(f"{actor.param.name}は　{target.param.name}　に　襲い掛かる！")
#         self.message_queue.append(" ")
#         if judge <= 0:
#             # 攻撃はずれ
#             # self.display_info.message += ["だけど、　攻撃は　失敗した"]
#             self.message_queue.append("だけど、　攻撃は　失敗した")
#         else:
#             # ダメージロール
#             crit_rate = actor.get_critical_rate(judge)
#             damage = ((actor.damageroll_melee() * crit_rate)
#                       - target.suppress_damage_melee())
#             if damage > 0:

#                 # self.display_info.message += [f"{actor.param.name}は、{target.param.name}に",
#                 #                             f"{damage}　ポイントの　ダメージを　与えた"]
#                 self.message_queue.append(f"{actor.param.name}は、{target.param.name}に")
#                 self.message_queue.append(f"{damage}　ポイントの　ダメージを　与えた")
#                 target.decrease_hp(damage)
#                 if not target.is_alive:
#                     self.message_queue.append(f"{target.param.name}　は　おっちんだ")
#             else:
#                 # self.display_info.message += [f"{actor.param.name}は、{target.param.name}に",
#                 #                             "ダメージを　与えられなかった"]
#                 self.message_queue.append(f"{actor.param.name}は、{target.param.name}に")
#                 self.message_queue.append("ダメージを　与えられなかった")
#         # self.phase = CommandPhase.SYN

#     # def update(self) -> CommandPhase:
#     #     """コマンド応答待ち"""
#     #     if self.phase == CommandPhase.ACK:
#     #         if self.display_info.target.update() == WindowAction.DISCARD:
#     #             return CommandPhase.FIN
#     #     else:
#     #         self.phase = CommandPhase.ACK
#     #     return self.phase

#     # def draw(self) -> DisplayInfo:
#     #     """コマンド描画情報送信"""
#     #     return self.display_info


class EnemyEscape(CommandBaseEntity):
    """エネミー専用行動：撤退"""

    def trigger(self) -> None:
        ...


class EnemySpecial(CommandBaseEntity):
    """エネミー専用行動：特殊攻撃"""

    def trigger(self) -> None:
        ...


class GrantReward(CommandBaseEntity):
    def trigger(self) -> None:
        enemy_list = self._ctx.targets
        pt = self.args[0]

        self.message_queue.append("敵との戦闘に　勝利した！！")
        # ここで勝利SEとBGMロード

        # お金
        reward_gold = sum([enemy.eparam.gold for enemy in enemy_list])
        pt.earn_gold(reward_gold)
        self.message_queue.append(f"パーティーは　{reward_gold}ゴールド　の儲け")
        # 経験値はメンバー人数割りで死亡者も全員獲得
        reward_exp = sum([enemy.param.exp for enemy in enemy_list])
        num = pt.get_member_count()
        for member in pt.get_allmember():
            getexp = px.ceil(reward_exp / num)
            member.gain_exp(getexp)
            self.message_queue.append(
                f"{member.param.name}は　経験値{getexp}　を稼いだ！"
            )

    def update(self) -> CommandPhase:
        def step_check() -> bool:
            return (
                self.display_info.target.update() == WindowAction.DISCARD
            ) or self.message_wait < 0

        try:
            match self.phase:
                case CommandPhase.SYN:
                    self.display_info.target.text_list.clear()
                    self.trigger()
                    self.display_info.message = [self.message_queue.popleft(), " "]
                    self.display_info.is_change = True
                    self.phase = CommandPhase.ACK
                case CommandPhase.ACK:
                    if step_check():
                        if not self.message_queue:
                            self.run_effect()
                            self.phase = CommandPhase.FINACK
                            # self.display_info.target.text_list.clear()
                        else:
                            self.display_info.message = [self.message_queue.popleft()]
                            self.display_info.is_change = True
                            self.message_wait = BATTLE_MESSAGE_FRAME
                case CommandPhase.FINACK:
                    self.cleanup()
                    self.phase = CommandPhase.FIN

            return self.phase
        except Exception as e:
            print(f"\n{self._ctx}\n{e}")
            return CommandPhase.FIN

    def cleanup(self):
        cmd = self.args[1]
        cmd()
