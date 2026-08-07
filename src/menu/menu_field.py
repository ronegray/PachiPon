"""
メニューモジュール：フィールド
"""

import logging
import pyxel as px
from gameutils.lib import (
    Menu,
    Window,
    ExecResult,
    RsltPush,
    RsltDiscard,
)
import service_locater as di
from entity import EntityContext
from item import ItemPool, StackPool
import command.entity_command as e_cmd


# ロギング設定
logger = logging.getLogger(__name__)


class MenuField(Menu):
    def __init__(
        self,
        ctx: EntityContext,
        command_package: e_cmd.CommandPackage,
        pool_item: ItemPool,
        pool_stack: StackPool,
    ):
        menu_pos = (4, 4)
        menu_shape = [2, 3]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.ctx = ctx
        self.command_package = command_package
        self.pool_item = pool_item
        self.pool_stack = pool_stack

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def enter_shop(self):
        """商店メニューを開く"""

        di.ref.scnmgr.next_scene("shop")
        return RsltDiscard()

    def show_status(self):
        """ステータスメニューを開く"""
        from menu import MenuStatus

        return RsltPush(MenuStatus, self)

    def select_item_category(self):
        """アイテム表示メニューを開く"""
        from menu import MenuSelectItemCategory

        return RsltPush(
            MenuSelectItemCategory,
            self.cursor_x + Window._chip_size + 1,
            self.cursor_y + Window._chip_size + 1,
            self.ctx,
            self.command_package,
        )

    def equip_item(self):
        """装備選択メニューを開く"""
        print("equip_item")
        from menu import MenuSelectEquipSlot

        return RsltPush(MenuSelectEquipSlot, self)

    def select_skill(self):
        """スキル選択メニューを開く"""
        from menu import MenuSelectSkillField

        return RsltPush(
            MenuSelectSkillField,
            self.ctx,
            {
                "x": self.x + self.width,
                "y": self.y + self.cursor_y,
                "w": px.width - self.width,
                "h": self.height,
            },
            self.command_package,
        )
