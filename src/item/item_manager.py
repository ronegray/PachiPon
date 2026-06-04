import json
from typing import Optional
from .item_protocol import ItemID, ItemType, ItemDef
from assets.asset_map import AssetID, AssetMap


class ItemManager:
    _definitions: dict[int, ItemDef] = {}

    @classmethod
    def initialize(cls) -> None:
        """JSONファイルを読み込んでアイテム定義を初期化する"""
        json_path = AssetMap.get_assetpath(AssetID.DATA_ITEM)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            cls._definitions = {}
            for tag_name, items in data.items():
                tag = ItemType[tag_name]
                stackable = (
                    tag == ItemType.CONSUME
                )  # 現状のルール: 消耗品のみスタック可

                for item_name, details in items.items():
                    if hasattr(ItemID, item_name):
                        def_id = ItemID[item_name].value
                        cls._definitions[def_id] = ItemDef(
                            def_id=def_id,
                            name=details.get("name", "Unknown"),
                            item_type=tag,
                            stackable=stackable,
                            price=details.get("price", 0),
                            description=details.get("description", ""),
                            atk=details.get("atk", 0),
                            dfn=details.get("dfn", 0),
                            spd=details.get("spd", 0),
                            effect_type=details.get("effect_type"),
                            effect_value=details.get("effect_value", 0),
                            is_percent=details.get("is_percent", False),
                        )
                    else:
                        print(
                            f"Warning: ItemID.{item_name} is not defined in ItemID enum."
                        )

        except Exception as e:
            print(f"Error loading items.json: {e}")

    @classmethod
    def get_def(cls, def_id: int) -> Optional[ItemDef]:
        """指定されたIDのアイテム定義を取得する"""
        return cls._definitions.get(def_id)

    @classmethod
    def get_all_definitions(cls) -> dict[int, ItemDef]:
        """すべてのアイテム定義を取得する"""
        return cls._definitions
