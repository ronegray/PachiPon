"""
メニューモジュール：バトル
"""

import logging
# from typing import Callable
# from dataclasses import dataclass

import pyxel as px
from gameutils.lib import (
    Menu,
    Window,
    ExecResult,
    RsltContinue,
    RsltPush,
    RsltDiscard,
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

# from entity import Party
from entity import Character, EntityContext
import command.entity_command as e_cmd

# ロギング設定
logger = logging.getLogger(__name__)


class SubReturnFlag:
    state: bool = False


class MenuBattle(Menu):
    def __init__(
        self,
        ctx_source: EntityContext,
        actor_list: list[Character],  # 逆順生存メンバーリスト
        battle_commands: dict,
        message_window: Window,
    ):
        menu_pos = (0, 192)
        menu_shape = [1, 4]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        # self.windows["main"].y = px.height - self.height
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        self.ctx_source: EntityContext = ctx_source  # 再帰先へのコンテキスト引継用
        self.context: EntityContext = EntityContext(
            ctx_source.situation,
            ctx_source.actor,
            ctx_source.allies,
            ctx_source.targets,
        )
        # logger.info(f"\nMenuBattle init \nsrc  {ctx_source}\nlocal{self.context}")
        self.actor_list: list[Character] = actor_list[0:]
        self.context.actor = self.ctx_source.actor = self.actor_list.pop()
        # logger.info(f"\nactors \nself{self.actor_list}\narg{actor_list}\nctx{self.context.actor}")
        self.context.actor.defend(False)  # コマンド入力前に一旦防御体勢解除
        self.battle_commands: dict = battle_commands
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
        # 名前ウインドウ定義
        name_pos = (self.x, self.y - 32)
        name_size = (80, 32)
        self.windows["sub2"] = Window("basic", *name_pos, *name_size, "once")
        self.windows["sub2"].set_message([self.context.actor.param.name])
        # サブメニューからの戻り済フラグ
        self.is_submenu_return: SubReturnFlag = SubReturnFlag()

    # def individual_update(self) -> ExecResult:
    #     if self.is_submenu_return.state:
    #         return RsltPush(MenuBattle, self.ctx_source, self.actor_list, self.battle_commands, self.message_window)
    #     return RsltContinue()

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

    def select_target(self):
        """ユーザ行動コマンド：攻撃する／ターゲットの選択メニューへ"""

        # self.battle_commands[self.context.actor.id] = e_cmd.DefenceMode(self.context, self.message_window)
        # return self.return_exec()
        # サブメニュー進入前に戻りフラグをOFF
        self.is_submenu_return.state = False
        # ここで引き継ぐコンテキストはソース側（可変事項は呼び出し先で設定）
        return RsltPush(
            MenuSelectTarget,
            self.ctx_source,
            self.actor_list,
            self.battle_commands,
            self.message_window,
            self.windows["sub"],
            self.is_submenu_return,
        )

    def select_item(self):
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

    def select_skill(self):
        """スキル表示メニューを開く"""
        # print("use skill")
        # print(f"{di.ref.hero.skills._learned_skills}")
        from menu import MenuSelectSkill

        return RsltPush(MenuSelectSkill, self.context)

    def defence_mode(self):
        """ユーザ行動コマンド：防御体勢"""
        # ally_list = [] # 防御にターゲット不要
        # target_list = [] # 防御にターゲット不要
        # ctx = self.context(self.actor, ally_list, target_list)
        # self.context.allies = []
        # self.context.targets = []
        self.battle_commands[self.context.actor.id] = e_cmd.DefenceMode(
            self.context, self.message_window
        )
        return self.return_exec()

    def return_exec(self):
        """コマンド入力完了確認"""
        if not self.actor_list:
            return RsltDiscard()
        return RsltPush(
            MenuBattle,
            self.ctx_source,
            self.actor_list,
            self.battle_commands,
            self.message_window,
        )


class MenuSelectTarget(Menu):
    """バトルサブメニュー：ターゲット選択"""

    def __init__(
        self,
        ctx_source: EntityContext,
        actor_list: list[Character],  # 逆順生存メンバーリスト
        battle_commands: dict,
        message_window: Window,
        ref_window: Window,
        submenu_return: SubReturnFlag,
    ):
        self.ctx_source: EntityContext = ctx_source  # 再帰先へのコンテキスト引継用
        self.context: EntityContext = EntityContext(
            ctx_source.situation,
            ctx_source.actor,
            ctx_source.allies,
            ctx_source.targets,
        )
        # print(f"\nsrc {id(self.ctx_source.targets)}\nctx {id(self.context.targets)}")
        self.actor_list: list[Character] = actor_list
        self.battle_commands: dict = battle_commands
        self.message_window: Window = message_window
        self.is_submenu_return: SubReturnFlag = submenu_return

        self.item_list: list = []
        self.generate_item_list()
        menu_pos = (ref_window.x, ref_window.y)
        menu_size = (ref_window.width, ref_window.height)

        super().__init__(
            "basic", *menu_pos, self.menu_shape, self.item_list, *menu_size
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

    def generate_item_list(self):
        """アイテムリストの生成"""

        menu_cols = 2
        enemy_count = len(self.context.targets)
        if enemy_count <= 0:
            errmsg = "ターゲット対象リストが空の状態です"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        else:
            tmp_item_list = [
                [
                    {
                        "id": f"{target.param.name}",
                        "action": "set_target",
                        "args": [target.id, "Attack"],
                    }
                ]
                for idx, target in enumerate(self.context.targets)
                if target.is_alive
            ]

            tmp_list = []
            cnt = 0
            for i, tmp_item in enumerate(tmp_item_list):
                if i % menu_cols == 0:
                    tmp_list = [].copy()
                tmp_list.append(tmp_item[0])
                if len(tmp_list) == menu_cols:
                    self.item_list.append(tmp_list.copy())
                    cnt += 2
            if len(tmp_item_list) != cnt:
                # list[list[dict[str, str]]]
                self.item_list.append(tmp_list.copy())

        self.menu_shape = [menu_cols, len(self.item_list)]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        try:
            selected_item = self.menu_items[pos_y][pos_x]
        except IndexError:
            # 空データを選択した時はスルー
            return RsltContinue()
        # logger.info(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        # logger.info(
        #     f"選択メニュー実行：{selected_item.item_label}"
        # )
        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def set_target(self, id: int, command: str) -> ExecResult:
        """コンテキストにターゲットを設定"""
        for i, target in enumerate(self.context.targets):
            if target.id == id:
                self.context.target_index = i
                print(f"{i}={target.param.name}")
        cmd = getattr(e_cmd, command)
        # logger.info(f"\nselect command\n{cmd}")
        # cmd(self.context, self.message_window)
        self.battle_commands[self.context.actor.id] = cmd(
            self.context, self.message_window
        )
        logger.info(f"\nctx for command list\n{self.context}")
        # # サブメニュー終了フラグを立てて前のメニューに戻る
        # self.is_submenu_return.state = True
        # return RsltPop()

        # 自分自身をpopしてから次メンバーのバトルメニューをpush（無理やり）
        import service_locater as di

        di.ref.scnmgr.get_now_scene().wndmgr.pop_stack()
        if not self.actor_list:
            return RsltDiscard()
        return RsltPush(
            MenuBattle,
            self.ctx_source,
            self.actor_list,
            self.battle_commands,
            self.message_window,
        )
