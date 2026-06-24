"""command_popup.py
イベント制御コマンドの生成：POPUP

- updateサイクル用
  - 指定ファイル名の画像読み込み
  - 画面サイズから画面中央となる描画位置を算出
- drawサイクル用
  - 画面の消去と読み込み済画像の表示
"""

# from app import AppContext
from .command_context import CommandContext, WindowHandler
from .evt_cmd_base import EventCommand, generator_type_command


def _make_popup(ctx: CommandContext) -> EventCommand:
    def _runner(filename: str, params: dict) -> generator_type_command:
        """
        ポップアップ表示準備・制御コマンド
        """
        # icnt = 0
        # ctx.sound.play_bgm(int(bgm_id))
        # params["window"] = AppContext.window
        wndmgr: WindowHandler = params["wndmgr"]
        wndmgr.generate_window()
        wndmgr.popup_message("テストメッセージ１")
        yield
        wndmgr.popup_message("テストメッセージ２")
        yield
        while wndmgr.has_stack():
            yield

        # wndmgr.push_stack(Window, "basic",         self,
        # font_size_name: FONT_SIZE_NAME,
        # x: int,
        # y: int,
        # width: int,
        # height: int,
        # window_mode: WINDOW_MODE,
        # wait_sec: float = 5.0,)
        # yield
        # while wndmgr.has_stack():
        #     yield

    # return EventCommand(run=run, draw=None)

    # def _drawer(params: dict) -> None:
    #     """
    #     画像表示コマンド
    #     """
    #     if params["wndmgr"] is None:
    #         return

    return EventCommand(runner=_runner, drawer=None)
