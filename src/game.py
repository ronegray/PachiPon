"""game.py
Pyxelアプリケーション本体モジュール
- Pyxelの初期化
- Pyxelのupdate/drawフレームの処理
"""
import pyxel as px
from const import APP_WIDTH, APP_HEIGHT, APP_TITLE, APP_FPS
from gameutils.base import check_file, read_json
import service_locater as di

# ロギング設定
import logging

logger = logging.getLogger(__name__)


class GameApp:
    def __init__(self):
        """アプリ環境初期化"""
        # 外部ライブラリ初期化１（基礎クラス）
        logger.info("Initialize - gameutils.base")
        from gameutils.base import initialize_input, load_config, FontManager

        initialize_input(APP_FPS)
        load_config()
        FontManager.initialize()

        # アセットマップ初期化
        logger.info("Initialize - AssetMap")
        from assets.asset_map import AssetMap

        AssetMap.initialize_assetmap()

        # サービスロケータ登録：シーンマネージャ
        logger.info("Initialize - SceneManager")
        from scene import SceneManager

        scnmgr = SceneManager()
        di.register(di.ServiceKey.SCENE_MANAGER, scnmgr)

        # サービスロケータ登録：フィールドマップ
        logger.info("Initialize - FieldMap")
        from field_map import MapGraph

        map = MapGraph()
        di.register(di.ServiceKey.MAPGRAPH, map)

        # フィールドマップ構造データロード
        from assets.asset_map import AssetID

        map_path = check_file(AssetMap.get_assetpath(AssetID.DATA_MAP), "r")
        if map_path:
            di.ref.map.load_from_json(read_json(map_path))
        else:
            logger.critical("マップ構造データファイルが見つかりません")
            quit()

        # サービスロケータ登録：パーティ
        logger.info("Initialize - Party")
        from entity import Party

        pt = Party()
        di.register(di.ServiceKey.PARTY, pt)

        # Pyxel初期化処理
        logger.info("Initialize - Pyxel")
        self.initialize_pyxel()

        # 外部ライブラリ初期化２（機能クラス）
        # from gameutils.lib import SoundManager
        # sndmgr = SoundManager()
        # di.register(di.ServiceKey.SOUND_MANAGER, sndmgr)
        # di.ref.sndmgr.load_bgm(0)

        # 初期表示シーン定義
        di.ref.scnmgr.push_stack("splash")
        # 開発用に通常画面まで一気に遷移
        di.ref.scnmgr.push_stack("title")
        di.ref.scnmgr.push_stack("map")

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

    def draw(self):
        """pyxel drawフレーム処理"""
        px.cls(px.COLOR_BLACK)
        di.ref.scnmgr.draw()
