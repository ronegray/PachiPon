"""bootstrap.py
IPL処理用モジュール
"""
import logging
import service_locater as di
from const import APP_FPS
from gameutils.base import (
    initialize_input,
    load_config,
    FontManager,
)
from assets.asset_map import AssetMap
from scene import SceneManager
from field_map import MapGraph
from entity import Party
from setup_log import setup_logging


# ロギング設定
logger = logging.getLogger(__name__)


def ipl():
    """Initial Program Loader"""
    # ログ設定の初期化
    setup_logging(logging.DEBUG)
    logger.info("log setup finished successfully.")

    # 外部ライブラリ初期化１（基礎クラス）
    logger.info("Initialize - gameutils.base")
    initialize_input(APP_FPS)
    load_config()
    FontManager.initialize()

    # アセットマップ初期化
    logger.info("Initialize - AssetMap")
    AssetMap.initialize_assetmap()

    # サービスロケータ登録：シーンマネージャ
    logger.info("Initialize - SceneManager")
    scnmgr = SceneManager()
    di.register(di.ServiceKey.SCENE_MANAGER, scnmgr)

    # サービスロケータ登録：フィールドマップ
    logger.info("Initialize - FieldMap")
    map = MapGraph()
    di.register(di.ServiceKey.MAPGRAPH, map)

    # サービスロケータ登録：パーティ
    logger.info("Initialize - Party")
    pt = Party()
    di.register(di.ServiceKey.PARTY, pt)
