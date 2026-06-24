"""menu_field.py
メニューモジュール：フィールド
"""

import logging
from typing import Callable

# import pyxel as px
from gameutils.lib import (
    Menu,
    Window,
    ExecResult,
    RsltPush,
)  # , WindowAction, RsltContinue
# import service_locater as di

# from entity.character import EquipSlot
# from entity import EquipSlot
# from item.item_protocol import Owner
# from item.item_manager import ItemManager
# from menu import MenuItemWindow#, MenuSelectItemCategory

# from .menu_equip_slot import SelectEquipSlot # コメントアウト
# from item import ItemState
# from command import CommandType, CommandContext

# ロギング設定
logger = logging.getLogger(__name__)


class MenuField(Menu):
    def __init__(self, ctx_builder: Callable):
        menu_pos = (Window._chip_size // 2, Window._chip_size // 2)
        menu_shape = [1, 6]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        self.build_context = ctx_builder  # コマンド生成メニューでのコンテキスト構築用

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
        # now_point = di.ref.pt._current_point
        # print(now_point)

    def show_status(self):
        """ステータス参照"""
        from menu import MenuStatus

        return RsltPush(MenuStatus, self)

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
        # print("use skill")
        # print(f"{di.ref.hero.skills._learned_skills}")
        from menu import MenuSelectSkill

        return RsltPush(MenuSelectSkill, self.build_context)
