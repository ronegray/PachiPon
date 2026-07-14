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
    MENU_ITEM_LIST,
    ExecResult,
    RsltContinue,
    RsltPush,
    RsltDiscard,
    # RsltReplace,
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

from entity import EntityContext, EntityBase
from skill import TargetType

import command.entity_command as e_cmd
# from command import Attack, DefenceMode, UseItem, UseSkill


# ロギング設定
logger = logging.getLogger(__name__)


# class SubReturnFlag:
#     state: bool = False


class MenuBattle(Menu):
    def __init__(
        self,
        # ctx_source: EntityContext,
        ctx: EntityContext,
        # actor_list: list[Character],  # 逆順生存メンバーリスト
        # battle_commands: dict,
        # message_window: Window,
        command_package: e_cmd.CommandPackage,
    ):
        menu_pos = (0, 192)
        menu_shape = [1, 4]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        # self.windows["main"].y = px.height - self.height
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        # self.ctx_source: EntityContext = ctx_source  # 再帰先へのコンテキスト引継用
        # self.context: EntityContext = EntityContext(
        #     situation=ctx_source.situation,
        #     actor=ctx_source.actor,
        #     target=ctx_source.target,
        #     allies=ctx_source.allies,
        #     targets=ctx_source.targets,
        # )
        self.context = ctx
        self.command_package = command_package
        # logger.info(f"\nMenuBattle init \nsrc  {ctx_source}\nlocal{self.context}")
        # self.actor_list: list[Character] = actor_list[0:]
        # self.actor_list: list[Character] = actor_list.copy()
        # # self.context.actor = self.ctx_source.actor = self.actor_list.pop()
        # self.context.actor = self.actor_list.pop()
        # logger.info(f"\nactors \nself{self.actor_list}\narg{actor_list}\nctx{self.context.actor}")
        self.context.actor.defend(False)  # コマンド入力前に一旦防御体勢解除
        # self.battle_commands: dict = battle_commands
        # self.message_window: Window = message_window
        # サブウインドウ定義
        self.windows["sub"] = Window(
            "basic",
            self.x + self.width,
            self.y,
            px.width - self.width,
            self.height,
            "once",
        )
        # 名前ウインドウ定義（表示順制御の為self.windowsに乗せない）
        name_pos = (self.x, self.y - 17)
        name_size = (80, 32)
        # self.windows["sub2"] = Window("basic", *name_pos, *name_size, "once")
        # self.windows["sub2"].set_message([self.context.actor.param.name])
        self.namewindow = Window("basic", *name_pos, *name_size, "once")
        # self.namewindow.set_message([self.context.actor.param.name])

    def draw(self):
        """名前ウインドウの下部を隠す為順序制御"""
        self.namewindow.draw()
        self.namewindow.drawText(
            self.namewindow.x + 6,
            self.namewindow.y + 4,
            [[self.context.actor.param.name]],
            px.COLOR_WHITE,
        )
        super().draw()

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        # logger.debug(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        # logger.debug(
        #     f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        # )
        result = selected_item.menu_action(*selected_item.action_args)

        # # return WindowAction.DISCARD
        # # return RsltContinue()
        # logger.debug(
        #     f".exec_menu {id(self)}/{self.context.actor}\nin {self.actor_list}"
        # )
        return result

    def select_target(self):
        """ユーザ行動コマンド：攻撃する／ターゲットの選択メニューへ"""

        # self.battle_commands[self.context.actor.id] = e_cmd.DefenceMode(self.context, self.message_window)
        # return self.return_exec()
        # # サブメニュー進入前に戻りフラグをOFF
        # self.is_submenu_return.state = False
        # サブメニューへの引継時、コンテキストは引き回し中に書き換えるとキャンセル動作がおかしくなる
        # self.context.pending_command = (
        #     lambda: e_cmd.Attack(self.context)#, self.message_window)
        # )

        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = e_cmd.Attack
        self.command_package.target_type = TargetType.ENEMY

        return RsltPush(
            MenuSelectBattleTarget,
            # self.context.actor,  # 追加
            # self.ctx_source,
            # self.actor_list,
            self.context,
            # self.battle_commands,
            # self.message_window,
            {
                "x": self.windows["sub"].x,
                "y": self.windows["sub"].y,
                "w": self.windows["sub"].width,
                "h": self.windows["sub"].height,
            },
            self.command_package.target_type,
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

        return RsltPush(
            MenuSelectSkill,
            # self.context.actor,  # 追加
            # self.ctx_source,
            # self.actor_list,
            self.context,
            # self.battle_commands,
            # self.message_window,
            # self.windows["sub"],
            {
                "x": self.windows["sub"].x,
                "y": self.windows["sub"].y,
                "w": self.windows["sub"].width,
                "h": self.windows["sub"].height,
            },
            # self.is_submenu_return,
            self.command_package,
        )

    def defence_mode(self):
        """ユーザ行動コマンド：防御体勢"""
        # self.battle_commands[self.context.actor.id] = e_cmd.DefenceMode(
        #     self.context, self.message_window
        # )
        # return self.return_exec()
        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = e_cmd.DefenceMode
        self.command_package.target_type = TargetType.SELF
        return RsltDiscard()

    # def return_exec(self):
    #     """コマンド入力完了確認"""
    #     # if not self.actor_list:
    #     #     return RsltDiscard()
    #     return RsltPush(
    #         MenuBattle,
    #         # self.ctx_source,
    #         # self.actor_list,
    #         self.context,
    #         # self.battle_commands,
    #         # self.message_window,
    #     )


class MenuSelectBattleTarget(Menu):
    """行動サブメニュー：戦闘ターゲット選択"""

    def __init__(
        self,
        # real_actor: Character,
        ctx_source: EntityContext,
        # actor_list: list[Character],  # 逆順生存メンバーリスト
        # battle_commands: dict,
        # message_window: Window,
        # サイズや位置を確認する為の参照用　実処理で使わない
        # ref_window: Window,
        ref_window: dict[str, int],
        # submenu_return: SubReturnFlag,
        target_type: TargetType,
        *args,
    ):
        # self.ctx_source: EntityContext = ctx_source  # 再帰先へのコンテキスト引継用
        # self.context: EntityContext = EntityContext(
        #     situation=ctx_source.situation,
        #     # ctx_source.actor,
        #     actor=real_actor,
        #     target=real_actor,
        #     allies=ctx_source.allies,
        #     targets=ctx_source.targets,
        # )
        # # print(f"\nsrc {id(self.ctx_source.targets)}\nctx {id(self.context.targets)}")
        # self.actor_list: list[Character] = actor_list
        self.context: EntityContext = ctx_source
        # self.battle_commands: dict = battle_commands
        # self.message_window: Window = message_window
        # self.command_name: str = command_name
        self.target_type: TargetType = target_type
        self.item_list: MENU_ITEM_LIST = []
        self.generate_item_list()
        menu_pos = (ref_window["x"], ref_window["y"])
        menu_size = (ref_window["w"], ref_window["h"])

        super().__init__(
            "basic", *menu_pos, self.menu_shape, self.item_list, *menu_size
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

    def generate_item_list(self):
        """メニュー項目リストの生成：ターゲット"""
        # 対象リストの振り分け
        match self.target_type:
            case TargetType.ENEMY | TargetType.ENEMIES:
                target_list = self.context.targets
            case TargetType.ALLY | TargetType.ALLIES:
                target_list = self.context.allies
            case TargetType.SELF:  # 単体対象オブジェクトはリスト化が必要
                target_list = [self.context.actor]
            case TargetType.ALL:
                target_list = self.context.targets + self.context.allies
            case _:
                target_list = self.context.targets

        menu_cols = 2
        enemy_count = len(target_list)
        if enemy_count <= 0:
            errmsg = "ターゲット対象リストが空の状態です"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        else:
            tmp_item_list = [
                [
                    {
                        "id": f"{target.param.name.ljust(9, "　")}",
                        "action": "set_target",
                        # # "args": [target.id, "Attack"],
                        # "args": [target.id, self.command_name],
                        "args": [target],
                    }
                ]
                for target in target_list
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

    # def individual_update(self) -> None:
    #     """キャンセル時に自分のIDのコマンドがあれば削除する"""
    #     if self.inputkey.cancel():
    #         self.battle_commands.pop(self.context.actor.id)

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

    # def set_target(self, id: int, command: str) -> ExecResult:
    #     """コンテキストにターゲットを設定"""
    # for i, target in enumerate(self.context.targets):
    #     if target.id == id:
    #         self.context.target_index = i
    #         logger.debug(f"{i}={target.param.name}")
    # cmd = getattr(e_cmd, command)
    # # logger.info(f"\nselect command\n{cmd}")
    # # cmd(self.context, self.message_window)
    def set_target(self, target: EntityBase) -> ExecResult:
        """コンテキストにターゲットを設定"""
        self.context.target = target
        # if self.context.pending_command is None:
        #     errmsg = f"コマンドが定義されていません：{self.context}"
        #     logger.critical(errmsg, exc_info=True)
        #     raise ValueError(errmsg)
        # self.battle_commands[self.context.actor.id] = (
        #     self.context.pending_command
        # )

        # # logger.info(f"\nctx for command list\n{self.context}")
        # # # サブメニュー終了フラグを立てて前のメニューに戻る
        # # self.is_submenu_return.state = True
        # # return RsltPop()

        # # # 自分自身をpopしてから次メンバーのバトルメニューをpush（無理やり）
        # # import service_locater as di
        # #
        # # di.ref.scnmgr.get_now_scene().wndmgr.pop_stack()

        # logger.debug(f"{self.battle_commands}")
        # # 自身をpopして次のメニューをpushする戻り値を採用
        # if not self.actor_list:
        #     return RsltDiscard()
        # return RsltReplace(
        #     MenuBattle,
        #     self.ctx_source,
        #     self.actor_list,
        #     self.battle_commands,
        #     self.message_window,
        # )
        return RsltDiscard()
