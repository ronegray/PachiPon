"""menu_item.py
メニューモジュール：アイテム（フィールド）
"""

import logging
import pyxel as px
import service_locater as di
from gameutils.lib import (
    Window,
    Menu,
    ExecResult,
    RsltPush,
)
from item import ItemType, ItemID, ItemState  # , ConsumeGrade


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectItemCategory(Menu):
    """アイテムカテゴリ選択メニュー"""

    def __init__(self, menu_pos_x: int, menu_pos_y: int) -> None:
        menu_pos = (menu_pos_x, menu_pos_y)
        menu_shape = [1, 3]
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
        return result

    def use_item(self):
        """消耗品アイテムメニュー表示"""
        return RsltPush(MenuUseItem)

    def show_keyitem(self):
        return RsltPush(MenuShowKeyItem)

    def show_equips(self):
        return RsltPush(MenuShowEquips)


class MenuItemBase(Menu):
    """アイテム用メニュー基本クラス"""

    _list_rows: int = 10
    pagelabel_size = 4 * 5  # 4ptフォント5文字

    def __init__(self):
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
            # px.width - x - Window._chip_size,
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
        # for i in range(0, len(item_desc) + 1):
        #     if (
        #         self.windows["sub"].fontdata.font.text_width(
        #             item_desc[start_row : i + 1]
        #         )
        #         > text_area_width
        #     ):
        #         message_list.append(item_desc[start_row:i])
        #         start_row = i
        for desc_string in item_desc:
            for i in range(0, len(desc_string) + 1):
                if (
                    self.windows["sub"].fontdata.font.text_width(
                        desc_string[start_row : i + 1]
                    )
                    > text_area_width
                ):
                    message_list.append(desc_string[start_row:i])
                    start_row = i
            # 最後の残りを結合
            message_list.append(desc_string[start_row:i])
        self.windows["sub"].set_message(message_list)

    def individual_update(self):
        """クラス固有の更新処理"""
        # 左右キーでのリスト内容切替
        if len(self.item_list) > 1:
            if self.inputkey.left():
                self.itemlist_index = (self.itemlist_index - 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                self.is_push_left = 1
                return
            if self.inputkey.right():
                self.itemlist_index = (self.itemlist_index + 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                self.is_push_right = 1

    def move_cursor(self) -> bool:
        """カーソル移動時に詳細ウインドウの内容を書き換える"""
        result = super().move_cursor()
        if result:
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


# class MenuUseItem(Menu):
class MenuUseItem(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    def __init__(self):
        """データ取得と表示ウインドウの再定義"""
        super().__init__()

    def generate_item_list(self):
        """アイテムリストの生成"""
        filteredlist = di.ref.pl_stack.get_by_state(ItemState.BAG)

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            self.item_list = [[{"id": "該当なし", "action": "None"}]]
        else:
            tmp_item_list = [
                [
                    {
                        "id": f"{di.ref.itemmgr.get_def(key).name} x {val}",
                        "action": "use_item",
                        "args": [key],
                    }
                ]
                for key, val in filteredlist.items()
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
        return [di.ref.itemmgr.get_def(self.target_item[0]["args"][0]).description]

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

    def use_item(self, item_id: ItemID):
        """選択アイテムの効果関数を呼び出し"""
        item_name = di.ref.itemmgr.get_def(item_id).name
        print(f"{item_id} {item_name}")
        self.windows["sub"].add_message(f"{item_name} をつかった")


class MenuShowKeyItem(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    def __init__(self):
        """データ取得と表示ウインドウの再定義"""
        super().__init__()

    def generate_item_list(self):
        """アイテムリストの生成"""
        tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        filteredlist = [
            {item_[0]: item_[1]}
            for item_ in tmplist.items()
            if item_[0] & 0xFF00 == ItemType.KEY_ITEM
        ]
        filteredlist = [
            [
                {
                    "id": items_.ins.param.name,
                    "action": "None",
                    "args": items_.ins.param.description,
                }
            ]
            for _, items_ in tmplist.items()
            if items_.ins.param.def_id & 0xFF00 == ItemType.KEY_ITEM
        ]

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            self.item_list = [[{"id": "該当なし", "action": "None"}]]
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

    def __init__(self):
        """データ取得と表示ウインドウの再定義"""
        # # x, y = 80, Window._chip_size
        # # self.item_list: list = []
        # # self.itemlist_index: int = 0
        # self.filter_cursor: int = 0
        # self.filter_name: list[str] = ["", "COMSUME", "LEGEND"]
        # self.filter_types = ConsumeGrade

        # # self.list_rows: int = 10
        # # self.inventory_count: int = 0
        # # self.generate_item_list()
        # # super().__init__("basic", x, y,
        # #                  [1,len(self.item_list[self.itemlist_index])],
        # #                  self.item_list[self.itemlist_index],
        # #                  px.width - x - Window._chip_size)
        # # self.windows["sub"] = Window("basic", x, y + self.windows["main"].height + 1,
        # #                              self.windows["main"].width, 64, "sub")
        # # self.is_push_left: int = 0
        # # self.is_push_right: int = 0
        # # # self.target_item = self.item_list[0][0]
        # # self.change_target_item()
        super().__init__()

    # def _get_filtered_list(self, raw_list: dict[ItemID, int]) -> dict[ItemID, int]:
    #     """フィルタリング処理"""
    #     target_type = getattr(
    #         self.filter_types, self.filter_name[self.filter_cursor], None
    #     )
    #     if target_type is None:
    #         return raw_list

    #     returnlist = [
    #         {item_[0]: item_[1]}
    #         for item_ in raw_list.items()
    #         if item_[0] & 0xFFF0 == target_type
    #     ]
    #     return returnlist[0]

    def generate_item_list(self):
        """アイテムリストの生成"""
        # tmplist = di.ref.pl_stack.get_by_state(ItemState.BAG)
        # filteredlist = self._get_filtered_list(tmplist)
        tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        # filteredlist = [
        #     {item_[0]: item_[1]}
        #     for item_ in tmplist.items()
        #     if item_[0] & 0xFF00 != ItemType.KEY_ITEM
        # ]
        filteredlist = [
            [
                {
                    "id": items_.ins.param.name,
                    "action": "None",
                    # "args": items_.ins.param.description,
                    "args": [items_.ins.param.def_id],
                }
            ]
            for _, items_ in tmplist.items()
            if items_.ins.param.def_id & 0xFF00 != ItemType.KEY_ITEM
        ]

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            # if self.filter_name == "":
            #     self.item_list = [[{"id": "なし", "action": "None"}]]
            # else:
            self.item_list = [[{"id": "該当なし", "action": "None"}]]
        else:
            # tmp_item_list = [[{"id":f"{di.ref.itemmgr.get_def(key).name} x {val}",
            #                    "action":"use_item", "args":[key]}]
            #                  for key,val in filteredlist.items() if val > 0]
            # self.item_list = [tmp_item_list[i:i+self.list_rows]
            #                   for i in range(0, self.inventory_count, self.list_rows)]
            self.item_list = [
                filteredlist[i : i + self._list_rows]
                for i in range(0, self.inventory_count, self._list_rows)
            ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    # def remap_itemlist(self):
    #     # self.menu_items = self.item_list[self.itemlist_index]
    #     self.build_menu_items(self.item_list[self.itemlist_index])
    #     self.menu_shape[1] = len(self.menu_items)
    #     self.cursor_position = [0,0]

    # def change_target_item(self):
    #     """選択アイテムを示す内部情報の変更"""
    #     self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]
    #     self.set_description_string()

    def get_item_desc(self) -> list[str]:
        # return self.target_item[0]["args"]
        item_def = di.ref.itemmgr.get_def(self.target_item[0]["args"][0])
        if item_def is None:
            return [""]
        match item_def.item_type:
            case ItemType.WEAPON:
                expect_dmg = item_def.hitdice * 4
                perf_txt = f"攻撃性能:{expect_dmg:>2}"
            case ItemType.GUARDER:
                perf_txt = (
                    f"防御性能:{item_def.defvalue} 魔法阻害:{item_def.magpenalty}"
                )
            case ItemType.ORNAMENT:
                perf_txt = "特殊な効果をもつ飾り"
            case _:
                perf_txt = ""
        return [f"{perf_txt}", f"{item_def.description}"]

    # def set_description_string(self):
    #     """詳細ウインドウに表示する文字列を設定"""
    #     # item_desc = di.ref.itemmgr.get_def(self.target_item[0]["args"][0]).description
    #     item_desc = self.target_item[0]["args"]
    #     text_area_width = self.windows["sub"].width - (Window._chip_size*2)
    #     message_list = []
    #     start_pos = 0
    #     for i in range(0, len(item_desc) + 1):
    #         if self.windows["s
    # ub"].fontdata.font.text_width(
    #               item_desc[start_pos:i+1]
    #         ) > text_area_width:
    #              message_list.append(item_desc[start_pos:i])
    #              start_pos = i
    #     # 最後の残りを結合
    #     message_list.append(item_desc[start_pos:i])
    #     self.windows["sub"].set_message(message_list)

    # def individual_update(self):
    #     """クラス固有の更新処理"""
    #     # 左右キーでのリスト内容切替
    #     if len(self.item_list) > 1:
    #         if self.inputkey.left():
    #                 self.itemlist_index = (self.itemlist_index-1)%len(self.item_list)
    #                 self.remap_itemlist()
    #                 self.change_target_item()
    #                 self.is_push_left = 1
    #                 return
    #         if self.inputkey.right():
    #                 self.itemlist_index = (self.itemlist_index+1)%len(self.item_list)
    #                 self.remap_itemlist()
    #                 self.change_target_item()
    #                 self.is_push_right = 1

    # def move_cursor(self) -> bool:
    #     """カーソル移動時に詳細ウインドウの内容を書き換える"""
    #     result = super().move_cursor()
    #     if result:
    #         self.change_target_item()
    #     return result
