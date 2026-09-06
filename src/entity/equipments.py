"""equipments.py
装備スロット管理モジュール
- 装備スロットの定義
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from item import (
    ItemID,
    ItemType,
    ItemState,
    PooledItem,
)
from skill import SkillID
import service_locater as di


# ロギング設定
logger = logging.getLogger(__name__)


class EquipSlot(StrEnum):
    WEAPON = "0"  # 武器
    GUARDER = "1"  # 防具
    ACCESSORY_1 = "2"  # 装飾品1
    ACCESSORY_2 = "3"  # 装飾品2
    CONSUME_1 = "4"  # 消耗品1
    CONSUME_2 = "5"  # 消耗品2


@dataclass
class Equips:
    """装備品管理クラス（Chacacterのコンポーネント）"""

    def __init__(self, owner_id: int):
        self.owner = owner_id
        # 現在装備しているアイテム
        self._equipped_items: dict[EquipSlot, PooledItem | None] = {
            EquipSlot.WEAPON: None,
            EquipSlot.GUARDER: None,
            EquipSlot.ACCESSORY_1: None,
            EquipSlot.ACCESSORY_2: None,
            EquipSlot.CONSUME_1: None,
            EquipSlot.CONSUME_2: None,
        }
        self._effect_cache: dict[SkillID, int | float] = {}

    def get_slot(self, slot: EquipSlot) -> PooledItem | None:
        """指定したスロットのアイテムを返す"""
        return self._equipped_items[slot]

    def _convert_stack(self, target: PooledItem) -> None:
        """装備アイテムのスタック化（装備スロット解除時）"""
        idx, plent = target

        # デバッグログ
        logger.debug(
            f"処理前個数：{
                di.ref.pl_stack.count(plent.ins.param.def_id, ItemState.BAG)
            }"
        )

        if plent.stat == ItemState.BAG:
            di.ref.pl_stack.add(plent.ins.param.def_id, ItemState.BAG)
            di.ref.pl_item.destroy(idx)

            # デバッグログ
            logger.debug(
                f"処理後個数：{
                    di.ref.pl_stack.count(plent.ins.param.def_id, ItemState.BAG)
                }"
            )

    def _convert_instance(self, def_id: ItemID) -> PooledItem:
        """スタックアイテムのインスタンス化（装備スロット定義時）"""
        # デバッグログ
        logger.debug(f"処理前個数：{di.ref.pl_stack.count(def_id, ItemState.BAG)}")

        if di.ref.pl_stack.count(def_id, ItemState.BAG) > 0:
            pooled = di.ref.pl_item.create(def_id, ItemState.BAG)
            di.ref.pl_stack.remove(def_id, ItemState.BAG)
        else:
            raise RuntimeError("インスタンス化指定アイテムが不足しています")

        # デバッグログ
        logger.debug(f"処理後個数：{di.ref.pl_stack.count(def_id, ItemState.BAG)}")

        return pooled

    def set_adjust_effect(self):
        self._effect_cache.clear()
        targets = [
            pooled_item for pooled_item in self._equipped_items.values() if pooled_item is not None
        ]
        efx_list = [
            [plent.ins.param.effect_id, plent.ins.param.effect_value]
            for _, plent in targets
            if plent.ins.param.effect_id is not None
        ]
        for efx_id, efx_value in efx_list:
            effect_id = getattr(SkillID, efx_id.upper())
            if effect_id is not None:
                self._effect_cache[effect_id] = efx_value

    def get_adjust_effect(self, effect_id: SkillID):
        """補正系エフェクトの取得"""
        return self._effect_cache.get(effect_id, 0)

    def equip_on_pool(self, slot: EquipSlot, pooled_item: PooledItem):
        """アイテムプールのアイテムを装備"""

        # 既にそのスロットに装備品がある場合は、それを外す
        if self._equipped_items[slot] is not None:
            self.equip_off(slot)  # 既存の装備を外す

        # 新しいアイテムを装備
        self._equipped_items[slot] = pooled_item
        _, plent = pooled_item
        plent.stat = ItemState(self.owner)

        # 補正効果キャッシュを更新
        self.set_adjust_effect()

    def equip_on_consume(self, slot: EquipSlot, def_id: ItemID):
        """スタックプールのアイテム（消耗品）を装備"""
        pooled_item = self._convert_instance(def_id)
        self.equip_on_pool(slot, pooled_item)

    def equip_off(self, slot: EquipSlot):
        """アイテムの装備解除（消耗品の場合はスタック変換）"""
        target = self.get_slot(slot)
        if target is None:
            return
        _, plent_off = target
        plent_off.stat = ItemState.BAG
        self._equipped_items[slot] = None
        if plent_off.ins.param.item_type == ItemType.CONSUME:
            self._convert_stack(target)

        # 補正効果キャッシュを更新
        self.set_adjust_effect()

    def use_consume(self, slot: EquipSlot):
        """装備中の消耗品を消費"""
        target = self.get_slot(slot)
        def_id = target[1].ins.param.def_id  # type: ignore

        # 装備から解除しスタックに変換
        self.equip_off(slot)

        # スタックから該当IDのアイテムを1つ削除
        di.ref.pl_stack.remove(def_id, ItemState.FREE, 1)
