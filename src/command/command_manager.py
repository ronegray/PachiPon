"""
CommandProtocolのみを相手にするスタック型Invoker
"""

from typing import Callable
from . import CommandProtocol, DisplayInfo, CommandPhase


def _render(display_info: DisplayInfo) -> None:
    """DisplayInfoを実際に画面へ出す処理"""
    display_info.target.draw()
    if display_info.message:
        if display_info.is_change:
            if isinstance(display_info.message, list):
                for message in display_info.message:
                    display_info.target.add_message(message)
            else:
                display_info.target.add_message(display_info.message)
            display_info.is_change = False
        display_info.target.draw_message()

    if display_info.graphic_command:
        for cmd in display_info.graphic_command:
            cmd()


class CommandManager:
    """push/popのコマンドスタックを持つ、唯一の共通Invoker。"""

    _commands: list[CommandProtocol]
    _on_empty: Callable | None

    def __init__(self) -> None:
        CommandManager._commands = []
        CommandManager._on_empty = None

    @property
    def stack_count(self) -> int:
        """スタックに積まれたコマンド数"""
        return len(self._commands)

    @property
    def is_empty(self) -> bool:
        """スタックが空かどうか。ターン進行等は呼び出し元がこれだけを見て
        判断する（空になった理由がEntity系かSystem系かは関知しない）。
        """
        return len(self._commands) == 0

    def set_on_empty(self, callback: Callable | None) -> None:
        """スタックが空になった時に実行する関数を登録"""
        self._on_empty = callback

    def push_command(self, command: CommandProtocol) -> None:
        """新しいCommandをスタックの最上段に積む。
        どの具象Commandかは一切問わない。型としてCommandProtocolを
        満たしてさえいれば、Entity系・System系を問わず受け入れる。
        """
        self._commands.append(command)

    def clear_commands(self) -> None:
        """コマンドスタックのクリア"""
        self._commands.clear()

    def update(self) -> None:
        """スタック最上段のみを1フレーム分進行させる。"""
        if self.is_empty:
            return
        if self._commands[-1].update() == CommandPhase.FIN:
            self._commands.pop()
            if self._on_empty and self.is_empty:
                self._on_empty()
                self._on_empty = None

    def draw(self) -> None:
        """スタック最上段のみ描画"""
        if self.is_empty:
            return
        display_info = self._commands[-1].draw()
        _render(display_info)
