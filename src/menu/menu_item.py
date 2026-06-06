"""menu_field.py
メニューモジュール：フィールド
"""
import pyxel as px
from gameutils.lib.window.window_base import Menu, Window, MenuItem as BaseMenuItem
from gameutils.lib.window.window_protocol import WindowAction, MENU_WINDOW_TYPE
from gameutils.base import FONT_SIZE_NAME, FontManager
from typing import Any, Callable, Optional, TypedDict


# MenuItemの辞書形式を定義
class ItemMenuData(TypedDict):
    id: str
    action: str  # "None"固定
    description: str
    # 実際のCallableはMenuItemWindowのexec_menuで呼び出すため、ここに保持しない
    callable_action: Optional[Callable[..., Any]]
    action_args: tuple


class MenuSelectItemCategory(Menu):
    """アイテムカテゴリ選択メニュー"""

    def __init__(self, menu_pos_x: int, menu_pos_y: int) -> None:
        menu_pos = (menu_pos_x, menu_pos_y)
        menu_shape = [1, 3]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

    def use_item(self):
        ...

    def show_keyitem(self):
        ...

    def show_equips(self):
        ...


class MenuItemWindow(Menu):
    """アイテム表示・選択用ウィンドウ"""

    def __init__(
        self,
        font_size_name: FONT_SIZE_NAME,
        x: int,
        y: int,
        width: int,
        height: int,
        items: list[ItemMenuData],
    ):
        self.all_items: list[ItemMenuData] = items
        self.page = 0
        tmp_font_data = FontManager.get_fontdata(font_size_name)
        self.items_per_page = (height - 16) // (tmp_font_data.height + 4)
        self.max_page = max(0, (len(items) - 1) // self.items_per_page)

        self.target_width = width
        self.target_height = height

        # Menuクラスの初期化
        # Menu.__init__はmenu_sourceとしてlist[list[dict[str, str]]]を期待する
        initial_menu_source = self._get_menu_source_from_items(
            self._get_current_page_items()
        )

        # ここでMenu.__init__を呼び出し、width/heightはダミーで渡し、後で上書きする
        # Menu.__init__内でcalculate_windowsizeが呼ばれてしまうため、
        # その結果を一旦受け入れ、その後Windowインスタンスを正しいサイズで再生成する
        super().__init__(
            font_size_name, x, y, [1, len(initial_menu_source)], initial_menu_source
        )

        # Windowインスタンスを正しいサイズと位置で再生成
        self.windows: dict[MENU_WINDOW_TYPE, Window] = {}
        self.windows["main"] = Window(
            font_size_name, x, y, self.target_width, self.target_height, "menu"
        )
        self.windows["main"].x = (
            x if x + self.target_width <= px.width else px.width - self.target_width
        )
        self.windows["main"].generate_window()

        # 説明ウィンドウの作成
        desc_width = (
            px.ceil(self.target_width // 2 / Window._chip_size) * Window._chip_size
        )
        desc_height = (
            px.ceil(self.target_height // 2 / Window._chip_size) * Window._chip_size
            - Window._chip_size
        )
        desc_x = self.windows["main"].x + self.windows["main"].width - desc_width
        desc_y = y + self.target_height - desc_height
        if desc_x < 0:
            desc_x = 0
        self.desc_y: list[int] = [8, desc_y]
        self.windows["sub"] = Window(
            font_size_name, desc_x, self.desc_y[1], desc_width, desc_height, "menu"
        )
        self.windows["sub"].draw = self._draw_description

        # menu_itemsはMenu.__init__で生成されるが、ItemMenuDataを直接参照するために再設定
        self._update_menu_items_internal(self._get_current_page_items())

    def _get_menu_source_from_items(
        self, items_data: list[ItemMenuData]
    ) -> list[list[dict[str, str]]]:
        """ItemMenuDataのリストからMenuクラスのmenu_source形式に変換する"""
        if not items_data:
            return [[{"id": "なし", "action": "None"}]]
        return [[{"id": item["id"], "action": "None"}] for item in items_data]

    def _get_current_page_items(self) -> list[ItemMenuData]:
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        return self.all_items[start:end]

    def _update_menu_items_internal(self, current_page_items: list[ItemMenuData]):
        """内部のmenu_itemsを更新し、Menuクラスの計算を再度走らせる"""
        menu_source = self._get_menu_source_from_items(current_page_items)
        self.menu_shape = [1, len(menu_source)]  # メニューの形状を更新
        # Menuクラスのcalculate_windowsizeを呼び出し、x_pos, y_posを更新
        self.calculate_windowsize()

        # 実際の表示データはall_itemsから取得するため、menu_items自体はダミーで良い
        # ここでは描画用にitem_labelのみ再設定
        self.menu_items = (
            [[BaseMenuItem(item["id"])] for item in current_page_items]
            if current_page_items
            else [[BaseMenuItem("なし")]]
        )

        # カーソル位置の調整
        self.cursor_position[1] = min(self.cursor_position[1], self.menu_shape[1] - 1)

    def update(self):
        inp = self.windows["main"].inp

        if inp.left():
            if self.page > 0:
                self.page -= 1
                self._update_menu_items_internal(self._get_current_page_items())
                return WindowAction.CONTINUE
        elif inp.right():
            if self.page < self.max_page:
                self.page += 1
                self._update_menu_items_internal(self._get_current_page_items())
                return WindowAction.CONTINUE

        return super().update()

    def exec_menu(self):
        """選択メニュー処理の実行。ItemMenuDataのcallable_actionを直接呼ぶ"""
        pos_x, pos_y = self.cursor_position
        current_page_items = self._get_current_page_items()
        if 0 <= pos_y < len(current_page_items):
            selected_item_data = current_page_items[pos_y]
            if selected_item_data["callable_action"]:
                selected_item_data["callable_action"](
                    *selected_item_data["action_args"]
                )
                return WindowAction.DISCARD

        return WindowAction.CONTINUE

    def draw_main(self):
        # メインウィンドウの描画（枠線、背景など）
        self.windows["main"].draw()

        # アイテムリストの描画
        # Menuクラスのdraw_mainはBaseMenuItemのitem_labelを使うため、ここで独自に描画する
        for row_idx, item_data in enumerate(self._get_current_page_items()):
            text_x = (
                self.windows["main"].x + self.column_x_pos[0] + Window._chip_size
            )  # + px.width // 6
            text_y = self.windows["main"].y + self.row_y_pos[row_idx]
            px.text(text_x, text_y, item_data["id"], px.COLOR_WHITE, self.font)

        # カーソル表示
        self.draw_cursor()

        # ページ番号の描画 (右上)
        page_str = f"{self.page+1:02}/{self.max_page+1:02}"
        font_small = FontManager.get_fontdata("small").font
        px.rect(
            self.windows["main"].x + self.windows["main"].width - 28,
            self.windows["main"].y,
            20,
            FontManager.get_fontdata("small").height,
            px.COLOR_NAVY,
        )
        px.text(
            self.windows["main"].x + self.windows["main"].width - 28,
            self.windows["main"].y,
            page_str,
            px.COLOR_WHITE,
            font_small,
        )

    #     # 説明文の描画
    #     self._draw_description()
    # self.windows["sub"].draw = self._draw_description

    def _draw_description(self):
        win = self.windows["sub"]
        if (
            self.row_y_pos[self.cursor_position[1]] + self.cursor_row_offset
            > self.desc_y[1]
        ):
            win.y = self.desc_y[0]
        else:
            win.y = self.desc_y[1]
        # win.draw()
        win.__class__.draw(win)
        pos_y = self.cursor_position[1]
        current_page_items = self._get_current_page_items()
        if 0 <= pos_y < len(current_page_items):
            item_data = current_page_items[pos_y]
            description_text = item_data.get("description", "")
            px.text(win.x + 8, win.y + 8, description_text, px.COLOR_WHITE, self.font)
