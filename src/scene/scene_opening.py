"""
シーンクラス：オープニングイベント
- ニューゲームイベントの表示
- 名前入力に遷移
"""

import logging
import pyxel as px
import service_locater as di
from const import APP_WIDTH, APP_HEIGHT
from .scene_base import BaseScene
from assets.asset_map import AssetID, AssetMap
from gameutils.base import (
    check_file,
    read_json,
    FontManager,
    shadowed_text,
    is_pressed,
)


logger = logging.getLogger(__name__)


class SceneOpening(BaseScene):
    """シーン：タイトル画面"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # 背景イメージ設定
        self.bgimage: px.Image = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_NEWGAME))
        self.bgpos_x = (px.width - self.bgimage.width) // 2
        self.bgpos_y = (px.height - self.bgimage.height) // 2

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
        self.op_msg_row_offset: float = self.font_opmsg.height * 1.25
        self.msg_end_line: int = -(len(self.op_message) * (self.font_opmsg.height + 3))

        self.is_finish: bool = False
        self.dither: float = 1
        """このシーンでは遷移元（タイトル）のBGMを引き継ぐ為load_bgmは無し"""

    def update(self) -> None:
        """更新ループ"""
        if self.is_finish:
            """オープニング終了時のフェードアウト"""
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

        # 決定キー押下中は早送り
        fastforward = 4 if is_pressed("decide", "keep") else 1
        self.message_top -= 0.5 * fastforward
        # キャンセルキーでスキップ
        if (self.message_top < self.msg_end_line) or is_pressed("cancel"):
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
