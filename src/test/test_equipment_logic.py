import pyxel
from item.item_manager import ItemManager
from item.item_pool import ItemPool
from item.item_protocol import ItemID, Owner
from character import Character, EquipmentSlot
from character_param import CharacterParam
from player_sprite import PlayerSprite
import service_locater as di
from service_locater import DIKey


def test_equipment():
    # Pyxel初期化（ヘッドレスモード）
    pyxel.init(160, 144, quit_key=pyxel.KEY_ESCAPE, fps=60)

    # 依存関係の初期化
    from gameutils.base import AssetManager

    AssetManager.get_rootpath(".")  # 現在のディレクトリをルートパスとして設定
    AssetManager.initialize_assetmap()
    ItemManager.initialize()
    item_pool = ItemPool()

    # キャラクター作成
    param = CharacterParam(
        name="TestHero",
        strength=10,
        defense=5,
        magic=0,
        hp=100,
        mp=50,
        speed=0,
        luck=0,
        exp=0,
        level=1,
    )
    sprite = PlayerSprite(0, 0, img=0)
    hero = Character(param, sprite, id=1)

    # サービスロケータ登録
    di.register(DIKey.HERO, hero)
    di.register(DIKey.ITMPOL, item_pool)

    print(f"Initial ATK: {di.ref.hero.get_attack_power()}")
    print(f"Initial DFN: {di.ref.hero.get_defense_power()}")

    # アイテム生成 (ダガー: ATK+2)
    dagger = di.ref.itempool.create(ItemID.DAGGER, owner_id=Owner.FREE.value)
    print(
        f"Created: {ItemManager.get_def(dagger.def_id).name} (ID: {dagger.instance_id})"
    )

    # 装備
    di.ref.hero.equipments.equip_on(dagger)
    print("Equipped Dagger")

    print(f"New ATK: {di.ref.hero.get_attack_power()} (Expected: 12)")
    print(f"Is Dagger equipped?: {dagger.state.equipped}")

    # 防具装備 (レザーアーマー: DFN+2)
    leather = di.ref.itempool.create(ItemID.LEATHER, owner_id=Owner.FREE.value)
    di.ref.hero.equipments.equip_on(leather)
    print("Equipped Leather Armor")
    print(f"New DFN: {di.ref.hero.get_defense_power()} (Expected: 7)")

    # 装備解除
    di.ref.hero.equipments.equip_off(EquipmentSlot.WEAPON)
    print("Unequipped Dagger")
    print(f"ATK after unequip: {di.ref.hero.get_attack_power()} (Expected: 10)")
    print(f"Is Dagger equipped?: {dagger.state.equipped}")

    pyxel.quit()


if __name__ == "__main__":
    try:
        test_equipment()
        print("Test Success!")
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback

        traceback.print_exc()
