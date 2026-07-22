"""
システムコマンドモジュール
"""
import logging

# from abc import abstractmethod
from typing import Generator
import pyxel as px
from gameutils.lib import WindowAction  # , Window,

# from const import COMMAND_STEPWAIT_FRAME
# from . import CommandBase, CommandPhase, DisplayInfo
from . import CommandBaseSequence

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseSystem(CommandBaseSequence):
    """システムに対するユーザ操作を表すコマンドの基底クラス"""

    pass
    # WAIT = "wait"  # 待機を示すリターンコマンド

    # def __init__(self, wnd: Window, *args, **kwargs) -> None:
    #     """初期化：コンテキストの引継"""
    #     self.display_info: DisplayInfo = DisplayInfo(wnd)
    #     self.step_wait = COMMAND_STEPWAIT_FRAME  # メッセージ待ち間隔
    #     self.se_no = 0  # サウンドエフェクトの番号
    #     self.args = args
    #     self.kwargs = kwargs
    #     self.phase = CommandPhase.SYN

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


class BattleStartEffect(CommandBaseSystem):
    """戦闘開始エフェクト"""

    def _sequence(self) -> Generator[list[str], None, None]:
        circle_size = 1
        circle_center = (px.width // 2, px.height // 2)
        circle_max = px.sqrt(circle_center[0] ** 2 + circle_center[1] ** 2)

        while circle_size < circle_max:
            # px.dither(circle_size / circle_max)

            self.display_info.graphic_command = [
                lambda: px.dither(circle_size / circle_max),
                # lambda: px.dither(0.1),
                lambda: px.circ(*circle_center, circle_size, px.COLOR_BLACK),
                lambda: px.dither(1),
            ]
            # px.dither(1)
            circle_size += 6
            yield [self.WAIT, "0"]

        # # ここで勝利SEとBGMロード
        # len_fanfale = "1"
        # yield ["敵との戦闘に　勝利した！！"]
        # yield [""]
        # yield [self.WAIT, len_fanfale]  # 勝利SEの長さを文字で返す

        # # お金
        # reward_gold = sum([enemy.eparam.gold for enemy in enemy_list])
        # pt.earn_gold(reward_gold)
        # yield [f"パーティーは　{reward_gold}ゴールド　の儲け"]

        # # 経験値はメンバー人数割りで死亡者も全員獲得
        # reward_exp = sum([enemy.param.exp for enemy in enemy_list])
        # num = pt.get_member_count()
        # for member in pt.get_allmember():
        #     getexp = px.ceil(reward_exp / num)
        #     member.gain_exp(getexp)
        #     yield [f"{member.param.name}は　経験値{getexp}　を稼いだ！"]

        return


class FoodShortageMessage(CommandBaseSystem):
    """フードが消費量に満たない場合の警告"""

    def _sequence(self) -> Generator[list[str], None, None]:
        yield [
            "食糧が　足りなくなった",
            "ターン経過毎に ＨＰとＭＰが５％ずつ",
            "減少してしまう・・・",
        ]
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]


class FoodShortageEffect(CommandBaseSystem):
    """フードが消費量に満たない場合の画面エフェクト"""

    def _sequence(self) -> Generator[list[str], None, None]:
        self.display_info.graphic_command = [
            lambda: px.dither(0.5),
            lambda: px.rect(0, 0, px.width, px.height, px.COLOR_RED),
            lambda: px.dither(1),
        ]
        yield [self.WAIT, "0"]
