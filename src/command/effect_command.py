"""
エフェクトコマンドモジュール
"""
import logging
import pyxel as px
from const import SoundID

# from abc import abstractmethod
from typing import Generator  # , Callable,

import service_locater as di
from . import DisplayInfo

# from effect import DiceRollEffect


# ロギング設定
logger = logging.getLogger(__name__)


# class CommandBaseEffect(CommandBaseSequence):
#     """エフェクト系コマンドの基底クラス"""

#     # @abstractmethod
#     # def get_draw_commands(self) -> list[Callable[[], None]]:
#     #     ...

#     # def draw(self) -> DisplayInfo:
#     #     # draw()はget_draw_commandsの結果をDisplayInfoに詰めるだけ
#     #     self.display_info.graphic_command = self.get_draw_commands()
#     #     return self.display_info
#     pass


# class DiceRoll(CommandBaseEffect):

# #     def get_draw_commands(self):

#     # def _effect_diceroll(dices: int) -> Generator[list[str], None, None]:
#     def _sequence(self) -> Generator[list[str], None, None]:
#         self.effect = DiceRollEffect()

#         self.effect.start(self.args[0])
#         while self.effect.is_rolling:
#             self.effect.update()
#             self.display_info

#         yield [self.WAIT, "0"]


#     def get_draw_commands(self) -> list[Callable[[], None]]:
#         return self.effect.get_draw_commands()


# class KickEvent(CommandBaseEffect):
#     """フィールドイベント起動処理"""

#     def _sequence(self) -> Generator[list[str], None, None]:
#         point = cast(EventPoint, self.args[0])
#         dices = point.kick_event()
#         # effect = DiceRollEffect()
#         # effect.load_diceimage()
#         effect = di.ref.efxdice
#         roll_frames = 60
#         effect.start(dices, roll_frames)
#         yield ["何が起こるか", "　おたのしみ！"]
#         while effect.is_rolling:
#             effect.update()
#             self.display_info.graphic_command = effect.get_draw_commands()
#             yield ["wait", "0"]
#         yield [f"出た目は・・・　{effect.total}"]
#         while self.display_info.target.update() == WindowAction.CONTINUE:
#             yield [self.WAIT, "0"]
#         for event_id, event_stat in point.event_list.event_stat.items():
#             if effect.total >= event_stat.threshold:
#                 event_stat.is_opened = True
#                 point.rise_event(event_id)
#                 break


def efx_diceroll(
    disp_info: DisplayInfo, dices: int
) -> Generator[list[str], None, None]:
    """コマンドジェネレータからダイスロールを実行する為のヘルパー関数"""
    # effect = DiceRollEffect()
    # effect.load_diceimage()
    effect = di.ref.efxdice
    effect.start(dices)
    se_ch = 3
    px.play(se_ch, SoundID.DICE_ROLL, resume=True)
    while effect.is_rolling:
        effect.update()
        disp_info.graphic_command = effect.get_draw_commands()
        yield ["wait", "0"]
    disp_info.graphic_command = None
    effect = None
