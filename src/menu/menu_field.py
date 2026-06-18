"""menu_field.py
メニューモジュール：フィールド
"""
import logging

# import pyxel as px
from gameutils.lib import (
    Menu,
    Window,
    ExecResult,
    RsltPush,
)  # , WindowAction, RsltContinue
import service_locater as di

# from entity.character import EquipSlot
# from entity import EquipSlot
# from item.item_protocol import Owner
# from item.item_manager import ItemManager
# from menu import MenuItemWindow#, MenuSelectItemCategory

# from .menu_equip_slot import SelectEquipSlot # コメントアウト
# from item import ItemState


# ロギング設定
logger = logging.getLogger(__name__)


class MenuField(Menu):
    def __init__(self):
        menu_pos = (Window._chip_size // 2, Window._chip_size // 2)
        menu_shape = [1, 5]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )
        result = selected_item.menu_action(*selected_item.action_args)

        # return WindowAction.DISCARD
        # return RsltContinue()
        return result

    def enter_shop(self):
        print("enter shop")
        now_point = di.ref.pt._current_point
        print(now_point)

    def show_status(self):
        # # print("show status")
        # # hero = di.ref.hero
        # # param = hero.base_param
        # mem_id = di.ref.pt.get_leader_id()
        # member = di.ref.pt.get_member(mem_id)
        # param = member.base_param

        # # # ステータス項目の構築
        # # status_lines = [
        # #     f"{param.name}",
        # #     f"レベル： {param.level:2}",
        # #     f"経験値： {param.exp:5}",
        # #     f"Ｈ　Ｐ： {param.hp:3}／{param.max_hp:3}",
        # #     f"Ｍ　Ｐ： {param.mp:3}／{param.max_mp:3}",
        # #     f"筋　力： {hero.strength:3}",
        # #     f"魔　力： {hero.arcane:3}",
        # #     f"耐　久： {hero.endurance:3}",
        # #     f"速　度： {hero.speed:3}",
        # #     f"幸　運： {hero.luck:3}",
        # #     # "--- 装備 ---"
        # # ]

        # # 装備項目の構築
        # slots = [
        #     (EquipSlot.WEAPON, "武　器"),
        #     (EquipSlot.GUARDER, "防　具"),
        #     (EquipSlot.ACCESSORY_1, "装飾１"),
        #     (EquipSlot.ACCESSORY_2, "装飾２"),
        #     (EquipSlot.CONSUME_1, "消費１"),
        #     (EquipSlot.CONSUME_2, "消費２"),
        # ]

        # # for slot, label in slots:
        # #     item_def = hero.equipments.get_itemdef(slot)
        # #     item_name = item_def.name if item_def else "なし"
        # #     status_lines.append(f"{label}： {item_name}")
        # status_lines = f"{param.name}"
        # status_lines += f"\nレベル： {param.level:2}"
        # status_lines += f"\n経験値： {param.exp:5}"
        # status_lines += f"\nＨ　Ｐ： {param.hp:3}／{param.max_hp:3}"
        # status_lines += f"\nＭ　Ｐ： {param.mp:3}／{param.max_mp:3}"
        # status_lines += f"\n筋　力： {member.strength:3}(+{member.bonus_str})"
        # status_lines += f"\n魔　力： {member.arcane:3}(+{member.bonus_arc})"
        # status_lines += f"\n耐　久： {member.endurance:3}(+{member.bonus_end})"
        # status_lines += f"\n速　度： {member.speed:3}(+{member.bonus_spd})"
        # status_lines += f"\n幸　運： {member.luck:3}(+{member.bonus_lck})"
        # equip_lines = ""
        # for slot, label in slots:
        #     pooled_item = member.equipments.get_slot(slot)
        #     if pooled_item is None:
        #         item_name = "なし"
        #     else:
        #         _, plent = pooled_item
        #         item_name = plent.ins.param.name
        #     # status_lines += f"\n{label}： {item_name}"
        #     equip_lines += f"{label}： {item_name}\n"

        # # ウィンドウのプッシュ
        # # サイズはメニューの位置から画面右下端まで
        # param_w, param_h = 128, 136
        # equip_w, equip_h = 128, 88

        # # 現在のシーンのWindowManagerを取得
        # wndmgr = di.ref.scnmgr.stacks[-1].wndmgr

        # # Windowをスタックに追加
        # # pos_x, pos_y = self.cursor_position
        # # cursor_x = self.windows["main"].x + self.column_x_pos[pos_x]
        # # cursor_y = (
        # #     self.windows["main"].y + self.row_y_pos[pos_y] + self.cursor_row_offset
        # # )
        # # win_param = wndmgr.push_stack(
        # #     Window, "basic", cursor_x + 8, cursor_y + 8, param_w, param_h, "once"
        # # )
        # pos_x = self.windows["main"].x + self.windows["main"].width
        # pos_y = 0
        # padding = 2
        # win_param = wndmgr.push_stack(
        #     Window, "basic", pos_x + padding, pos_y + padding, param_w, param_h, "once"
        # )
        # win_equip = wndmgr.push_stack(
        #     Window, "basic", win_param.x,
        #     win_param.y + win_param.height + padding, equip_w, equip_h, "once"
        # )
        # if isinstance(win_param, Window):
        #     win_param.text_list = [status_lines]
        # if isinstance(win_equip, Window):
        #     win_equip.text_list = [equip_lines]
        from menu import MenuStatus

        # di.ref.scnmgr.stacks[-1].wndmgr.push_stack(
        #     MenuSelectItemCategory,
        #     self.cursor_x + Window._chip_size,
        #     self.cursor_y + Window._chip_size,
        # )
        return RsltPush(MenuStatus)

    def select_item_category(self):
        """アイテム表示メニューを開く"""
        # print("select item category")
        from menu import MenuSelectItemCategory

        # di.ref.scnmgr.stacks[-1].wndmgr.push_stack(
        #     MenuSelectItemCategory,
        #     self.cursor_x + Window._chip_size,
        #     self.cursor_y + Window._chip_size,
        # )
        return RsltPush(
            MenuSelectItemCategory,
            self.cursor_x + Window._chip_size + 1,
            self.cursor_y + Window._chip_size + 1,
        )

    def equip_item(self):
        """装備選択メニューを開く"""
        print("equip_item")
        # print("select item category")
        from menu import MenuSelectEquipSlot

        # di.ref.scnmgr.stacks[-1].wndmgr.push_stack(
        #     MenuSelectItemCategory,
        #     self.cursor_x + Window._chip_size,
        #     self.cursor_y + Window._chip_size,
        # )
        return RsltPush(MenuSelectEquipSlot)

    def use_skill(self):
        """スキル表示メニューを開く"""
        print("use skill")
