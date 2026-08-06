"""
シーンモジュール：ショップ
"""

import logging
import pyxel as px
from gameutils.base import check_file, read_string
from gameutils.lib import Window, WindowAction
import service_locater as di
from field_map import PointPlaceType
from menu import MenuSelectShopCategory
from . import BaseScene

# ロギング設定
logger = logging.getLogger(__name__)


class SceneShop(BaseScene):
    """シーン基底クラス"""

    def __init__(self) -> None:
        """初期化：シーン別ウインドウマネージャ生成"""
        self.situation = "system"
        super().__init__()

        # 背景用に直前画面のスクリーンポインタからイメージ生成
        self.bgimage: px.Image = px.Image(px.width, px.height)
        bgpointer = self.bgimage.data_ptr()
        bgpointer[:] = px.screen.data_ptr()

        # メッセージ用ウインドウの生成
        message_pos = (0, 184)
        message_size = (px.width, 72)
        self.message_window = Window("basic", *message_pos, *message_size, "once", 0)
        self.message_window.update_row_max(self.message_window._max_msg_rows + 1)
        # 地点別の対応
        eventpoint = di.ref.pt.get_current_point()
        self.is_shop: bool = True
        match eventpoint.point_type:
            case PointPlaceType.CAPITAL_CITY:
                enter_message = (
                    "ご来店ありがとうございます。\n本日はどういった御用件でしょう？"
                )
                filename = "assets/image/shop_city.bmp"
            case PointPlaceType.TOWN:
                enter_message = "ようこそウチの店へ！\nどんな物を探してるんだ？"
                filename = "assets/image/shop_town.bmp"
            case PointPlaceType.VILLAGE:
                enter_message = "いらっしゃ～～い\nなんか買っていくかね？"
                filename = "assets/image/shop_village.bmp"
            case _:
                self.message_window.set_message(["ここには　お店は　みあたらない"])
                self.is_shop = False
                return

        self.is_goodbye: bool = False
        self.message_window.set_message([enter_message])
        self.shopimage: px.Image = px.Image.from_image(filename)

        # ショップメニュー
        self.wndmgr.push_stack(MenuSelectShopCategory, di.ref.pt, self.message_window)
        self.load_bgm()

    def load_bgm(self) -> None:
        """シーン切替時のBGMロード"""
        path = check_file("assets/sound/shop.txt")
        if path is not None:
            score_data = read_string(path)
        else:
            raise FileNotFoundError("ファイルがない！")
        # px.stop()
        # for i, mml in enumerate(score_data):
        #     px.channels[i].play(mml, loop=True)
        px.stop()
        for i, ch in enumerate(px.channels):
            mml = "R"
            if i < len(score_data):
                mml = score_data[i]
            ch.play(mml, loop=True)

    def update(self) -> None:
        """更新処理
        - ショップが無い場合はメッセージウインドウのボタン押下処理で抜ける
        """
        # ショップ無
        if self.is_shop is False:
            if self.message_window.update() == WindowAction.DISCARD:
                di.ref.scnmgr.previous_scene(False)
            return

        # 退店
        if self.is_goodbye:
            if self.message_window.update() == WindowAction.DISCARD:
                di.ref.scnmgr.previous_scene()
            return

        # ショップ有
        if di.ref.cmdmgr.is_empty:
            self.wndmgr.update()
        if not self.wndmgr.has_stack:
            self.message_window.clear_message()
            # 地点別の対応
            eventpoint = di.ref.pt.get_current_point()
            self.is_shop: bool = True
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    bye_message = "またのご来店をお待ちしております"
                case PointPlaceType.TOWN:
                    bye_message = "また来てくれよなっ！"
                case PointPlaceType.VILLAGE:
                    bye_message = "また来なさるがええ"
                case _:
                    return

            self.message_window.set_message([bye_message])  # type: ignore
            if not self.message_window.is_indicator:
                self.message_window.update_indicator(True)

            self.is_goodbye = True
            # if self.message_window.update() == WindowAction.DISCARD:
            #     # di.ref.scnmgr.previous_scene([bye_message])

    def draw(self) -> None:
        px.blt(0, 0, self.bgimage, 0, 0, self.bgimage.width, self.bgimage.height)

        # ショップメニュー存在時（ショップ有＆メニュー破棄前）
        if self.wndmgr.has_stack:
            px.blt(
                (px.width - self.shopimage.width) // 2,
                self.shopimage.height // 8,
                self.shopimage,
                0,
                0,
                self.shopimage.width,
                self.shopimage.height,
            )
            di.ref.pt.draw_ptinfo()
            self.wndmgr.draw()

        self.message_window.draw()
        self.message_window.draw_message()
