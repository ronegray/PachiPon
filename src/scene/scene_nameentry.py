"""
シーンクラス：ネームエントリ
"""

import logging
import pyxel as px
from const import BASE_PARAM
from assets.asset_map import AssetID, AssetMap

# import service_locater as di
from menu import MenuNameEntry
from entity import EntityParam
from .scene_base import BaseScene

logger = logging.getLogger(__name__)


class SceneNameEntry(BaseScene):
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
        self.param = EntityParam(
            name="",
            strength=BASE_PARAM,
            arcane=BASE_PARAM,
            endurance=BASE_PARAM,
            speed=BASE_PARAM,
            luck=BASE_PARAM,
        )
        self.wndmgr.push_stack(MenuNameEntry, self.param)

        """このシーンでは遷移元（タイトル）のBGMを引き継ぐ為load_bgmは無し"""

    def update(self) -> None:
        """更新ループ"""
        # メニュー更新
        if self.wndmgr.has_stack:
            self.wndmgr.update()

    def draw(self) -> None:
        """描画ループ"""
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
