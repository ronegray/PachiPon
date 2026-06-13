import json

# from typing import Optional
from .item_protocol import ItemID, ItemType, ItemDef
from assets.asset_map import AssetID, AssetMap


class ItemManager:
    _master_def: dict[ItemID, ItemDef] = {}

    def __init__(self) -> None:
        """JSONファイルを読み込んでアイテム定義を初期化する"""
        json_path = AssetMap.get_assetpath(AssetID.DATA_ITEM)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            self._master_def = {}
            for type_name, item_data in json_data.items():
                item_type = ItemType[type_name]
                stackable = (
                    item_type == ItemType.CONSUME
                )  # 現状のルール: 消耗品のみスタック可

                for item_name, details in item_data.items():
                    if hasattr(ItemID, item_name):
                        # def_id = ItemID[item_name].value
                        def_id = ItemID[item_name]
                        self._master_def[def_id] = ItemDef(
                            def_id=def_id,
                            name=details.get("name", "Unknown"),
                            item_type=item_type,
                            stackable=stackable,
                            price=details.get("price", 0),
                            description=details.get("description", ""),
                            hitdice=details.get("hitdice", 0),
                            defvalue=details.get("defcalue", 0),
                            magpenalty=details.get("magpenalty", 0),
                            effect_type=details.get("effect_type"),
                            effect_value=details.get("effect_value", 0.0),
                            is_percent=details.get("is_percent", False),
                        )
                    else:
                        print(
                            f"Warning: ItemID.{item_name} is not defined in ItemID enum."
                        )

        except Exception as e:
            print(f"Error loading items.json: {e}")

    def get_def(self, def_id: ItemID) -> ItemDef | None:
        """指定されたIDのアイテム定義を取得する"""
        return self._master_def.get(def_id)

    def get_all_definitions(self) -> dict[ItemID, ItemDef]:
        """すべてのアイテム定義を取得する"""
        return self._master_def
