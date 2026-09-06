"""
アイテム情報管理モジュール
- マスタ定義ファイルの情報を保持
- 指定したID(ItemDef)のアイテム情報を提供
"""

import logging
from gameutils.base import check_file, read_json
from assets.asset_map import AssetID, AssetMap
from const import CELL_PRICE_MULTIPLIER
from . import ItemID, ItemType, ItemDef, ItemTargetType, ItemRank

# ロギング設定
logger = logging.getLogger(__name__)


class ItemRepository:
    _master_def: dict[ItemID, ItemDef]

    def __init__(self) -> None:
        """JSONファイルを読み込んでアイテム定義を初期化する"""
        path_check = AssetMap.get_assetpath(AssetID.DATA_ITEM)
        json_path = check_file(path_check)
        if json_path:
            json_data = read_json(json_path)
        else:
            errmsg = "アイテム定義データファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        ItemRepository._master_def = {}
        for type_name, item_data in json_data.items():
            item_type = ItemType[type_name]
            is_stackable = item_type == ItemType.CONSUME  # 現状のルール: 消耗品のみスタック可

            for item_name, details in item_data.items():
                if hasattr(ItemID, item_name):
                    # def_id = ItemID[item_name].value
                    def_id = ItemID[item_name]
                    ItemRepository._master_def[def_id] = ItemDef(
                        def_id=def_id,
                        name=details.get("name", "Unknown"),
                        item_type=item_type,
                        target_type=ItemTargetType[details.get("target_type", "NONE")],
                        stackable=is_stackable,
                        rank=ItemRank[details.get("rank", "JUNK")],
                        price=details.get("price", 0),
                        description=details.get("description", ""),
                        hitdice=details.get("hitdice", 0),
                        defvalue=details.get("defvalue", 0),
                        magpenalty=details.get("magpenalty", 0),
                        effect_id=details.get("effect_type"),
                        effect_value=details.get("effect_value", 0.0),
                        is_percent=details.get("is_percent", False),
                    )
                else:
                    print(f"Warning: ItemID.{item_name} is not defined in ItemID enum.")

    def get_def(self, def_id: ItemID) -> ItemDef | None:
        """指定されたIDのアイテム定義を取得する"""
        return self._master_def.get(def_id)

    def get_def_by_type(self, item_type: ItemType) -> dict[ItemID, ItemDef]:
        """指定されたアイテムタイプのアイテム定義を取得する"""
        result = {
            item_id: item_def
            for item_id, item_def in self._master_def.items()
            if item_def.item_type == item_type
        }
        return result

    def get_all_definitions(self) -> dict[ItemID, ItemDef]:
        """すべてのアイテム定義を取得する"""
        return self._master_def

    def calc_cellprice(self, def_id: ItemID) -> int:
        item_def = self.get_def(def_id)
        return int(item_def.price * CELL_PRICE_MULTIPLIER)  # type: ignore
