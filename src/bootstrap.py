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
from item import ItemManager, ItemPool, StackPool, ItemState
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

    # アイテムデータ初期化
    logger.info("Initialize - Item MasterData")
    itemmgr = ItemManager()
    di.register(di.ServiceKey.ITEM_MANAGER, itemmgr)
    pl_item = ItemPool()
    di.register(di.ServiceKey.ITEMPOOL, pl_item)
    pl_stack = StackPool()
    di.register(di.ServiceKey.STACKPOOL, pl_stack)

    # プロトタイプ用初期アイテム (items.jsonの全アイテムを2つずつ作成)
    for item_def_id, item_def in di.ref.itemmgr.get_all_definitions().items():
        for _ in range(2):
            if item_def.stackable:
                di.ref.pl_stack.add(
                    item_def_id, ItemState.BAG, 1
                )  # スタック可能な場合は1つずつ追加
            else:
                di.ref.pl_item.create(
                    item_def_id, ItemState.BAG
                )  # スタック不可の場合はインスタンスを作成

    pass
