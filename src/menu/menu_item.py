"""menu_item.py
メニューモジュール：アイテム（フィールド）
"""

import logging
import pyxel as px
from const import SoundID

import service_locater as di
from gameutils.lib import Window, Menu, ExecResult, RsltPush, RsltDiscard, RsltContinue
from helper import upper_int_format, format_leftright
from item import (
    ItemType,
    ItemID,
    ItemState,
    ItemTargetType,
)
from entity import EntityContext
import command.entity_command as e_cmd


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectItemCategory(Menu):
    """アイテムカテゴリ選択メニュー"""

    def __init__(
        self,
        menu_pos_x: int,
        menu_pos_y: int,
        ctx: EntityContext,
        command_package: e_cmd.CommandPackage,
    ) -> None:
        menu_pos = (menu_pos_x, menu_pos_y)
        menu_shape = [1, 3]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.ctx = ctx
        self.command_package = command_package

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
        return result

    def use_item(self):
        """消耗品アイテムメニュー表示"""
        return RsltPush(
            MenuUseItem,
            self.ctx,
            self.command_package,
        )

    def show_keyitem(self):
        return RsltPush(MenuShowKeyItem)

    def show_equips(self):
        return RsltPush(MenuShowEquips)


class MenuItemBase(Menu):
    """アイテム用メニュー基本クラス"""

    _list_rows: int = 10
    pagelabel_size = 4 * 5  # 4ptフォント5文字

    def __init__(
        self,
    ) -> None:
        """データ取得と表示ウインドウの再定義"""

        menu_pos = (80, Window._chip_size)
        w = 104
        self.item_list: list = []
        self.itemlist_index: int = 0
        self.generate_item_list()
        super().__init__(
            "basic",
            *menu_pos,
            [1, len(self.item_list[self.itemlist_index])],
            self.item_list[self.itemlist_index],
            w,
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        self.windows["sub"] = Window(
            "basic",
            menu_pos[0],
            menu_pos[1] + self.height + 1,
            self.width,
            64,
            "sub",
        )
        self.is_push_left: int = 0
        self.is_push_right: int = 0
        self.change_target_item()

    def generate_item_list(self):
        ...

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""
        self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]
        self.set_description_string()

    def remap_itemlist(self):
        self.build_menu_items(self.item_list[self.itemlist_index])
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0, 0]

    def get_item_desc(self) -> list[str]:
        ...

    def set_description_string(self):
        """詳細ウインドウに表示する文字列を設定"""
        item_desc = self.get_item_desc()
        text_area_width = self.windows["sub"].width - (Window._chip_size * 2)
        message_list = []
        start_row = 0
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
            message_list.append(desc_string[start_row:i])  # type: ignore
        self.windows["sub"].set_message(message_list)

    def individual_update(self):
        """クラス固有の更新処理"""
        # 左右キーでのリスト内容切替
        if len(self.item_list) > 1:
            if self.inputkey.left():
                px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
                self.itemlist_index = (self.itemlist_index - 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                self.is_push_left = 1
                return
            if self.inputkey.right():
                px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
                self.itemlist_index = (self.itemlist_index + 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                self.is_push_right = 1

    def move_cursor(self) -> bool:
        """カーソル移動時に詳細ウインドウの内容を書き換える"""
        result = super().move_cursor()
        if result:
            px.play(self.se_ch, SoundID.CURSOR_VERTICAL, resume=True)
            self.change_target_item()
        return result

    def draw_main(self) -> None:
        """ページ表示の追加"""
        super().draw_main()
        x = self.x + self.width - (self.pagelabel_size + Window._chip_size)
        y = self.y
        px.rect(
            x,
            y,
            self.pagelabel_size,
            Window._chip_size,
            self.windows["main"]._image_chips.pget(7, 7),
        )
        px.text(
            x,
            y,
            f"{self.itemlist_index + 1:02}/{len(self.item_list):02}",
            px.COLOR_WHITE,
        )


class MenuUseItem(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    def __init__(
        self,
        ctx: EntityContext,
        command_package: e_cmd.CommandPackage,
    ):
        """データ取得と表示ウインドウの再定義"""
        self.inventory_count: int = 0
        super().__init__()

        self.ctx = ctx
        self.command_package = command_package

    def generate_item_list(self):
        """アイテムリストの生成"""
        filtereddict = di.ref.pl_stack.get_by_state(ItemState.BAG)

        self.inventory_count = len(filtereddict)
        if self.inventory_count <= 0:
            self.item_list = [[[{"id": "該当なし", "action": "None", "args": [""]}]]]
        else:
            tmp_item_list = [
                [
                    {
                        "id": format_leftright(
                            di.ref.itemrps.get_def(key).name,  # type: ignore
                            f"ｘ{upper_int_format(val, 2)}",
                        ),
                        "action": "use_item",
                        "args": [key],
                    }
                ]
                for key, val in filtereddict.items()
                if val > 0
            ]
            self.item_list = [
                tmp_item_list[i : i + self._list_rows]
                for i in range(0, self.inventory_count, self._list_rows)
            ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def get_item_desc(self) -> list[str]:
        target_item = di.ref.itemrps.get_def(self.target_item[0]["args"][0])
        if target_item is None:
            desc = "持っていない"
        else:
            desc = target_item.description
        return [desc]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if self.inventory_count == 0:
            return RsltContinue()
        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )
        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def use_item(self, item_id: ItemID):
        """選択アイテムの効果関数を呼び出し"""
        item_def = di.ref.itemrps.get_def(item_id)
        if item_def is None:
            errmsg = f"該当IDのアイテムが定義されていません：{item_id}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        from menu import MenuSelectFieldTarget

        # コマンドパッケージに選択内容登録
        self.command_package.selected_action = getattr(e_cmd, item_def.effect_id)
        self.command_package.target_type = ItemTargetType(item_def.target_type)
        self.command_package.selected_args = {
            "item_def": item_def,
            "pl_stack": di.ref.pl_stack,
        }
        if self.command_package.target_type == ItemTargetType.NONE:
            # ターゲットがない場合は抜けてそのまま処理実行
            return RsltDiscard()
        return RsltPush(
            MenuSelectFieldTarget,
            self.ctx,
            self.command_package.target_type,
        )


class MenuShowKeyItem(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    def __init__(self) -> None:
        """データ取得と表示ウインドウの再定義"""
        super().__init__()

    def generate_item_list(self):
        """アイテムリストの生成"""
        tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        filteredlist = [
            [
                {
                    "id": items_.ins.param.name,
                    "action": "None",
                    "args": items_.ins.param.description,
                }
            ]
            for _, items_ in tmplist.items()
            if items_.ins.param.item_type == ItemType.KEY_ITEM
        ]

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            self.item_list = [
                [[{"id": "該当なし", "action": "None", "args": ["対象を持っていない"]}]]
            ]
        else:
            self.item_list = [
                filteredlist[i : i + self._list_rows]
                for i in range(0, self.inventory_count, self._list_rows)
            ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def get_item_desc(self) -> list[str]:
        return [self.target_item[0]["args"]]


class MenuShowEquips(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    def __init__(self) -> None:
        """データ取得と表示ウインドウの再定義"""
        super().__init__()

    def generate_item_list(self):
        """アイテムリストの生成"""
        tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        filteredlist = [
            [
                {
                    "id": items_.ins.param.name,
                    "action": "None",
                    "args": [items_.ins.param.def_id],
                }
            ]
            for _, items_ in tmplist.items()
            if items_.ins.param.item_type != ItemType.KEY_ITEM
        ]

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            self.item_list = [[[{"id": "該当なし", "action": "None", "args": [""]}]]]
        else:
            self.item_list = [
                filteredlist[i : i + self._list_rows]
                for i in range(0, self.inventory_count, self._list_rows)
            ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def get_item_desc(self) -> list[str]:
        item_def = di.ref.itemrps.get_def(self.target_item[0]["args"][0])
        if item_def is None:
            return ["対象を持っていない"]
        match item_def.item_type:
            case ItemType.WEAPON:
                expect_dmg = item_def.hitdice * 4
                perf_txt = f"攻撃:{upper_int_format(expect_dmg, 2)}"
            case ItemType.GUARDER:
                perf_txt = f"防御:{upper_int_format(item_def.defvalue, 2)} 魔法阻害:{upper_int_format(item_def.magpenalty, 1)}"
            case ItemType.ORNAMENT:
                perf_txt = "特殊な効果をもつ飾り"
            case _:
                perf_txt = ""
        return [f"{perf_txt}", f"{item_def.description}"]
