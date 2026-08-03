"""
メニューモジュール：ショップ
"""

import logging
import pyxel as px
from const import SoundID

import service_locater as di
from gameutils.lib import (
    Window,
    Menu,
    ExecResult,
    RsltPush,
    RsltContinue,
)  # , RsltDiscard
from helper import upper_int_format, format_leftright
from item import (
    ItemType,
    # ItemRank,
)
from entity import Party
from field_map import PointPlaceType
import command.system_command as s_cmd


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectShopCategory(Menu):
    """アイテムカテゴリ選択メニュー"""

    def __init__(self, party: Party, message_window: Window) -> None:
        self.pt = party
        self.message_window = message_window

        menu_pos = (0, 0)
        menu_shape = [5, 1]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        self.windows["main"].x = (px.width - self.width) // 2
        self.windows["main"].y = self.message_window.y - self.height + Window._chip_size

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

    def buy_consume(self):
        """消耗品アイテムメニュー表示"""
        return RsltPush(MenuBuyConsume, self.pt, self.message_window, self.y)

    def buy_foods(self):
        return RsltPush(
            MenuBuyFoods, self.pt, self.message_window, self.y
        )  # , self.pool_item, self.pool_stack)

    def buy_equips(self):
        return RsltPush(
            MenuBuyEquips, self.pt, self.message_window, self.y
        )  # , self.pool_item, self.pool_stack)


class MenuItemBase(Menu):
    """アイテム用メニュー基本クラス"""

    _list_rows: int = 8
    pagelabel_size = 4 * 5  # 4ptフォント5文字

    def __init__(self, party: Party, message_window: Window, y: int) -> None:
        """データ取得と表示ウインドウの再定義"""
        self.pt = party
        self.message_window = message_window

        y_offset = 1
        menu_w, menu_h = 160, 120
        menu_pos = (Window._chip_size // 2, y - menu_h - y_offset)
        self.item_list: list = []
        self.itemlist_index: int = 0
        self.inventory_count: int = 0
        self.generate_item_list()
        super().__init__(
            "basic",
            *menu_pos,
            [1, len(self.item_list[self.itemlist_index])],
            self.item_list[self.itemlist_index],
            menu_w,
            menu_h,
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        sub_w, sub_h = 88, 104
        self.windows["sub"] = Window(
            "basic",
            menu_pos[0] + self.width + 1,
            self.y + self.height - sub_h,
            sub_w,
            sub_h,
            "sub",
        )
        # self.is_push_left: int = 0
        # self.is_push_right: int = 0
        # self.change_target_item()
        self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]
        self.set_description_string()

    def generate_item_list(self):
        ...

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""
        self.target_item = self.item_list[self.itemlist_index][self.cursor_position[1]]
        self.set_description_string()

    def remap_itemlist(self):
        """アイテムリストのページ更新"""
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
        """クラス固有の更新処理
        - キャンセル押下時はカテゴリ選択メニューに戻ってメッセージ設定"""

        if self.inputkey.cancel():
            # self.message_window.clear_message()
            self.message_window.update_indicator(False)
            # 地点別の対応
            eventpoint = di.ref.pt.get_current_point()
            match eventpoint.point_type:
                case PointPlaceType.CAPITAL_CITY:
                    suggest_message = "他の商品も是非ご覧下さいませ"
                case PointPlaceType.TOWN:
                    suggest_message = "まだまだあるぜ！色々見てってくれよな"
                case PointPlaceType.VILLAGE:
                    suggest_message = "大したもんはないが、見てみるかね？"
                case _:
                    return
            self.message_window.set_message([suggest_message])  # type: ignore

        # 左右キーでのリスト内容切替
        if len(self.item_list) > 1:
            if self.inputkey.left():
                px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
                self.itemlist_index = (self.itemlist_index - 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                # self.is_push_left = 1
                return
            if self.inputkey.right():
                px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
                self.itemlist_index = (self.itemlist_index + 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                # self.is_push_right = 1

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
        # ページ表示
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


class MenuBuyConsume(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    # def __init__(
    #     self,
    #     # ctx: EntityContext,
    #     # command_package: e_cmd.CommandPackage,
    # ):
    #     """データ取得と表示ウインドウの再定義"""
    #     super().__init__()

    #     # self.ctx = ctx
    #     # self.command_package = command_package
    #     self.inventory_count: int = 0

    def generate_item_list(self):
        """アイテムリストの生成"""
        eventpoint_rank = self.pt.get_current_point().point_type.value
        # filtereddict = di.ref.pl_stack.get_by_state(ItemState.BAG)
        filtereddict = di.ref.itemrps.get_def_by_type(ItemType.CONSUME)
        # eventpoint_rank = self.pt.get_current_point().point_type.value

        tmp_item_list = [
            [
                {
                    "id": format_leftright(
                        item_def.name, f"　{upper_int_format(item_def.price, 6)}Ｇ", 34
                    ),
                    "action": "none",
                    "args": [item_def],
                }
            ]
            for _, item_def in filtereddict.items()
            if eventpoint_rank >= item_def.rank.value >= eventpoint_rank - 1
        ]
        self.inventory_count = len(tmp_item_list)
        self.item_list = [
            tmp_item_list[i : i + self._list_rows]
            for i in range(0, self.inventory_count, self._list_rows)
        ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def get_item_desc(self) -> list[str]:
        # target_item = di.ref.itemrps.get_def(self.target_item[0]["args"][0])
        target_item = self.target_item[0]["args"][0]
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

        cmd = s_cmd.ShopPurchase(
            self.message_window,
            self.pt,
            selected_item.action_args[0],
            di.ref.pl_stack.add,
        )
        di.ref.cmdmgr.push_command(cmd)
        return RsltContinue()


class MenuBuyFoods(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    # def __init__(self) -> None:
    #     """データ取得と表示ウインドウの再定義"""
    #     super().__init__()

    def generate_item_list(self):
        """アイテムリストの生成"""
        # tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        # filteredlist = [
        #     [
        #         {
        #             "id": items_.ins.param.name,
        #             "action": "None",
        #             "args": items_.ins.param.description,
        #         }
        #     ]
        #     for _, items_ in tmplist.items()
        #     if items_.ins.param.item_type == ItemType.KEY_ITEM
        # ]

        # self.inventory_count = len(filteredlist)
        # if self.inventory_count <= 0:
        #     self.item_list = [[[{"id": "該当なし", "action": "None", "args": [""]}]]]
        # else:
        #     self.item_list = [
        #         filteredlist[i : i + self._list_rows]
        #         for i in range(0, self.inventory_count, self._list_rows)
        # ]
        self.item_list = [
            [
                [
                    {"id": "１０食分", "action": "none", "args": [1]},
                ],
                [
                    {"id": "１００食分", "action": "none", "args": [10]},
                ],
                [
                    {"id": "１０００食分", "action": "none", "args": [100]},
                ],
                [{"id": "９９００食分", "action": "none", "args": [990]}],
            ]
        ]

        # # ページインデックスが範囲外にならないよう補正
        # if self.itemlist_index >= len(self.item_list):
        #     self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def get_item_desc(self) -> list[str]:
        return ["とってもとっても\nおいしそう！！"]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        cmd = s_cmd.PurchaseFoods(
            self.message_window, self.pt, selected_item.action_args[0]
        )
        di.ref.cmdmgr.push_command(cmd)
        return RsltContinue()


class MenuBuyEquips(MenuItemBase):
    """消耗品アイテム表示・選択用メニュー"""

    # def __init__(self) -> None:
    #     """データ取得と表示ウインドウの再定義"""

    #     super().__init__()

    def generate_item_list(self):
        """アイテムリストの生成"""
        eventpoint_rank = self.pt.get_current_point().point_type.value
        # tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        filtereddict_w = di.ref.itemrps.get_def_by_type(ItemType.WEAPON)
        filtereddict_g = di.ref.itemrps.get_def_by_type(ItemType.GUARDER)
        filtereddict_o = di.ref.itemrps.get_def_by_type(ItemType.ORNAMENT)
        filtereddict = filtereddict_w | filtereddict_g | filtereddict_o
        # filteredlist = [
        #     [
        #         {
        #             "id": items_.ins.param.name,
        #             "action": "None",
        #             "args": [items_.ins.param.def_id],
        #         }
        #     ]
        #     for _, items_ in tmplist.items()
        #     if items_.ins.param.item_type != ItemType.KEY_ITEM
        # ]
        tmp_item_list = [
            [
                {
                    "id": format_leftright(
                        item_def.name, f"　{upper_int_format(item_def.price, 6)}Ｇ", 34
                    ),
                    "action": "none",
                    "args": [item_def],
                }
            ]
            for _, item_def in filtereddict.items()
            if eventpoint_rank >= item_def.rank.value >= eventpoint_rank - 1
        ]

        self.inventory_count = len(tmp_item_list)
        self.inventory_count = len(tmp_item_list)
        self.item_list = [
            tmp_item_list[i : i + self._list_rows]
            for i in range(0, self.inventory_count, self._list_rows)
        ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def get_item_desc(self) -> list[str]:
        # item_def = di.ref.itemrps.get_def(self.target_item[0]["args"][0])
        item_def = self.target_item[0]["args"][0]

        match item_def.item_type:
            case ItemType.WEAPON:
                # expect_dmg = item_def.hitdice * 4
                # perf_txt1 = f"攻撃:{upper_int_format(expect_dmg, 2)}"
                perf_txt1 = f"攻撃:{upper_int_format(item_def.expect_damage, 2)}"
                return [f"{perf_txt1}", f"{item_def.description}"]
            case ItemType.GUARDER:
                perf_txt1 = f"防御:{upper_int_format(item_def.defvalue, 2)}"
                perf_txt2 = f"魔法阻害:{upper_int_format(item_def.magpenalty, 1)}"
            case ItemType.ORNAMENT:
                perf_txt1 = "特殊な効果を"
                perf_txt2 = "　もつ飾り"
            case _:
                perf_txt1 = perf_txt2 = ""
        return [f"{perf_txt1}", f"{perf_txt2}", f"{item_def.description}"]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        cmd = s_cmd.ShopPurchase(
            self.message_window,
            self.pt,
            selected_item.action_args[0],
            di.ref.pl_item.create,
        )
        di.ref.cmdmgr.push_command(cmd)
        return RsltContinue()
