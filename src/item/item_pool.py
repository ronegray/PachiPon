from .item_protocol import ItemInstance
from collections import defaultdict, deque
from typing import Optional


class ItemPool:
    """全アイテムインスタンスを一元管理するプール"""

    def __init__(self, capacity: int = 4096):
        self._free: deque[int] = deque(range(capacity))
        self._items: dict[int, ItemInstance] = {}

    def create(self, def_id: int, owner_id: int) -> ItemInstance:
        """アイテムをプールに生成し、インスタンスを返す"""
        if not self._free:
            raise RuntimeError("ItemPool capacity exceeded")

        iid = self._free.popleft()
        inst = ItemInstance(instance_id=iid, def_id=def_id, owner_id=owner_id)
        self._items[iid] = inst
        return inst

    def destroy(self, iid: int) -> None:
        """アイテムを破棄し、IDを再利用可能にする"""
        self._items.pop(iid, None)
        self._free.append(iid)

    def get(self, iid: int) -> Optional[ItemInstance]:
        """IDからインスタンスを取得する"""
        return self._items.get(iid)

    def transfer(self, iid: int, new_owner: int) -> None:
        """所有者変更"""
        if iid in self._items:
            self._items[iid].owner_id = new_owner

    def get_by_owner(self, owner_id: int) -> list[ItemInstance]:
        """指定した所有者が持つアイテムリストを取得する"""
        return [inst for inst in self._items.values() if inst.owner_id == owner_id]


# --- スタック管理（素材など） ---
class StackPool:
    """(def_id, owner_id) → 数量 のシンプル管理"""

    def __init__(self):
        # {(def_id, owner_id): count}
        self._stacks: dict[tuple[int, int], int] = defaultdict(int)

    def add(self, def_id: int, owner_id: int, count: int = 1) -> None:
        self._stacks[(def_id, owner_id)] += count

    def remove(self, def_id: int, owner_id: int, count: int = 1) -> bool:
        key = (def_id, owner_id)
        if self._stacks[key] < count:
            return False  # 所持数不足
        self._stacks[key] -= count
        if self._stacks[key] == 0:
            del self._stacks[key]
        return True

    def transfer(
        self, def_id: int, from_owner: int, to_owner: int, count: int = 1
    ) -> bool:
        if self.remove(def_id, from_owner, count):
            self.add(def_id, to_owner, count)
            return True
        return False

    def count(self, def_id: int, owner_id: int) -> int:
        return self._stacks.get((def_id, owner_id), 0)
