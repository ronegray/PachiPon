"""
起動処理用モジュール

- Pyxelに依存しないクラスの初期化
- 各種管理系クラスのサービスロケータ登録

"""

import logging
import service_locater as di
from const import APP_FPS
from gameutils.base import (
    initialize_input,
    load_keyconfig,
    FontManager,
)
from assets.asset_map import AssetMap
from scene import SceneManager
from field_map import MapGraph
from item import ItemManager, ItemPool, StackPool
from entity import Party, EnemyManager
from command import CommandManager
from skill import SkillManager
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
    load_keyconfig()
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

    # サービスロケータ登録：エネミーマネージャ
    logger.info("Initialize - Enemy")
    enmmgr = EnemyManager()
    di.register(di.ServiceKey.ENEMY_MANAGER, enmmgr)

    # サービスロケータ登録：コマンドマネージャ
    logger.info("Initialize - Command")
    cmdmgr = CommandManager()
    di.register(di.ServiceKey.COMMAND_MANAGER, cmdmgr)

    # サービスロケータ登録：アイテムマネージャ
    logger.info("Initialize - Item MasterData")
    itemmgr = ItemManager()
    di.register(di.ServiceKey.ITEM_MANAGER, itemmgr)
    # アイテムデータ初期化
    pl_item = ItemPool()
    di.register(di.ServiceKey.ITEMPOOL, pl_item)
    pl_stack = StackPool()
    di.register(di.ServiceKey.STACKPOOL, pl_stack)

    # サービスロケータ登録：スキルマネージャ
    logger.info("Initialize - Skill MasterData")
    sklmgr = SkillManager()
    di.register(di.ServiceKey.SKILL_MANAGER, sklmgr)

    """リリース時は削除する"""
    # プロトタイプ用初期アイテム (items.jsonの全アイテムを2つずつ作成)
    from item import ItemState

    for item_def_id, item_def in di.ref.itemmgr.get_all_definitions().items():
        for _ in range(5):
            if item_def.stackable:
                di.ref.pl_stack.add(
                    item_def_id, ItemState.BAG, 1
                )  # スタック可能な場合は1つずつ追加
            else:
                di.ref.pl_item.create(
                    item_def_id, ItemState.BAG
                )  # スタック不可の場合はインスタンスを作成

    from entity import EquipSlot
    from item import ItemID

    for member in di.ref.pt.get_allmember():
        pooled_item = di.ref.pl_item.get_by_category(ItemID.SACREDWEAPON)
        member.equipments.equip_on_pool(EquipSlot.WEAPON, list(pooled_item.items())[-1])
        pooled_item = di.ref.pl_item.get_by_category(ItemID.HOLYGUARD)
        member.equipments.equip_on_pool(
            EquipSlot.GUARDER, list(pooled_item.items())[-1]
        )
        pooled_item = di.ref.pl_item.get_by_category(ItemID.HISPDAMULET)
        member.equipments.equip_on_pool(
            EquipSlot.ACCESSORY_1, list(pooled_item.items())[-1]
        )
        pooled_item = di.ref.pl_item.get_by_category(ItemID.HILCKAMULET)
        member.equipments.equip_on_pool(
            EquipSlot.ACCESSORY_2, list(pooled_item.items())[-1]
        )
        member.equipments.equip_on_consume(EquipSlot.CONSUME_1, ItemID.HEALPOT)
        member.equipments.equip_on_consume(EquipSlot.CONSUME_2, ItemID.MAGICPOT)

    from skill import SkillID

    di.ref.hero.skills.learn_skill(SkillID.SACRED_ARROW)
    di.ref.mem2.skills.learn_skill(SkillID.HEALING_HAND)
