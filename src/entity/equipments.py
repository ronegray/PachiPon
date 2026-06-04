"""equipments.py
装備スロット管理モジュール
- 装備スロットの定義
"""
from dataclasses import dataclass, field
from enum import IntEnum, auto
from item import ItemManager, ItemInstance, ItemDef, ItemType, ItemOwner


class EquipSlot(IntEnum):
    WEAPON = auto()  # 武器
    GUARDER = auto()  # 防具
    ACCESSORY_1 = auto()  # 装飾品1
    ACCESSORY_2 = auto()  # 装飾品2
    CONSUME_1 = auto()  # 消耗品1
    CONSUME_2 = auto()  # 消耗品2


@dataclass
class Equips:
    _owner_character_id: int

    def __post_init__(self):
        # ItemManagerをサービスロケータから取得
        # ItemManager はクラスメソッドしか持たないのでインスタンス化不要
        pass

    _equipped_items: dict[EquipSlot, ItemInstance | None] = field(
        default_factory=lambda: {
            EquipSlot.WEAPON: None,
            EquipSlot.GUARDER: None,
            EquipSlot.ACCESSORY_1: None,
            EquipSlot.ACCESSORY_2: None,
            EquipSlot.CONSUME_1: None,
            EquipSlot.CONSUME_2: None,
        }
    )
    _cached_itemdefs: dict[EquipSlot, ItemDef | None] = field(
        default_factory=lambda: {
            EquipSlot.WEAPON: None,
            EquipSlot.GUARDER: None,
            EquipSlot.ACCESSORY_1: None,
            EquipSlot.ACCESSORY_2: None,
            EquipSlot.CONSUME_1: None,
            EquipSlot.CONSUME_2: None,
        }
    )

    def _get_slot_from_item_tag(self, item_tag: ItemType) -> EquipSlot | None:
        # 武器、防具、装飾品は専用スロットに装備
        if item_tag == ItemType.WEAPON:
            return EquipSlot.WEAPON
        if item_tag == ItemType.GUARDER:
            return EquipSlot.GUARDER
        if item_tag == ItemType.ACCESSORY:
            if self._equipped_items[EquipSlot.ACCESSORY_1] is None:
                return EquipSlot.ACCESSORY_1
            else:
                return EquipSlot.ACCESSORY_2
        # 消耗品は空いているスロットに装備（優先度: CONSUME_1 -> CONSUME_2）
        if item_tag == ItemType.CONSUME:
            if self._equipped_items[EquipSlot.CONSUME_1] is None:
                return EquipSlot.CONSUME_1
            else:
                return EquipSlot.CONSUME_2
        return None

    def equip_on(self, item_instance: ItemInstance) -> ItemInstance | None:
        item_def = ItemManager.get_def(item_instance.def_id)
        if not item_def:
            return None

        slot = self._get_slot_from_item_tag(item_def.item_type)
        if slot is None:
            return None  # 装備できないアイテム

        # 既にそのスロットに装備品がある場合は、それを外して返す
        unequipped_item = None
        if self._equipped_items[slot] is not None:
            unequipped_item = self.equip_off(slot)  # 既存の装備を外す

        # 新しいアイテムを装備
        self._equipped_items[slot] = item_instance
        item_instance.owner_id = self._owner_character_id
        item_instance.state.equipped = True
        self._cached_itemdefs[slot] = item_def  # キャッシュを更新
        return unequipped_item

    def equip_off(self, slot: EquipSlot) -> ItemInstance | None:
        item_instance = self._equipped_items[slot]
        if item_instance is not None:
            item_instance.owner_id = ItemOwner.BAG.value  # バッグに戻す
            item_instance.state.equipped = False
            self._equipped_items[slot] = None
            self._cached_itemdefs[slot] = None  # キャッシュをクリア
        return item_instance

    def get_itemdef(self, slot: EquipSlot) -> ItemDef | None:
        item_instance = self._equipped_items[slot]
        if item_instance is None:  # 装備されていない場合はNoneを返す
            return None

        if self._cached_itemdefs[slot] is None:
            # キャッシュがなければItemManagerから取得してキャッシュする
            item_def = ItemManager.get_def(item_instance.def_id)
            self._cached_itemdefs[slot] = item_def
        return self._cached_itemdefs[slot]
