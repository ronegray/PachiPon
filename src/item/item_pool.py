import logging
from collections import defaultdict, deque
import service_locater as di
from .item_protocol import (
    ItemID,
    ItemType,
    ItemState,
    ItemInstance,
    PoolEntry,
    PooledItem,
)  # , UniqueIdentifyItem


# ロギング設定
logger = logging.getLogger(__name__)


class ItemPool:
    """全アイテムインスタンスを一元管理するプール"""

    # a = {"id": int, "inst": ItemInstance, "item": ItemState}

    def __init__(self, capacity: int = 4096):
        self._free: deque[int] = deque(range(capacity))
        # self._items: dict[int, PoolEntry] = {}
        self._items: dict[int, PoolEntry] = {}

    def get_def(self, def_id: ItemID):
        return di.ref.itemmgr.get_def(def_id)

    # def create(self, def_id: ItemID, state: ItemState) -> tuple[int, PoolEntry]:
    def create(self, def_id: ItemID, state: ItemState) -> PooledItem:
        """アイテムをプールに生成し、インスタンスを返す"""
        if not self._free:
            raise RuntimeError("ItemPool capacity exceeded")

        iid = self._free.popleft()
        item_def = self.get_def(def_id)
        if item_def is None:
            errmsg = f"アイテムIDが定義されていません：{def_id}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        # プールエントリ情報を生成し、フリー利用IDをキーにプール追加
        pe = PoolEntry(ins=ItemInstance(param=item_def), stat=state)
        self._items[iid] = pe

        return iid, pe

    def destroy(self, iid: int) -> None:
        """アイテムを破棄し、IDを再利用可能にする"""
        self._items.pop(iid, None)
        self._free.append(iid)

    def get(self, iid: int) -> PoolEntry | None:
        """IDからインスタンスを取得する"""
        return self._items.get(iid)

    def transfer(self, iid: int, new_owner: ItemState) -> None:
        """所有者変更"""
        if iid in self._items:
            self._items[iid].stat = new_owner

    def get_by_state(self, owner_id: ItemState) -> dict[int, PoolEntry]:
        """指定した所有者が持つアイテムリストを取得する"""
        return {uqid: pe for uqid, pe in self._items.items() if pe.stat == owner_id}

    def get_by_type(self, item_type: ItemType) -> dict[int, PoolEntry]:
        """指定したタイプのアイテムリストを取得する"""
        return {
            uqid: pe
            for uqid, pe in self._items.items()
            if pe.ins.param.item_type == item_type
        }

    def get_by_category(self, item_category: ItemID) -> dict[int, PoolEntry]:
        """指定したカテゴリ（アイテム種）のアイテムリストを取得する"""
        return {
            uqid: pe
            for uqid, pe in self._items.items()
            if pe.ins.param.def_id == item_category
        }


# --- スタック管理（素材など） ---
class StackPool:
    """(def_id, owner_id) → 数量 のシンプル管理"""

    def __init__(self):
        # {(def_id, owner_id): count}
        self._stacks: dict[tuple[ItemID, ItemState], int] = defaultdict(int)

    def get_def(self, def_id: ItemID):
        return di.ref.itemmgr.get_def(def_id)

    def add(self, def_id: ItemID, state: ItemState, count: int = 1) -> None:
        """スタックへのアイテム追加・数量加算"""
        self._stacks[(def_id, state)] += count

    def remove(self, def_id: ItemID, owner_id: ItemState, count: int = 1) -> bool:
        """スタックアイテムの数量減算・削除"""
        key = (def_id, owner_id)
        if self._stacks[key] < count:
            return False  # 所持数不足
        self._stacks[key] -= count
        if self._stacks[key] == 0:
            del self._stacks[key]
        return True

    def transfer(
        self, def_id: ItemID, from_owner: ItemState, to_owner: ItemState, count: int = 1
    ) -> bool:
        """スタックアイテムの移動（BAG⇔FREEの行き来を想定）"""
        if self.remove(def_id, from_owner, count):
            self.add(def_id, to_owner, count)
            return True
        return False

    def count(self, def_id: ItemID, owner_id: ItemState) -> int:
        return self._stacks.get((def_id, owner_id), 0)

    def get_by_state(self, state: ItemState) -> dict[ItemID, int]:
        """指定した者が持つアイテムリストを取得する"""
        return {
            keypair[0]: cnt
            for keypair, cnt in self._stacks.items()
            if keypair[1] == state
        }
