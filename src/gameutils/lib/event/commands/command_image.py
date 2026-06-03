"""command_image.py
イベント制御コマンドの生成：IMAGE

- updateサイクル用
  - 指定ファイル名の画像読み込み
  - 画面サイズから画面中央となる描画位置を算出
- drawサイクル用
  - 画面の消去と読み込み済画像の表示
"""
import pyxel as px

# from app import AppContext
from .command_context import CommandContext
from .evt_cmd_base import EventCommand, generator_type_command


def _make_image(ctx: CommandContext) -> EventCommand:
    def _runner(filename: str, params: dict) -> generator_type_command:
        """
        画像表示準備・制御コマンド
        """
        icnt = 0
        params["img"] = px.Image.from_image(filename)
        params["x"] = (px.width - params["img"].width) // 2
        params["y"] = (px.height - params["img"].height) // 2
        while icnt < 60:
            yield
            icnt += 1
        return

    def _drawer(imginfo: dict) -> None:
        """
        画像表示コマンド
        """
        if imginfo["img"] is None:
            return
        px.cls(0)
        px.blt(
            imginfo["x"],
            imginfo["y"],
            imginfo["img"],
            0,
            0,
            imginfo["img"].width,
            imginfo["img"].height,
        )

    return EventCommand(runner=_runner, drawer=_drawer)
