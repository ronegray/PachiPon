"""window_manager.py
ウインドウ・メニュー管理クラス

- 管理機能
  - ウインドウとメニューのスタックを管理（追加・削除）
  - 最終スタックの更新と描画
  - スタックの全終了を最終スタックから依頼可能
  - ウインドウとメニューのキー操作を外部から上書き可能(自作inputモジュールを想定)
"""

# from __future__ import annotations
from . import (
    WindowAction,
    Window,
    Menu,
    RsltContinue,
    RsltDiscard,
    RsltPop,
    RsltPush,
    RsltReplace,
)


class WindowManager:
    """Window/Menuインスタンス管理クラス"""

    def __init__(self):
        """初期化"""
        # 非シングルトン利用が前提の為スタックはインスタンス変数として定義
        self._stacks: list[Window | Menu] = []

    def push_stack(self, class_name, *args, **kwargs) -> Window | Menu:
        """指定クラスのインスタンスをスタックに追加"""
        instance = class_name(*args, **kwargs)
        self._stacks.append(instance)
        return instance

    def pop_stack(self) -> int:
        """スタック末尾のインスタンスを削除"""
        self._stacks.pop()
        return len(self._stacks)

    def clear_stack(self) -> None:
        """メニュースタックをクリア"""
        self._stacks.clear()

    def get_stack(self, from_last: int = 0) -> Window | Menu:
        """末尾から数えて指定した順番のメニュースタックを取得"""
        list_index = -(1 + from_last)
        try:
            result = self._stacks[list_index]
        except IndexError:
            result = self._stacks[-1]
        return result

    def update(self) -> WindowAction:
        """管理クラス配下のインスタンス更新およびインスタンス応答の処理"""
        action = WindowAction.NOTHING
        if len(self._stacks):
            action = self._stacks[-1].update()
            match action:
                case WindowAction.CONTINUE:
                    # そのまま続ける
                    pass
                case WindowAction.CLOSE:
                    # 現在の階層をクローズして前のスタックへ戻る
                    self.pop_stack()
                case WindowAction.DISCARD:
                    # 全階層をクローズしてスタックを全消去
                    self.clear_stack()
                case WindowAction.EXECUTE:
                    # 基本的にEXECUTEを返すのはMenuのみだが念の為
                    if isinstance(self._stacks[-1], Menu):
                        exec_result = self._stacks[-1].exec_menu()
                        match exec_result:
                            case RsltContinue():
                                pass
                            case RsltPop():
                                self.pop_stack()
                            case RsltDiscard():
                                self.clear_stack()
                            case RsltReplace():
                                self.pop_stack()
                                self.push_stack(
                                    exec_result.class_name,
                                    *exec_result.args_pos,
                                    *exec_result.args_key,
                                )
                            case RsltPush():
                                self.push_stack(
                                    exec_result.class_name,
                                    *exec_result.args_pos,
                                    *exec_result.args_key,
                                )
                case _:
                    print(action)
                    action = WindowAction.NOTHING
        return action

    def draw(self) -> None:
        """管理クラス配下のインスタンスをスタックの奥から順に描画"""
        if len(self._stacks):
            for window in self._stacks:
                window.draw()
                if isinstance(window, Window):
                    window.draw_message()

    @property
    def has_stack(self) -> bool:
        """スタックの有無"""
        return len(self._stacks) > 0

    @property
    def stack_count(self) -> int:
        """スタックに積まれたメニュー数"""
        return len(self._stacks)
