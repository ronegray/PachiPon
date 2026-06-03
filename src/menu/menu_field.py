# import pyxel as px
from gameutils.lib.window import Menu, Window
from gameutils.base import FONT_SIZE_NAME
import service_locater as di
from entity.character import EquipmentSlot
# from item.item_protocol import Owner
# from item.item_manager import ItemManager
# from .menu_item import MenuItemWindow
# from .menu_equip_slot import SelectEquipSlot # コメントアウト


class MenuField(Menu):
    def __init__(self, font_size_name: FONT_SIZE_NAME, x: int, y: int):
        menu_data = [
            [{"id": "ダイス", "action": "None"}],
            [{"id": "ステータス", "action": "show_status"}],
            [{"id": "アイテム", "action": "show_items"}],
            [{"id": "装備", "action": "None"}],  # show_equip_menu から None に戻す
            [{"id": "スキル", "action": "None"}],
        ]
        super().__init__(font_size_name, x, y, [1, 5], menu_data)

    def show_status(self):
        hero = di.ref.hero
        param = hero.param

        # ステータス項目の構築
        status_lines = [
            f"{param.name}",
            f"レベル： {param.level:2}",
            f"経験値： {param.exp:5}",
            f"Ｈ　Ｐ： {param.hp:3}／{param.max_hp:3}",
            f"Ｍ　Ｐ： {param.mp:3}／{param.max_mp:3}",
            f"筋　力： {param.strength:3}",
            f"魔　力： {param.magic:3}",
            f"耐　久： {param.defense:3}",
            f"速　度： {param.speed:3}",
            f"幸　運： {param.luck:3}",
            # "--- 装備 ---"
        ]

        # 装備項目の構築
        slots = [
            (EquipmentSlot.WEAPON, "武　器"),
            (EquipmentSlot.GUARDER, "防　具"),
            (EquipmentSlot.ACCESSORY_1, "装飾１"),
            (EquipmentSlot.ACCESSORY_2, "装飾２"),
            (EquipmentSlot.CONSUME_1, "消費１"),
            (EquipmentSlot.CONSUME_2, "消費２"),
        ]

        for slot, label in slots:
            item_def = hero.equipments.get_itemdef(slot)
            item_name = item_def.name if item_def else "なし"
            status_lines.append(f"{label}： {item_name}")

        # ウィンドウのプッシュ
        # サイズはメニューの位置から画面右下端まで
        # main_win = self.windows["main"]
        win_width = 128
        win_height = 208

        # 現在のシーンのWindowManagerを取得
        wndmgr = di.ref.scnmgr.stacks[-1].wndmgr

        # Windowをスタックに追加
        pos_x, pos_y = self.cursor_position
        cursor_x = self.windows["main"].x + self.column_x_pos[pos_x]
        cursor_y = (
            self.windows["main"].y + self.row_y_pos[pos_y] + self.cursor_row_offset
        )
        wndmgr.push_stack(
            Window, "basic", cursor_x + 8, cursor_y + 8, win_width, win_height, "once"
        )

        # メッセージを追加（Windowインスタンスはスタックの最後にある）
        new_win = wndmgr.stacks[-1]
        if isinstance(new_win, Window):
            # for line in status_lines:
            #     new_win.add_message(line)
            new_win.text_list = status_lines

    def show_items(self):
        """アイテム表示メニューを開く"""
        pass

    #     item_pool = di.ref.itempool
    #     stack_pool = di.ref.stkpool

    #     menu_items = []

    #     # StackPool (消耗品など) から取得
    #     # _stacks: dict[tuple[int, int], int] = {(def_id, owner_id): count}
    #     for (def_id, owner_id), count in stack_pool._stacks.items():
    #         if owner_id == Owner.BAG:
    #             item_def = ItemManager.get_def(def_id)
    #             if item_def:
    #                 menu_items.append(
    #                     {
    #                         "id": f"{item_def.name} x{count}",
    #                         "action": "None",
    #                         "description": item_def.description,
    #                         "callable_action": None,
    #                         "action_args": (),
    #                     }
    #                 )

    #     # ItemPool (装備品など) から取得
    #     bag_items = item_pool.get_by_owner(Owner.BAG)
    #     for inst in bag_items:
    #         item_def = ItemManager.get_def(inst.def_id)
    #         if item_def:
    #             menu_items.append(
    #                 {
    #                     "id": item_def.name,
    #                     "action": "None",
    #                     "description": item_def.description,
    #                     "callable_action": None,
    #                     "action_args": (),
    #                 }
    #             )

    #     if not menu_items:
    #         menu_items.append(
    #             {
    #                 "id": "なし",
    #                 "action": "None",
    #                 "description": "アイテムを持っていません",
    #                 "callable_action": None,
    #                 "action_args": (),
    #             }
    #         )

    #     # ウィンドウサイズと位置の設定
    #     # menu_fieldの描画右端位置から画面右端まで
    #     # 画面上端から下端まで
    #     main_win = self.windows["main"]
    #     x = main_win.x + main_win.width
    #     y = 0
    #     width = pyxel.width - x
    #     height = pyxel.height

    #     # 最小幅の確保
    #     if width < 64:
    #         width = 64
    #         x = pyxel.width - width

    #     # 現在のシーンのWindowManagerを取得
    #     wndmgr = di.ref.scnmgr.stacks[-1].wndmgr

    #     # MenuItemWindowをスタックに追加
    #     # MenuItemWindow(font_size_name, x, y, width, height, items)
    #     wndmgr.push_stack(MenuItemWindow, "basic", x, y, width, height, menu_items)

    # # def show_equip_menu(self):
    # #     """装備選択メニューを開く"""
    # #     hero: Character = di.ref.hero
    # #
    # #     main_win = self.windows["main"]
    # #     x = main_win.x + main_win.width
    # #     y = 0 # フィールドメニューのすぐ右、画面上端から
    # #
    # #     wndmgr = di.ref.scnmgr.stacks[-1].wndmgr
    # #     wndmgr.push_stack(SelectEquipSlot, "basic", x, y, hero)
