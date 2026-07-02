"""command_manager.py

CommandManager: CommandProtocolのみを相手にするスタック型Invoker。

設計方針:
- 系統判定は行わない。CommandManagerが知っているのはCommandProtocol
  （update()/draw()）だけで、push されてきたものがEntity系かSystem系かを
  一切問い合わせない。新しいCommand種別を追加してもこのクラスは無修正のまま
  でよい（Open/Closedの実践）。
- update()はスタック最上段のみを進行させる。最上段が完了(Phase.DONE)したら
  popする。
- draw()はスタック全体を下から上へ描画する。これにより、例えば
  「呪文使用の確認メッセージ」の下に元のメニュー画面が見え続ける、という
  レイヤー表示が自然に成立する（updateと違い、drawは『今のスタック構造を
  そのまま描くだけ』なので全件描画してよい）。
- push/pop前後の検証（MP消費の可否チェックや、ターン進行など）は
  CommandManagerの責務にしない。前者はCommand生成前にClient側が、
  後者はScene側がスタックの空き状況（is_empty）を見て判断する。
"""

# from __future__ import annotations

from . import CommandBase, DisplayInfo, CommandPhase


def _render(display_info: DisplayInfo) -> None:
    """DisplayInfoを実際に画面へ出す処理。
    実プロジェクトではここを pyxel の px.rect()/px.text() 等の呼び出しに
    置き換える。サンプルでは標準出力で代替する。
    """
    # if display_info.sub_message:
    #     print(f"[window] {display_info.message} / {display_info.sub_message}")
    # else:
    # print(f"[window] {display_info.message}")
    display_info.target.draw()
    # display_info.target.set_message(display_info.message)
    if display_info.is_change:
        if isinstance(display_info.message, list):
            for message in display_info.message:
                display_info.target.add_message(message)
        else:
            display_info.target.add_message(display_info.message)
        display_info.is_change = False
    display_info.target.draw_message()


class CommandManager:
    """push/popのコマンドスタックを持つ、唯一の共通Invoker。"""

    _stacks: list[CommandBase]

    def __init__(self) -> None:
        CommandManager._stacks = []

    @property
    def stack_count(self) -> int:
        """スタックに積まれたコマンド数"""
        return len(self._stacks)

    @property
    def is_empty(self) -> bool:
        """スタックが空かどうか。ターン進行等は呼び出し元がこれだけを見て
        判断する（空になった理由がEntity系かSystem系かは関知しない）。
        """
        return len(self._stacks) == 0

    def push_command(self, command: CommandBase) -> None:
        """新しいCommandをスタックの最上段に積む。
        どの具象Commandかは一切問わない。型としてCommandProtocolを
        満たしてさえいれば、Entity系・System系を問わず受け入れる。
        """
        self._stacks.append(command)

    def update(self) -> None:
        """スタック最上段のみを1フレーム分進行させる。"""
        if self.is_empty:
            return
        state = self._stacks[-1].update()
        # if state is CommandPhase.SYNACK:
        #     print(f"{self._stacks[-1]._ctx.actor.param.name} to {self._stacks[-1]._ctx.targets[self._stacks[-1]._ctx.target_index].param.name}")
        if state is CommandPhase.FIN:
            self._stacks.pop()

    def draw(self) -> None:
        """スタック最上段のみ描画"""
        if self.is_empty:
            return
        command = self._stacks[-1]
        # if command.phase == CommandPhase.ACK:
        #     display_info = command.draw()
        # # if display_info is not None:
        # #     _render(display_info)
        #     _render(display_info)
        display_info = command.draw()
        _render(display_info)
