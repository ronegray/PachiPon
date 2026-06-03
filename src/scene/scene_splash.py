"""splash.py
シーンクラス：スプラッシュ画面
- スプラッシュ画面の表示
"""
import pyxel as px
import service_locater as di
from .scene_base import BaseScene
from gameutils.base import is_pressed
from assets.asset_map import AssetID, AssetMap


class SceneSplash(BaseScene):
    """シーン：スプラッシュ画面"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        # スプラッシュロゴの取得
        self.logo = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_SPLASH))

        # 描画関連パラメタの指定
        self.logo_address = (
            (px.width - self.logo.width) // 2,
            (px.height - self.logo.height) // 2,
        )
        self.alpha = 0.0  # ディザ状態（0透明⇔1不透明）
        self.multi = 4  # フレーム毎のalphaの増減値

    def update(self) -> None:
        """更新ループ"""
        # 決定／キャンセルキーでスキップ
        if is_pressed("decide") or is_pressed("cancel"):
            self.to_title()

        # フェードイン／アウト
        if self.alpha > 1.5:
            self.multi = -5
        self.alpha += self.multi * 0.01

        # フェードアウト後タイトルシーンへ遷移
        if self.alpha < -1.25:
            self.to_title()

    def to_title(self):
        # di.ref.app.scene = di.ref.app.change_scene("title")
        di.ref.scnmgr.next_scene("title")
        px.dither(1)

    def draw(self) -> None:
        """描画ループ"""
        px.cls(0)
        px.dither(self.alpha)
        px.blt(
            *self.logo_address,
            self.logo,
            0,
            0,
            self.logo.width,
            self.logo.height,
            colkey=px.COLOR_BLACK,
        )
