"""
Command系基底クラス

コマンド関連クラスの契約となる抽象クラス
"""

# from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generator
from gameutils.lib import Window, WindowAction
from const import COMMAND_STEPWAIT_FRAME
from . import CommandPhase, DisplayInfo


class CommandBase(ABC):
    """コマンド基底クラス"""

    phase: CommandPhase

    @abstractmethod
    def update(self) -> CommandPhase:
        ...

    @abstractmethod
    def draw(self) -> DisplayInfo:
        ...


class CommandBaseSequence(CommandBase):
    """_sequenceジェネレータを持つコマンドの共通実装"""

    WAIT = "wait"  # 待機を示すリターンコマンド

    def __init__(self, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        self.display_info: DisplayInfo = DisplayInfo(wnd)
        self.step_wait = COMMAND_STEPWAIT_FRAME  # メッセージ待ち間隔
        self.se_ch = 3  # サウンドエフェクトのチャンネル番号
        self.args = args
        self.kwargs = kwargs
        self.phase = CommandPhase.SYN

    @abstractmethod
    def _sequence(self) -> Generator[list[str], None, None]:
        ...
        # """サブクラスが実装すべき処理シーケンス"""

    def update(self) -> CommandPhase:
        match self.phase:
            case CommandPhase.SYN:
                self.display_info.target.message_list.clear()
                self._gen = self._sequence()
                self._advance()
                self.phase = CommandPhase.ACK
            case CommandPhase.ACK:
                if (
                    self.display_info.target.update() == WindowAction.DISCARD
                    or self.step_wait < 0
                ):
                    self._advance()
                self.step_wait -= 1
        return self.phase

    def _advance(self):
        try:
            result = next(self._gen)
            if result:
                if result[0] == self.WAIT:
                    self.step_wait = int(result[1]) * COMMAND_STEPWAIT_FRAME
                else:
                    self.display_info.message = result
                    self.display_info.is_change = True
                    self.step_wait = COMMAND_STEPWAIT_FRAME
            else:
                self.step_wait = 0
        except StopIteration:
            self.phase = CommandPhase.FIN

    def draw(self) -> DisplayInfo:
        """コマンド描画情報送信"""
        return self.display_info
