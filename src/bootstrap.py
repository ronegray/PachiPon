"""
起動処理用モジュール

- Pyxelに依存しないクラスの初期化
- 各種管理系クラスのサービスロケータ登録

"""

import logging
from setup_log import setup_logging
import service_locater as di
from const import APP_FPS
from gameutils.base import (
    initialize_input,
    load_keyconfig,
    check_file,
    read_json,
    FontManager,
    SoundManager,
    BGM_CHANNELS,
    SE_INSTANT_CH,
    SE_SUSTAIN_CH,
    # ToneManager,
)
from config import ApplicationConfig, CONF_VOLUME  # , CONF_DISP_SIZE, CONF_TEXT_SPEED
from assets.asset_map import AssetMap, AssetID
from scene import SceneManager
from field_map import MapGraph
from item import ItemRepository, ItemPool, StackPool
from entity import Party, EnemyRepository
from command import CommandManager
from skill import SkillRepository
from effect import DiceRollEffect
from event import EventRepository

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
    # tonemgr = ToneManager()
    sndmgr = SoundManager()
    di.register(di.ServiceKey.SOUND_MANAGER, sndmgr)
    di.ref.sndmgr.load_music_master()

    # アセットマップ初期化
    logger.info("Initialize - AssetMap")
    AssetMap.initialize_assetmap()

    # コンフィグ設定のロード
    path = check_file(AssetMap.get_assetpath(AssetID.SYSCONFIG))
    # コンフィグファイルが無ければApplicationConfigのデフォルト値使用
    if path is None:
        conf = ApplicationConfig()
    else:
        data = read_json(path)
        conf = ApplicationConfig(**data)
    di.register(di.ServiceKey.APP_CONFIG, conf)
    bgm_factor = CONF_VOLUME[di.ref.conf.vol_bgm]["args"][1]
    di.ref.sndmgr.set_basegain_factor(bgm_factor, BGM_CHANNELS)
    se_factor = CONF_VOLUME[di.ref.conf.vol_se]["args"][1]
    di.ref.sndmgr.set_basegain_factor(se_factor, (SE_INSTANT_CH, SE_SUSTAIN_CH))

    # サービスロケータ登録：シーンマネージャ
    logger.info("Initialize - SceneManager")
    scnmgr = SceneManager()
    di.register(di.ServiceKey.SCENE_MANAGER, scnmgr)

    # サービスロケータ登録：フィールドマップ
    logger.info("Initialize - FieldMap")
    map = MapGraph()
    di.register(di.ServiceKey.MAPGRAPH, map)

    # サービスロケータ登録：コマンドマネージャ
    logger.info("Initialize - CommandManager")
    cmdmgr = CommandManager()
    di.register(di.ServiceKey.COMMAND_MANAGER, cmdmgr)

    # サービスロケータ登録：イベントリポジトリ
    logger.info("Initialize - Event MasterData")
    evtrps = EventRepository()
    di.register(di.ServiceKey.EVENT_REPOSITORY, evtrps)

    # サービスロケータ登録：ダイスロールエフェクト
    logger.info("Initialize - DiceRollEffect")
    efxdice = DiceRollEffect()
    di.register(di.ServiceKey.DICEROLL_EFFECT, efxdice)

    # サービスロケータ登録：パーティ
    logger.info("Initialize - Party")
    # pt = Party(scnmgr=di.ref.scnmgr, map=di.ref.map, cmdmgr=di.ref.cmdmgr)
    pt = Party(map=di.ref.map)
    di.register(di.ServiceKey.PARTY, pt)

    # サービスロケータ登録：エネミーリポジトリ
    logger.info("Initialize - Enemy MasterData")
    enmrps = EnemyRepository()
    di.register(di.ServiceKey.ENEMY_REPOSITORY, enmrps)

    # サービスロケータ登録：アイテムリポジトリ
    logger.info("Initialize - Item MasterData")
    itemrps = ItemRepository()
    di.register(di.ServiceKey.ITEM_REPOSITORY, itemrps)
    # アイテムデータプール初期化
    logger.info("Initialize - Item ObjectData")
    pl_item = ItemPool()
    di.register(di.ServiceKey.ITEMPOOL, pl_item)
    pl_stack = StackPool()
    di.register(di.ServiceKey.STACKPOOL, pl_stack)

    # サービスロケータ登録：スキルリポジトリ
    logger.info("Initialize - Skill MasterData")
    sklrps = SkillRepository()
    di.register(di.ServiceKey.SKILL_REPOSITORY, sklrps)

    # """リリース時は削除する"""
    # # プロトタイプ用初期アイテム (items.jsonの全アイテムを2つずつ作成)
    # di.ref.pt.regist_dummy_hero()
    # from item import ItemState

    # for item_def_id, item_def in di.ref.itemrps.get_all_definitions().items():
    #     for _ in range(5):
    #         if item_def.stackable:
    #             di.ref.pl_stack.add(
    #                 item_def_id, ItemState.BAG, 1
    #             )  # スタック可能な場合は1つずつ追加
    #         else:
    #             di.ref.pl_item.create(
    #                 item_def_id, ItemState.BAG
    #             )  # スタック不可の場合はインスタンスを作成

    # from entity import EquipSlot
    # from item import ItemID

    # for member in di.ref.pt.get_allmember():
    #     pooled_item = di.ref.pl_item.get_by_category(ItemID.SACREDWEAPON)
    #     member.equipments.equip_on_pool(EquipSlot.WEAPON, list(pooled_item.items())[-1])
    #     pooled_item = di.ref.pl_item.get_by_category(ItemID.HOLYGUARD)
    #     member.equipments.equip_on_pool(
    #         EquipSlot.GUARDER, list(pooled_item.items())[-1]
    #     )
    #     pooled_item = di.ref.pl_item.get_by_category(ItemID.HISPDAMULET)
    #     member.equipments.equip_on_pool(
    #         EquipSlot.ACCESSORY_1, list(pooled_item.items())[-1]
    #     )
    #     pooled_item = di.ref.pl_item.get_by_category(ItemID.HILCKAMULET)
    #     member.equipments.equip_on_pool(
    #         EquipSlot.ACCESSORY_2, list(pooled_item.items())[-1]
    #     )
    #     member.equipments.equip_on_consume(EquipSlot.CONSUME_1, ItemID.HEALPOT)
    #     member.equipments.equip_on_consume(EquipSlot.CONSUME_2, ItemID.MAGICPOT)

    # from skill import SkillID

    # # di.ref.hero.skills.learn_skill(SkillID.SACRED_ARROW)
    # pt.get_member(0).skills.learn_skill(SkillID.SACRED_ARROW)
    # # di.ref.mem2.skills.learn_skill(SkillID.HEALING_HAND)
    # pt.get_member(0).skills.learn_skill(SkillID.HEALING_HAND)
