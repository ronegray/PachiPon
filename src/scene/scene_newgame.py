"""scene_newgame.py
シーンクラス：ニューゲーム画面
- ニューゲームイベントの表示
- 名前入力に遷移
"""

import logging
import pyxel as px
import service_locater as di
from const import APP_WIDTH, APP_HEIGHT
from .scene_base import BaseScene
from menu import MenuNameEntry
from assets.asset_map import AssetID, AssetMap
from gameutils.base import (
    check_file,
    # read_string,
    read_json,
    FontManager,
    shadowed_text,
    is_pressed,
)


logger = logging.getLogger(__name__)


class SceneNewGame(BaseScene):
    """シーン：タイトル画面"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # 背景イメージ設定
        self.bgimage: px.Image = px.Image.from_image(
            AssetMap.get_assetpath(AssetID.IMAGE_NEWGAME)
        )
        self.bgpos_x = (px.width - self.bgimage.width) // 2
        self.bgpos_y = (px.height - self.bgimage.height) // 2

        # メニュー生成
        self.user_name: str = ""
        self.wndmgr.push_stack(MenuNameEntry)

        # オープニングメッセージ
        path = check_file(AssetMap.get_assetpath(AssetID.DATA_OP_MESSAGE))
        if path is None:
            errmsg = "オープニングメッセージファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        self.font_opmsg = FontManager.get_fontdata("large")
        if self.font_opmsg.font is None:
            errmsg = "日本語フォントデータが定義されていません"
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)

        self.op_message: list = read_json(path)
        self.message_top: float = APP_HEIGHT
        # self.msg_end_line: int = -100
        self.op_msg_row_offset: float = self.font_opmsg.height * 1.25
        self.msg_end_line: int = -(len(self.op_message) * (self.font_opmsg.height + 3))

        self.is_finish: bool = False
        self.dither: float = 1
        # self.fastforward = 1 # 決定キーは早送り
        """このシーンでは遷移元（タイトル）のBGMを引き継ぐ為load_bgmは無し"""

    def update(self) -> None:
        """更新ループ"""
        if self.is_finish:
            is_break = False
            for ch in px.channels:
                ch.gain -= 0.001
                if ch.gain <= 0:
                    is_break = True
            self.dither -= 0.01
            if is_break:
                for ch in px.channels:
                    ch.gain = 0.125
                px.dither(1)
                di.ref.scnmgr.change_scene("map")

        # メニュー更新
        if self.wndmgr.has_stack:
            self.wndmgr.update()
        else:
            # 決定キー押下中は早送り
            fastforward = 4 if is_pressed("decide", "keep") else 1
            self.message_top -= 0.5 * fastforward
            # キャンセルキーでスキップ
            if (self.message_top < self.msg_end_line) or is_pressed("cancel"):
                # """暫定処理：BGMロード"""
                # path = check_file("assets/sound/opjingle.txt")
                # if path is not None:
                #     score_data = read_string(path)
                # else:
                #     raise FileNotFoundError("ファイルがない！")
                # for i, mml in enumerate(score_data):
                #     px.sounds[i].mml(mml)
                # px.musics[0].set([0], [1], [2])
                # px.stop()
                # px.playm(0)
                # while px.play_pos(0) is not None:
                #     pass
                self.is_finish = True

    def draw(self) -> None:
        """描画ループ"""
        px.dither(self.dither)
        px.cls(px.COLOR_BLACK)
        # 背景イメージ描画
        px.blt(
            self.bgpos_x,
            self.bgpos_y,
            self.bgimage,
            0,
            0,
            self.bgimage.width,
            self.bgimage.height,
            colkey=px.COLOR_BLACK,
        )

        # メニュー描画
        if self.wndmgr.has_stack:  # 名前入力中
            self.wndmgr.draw()
        else:
            shadowed_text(
                APP_WIDTH - 60,
                APP_HEIGHT - 16,
                "FF/decide key\nskip/cancel key",
                px.COLOR_PEACH,
            )
            for i, data in enumerate(self.op_message):
                msg_y = i * self.op_msg_row_offset + self.message_top
                if msg_y < 0:
                    continue
                tw = self.font_opmsg.font.text_width(data)  # type: ignore
                msg_x = (px.width - tw) / 2
                shadowed_text(
                    msg_x,
                    msg_y,
                    data,
                    px.COLOR_WHITE,
                    self.font_opmsg.font,
                    px.COLOR_BLACK,
                )
