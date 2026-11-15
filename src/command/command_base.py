"""
Command系基底クラス

コマンド関連クラスの契約となる抽象クラス
"""

from abc import ABC, abstractmethod
from typing import Generator
from enum import StrEnum
import service_locater as di
from gameutils.lib import Window, WindowAction

from const import SoundID
from config import CONF_TEXT_SPEED
from . import CommandPhase, DisplayInfo


class CommandProtocol(ABC):
    """コマンド基底クラス"""

    phase: CommandPhase

    @abstractmethod
    def update(self) -> CommandPhase:
        ...

    @abstractmethod
    def draw(self) -> DisplayInfo:
        ...


class SeqSubCmd(StrEnum):
    """データ側に持たせるサブコマンド文字列"""

    WAIT = "WAIT"
    SE_SUSTAIN = "SE_SUSTAIN"
    SE_INSTANT = "SE_INSTANT"


class CommandBaseSequence(CommandProtocol):
    """_sequenceジェネレータを持つコマンドの共通実装"""

    def __init__(self, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        self.display_info: DisplayInfo = DisplayInfo(wnd)
        self._local_waitframe = CONF_TEXT_SPEED[di.ref.conf.text_speed]["args"][1]
        self.step_wait = self._local_waitframe  # メッセージ待ち間隔
        # self.se_ch = 3  # サウンドエフェクトのチャンネル番号
        self.args = args
        self.kwargs = kwargs
        self.phase = CommandPhase.SYN
        self.se_cmd = {
            SeqSubCmd.SE_SUSTAIN: di.ref.sndmgr.play_se_sustain,
            SeqSubCmd.SE_INSTANT: di.ref.sndmgr.play_se_instant,
        }

    @abstractmethod
    def _sequence(self) -> Generator[list, None, None]:
        ...
        # """サブクラスが実装すべき処理シーケンス"""

    def _wait_finish(self) -> Generator[list, None, None]:
        """イベント終了時のキー待ち処理"""
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [SeqSubCmd.WAIT, 0]
        # Window側でFalse制御しているはず　問題が起きたら復旧
        # self.display_info.target.update_indicator(False)
        return

    def update(self) -> CommandPhase:
        match self.phase:
            case CommandPhase.SYN:
                self.display_info.target.message_list.clear()
                self._gen = self._sequence()
                self.phase = CommandPhase.ACK
                self._advance()
            case CommandPhase.ACK:
                if (
                    self.display_info.target.update() == WindowAction.DISCARD
                    or self.step_wait == -1
                ):
                    self._advance()
                self.step_wait -= 1
        return self.phase

    def _advance(self):
        # try:
        #     result = next(self._gen)
        #     if result:
        #     #     if result[0] == self.WAIT:
        #     #         self.step_wait = int(result[1]) * self._local_waitframe
        #     #     else:
        #     #         self.display_info.message = result
        #     #         self.display_info.is_change = True
        #     #         self.step_wait = self._local_waitframe
        #         cmd = getattr(SeqSubCmd, result[0], None)
        #         match cmd:
        #             case SeqSubCmd.WAIT:
        #                 self.step_wait = int(result[1]) * self._local_waitframe
        #             case SeqSubCmd.SE_SUSTAIN | SeqSubCmd.SE_INSTANT:
        #                 se_cmd = {"SE_SUSTAIN": di.ref.sndmgr.play_se_sustain,
        #                           "SE_INSTANT": di.ref.sndmgr.play_se_instant}
        #                 sound_id = getattr(SoundID, result[1], None)
        #                 if sound_id:
        #                     se_cmd[result[0]](sound_id)
        #                     self.step_wait = 0
        #             case _:
        #                 # サブコマンドでない場合は通常メッセージと扱う
        #                 self.display_info.message = result
        #                 self.display_info.is_change = True
        #                 self.step_wait = self._local_waitframe
        #     else:
        #         self.step_wait = 0
        # except StopIteration:
        #     self.phase = CommandPhase.FIN
        try:
            result = next(self._gen)
        except StopIteration:
            self.phase = CommandPhase.FIN
            return

        if not result:
            self.step_wait = 0
            return

        match result[0]:
            case SeqSubCmd.WAIT:
                self.step_wait = int(result[1]) * self._local_waitframe
            case SeqSubCmd.SE_INSTANT | SeqSubCmd.SE_SUSTAIN as se:
                se_id = SoundID[result[1]] if isinstance(result[1], str) else result[1]
                self.se_cmd[se](se_id)
                self.step_wait = 0
            case _:
                # サブコマンドでない場合は通常メッセージと扱う
                self.display_info.message = result
                self.display_info.is_change = True
                self.step_wait = self._local_waitframe

    def draw(self) -> DisplayInfo:
        """コマンド描画情報送信"""
        return self.display_info
