"""command_bgm.py
イベント制御コマンドの生成：BGM
※即時命令

- updateサイクル用
  - 指定ファイル名の画像読み込み
  - 画面サイズから画面中央となる描画位置を算出
- drawサイクルなし
"""
# import pyxel as px
# from app import AppContext
from .command_context import CommandContext
from .evt_cmd_base import EventCommand  # , generator_type_command


def _make_command(ctx: CommandContext) -> EventCommand:
    def _runner(bgm_id: str, state: dict):
        # ctx.sound.load_bgm(int(bgm_id))
        ctx.sound.play_bgm(int(bgm_id))

    return EventCommand(runner=_runner, is_instant=True)


# def _runner(filename:str, imginfo: dict):
#     """
#     画像表示準備・制御コマンド
#     """
#     icnt = 0
#     imginfo["img"] = px.Image.from_image(filename)
#     imginfo["x"] = (px.width-imginfo["img"].width)//2
#     imginfo["y"] = (px.height-imginfo["img"].height)//2
#     while icnt < 120:
#         yield
#         icnt += 1
#     return


# def _drawer(imginfo: dict) -> None:
#     """
#     画像表示コマンド
#     """
#     if imginfo["img"] is None:
#         return
#     px.cls(0)
#     px.blt(imginfo["x"], imginfo["y"], imginfo["img"],
#             0,0,imginfo["img"].width,imginfo["img"].height)


# cmd_image = EventCommand(runner=_runner, drawer=_drawer)
