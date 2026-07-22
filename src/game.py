"""game.py
Pyxelアプリケーション本体モジュール
- Pyxelの初期化
- Pyxelのupdate/drawフレームの処理
"""

import logging
import pyxel as px
from const import APP_WIDTH, APP_HEIGHT, APP_TITLE, APP_FPS
import service_locater as di


# ロギング設定
logger = logging.getLogger(__name__)


class GameApp:
    def __init__(self):
        """アプリ環境初期化"""

        # Pyxel初期化処理
        logger.info("Initialize - Pyxel")
        self.initialize_pyxel()

        # di.ref.hero.sprite.img = px.Image.from_image("assets/image/character16.bmp")
        # 外部ライブラリ初期化２（機能クラス）
        # from gameutils.lib import SoundManager
        # sndmgr = SoundManager()
        # di.register(di.ServiceKey.SOUND_MANAGER, sndmgr)
        # di.ref.sndmgr.load_bgm(0)
        # 背景マップ画像ロード
        di.ref.map.load_mapimage()
        # ダイス画像ロード
        di.ref.efxdice.load_diceimage()
        # パーティー用情報ウィンドウ定義
        di.ref.pt.generate_pt_window()

        # 初期表示シーン定義
        di.ref.scnmgr.next_scene("splash")

        """開発用に通常画面まで一気に遷移
        リリース時は削除"""
        di.ref.scnmgr.next_scene("title")
        di.ref.scnmgr.next_scene("map")

        # Pyxel実行開始
        logger.info("Start Pyxel frame procedure.")
        px.run(self.update, self.draw)

    def initialize_pyxel(self, scale: int | None = None):
        """Pyxelアプリケーション初期化"""
        px.init(
            APP_WIDTH,
            APP_HEIGHT,
            APP_TITLE,
            APP_FPS,
            quit_key=px.KEY_NONE,
            display_scale=scale,
        )
        from assets.asset_map import AssetMap, AssetID

        px.load(AssetMap.get_assetpath(AssetID.PYXRES))

    def update(self):
        """pyxel updateフレーム処理"""
        di.ref.scnmgr.update()
        # # コマンドupdate結果でスタッククリアされたら
        # is_executing = not di.ref.cmdmgr.is_empty
        di.ref.cmdmgr.update()
        # if is_executing and di.ref.cmdmgr.is_empty:
        #     di.ref.scnmgr.get_now_scene().wndmgr.clear_stack()

    def draw(self):
        """pyxel drawフレーム処理"""
        px.cls(px.COLOR_BLACK)
        di.ref.scnmgr.draw()
        di.ref.cmdmgr.draw()
