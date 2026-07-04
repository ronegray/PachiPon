"""
シーンクラス：スプラッシュ画面
- スプラッシュ画面の表示
"""

import pyxel as px
import service_locater as di
from .scene_base import BaseScene
from gameutils.base import is_pressed
from gameutils.lib import Window

# from assets.asset_map import AssetID, AssetMap
from command.system_command import BattleStartEffect


class SceneBattleSplash(BaseScene):
    """シーン：スプラッシュ画面"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"

        # 背景用に直前画面のスクリーンポインタからイメージ生成
        self.bgimage: px.Image = px.Image(px.width, px.height)
        bgpointer = self.bgimage.data_ptr()
        bgpointer[:] = px.screen.data_ptr()

        dummy = Window("basic", 0, 0, 1, 1, "menu")
        di.ref.cmdmgr.push_command(BattleStartEffect(dummy))
        """このシーンではbgmは無し SEのみ"""
        px.play(3, 63)

    def update(self) -> None:
        """更新ループ"""
        # 決定／キャンセルキーでスキップ
        if is_pressed("decide") or is_pressed("cancel"):
            di.ref.cmdmgr._stacks.pop()
            self.to_battle()
            return

        if di.ref.cmdmgr.is_empty:
            self.to_battle()

    def to_battle(self):
        di.ref.scnmgr.step_next_scene("battle")
        px.dither(1)

    def draw(self) -> None:
        """描画ループ"""
        px.blt(0, 0, self.bgimage, 0, 0, self.bgimage.width, self.bgimage.height)
