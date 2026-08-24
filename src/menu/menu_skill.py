"""
メニューモジュール：スキル使用

- 使用するスキルを選択
- 使用スキルのターゲットを選択
"""

import logging
import pyxel as px
from gameutils.lib import (
    Menu,
    Window,
    ExecResult,
    RsltContinue,
    RsltPush,
    RsltPop,
    RsltDiscard,
)
from const import SoundID
import service_locater as di
from helper import upper_int, format_leftright
from entity import EntityContext
from skill import SkillDef, SkillTargetType
import command.entity_command as e_cmd


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectSkillBattle(Menu):
    """行動サブメニュー：戦闘時使用スキル選択"""

    _list_rows: int = 8
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
        self.skill_list: list[list[dict[str, str | list]]] = []
        self.generate_item_list()

        menu_pos = (ref_window["x"], ref_window["y"])
        menu_size = (
            (ref_window["w"], ref_window["h"])
            if self.ctx.situation == "battle"
            else (104, 144)
        )
        super().__init__(
            "basic", *menu_pos, self.menu_shape, self.skill_list, *menu_size
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        # """使用するスキルを選択データ取得と表示ウインドウの再定義"""
        self.member_index: int = 0

        if self.ctx.situation == "battle":
            info_height = 8 + 8 + 8  # 上枠＋フォント分8px + 下枠
            sub_pos = (0, ref_window["y"] - info_height)
            sub_size = (px.width, info_height)
        else:
            info_height = 8 + (16 * 3) + 8  # 上枠＋フォント分16px + 下枠
            sub_pos = (ref_window["x"], ref_window["y"] + self.height + 1)
            sub_size = (self.width, info_height)
        self.windows["sub"] = Window("basic", *sub_pos, *sub_size, "sub")

        self.change_target_item()

        # フィールド時は利用者名前ウインドウ
        if self.ctx.situation == "field":
            namewindow_height = Window._chip_size + 16
            self.windows["sub2"] = Window(
                "basic",
                menu_pos[0],
                menu_pos[1] - namewindow_height,
                self.width,
                namewindow_height,
                "sub",
            )
            self.windows["sub2"].set_message([self.ctx.actor.param.name])

    def generate_item_list(self):
        """メニュー項目リストの生成：スキル"""
        # コンテキストシチュエーションに応じてメニューカラム数変更
        menu_cols = self._menu_col_criteria.get(self.ctx.situation, 1)

        actor = self.ctx.actor
        tmplist = actor.skills.get_learned_skill_def()

        self.item_count = len(tmplist)
        if self.item_count <= 0:
            self.skill_list = [
                [{"id": "該当なし", "action": "None", "args": ["習得していない"]}]
            ]
        else:
            tmp_item_list = [
                [
                    {
                        "id": format_leftright(
                            skill_def.name, upper_int(skill_def.cost)
                        ),
                        "action": "select_target",
                        "args": [skill_def],
                    }
                ]
                for skill_def in tmplist
            ]
            if len(tmp_item_list) <= 0:
                self.skill_list = [
                    [{"id": "該当なし", "action": "None", "args": ["習得していない"]}]
                ]
            else:
                if menu_cols > 1:
                    self.item_list_multicol(menu_cols, tmp_item_list)
                else:
                    self.skill_list = tmp_item_list.copy()

        self.menu_shape = [min(len(tmplist), menu_cols), len(self.skill_list)]

    def item_list_multicol(self, menu_cols: int, tmp_item_list: list):
        """シチュエーション毎のメニューカラムに応じたアイテムリスト生成"""
        tmp_list = []
        cnt = 0
        for i, tmp_item in enumerate(tmp_item_list):
            if i % menu_cols == 0:
                tmp_list = [].copy()
            tmp_list.append(tmp_item[0])
            if len(tmp_list) == menu_cols:
                self.skill_list.append(tmp_list.copy())
                cnt += 2
        if len(tmp_item_list) != cnt:
            self.skill_list.append(tmp_list.copy())

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""

        self.target_item = self.skill_list[self.cursor_position[1]]
        self.set_description_string()

    def remap_itemlist(self):
        self.build_menu_items(self.skill_list)
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0, 0]

    def set_actor_name(self):
        member = self.ctx.allies[self.member_index]
        self.windows["sub2"].set_message([member.param.name])

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

    def individual_update(self) -> None:
        """クラス固有の更新処理"""
        if self.ctx.situation == "battle":
            return

        def _update_list():
            self.generate_item_list()
            self.build_menu_items(self.skill_list)
            self.change_target_item()
            self.set_actor_name()

        if self.inputkey.left():
            self.member_index = (self.member_index - 1) % len(self.ctx.allies)
            _update_list()
        if self.inputkey.right():
            self.member_index = (self.member_index + 1) % len(self.ctx.allies)
            _update_list()

    def move_cursor(self) -> bool:
        """カーソル移動時に詳細ウインドウの内容を書き換える"""
        result = super().move_cursor()
        if result:
            self.change_target_item()
        return result

    def get_item_desc(self) -> list[str]:
        # return [self.target_item[self.cursor_position[0]]["args"][0].description]  # type: ignore
        target_item = di.ref.itemrps.get_def(self.target_item[0]["args"][0])  # type: ignore
        if target_item is None:
            desc = "対象を持っていない"
        else:
            desc = target_item.description
        return [desc]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if self.item_count == 0:
            return RsltContinue()
        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def select_target(self, skill_def: SkillDef) -> ExecResult:
        """使用するスキルの情報を元にターゲット選択メニューを呼び出し"""
        if not self.ctx.actor.check_mp(skill_def.cost):
            self.windows["sub"].set_message(["ＭＰが足りません"])
            return RsltContinue()

        match self.ctx.situation:
            case "field":
                return RsltContinue()
            case "battle":
                from menu import MenuSelectBattleTarget

                # コマンドパッケージに選択内容登録
                self.command_package.selected_action = getattr(
                    e_cmd, skill_def.effect_func
                )
                self.command_package.target_type = skill_def.target_type  # type: ignore
                self.command_package.selected_args = {"skillinfo": skill_def}

                if skill_def.target_type in (
                    SkillTargetType.ALLIES,
                    SkillTargetType.ENEMIES,
                ):
                    return RsltDiscard()

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
            case _:
                return RsltContinue()


class MenuSelectSkillField(Menu):
    """行動サブメニュー：フィールド時使用スキル選択"""

    _list_rows: int = 8

    def __init__(
        self,
        ctx: EntityContext,
        ref_window: dict[str, int],
        command_package: e_cmd.CommandPackage,
    ):
        self.ctx = ctx
        self.command_package = command_package

        self.item_count: int = 0
        self.skill_list: list[list[dict[str, str | list]]] = []
        self.generate_item_list()

        menu_pos = (ref_window["x"], ref_window["y"])
        menu_size = (104, 144)
        super().__init__(
            "basic", *menu_pos, self.menu_shape, self.skill_list, *menu_size
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.member_index: int = 0

        # スキル詳細情報ウインドウ
        info_height = 8 + (16 * 3) + 8  # 上枠＋フォント分16px + 下枠
        sub_pos = (ref_window["x"], ref_window["y"] + self.height + 1)
        sub_size = (self.width, info_height)
        self.windows["sub"] = Window("basic", *sub_pos, *sub_size, "sub")

        self.change_target_item()

        # フィールド時は利用者名前ウインドウ
        namewindow_height = Window._chip_size + 16
        self.windows["sub2"] = Window(
            "basic",
            menu_pos[0],
            menu_pos[1] - namewindow_height,
            self.width,
            namewindow_height,
            "sub",
        )
        self.set_actor_name()

    def generate_item_list(self):
        """メニュー項目リストの生成：スキル"""
        # コンテキストシチュエーションに応じてメニューカラム数変更
        menu_cols = 1

        actor = self.ctx.actor
        tmplist = actor.skills.get_learned_skill_def()

        self.item_count = len(tmplist)
        if self.item_count <= 0:
            self.skill_list = [[{"id": "該当なし", "action": "None", "args": [""]}]]
        else:
            tmp_item_list = [
                [
                    {
                        "id": format_leftright(
                            skill_def.name, upper_int(skill_def.cost)
                        ),
                        "action": "select_target",
                        "args": [skill_def],
                    }
                ]
                for skill_def in tmplist
            ]
            if len(tmp_item_list) <= 0:
                self.skill_list = [[{"id": "該当なし", "action": "None", "args": [""]}]]
            else:
                if menu_cols > 1:
                    self.item_list_multicol(menu_cols, tmp_item_list)
                else:
                    self.skill_list = tmp_item_list.copy()

        self.menu_shape = [menu_cols, len(self.skill_list)]

    def item_list_multicol(self, menu_cols: int, tmp_item_list: list):
        """シチュエーション毎のメニューカラムに応じたアイテムリスト生成"""
        tmp_list = []
        cnt = 0
        for i, tmp_item in enumerate(tmp_item_list):
            if i % menu_cols == 0:
                tmp_list = [].copy()
            tmp_list.append(tmp_item[0])
            if len(tmp_list) == menu_cols:
                self.skill_list.append(tmp_list.copy())
                cnt += 2
        if len(tmp_item_list) != cnt:
            self.skill_list.append(tmp_list.copy())

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""

        self.target_item = self.skill_list[self.cursor_position[1]]
        self.set_description_string()

    def remap_itemlist(self):
        self.build_menu_items(self.skill_list)
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0, 0]

    def set_actor_name(self):
        member = self.ctx.actor = self.ctx.allies[self.member_index]
        self.windows["sub2"].set_message([member.param.name])

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

    def individual_update(self) -> None:
        """クラス固有の更新処理"""
        if self.ctx.situation == "battle":
            return

        def _update_list():
            self.set_actor_name()
            self.generate_item_list()
            self.build_menu_items(self.skill_list)
            self.change_target_item()

        # if self.inputkey.left():
        if self.inputkey.LS():
            # px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
            self.se.play(SoundID.PAGE_ARROW)
            self.member_index = (self.member_index - 1) % len(self.ctx.allies)
            _update_list()
        # if self.inputkey.right():
        if self.inputkey.RS():
            # px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
            self.se.play(SoundID.PAGE_ARROW)
            self.member_index = (self.member_index + 1) % len(self.ctx.allies)
            _update_list()

    def move_cursor(self) -> bool:
        """キー入力に応じたカーソル移動とインデックス制御"""
        result = False
        if self.inputkey.up():
            self.cursor_position[1] = (self.cursor_position[1] - 1) % self.menu_shape[1]
            result = True
        if self.inputkey.down():
            self.cursor_position[1] = (self.cursor_position[1] + 1) % self.menu_shape[1]
            result = True
        if result:
            self.change_target_item()
        return result

    def get_item_desc(self) -> list[str]:
        skill_def = self.target_item[0]["args"][0]
        if isinstance(skill_def, SkillDef):
            desc = skill_def.description  # type: ignore
        else:
            desc = "習得していない"
        return [desc]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            return RsltContinue()

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def select_target(self, skill_def: SkillDef) -> ExecResult:
        """使用するスキルの情報を元にターゲット選択メニューを呼び出し"""

        if skill_def.target_type in (SkillTargetType.ENEMY, SkillTargetType.ENEMIES):
            self.windows["sub"].set_message(["ここでは　つかえない"])
            return RsltPop([])

        if not self.ctx.actor.check_mp(skill_def.cost):
            self.windows["sub"].set_message(["ＭＰが足りません"])
            return RsltContinue()

        from menu import MenuSelectFieldTarget

        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = getattr(e_cmd, skill_def.effect_func)
        self.command_package.target_type = skill_def.target_type  # type: ignore
        self.command_package.selected_args = {"skillinfo": skill_def}

        if skill_def.target_type in (SkillTargetType.ALLIES, SkillTargetType.ENEMIES):
            return RsltDiscard()

        return RsltPush(
            MenuSelectFieldTarget,
            self.ctx,
            self.command_package.target_type,
        )
