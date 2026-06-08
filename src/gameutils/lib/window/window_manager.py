"""window_manager.py
ウインドウ・メニュー管理クラス

- 管理機能
  - ウインドウとメニューのスタックを管理（追加・削除）
  - 最終スタックの更新と描画
  - スタックの全終了を最終スタックから依頼可能
  - ウインドウとメニューのキー操作を外部から上書き可能(自作inputモジュールを想定)
"""
from __future__ import annotations
from .window_protocol import WindowAction
from .window_base import Window, Menu, RsltContinue, RsltDiscard, RsltPop, RsltPush


class WindowManager:
    """Window/Menuインスタンス管理クラス"""

    def __init__(self):
        """初期化"""
        self.stacks: list[Window | Menu] = []

    def push_stack(self, class_name, *args, **kwargs):
        """指定クラスのインスタンスをスタックに追加"""
        instance = class_name(*args, **kwargs)
        self.stacks.append(instance)

    def pop_stack(self):
        """スタック末尾のインスタンスを削除"""
        self.stacks.pop()

    def update(self):
        """管理クラス配下のインスタンス更新およびインスタンス応答の処理"""
        if len(self.stacks):
            action = self.stacks[-1].update()
            match action:
                case WindowAction.CONTINUE:
                    # そのまま続ける
                    pass
                case WindowAction.CLOSE:
                    # 現在の階層をクローズして前のスタックへ戻る
                    self.pop_stack()
                case WindowAction.DISCARD:
                    # 全階層をクローズしてスタックを全消去
                    self.stacks.clear()
                case WindowAction.EXECUTE:
                    # 基本的にEXECUTEを返すのはMenuのみだが念の為
                    if isinstance(self.stacks[-1], Menu):
                        exec_result = self.stacks[-1].exec_menu()
                        match exec_result:
                            case RsltContinue():
                                pass
                            case RsltPop():
                                self.pop_stack()
                            case RsltDiscard():
                                self.stacks.clear()
                            case RsltPush():
                                self.push_stack(
                                    exec_result.class_name,
                                    *exec_result.args_pos,
                                    *exec_result.args_key,
                                )

    def draw(self):
        """管理クラス配下のインスタンスをスタックの奥から順に描画"""
        if len(self.stacks):
            for window in self.stacks:
                window.draw()
                if isinstance(window, Window):
                    window.draw_message()

    @property
    def has_stack(self) -> bool:
        """スタックの有無"""
        return len(self.stacks) > 0
