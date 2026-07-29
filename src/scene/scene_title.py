"""scene_title.py
シーンクラス：タイトル画面
- タイトル画面の表示
  - 背景イメージ
  - タイトルメニュー
"""

import pyxel as px
from const import APP_WIDTH, APP_HEIGHT, APP_VERSION
from .scene_base import BaseScene
from menu import MenuTitle
from assets.asset_map import AssetID, AssetMap
from gameutils.base import check_file, read_string


class SceneTitle(BaseScene):
    """シーン：タイトル画面"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # 背景イメージ設定
        self.bgimage = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_TITLE))
        self.bgpos = (
            (px.width - self.bgimage.width) // 2,
            (px.height - self.bgimage.height) // 2,
        )
        # タイトルロゴ設定
        self.logo = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_LOGO))
        self.logopos = (
            (px.width - self.logo.width) // 2,
            (px.height - self.logo.height) // 2,
        )

        # メニュー生成
        self.wndmgr.push_stack(MenuTitle)

        # """暫定処理：BGMロード"""
        # path = check_file("assets/sound/title.txt")
        # if path is not None:
        #     score_data = read_string(path)
        # else:
        #     raise FileNotFoundError("ファイルがない！")
        # for i, mml in enumerate(score_data):
        #     px.sounds[i].mml(mml)
        # px.musics[0].set([0], [1], [2], [3])
        # px.playm(0, loop=True)
        self.load_bgm()

    def load_bgm(self) -> None:
        """シーン切替時のBGMロード"""
        """暫定処理：BGMロード"""
        path = check_file("assets/sound/title.txt")
        if path is not None:
            score_data = read_string(path)
        else:
            raise FileNotFoundError("ファイルがない！")
        for i, mml in enumerate(score_data):
            #     px.sounds[i].mml(mml)
            # px.musics[0].set([0], [1], [2], [3])
            # px.playm(0, loop=True)
            px.channels[i].play(mml, loop=True)

    def update(self) -> None:
        """更新ループ"""
        # メニュー更新
        self.wndmgr.update()

    def draw(self) -> None:
        """描画ループ"""
        # 背景イメージ描画
        px.blt(
            *self.bgpos,
            self.bgimage,
            0,
            0,
            self.bgimage.width,
            self.bgimage.height,
            colkey=px.COLOR_BLACK,
        )
        px.blt(
            *self.logopos,
            self.logo,
            0,
            0,
            self.logo.width,
            self.logo.height,
            colkey=px.COLOR_BLACK,
        )
        # メニュー描画
        self.wndmgr.draw()
        # バージョン表示
        px.text(APP_WIDTH - 40, APP_HEIGHT - 8, f"ver {APP_VERSION}", px.COLOR_WHITE)
