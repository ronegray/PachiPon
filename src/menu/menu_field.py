"""menu_field.py
メニューモジュール：フィールド
"""

import logging
#####from typing import Callable

import pyxel as px
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

from entity import EntityContext  # Character,

# ロギング設定
logger = logging.getLogger(__name__)


class MenuField(Menu):
    # def __init__(self, ctx_builder: Callable):
    #     menu_pos = (Window._chip_size // 2, Window._chip_size // 2)
    #     menu_shape = [2, 3]
    #     super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
    #     self.cursor_row_offset += 2  # k8x12Sの縦長分対応
    #     self.build_context = ctx_builder  # コマンド生成メニューでのコンテキスト構築用
    def __init__(
        self,
        ctx_source: EntityContext,
        # actor_list: list[Character],  # 逆順生存メンバーリスト
        # battle_commands: dict,
        message_window: Window,
    ):
        menu_pos = (Window._chip_size // 2, Window._chip_size // 2)
        menu_shape = [2, 3]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.ctx_source: EntityContext = ctx_source  # 再帰先へのコンテキスト引継用
        self.context: EntityContext = EntityContext(
            ctx_source.situation,
            ctx_source.actor,
            ctx_source.allies,
            ctx_source.targets,
        )
        # logger.info(f"\nMenuBattle init \nsrc  {ctx_source}\nlocal{self.context}")
        # self.actor_list: list[Character] = actor_list[0:]
        # self.actor_list: list[Character] = actor_list.copy()
        # self.context.actor = self.ctx_source.actor = self.actor_list.pop()
        # self.context.actor = self.ctx.
        # logger.info(f"\nactors \nself{self.actor_list}\narg{actor_list}\nctx{self.context.actor}")
        # self.context.actor.defend(False)  # コマンド入力前に一旦防御体勢解除
        # self.battle_commands: dict = battle_commands
        self.message_window: Window = message_window
        # サブウインドウ定義
        self.windows["sub"] = Window(
            "basic",
            self.x + self.width,
            self.y,
            px.width - self.width,
            self.height,
            "once",
        )
        # # 名前ウインドウ定義（表示順制御の為self.windowsに乗せない）
        # name_pos = (self.x, self.y - 17)
        # name_size = (80, 32)
        # # self.windows["sub2"] = Window("basic", *name_pos, *name_size, "once")
        # # self.windows["sub2"].set_message([self.context.actor.param.name])
        # self.namewindow = Window("basic", *name_pos, *name_size, "once")
        # # self.namewindow.set_message([self.context.actor.param.name])

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

        return RsltPush(
            MenuSelectItemCategory,
            self.cursor_x + Window._chip_size + 1,
            self.cursor_y + Window._chip_size + 1,
        )

    def equip_item(self):
        """装備選択メニューを開く"""
        print("equip_item")
        from menu import MenuSelectEquipSlot

        return RsltPush(MenuSelectEquipSlot)

    def use_skill(self):
        """スキル表示メニューを開く"""
        # print("use skill")
        # print(f"{di.ref.hero.skills._learned_skills}")
        # from menu import MenuSelectSkillold

        # return RsltPush(MenuSelectSkillold, self.build_context)
        from menu import MenuSelectSkill

        return RsltPush(
            MenuSelectSkill,
            self.context.actor,
            self.ctx_source,
            [],
            {},
            self.message_window,
            self.message_window,
        )
        # self,
        # real_actor: Character,
        # ctx_source: EntityContext,
        # actor_list: list[Character],  # 逆順生存メンバーリスト
        # battle_commands: dict,
        # message_window: Window,
        # # サイズや位置を確認する為の参照用　実処理で使わない
        # ref_window: Window,
