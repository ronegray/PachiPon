"""window_base.py
ウインドウ・メニュークラス

- ウインドウ機能
  - 任意サイズのウインドウ表示
  - 定義したテキストの表示
  - リストテキストの場合はページ送り
  - クローズ契機をボタン押下／一定時間後／全ページ送り後に指定可能
- メニュー機能(abstructとして利用)
  - 指定項目リストに応じたメニュー表示
    - 指定項目リストのjson読み込み機能
  - メニューウインドウサイズは項目に応じて自動設定
  - 基本的機能のみ提供。用途に応じて継承する
"""

# from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
from itertools import zip_longest
import pyxel as px

from ...libconfig import ResourcePath
from ...base import check_file, read_json, FONT_SIZE_NAME, FontManager
from . import WINDOW_MODE, MENU_WINDOW_TYPE, WindowAction
from ._wrapper_input import WindowInputWrapper, set_default_pyxel_input


class WindowInputHandler:
    """Window/Menuクラス共通の入力ハンドラクラス"""

    _wrapper: WindowInputWrapper = set_default_pyxel_input()

    @classmethod
    def update_window_input(cls, wrapper_dict: dict[str, Callable[[], bool]]) -> None:
        """外部入力機能による定義更新"""
        cls._wrapper = WindowInputWrapper(
            up=wrapper_dict.get("up", lambda: False),
            down=wrapper_dict.get("down", lambda: False),
            left=wrapper_dict.get("left", lambda: False),
            right=wrapper_dict.get("right", lambda: False),
            decide=wrapper_dict.get("decide", lambda: False),
            cancel=wrapper_dict.get("cancel", lambda: False),
            other1=wrapper_dict.get("other1", lambda: False),
            other2=wrapper_dict.get("other2", lambda: False),
            LS=wrapper_dict.get("LS", lambda: False),
            RS=wrapper_dict.get("RS", lambda: False),
        )

    @classmethod
    def load_default_input(cls) -> None:
        """個別要求により設定変更した場合の復旧用"""
        cls._wrapper = set_default_pyxel_input()

    @classmethod
    def get(cls) -> WindowInputWrapper:
        """入力ハンドラの取得"""
        return cls._wrapper


class Window:
    """汎用ウインドウクラス"""

    _chip_size: int = 8
    _image_chips: px.Image
    _max_msg_rows: int = 3
    _indicator_address: tuple = (16, 8, 8, 4)

    def __init__(
        self,
        font_size_name: FONT_SIZE_NAME,
        x: int,
        y: int,
        width: int,
        height: int,
        window_mode: WINDOW_MODE,
        wait_sec: float = 5.0,
    ):
        try:
            self._image_chips = px.Image.from_image(ResourcePath.WINDOW_CHIP)
        except AttributeError:
            exit()

        # 管理クラスへの参照
        self.fontdata = FontManager.get_fontdata(font_size_name)
        self.font = self.fontdata.font
        self.inp = WindowInputHandler.get()
        # 共通基本パラメータ
        self.x = (
            x if x + width <= px.width else px.width - width
        )  # 右端からはみ出す場合を考慮
        self.y = y
        self.width = width
        self.height = height
        # クラス個別パラメータ
        self.window_mode = window_mode
        self.wait_frame = px.ceil(wait_sec * 30)  # fps = 30
        self.frame_counter = 0
        self.text_list: list[str] = []
        self.window_image = px.Image(self.width, self.height)
        self.is_indicator: bool = False

        self.chip_cnt_w = self.width // self._chip_size
        self.chip_cnt_h = self.height // self._chip_size
        # ウインドウイメージ生成処理
        self.generate_window()

    def generate_window(self):
        """ウインドウイメージを生成（self.window_imageとして保持）"""
        chip_wxh = [self._chip_size, self._chip_size]
        lefttop = [0, 0] + chip_wxh
        righttop = [8, 0] + chip_wxh
        leftbottom = [0, 8] + chip_wxh
        rightbottom = [8, 8] + chip_wxh
        left = [0, 16] + chip_wxh
        right = [8, 16] + chip_wxh
        top = [0, 24] + chip_wxh
        bottom = [8, 24] + chip_wxh
        # 枠線
        for Ypos in range(self.chip_cnt_h):
            for Xpos in range(self.chip_cnt_w):
                # 四隅
                if Ypos == 0 and Xpos == 0:
                    self.window_image.blt(
                        0, 0, self._image_chips, *lefttop, colkey=0
                    )  # 左上
                elif Ypos == 0 and Xpos == self.chip_cnt_w - 1:
                    self.window_image.blt(
                        self.width - self._chip_size,
                        0,
                        self._image_chips,
                        *righttop,
                        colkey=0,
                    )  # 右上
                elif Ypos == self.chip_cnt_h - 1 and Xpos == 0:
                    self.window_image.blt(
                        0,
                        self.height - self._chip_size,
                        self._image_chips,
                        *leftbottom,
                        colkey=0,
                    )  # 左下
                elif Ypos == self.chip_cnt_h - 1 and Xpos == self.chip_cnt_w - 1:
                    self.window_image.blt(
                        self.width - self._chip_size,
                        self.height - self._chip_size,
                        self._image_chips,
                        *rightbottom,
                        colkey=0,
                    )  # 右下
                # 枠線
                elif Ypos == 0:  # 上端
                    self.window_image.blt(
                        (Xpos * self._chip_size),
                        Ypos,
                        self._image_chips,
                        *top,
                        colkey=0,
                    )
                elif Xpos == 0:  # 左端
                    self.window_image.blt(
                        Xpos,
                        (Ypos * self._chip_size),
                        self._image_chips,
                        *left,
                        colkey=0,
                    )
                elif Ypos == self.chip_cnt_h - 1:  # 下端
                    self.window_image.blt(
                        (Xpos * self._chip_size),
                        self.height - self._chip_size,
                        self._image_chips,
                        *bottom,
                        colkey=0,
                    )
                elif Xpos == self.chip_cnt_w - 1:  # 右端
                    self.window_image.blt(
                        self.width - self._chip_size,
                        (Ypos * self._chip_size),
                        self._image_chips,
                        *right,
                        colkey=0,
                    )
        # 塗りつぶし
        self.window_image.rect(
            self._chip_size,
            self._chip_size,
            self.width - (self._chip_size * 2),
            self.height - (self._chip_size * 2),
            self._image_chips.pget(7, 7),
        )

    def update_row_max(self, row_max: int) -> None:
        """add_message時の最大行カウント値を更新"""
        if (self.height - Window._chip_size) > (self.fontdata.height * row_max):
            self._max_msg_rows = row_max

    def update(self) -> WindowAction:
        self.frame_counter += 1
        # menuモードのウインドウは基本的にupdateを実行しないが念の為
        if self.window_mode == "menu":
            return WindowAction.CONTINUE
        # waitモード時は待機フレーム数が過ぎると全終了
        if self.window_mode == "wait" and self.frame_counter <= self.wait_frame:
            return WindowAction.DISCARD
        # waitモード時は待機フレーム数の半分を過ぎるまでキー入力を受け付けない
        if self.window_mode == "wait" and self.frame_counter <= self.wait_frame // 2:
            self.is_indicator = True  # インジケータ点灯フラグON
            return WindowAction.CONTINUE

        # ボタンを押したら終わりのタイプはすぐインジケータ点灯
        if self.window_mode in ("once", "page"):
            self.is_indicator = True

        # 決定またはキャンセルキー処理
        if self.inp.decide() or self.inp.cancel():
            match self.window_mode:
                # ページ送り以外では全終了
                case "once" | "wait":
                    return WindowAction.DISCARD
                # ページ送り時は内部テキストリストを次に進める
                case "page":
                    self.text_list.pop(0)
                    # 最終メッセージを送った後は全終了
                    if len(self.text_list):
                        return WindowAction.CONTINUE
                    else:
                        return WindowAction.DISCARD

        return WindowAction.CONTINUE

    def draw(self):
        # ウインドウ描画
        px.blt(
            self.x,
            self.y,
            self.window_image,
            0,
            0,
            self.width,
            self.height,
            colkey=px.COLOR_BLACK,
        )
        # ボタン押下アイコン
        if self.frame_counter >= self.wait_frame // 2:
            if px.frame_count // 8 % 2 == 0:
                px.blt(
                    self.x + self.width // 2 - (self._indicator_address[2] // 2),
                    self.y + self.height - self._indicator_address[3] - 1,
                    self._image_chips,
                    # 35,
                    # 248,
                    # 5,
                    # 8,
                    *Window._indicator_address,
                    # colkey=0,
                    # rotate=90,
                )

    def drawText(self, x: int, y: int, text_list: list, col: int = px.COLOR_WHITE):
        for i, data in enumerate(text_list):
            # try:
            #     textcolor = data[1]
            #     # text = data[0]
            # except IndexError:
            #     textcolor = px.COLOR_WHITE
            #     # text = data
            px.text(
                x,
                y + (i * int(self.fontdata.height * 1.5)),
                data[0],
                # text,
                # col=textcolor,
                col=col,
                font=self.font,
            )
        return

    def set_message(self, message_text: list[str]) -> None:
        if self.window_mode == "menu":
            return
        self.text_list = message_text

    def add_message(self, message_text: str) -> None:
        if self.window_mode == "menu":
            return
        self.text_list.append(message_text)
        while len(self.text_list) > self._max_msg_rows:
            self.text_list.pop(0)

    def draw_message(self):
        pos_x = self.x + self._chip_size
        pos_y = self.y + self._chip_size
        if self.window_mode == "page":
            text = "" if not self.text_list else self.text_list[0]
            px.text(
                pos_x,
                pos_y + (0 * int(self.fontdata.height * 1.5)),
                text,
                px.COLOR_WHITE,
                font=self.font,
            )
        else:
            for i, text in enumerate(self.text_list):
                px.text(
                    pos_x,
                    pos_y + (i * int(self.fontdata.height * 1.5)),
                    text,
                    px.COLOR_WHITE,
                    font=self.font,
                )
        return


@dataclass
class MenuItem:
    """メニュー表示内容と処理を組み合わせて管理"""

    item_label: str  # 画面に表示する文字列
    menu_action: Callable[..., Any] | None = None  # 実行する関数オブジェクト
    action_args: tuple[Any, ...] = field(
        default_factory=tuple
    )  # 関数に渡す引数（あれば）
    # is_disabled: bool = False                # (将来用) 選択不可フラグなどを足しても便利です


type MENU_ITEM_LIST = list[list[dict[str, Any]]]


class ExecResult:
    """exec_menuの戻り値基底クラス
    具象実装も本ファイルにて後述
    """

    ...


class Menu:
    """メニュー基底クラス"""

    # 固定メニュー項目データ読込
    file = "assets/data/menu_structure.json"
    path = check_file(file)
    assert (
        path is not None
    ), f"固定メニュー項目データの読み込みに失敗しました：file={file}"
    menu_item_data = read_json(path)
    # _MENU_ITEM_CASHE: dict[str, list[list[dict[str, str|list]]]] = dict(menu_item_data)
    _MENU_ITEM_CASHE: dict[str, MENU_ITEM_LIST] = dict(menu_item_data)

    def __init__(
        self,
        font_size_name: FONT_SIZE_NAME,
        x: int,
        y: int,  # width: int, height: int,
        menu_shape: list[int],
        # menu_source: str | list[list[dict[str, str|list]]],
        menu_source: str | MENU_ITEM_LIST,
        w: int = 0,
        h: int = 0,
    ):
        # 管理クラスへの参照
        self.img_cursor = [16, 0, Window._chip_size, Window._chip_size]
        self.fontdata = FontManager.get_fontdata(font_size_name)
        self.font = self.fontdata.font
        self.cursor_row_offset = px.ceil((self.fontdata.height - Window._chip_size) / 2)
        # クラス個別パラメータ
        self.cursor_position: list[int] = [0, 0]
        self.menu_shape: list = menu_shape  # 横軸数,縦軸数
        self.menu_items: list[list[MenuItem]] = []
        self.build_menu_items(menu_source)
        # 共通基本パラメータ
        self.column_x_pos: list[int] = []
        # フォントサイズを元にウインドウサイズ算出
        calc_winsize = self.calculate_windowsize()
        width = w if w > 0 else calc_winsize[0]
        height = h if h > 0 else calc_winsize[1]

        adjusted_x = (
            x if x + width <= px.width else px.width - width
        )  # 右端からはみ出す場合を考慮
        # ウインドウ生成処理
        self.windows: dict[MENU_WINDOW_TYPE, Window] = {}
        self.windows["main"] = Window(
            font_size_name, adjusted_x, y, width, height, "menu"
        )
        self.cursor_x = self.cursor_y = 0
        self.inputkey = WindowInputHandler.get()

    @property
    def x(self):
        return self.windows["main"].x

    @property
    def y(self):
        return self.windows["main"].y

    @property
    def width(self):
        return self.windows["main"].width

    @property
    def height(self):
        return self.windows["main"].height

    # def build_menu_items(self, menu_source: str | list[list[dict[str, str|list]]]):
    def build_menu_items(self, menu_source: str | MENU_ITEM_LIST):
        if isinstance(menu_source, str):  # メニュー固定項目指定時
            tmp_menudata = self._MENU_ITEM_CASHE[menu_source]
        else:  # 動的指定
            tmp_menudata = menu_source  # 横軸テキスト[a,b,c],,,※縦軸数分
        try:
            self.menu_items = [
                [
                    MenuItem(
                        item_label=data["id"],
                        menu_action=getattr(self, data["action"], None),
                        action_args=tuple(data.get("args", [])),
                    )
                    for data in row
                ]
                for row in tmp_menudata
            ]
        except TypeError:
            self.menu_items = [
                [
                    MenuItem(
                        item_label=str(data),
                        menu_action=None,
                        action_args=tuple(""),
                    )
                    for data in row
                ]
                for row in tmp_menudata
            ]

    def calculate_windowsize(self) -> list[int]:
        """メニューウインドウの幅／高さの算出と、描画アドレスのキャッシュ"""
        menuwidth = menuheight = 0
        framesize = Window._chip_size * 2  # 左右または上下の枠サイズ合計
        # --- 幅(X座標)の計算と保持 ---
        offset_cursor = Window._chip_size + (
            Window._chip_size // 4
        )  # カーソルサイズ、文字との余白
        offset_sepalete_col = (
            2 if self.font is None else self.font.text_width(" ") // 2
        )  # 項目間余白

        # 文字列／カーソル表示用のpixelアドレスキャッシュ初期化
        self.column_x_pos = []
        current_x = Window._chip_size  # 描画初期アドレスを枠のすぐ右に定義

        # column_items: list[list[MenuItem]] = [
        #     list(col) for col in zip(*self.menu_items)
        # ]
        # 横あり奇数リストの対策
        column_items: list[list[MenuItem]] = [
            [item for item in col if item is not None]
            for col in zip_longest(*self.menu_items)
        ]
        for column_data in column_items:
            if column_data is None:
                continue
            # 現在のカラムのX座標を記録
            self.column_x_pos.append(current_x)

            if self.font:
                text_list = [items.item_label for items in column_data]
                max_column_textlen = self.font.text_width(
                    max(text_list, key=self.font.text_width)
                )
            else:
                # デフォルトフォントの場合の文字長は4ピクセル
                max_column_textlen = (
                    max([len(item.item_label) for item in column_data]) * 4
                )
            colwidth = offset_cursor + max_column_textlen + offset_sepalete_col
            menuwidth += colwidth
            current_x += colwidth
        # print(f"{self.menu_items}\n{column_items}\n{self.column_x_pos}")
        # チップサイズで丸めて最終的な幅を算出
        menuwidth = (
            px.ceil((menuwidth + framesize) / Window._chip_size) * Window._chip_size
        )

        # 高さ
        rows = self.menu_shape[1]
        offset_sepalete_row = self.fontdata.height // 2
        # 文字列／カーソル表示用のpixelアドレスキャッシュ初期化
        self.row_y_pos: list[int] = []
        current_y = (
            Window._chip_size - 1
        )  # 描画初期アドレスを枠の下(余白埋め気味)に定義

        for _ in range(rows):
            self.row_y_pos.append(current_y)
            current_y += self.fontdata.height + offset_sepalete_row

        # 最終行はオフセット不要（枠の余白が相当するため
        menuheight = (
            rows * (self.fontdata.height + offset_sepalete_row) - offset_sepalete_row
        )
        # チップサイズで丸めて最終的な幅を算出
        menuheight = (
            px.ceil((menuheight + framesize) / Window._chip_size) * Window._chip_size
        )

        return [menuwidth, menuheight]

    def update_menu_size(self, menu_items: list | None = None):
        """メニュー項目の変化に合わせたウインドウサイズの変更"""
        if menu_items:
            self.menu_items = menu_items
        self.menu_shape = [len(self.menu_items), len(self.menu_items[0])]
        self.calculate_windowsize()

    def update(self) -> WindowAction:
        """更新"""
        self.individual_update()
        RC = self.key_check()
        return RC

    def key_check(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.move_cursor():
            pass
        elif self.inputkey.decide():
            return WindowAction.EXECUTE
        elif self.inputkey.cancel():
            return WindowAction.CLOSE
        return WindowAction.CONTINUE

    # def individual_key_check(self, inp: WindowInputWrapper) -> bool:
    #     """メニュー個別のキー判定用"""
    #     ...
    # 個別キー判定など入れずに、key_checkのオーバーライドで実装する

    def individual_update(self) -> Any:
        """メニュー個別のupdateフレーム処理内容"""
        ...

    def move_cursor(self) -> bool:
        """キー入力に応じたカーソル移動とインデックス制御"""
        if self.inputkey.up():
            self.cursor_position[1] = (self.cursor_position[1] - 1) % self.menu_shape[1]
            return True
        if self.inputkey.left():
            self.cursor_position[0] = (self.cursor_position[0] - 1) % self.menu_shape[0]
            return True
        if self.inputkey.down():
            self.cursor_position[1] = (self.cursor_position[1] + 1) % self.menu_shape[1]
            return True
        if self.inputkey.right():
            self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]
            return True
        return False

    def exec_menu(self) -> ExecResult:
        ...

    def draw(self):
        """描画"""
        for name, win in self.windows.items():
            win.draw()
            win.draw_message()
            if name == "main":
                self.draw_main()

    def draw_main(self):
        """メニュー項目文字表示"""
        # try:
        for row_idx, row in enumerate(self.menu_items):
            for col_idx, item in enumerate(row):
                text_x = (
                    self.windows["main"].x
                    + self.column_x_pos[col_idx]
                    + Window._chip_size
                )  # カーソルの右隣
                text_y = self.windows["main"].y + self.row_y_pos[row_idx]
                px.text(text_x, text_y, item.item_label, px.COLOR_WHITE, self.font)
        self.draw_cursor()

    # except IndexError as e:
    #     print(
    #         # f"\nmenu={self.menu_items}\nitem={item}\n{self.column_x_pos}-{col_idx}"
    #         f"{self.menu_items}\n{e}"
    #     )
    #     px.quit()

    def draw_cursor(self):
        """メニューカーソル表示"""
        pos_x, pos_y = self.cursor_position
        self.cursor_x = self.windows["main"].x + self.column_x_pos[pos_x]
        self.cursor_y = (
            self.windows["main"].y + self.row_y_pos[pos_y] + self.cursor_row_offset
        )
        px.blt(
            self.cursor_x,
            self.cursor_y,
            self.windows["main"]._image_chips,
            *self.img_cursor,
            colkey=px.COLOR_BLACK,
        )


class RsltPush(ExecResult):
    """exec_menu内でサブメニューをpushする時"""

    def __init__(self, class_name: type[Window] | type[Menu], *args, **kwargs):
        self.class_name = class_name
        self.args_pos = args
        self.args_key = kwargs


@dataclass
class RsltPop(ExecResult):
    """exec_menu内で自メニューをpopする時"""

    on_pop: list[Callable[[], None]]


@dataclass
class RsltDiscard(ExecResult):
    """exec_menu後にメニュースタックをクリアする時"""

    pass


@dataclass
class RsltContinue(ExecResult):
    """そのまま続ける時"""

    pass


class RsltReplace(RsltPush):
    """exec_menu内で自身をPOP後次のメニューをpushする時
    マネージャ側でpop後pushの値を使って処理
    """

    ...


# class MenuYesNo(Menu):
#     def __init__(self, x, y, msg:list, command_instance, parent):
#         super().__init__(x + 2*G_.CHIP_PIXEL, y + (len(msg)*2+1)*G_.CHIP_PIXEL , [1,2],  [["はい"],["いいえ"]], 4, 3)
#         self.address = [x,y]
#         _textlength = 0
#         for texts in msg:
#             _textlength = max(len(texts),_textlength)
#         _msg_window_width = (_textlength*2+2)*G_.CHIP_PIXEL
#         if x + _msg_window_width > px.width:
#             x = px.width - _msg_window_width
#         self.message_window  = Window(x, y, _msg_window_width, (len(msg)*2+2)*G_.CHIP_PIXEL, 0)
#         self.message = msg
#         self.command_instance     = command_instance
#         self.parent = parent

#     def update(self):
#         if self.is_command:
#             return self.chkCmdRtn()
#         btn = comf.get_button_state()
#         if btn["a"]:
#             px.play(3,G_.SNDEFX["pi"], resume=True)
#             match self.cursor_position[1] % self.menu_shape[1]:
#                 case 0:
#                     self.command_instance.exec()
#                     self.is_command = True
#                 case 1:
#                     return False
#             return True
#         if btn["b"]:
#             if self.is_command:
#                 return True
#             else:
#                 return False

#         self.moveCursor()
#         return True

#     def draw(self):
#         if self.is_command:
#             self.command_instance.draw()
#         else:
#             self.message_window.draw()
#             self.message_window.drawText(self.address[0]+8,self.address[1]+8, self.message)
#             self.drawMenu()
