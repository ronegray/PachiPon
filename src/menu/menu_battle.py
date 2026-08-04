"""
メニューモジュール：バトル
"""

import logging
from typing import cast  # Callable
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

from entity import EntityContext, EntityBase, Character, EquipSlot
from skill import SkillTargetType  # , SkillID

import command.entity_command as e_cmd
# from command import Attack, DefenceMode, UseItem, UseSkill


# ロギング設定
logger = logging.getLogger(__name__)


# class SubReturnFlag:
#     state: bool = False


class MenuBattle(Menu):
    def __init__(
        self,
        ctx: EntityContext,
        command_package: e_cmd.CommandPackage,
    ):
        menu_pos = (0, 192)
        menu_shape = [1, 4]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.ctx = ctx
        self.command_package = command_package

        # コマンド用サブウインドウ
        sub_pos = (self.x + self.width, self.y)
        sub_size = (px.width - self.width, self.height)
        self.windows["sub"] = Window("basic", *sub_pos, *sub_size, "once")

        # 名前ウインドウ定義（表示順制御の為self.windows乗せない）
        name_pos = (self.x, self.y - 17)
        name_size = (80, 32)
        self.namewindow = Window("basic", *name_pos, *name_size, "once")

        # コマンド入力前に一旦防御体勢解除
        self.ctx.actor.defend(False)

    def draw(self):
        """名前ウインドウの下部を隠す為順序制御"""
        self.namewindow.draw()
        self.namewindow.drawText(
            self.namewindow.x + 6,
            self.namewindow.y + 4,
            [[self.ctx.actor.param.name]],
            px.COLOR_WHITE,
        )
        super().draw()

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

    def select_target(self):
        """ユーザ行動コマンド：攻撃する／ターゲットの選択メニューへ"""

        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = e_cmd.Attack
        self.command_package.target_type = SkillTargetType.ENEMY

        return RsltPush(
            MenuSelectBattleTarget,
            self.ctx,
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
        return RsltPush(
            MenuSelectItem,
            self.ctx,
            {
                "x": self.windows["sub"].x,
                "y": self.windows["sub"].y,
                "w": self.windows["sub"].width,
                "h": self.windows["sub"].height,
            },
            self.command_package,
        )

    def select_skill(self):
        """スキル選択メニューを開く"""
        from menu import MenuSelectSkillBattle

        return RsltPush(
            MenuSelectSkillBattle,
            self.ctx,
            {
                "x": self.windows["sub"].x,
                "y": self.windows["sub"].y,
                "w": self.windows["sub"].width,
                "h": self.windows["sub"].height,
            },
            self.command_package,
        )

    def defence_mode(self):
        """ユーザ行動コマンド：防御体勢"""
        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = e_cmd.DefenceMode
        self.command_package.target_type = SkillTargetType.SELF

        return RsltDiscard()


class MenuSelectBattleTarget(Menu):
    """行動サブメニュー：戦闘ターゲット選択"""

    def __init__(
        self,
        # real_actor: Character,
        ctx: EntityContext,
        # actor_list: list[Character],  # 逆順生存メンバーリスト
        # battle_commands: dict,
        # message_window: Window,
        # サイズや位置を確認する為の参照用　実処理で使わない
        # ref_window: Window,
        ref_window: dict[str, int],
        # submenu_return: SubReturnFlag,
        target_type: SkillTargetType,
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
        self.ctx: EntityContext = ctx
        # self.battle_commands: dict = battle_commands
        # self.message_window: Window = message_window
        # self.command_name: str = command_name
        self.target_type: SkillTargetType = target_type
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
            case SkillTargetType.ENEMY | SkillTargetType.ENEMIES:
                target_list = self.ctx.targets
            case SkillTargetType.ALLY | SkillTargetType.ALLIES:
                target_list = self.ctx.allies
            case SkillTargetType.SELF:  # 単体対象オブジェクトはリスト化が必要
                target_list = [self.ctx.actor]
            case SkillTargetType.ALL:
                target_list = self.ctx.targets + self.ctx.allies
            case _:
                target_list = self.ctx.targets

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
                        "id": f"{target.param.name.ljust(9, '　')}",
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
        self.ctx.target = target
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


class MenuSelectItem(Menu):
    """行動サブメニュー：戦闘時使用アイテム選択　※バトル専用"""

    # _list_rows: int = 10
    # _pagelabel_size = 4 * 5  # 4ptフォント5文字
    _menu_col_criteria = {"field": 1, "battle": 2}

    def __init__(
        self,
        ctx: EntityContext,
        ref_window: dict[str, int],
        command_package: e_cmd.CommandPackage,
    ):
        self.ctx = ctx
        self.command_package = command_package

        self.item_count: int = 0
        self.item_list: list[list[dict[str, str | list]]] = []

        self.consume_list = []
        actor: Character = cast(Character, self.ctx.actor)
        plent_cons1 = actor.equipments.get_slot(EquipSlot.CONSUME_1)
        plent_cons2 = actor.equipments.get_slot(EquipSlot.CONSUME_2)
        if plent_cons1 is not None:
            self.consume_list.append(
                (EquipSlot.CONSUME_1, plent_cons1[0], plent_cons1[1])
            )
        if plent_cons2 is not None:
            self.consume_list.append(
                (EquipSlot.CONSUME_2, plent_cons2[0], plent_cons2[1])
            )

        self.generate_item_list()

        menu_pos = (ref_window["x"], ref_window["y"])
        menu_size = (ref_window["w"], ref_window["h"])
        super().__init__(
            "basic", *menu_pos, self.menu_shape, self.item_list, *menu_size
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        # 詳細情報ウインドウ
        info_height = 24
        self.windows["sub"] = Window(
            "basic",
            0,
            menu_pos[1] - info_height,
            px.width,
            info_height,
            "sub",
        )

        self.change_target_item()

        # # フィールド時は利用者名前ウインドウ
        # if self.context.situation == "field":
        #     # self.set_actor_name()
        #     namewindow_height = Window._chip_size + 16
        #     self.windows["sub2"] = Window(
        #         "basic",
        #         menu_pos[0],
        #         menu_pos[1] - namewindow_height,
        #         self.width,
        #         namewindow_height,
        #         "sub",
        #     )
        #     self.windows["sub2"].set_message([self.context.actor.param.name])

    def generate_item_list(self):
        """メニュー項目リストの生成：スキル"""
        # コンテキストシチュエーションに応じてメニューカラム数変更
        menu_cols = 1

        # actor: Character = cast(Character, self.context.actor)
        # plent_cons1 = actor.equipments.get_slot(EquipSlot.CONSUME_1)
        # plent_cons2 = actor.equipments.get_slot(EquipSlot.CONSUME_2)

        # tmplist = [consume for consume in (plent_cons1, plent_cons2)
        #            if consume is not None]

        self.item_count = len(self.consume_list)
        if self.item_count <= 0:
            self.item_list = [[{"id": "該当なし", "action": "None", "args": [""]}]]
        else:
            tmp_item_list = [
                [
                    {
                        "id": f"{pool_entry.ins.param.name}",
                        "action": "select_target",
                        "args": [slot, iid, pool_entry],
                    }
                ]
                for slot, iid, pool_entry in self.consume_list
            ]
            if len(tmp_item_list) <= 0:
                self.item_list = [
                    [
                        {
                            "id": "該当なし",
                            "action": "None",
                            "args": [
                                "",
                            ],
                        }
                    ]
                ]
            else:
                # if menu_cols > 1:
                #     self.item_list_multicol(menu_cols, tmp_item_list)
                # else:
                self.item_list = tmp_item_list.copy()

        self.menu_shape = [menu_cols, len(self.item_list)]

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""
        self.target_item = self.item_list[self.cursor_position[1]]
        self.set_description_string()

    def set_description_string(self):
        """詳細ウインドウに表示する文字列を設定"""
        item_desc = self.get_item_desc()
        text_area_width = self.windows["sub"].width - (Window._chip_size * 2)
        message_list = []
        i = start_row = 0

        for desc_string in item_desc:
            for i in range(0, len(desc_string) + 1):
                if (
                    self.windows["sub"].fontdata.font.text_width(  # type: ignore
                        desc_string[start_row : i + 1]
                    )
                    > text_area_width
                ):
                    message_list.append(desc_string[start_row:i])
                    start_row = i
            # 最後の残りを結合
            message_list.append(desc_string[start_row:i])
        self.windows["sub"].set_message(message_list)

    def move_cursor(self) -> bool:
        """カーソル移動時に詳細ウインドウの内容を書き換える"""
        result = super().move_cursor()
        if result:
            self.change_target_item()
        return result

    def get_item_desc(self) -> list[str]:
        """アイテム詳細情報取得"""
        if len(self.target_item[0]["args"]) < 2:
            desc = "装備なし"
        else:
            desc = self.target_item[0]["args"][2].ins.param.description  # type: ignore
        return [desc]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        # logger.info(
        #     f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        # )
        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def select_target(self, *args) -> ExecResult:
        """味方メンバーターゲット選択メニューを呼び出し"""

        eq_slot, item_iid, plent = self.target_item[0]["args"]
        func_name = plent.ins.param.effect_id  # type: ignore

        from menu import MenuSelectBattleTarget

        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = getattr(e_cmd, func_name)
        self.command_package.target_type = SkillTargetType.ALLY  # type: ignore
        self.command_package.selected_args = {
            "item_def": plent.ins.param,  # type: ignore
            "slot": eq_slot,
        }

        # return RsltPush(
        #     MenuSelectBattleTarget,
        #     self.context.actor,  # 追加
        #     self.ctx_source,
        #     self.actor_list,
        #     self.battle_commands,
        #     self.message_window,
        #     self.windows["sub"],
        #     # self.is_submenu_return,
        #     skill_id,
        # )

        return RsltPush(
            MenuSelectBattleTarget,
            self.ctx,
            {
                "x": self.windows["main"].x,
                "y": self.windows["main"].y,
                "w": self.windows["main"].width,
                "h": self.windows["main"].height,
            },
            self.command_package.target_type,
        )

        # return RsltContinue()
