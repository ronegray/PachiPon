from pathlib import Path
from item import ItemManager, ItemOwner, ItemPool, StackPool
import service_locater as di
from gameutils.base import AssetManager


def test_init():
    app_root_path = Path(".").resolve()
    AssetManager.get_rootpath(str(app_root_path))
    AssetManager.initialize_assetmap()
    ItemManager.initialize()

    di.register(di.DIKey.ITMPOL, ItemPool())
    di.register(di.DIKey.STKPOL, StackPool())

    for item_def_id, item_def in ItemManager.get_all_definitions().items():
        for _ in range(2):
            if item_def.stackable:
                di.ref.stkpool.add(item_def_id, ItemOwner.BAG, 1)
            else:
                di.ref.itempool.create(item_def_id, ItemOwner.BAG)

    bag_items = di.ref.itempool.get_by_owner(ItemOwner.BAG)
    print(f"ItemPool (Non-stackable) items in BAG: {len(bag_items)}")

    for item_def_id, item_def in ItemManager.get_all_definitions().items():
        if item_def.stackable:
            count = di.ref.stkpool.count(item_def_id, ItemOwner.BAG)
            print(f"Stackable Item {item_def.name} (ID:{item_def_id}) count: {count}")


if __name__ == "__main__":
    test_init()
