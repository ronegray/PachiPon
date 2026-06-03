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
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
import pyxel as px

# from ..asset import AssetID, AssetManager
# from ..file import check_file, read_json
# from ..input import InputHandler
from ...libconfig import ResourcePath
from gameutils.base import check_file, read_json, FONT_SIZE_NAME, FontManager

# from ...base import AssetID,AssetManager,check_file,read_json#, InputHandler
# from ...base import FONT_SIZE_NAME, FontManager, shadowed_text
# from .window_protocol import FONT_SIZE_NAME, WINDOW_MODE, MENU_WINDOW_TYPE, WindowAction
from .window_protocol import WINDOW_MODE, MENU_WINDOW_TYPE, WindowAction
# from .window_manager import WindowManager

# class MenuInputHandler:
#     """入力制御クラス"""
#     # 操作名ごとにデフォルト実装を定義
#     _input_handlers: dict[str, Callable[[], bool]] = {
#         "up": lambda: px.btnp(px.KEY_UP, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP, 12, 6),
#         "down": lambda: px.btnp(px.KEY_DOWN, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN, 12, 6),
#         "left": lambda: px.btnp(px.KEY_LEFT, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT, 12, 6),
#         "right": lambda: px.btnp(px.KEY_RIGHT, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT, 12, 6),
#         "decide": lambda: px.btnp(px.KEY_RETURN) or px.btnp(px.GAMEPAD1_BUTTON_A),
#         "cancel": lambda: px.btnp(px.KEY_ESCAPE) or px.btnp(px.GAMEPAD1_BUTTON_B),
#     }

#     @classmethod
#     def set_input_handler(cls, action: str, handler: Callable[[], bool]) -> None:
#         """入力制御の更新（外部入力モジュール利用時のコンフィグ反映を想定）"""
#         cls._input_handlers[action] = handler

#     @classmethod
#     def is_pressed(cls, action: str) -> bool:
#         """キー入力判定関数"""
#         handler = cls._input_handlers[action]
#         return handler() if handler else False

# MenuInputHandler = InputHandler()
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
    def get(cls) -> WindowInputWrapper:
        """入力ハンドラの取得"""
        return cls._wrapper


# @dataclass
# class FontData:
#     """フォント名とフォントオブジェクトの対応付け"""
#     name: FONT_SIZE_NAME  # サイズ名
#     font: px.Font | None  # フォントオブジェクト
#     height: int = 6  # フォントの高さ


# class FontHandler:
#     """フォント管理クラス"""
#     _fontdata: dict[FONT_SIZE_NAME, FontData] = {}

#     # def __init__(self):
#     @classmethod
#     def initialize(cls):
#         """フォント情報を設定(BDFフォントの場合はフォントファイルのSIZEを取得)"""
#         font_file_name: dict[FONT_SIZE_NAME, str] = {
#             "small": "default",
#             "basic": "umplus_j10r.bdf",
#             "large": "unifont_jp-17.0.04.bdf",
#         }
#         for size_name, file_name in font_file_name.items():
#             # self.fontdata[size_name].name = size_name
#             # self.fontdata[size_name].font = px.Font(f"assets/font/{file_name}")
#             if size_name == "small":
#                 cls._fontdata[size_name] = FontData(size_name, None, 4)
#                 continue

#             if file_name.endswith(".bdf"):
#                 #print(os.getcwd())
#                 with open(f"assets/font/{file_name}", mode="r", encoding="utf-8") as f:
#                     data = f.readline()
#                     while data.find("SIZE") == -1:
#                         data = f.readline()
#                     # self.font_heights[size_name] = int(data.split(" ")[1])
#                     # self.fontdata[size_name].height = int(data.split(" ")[1])
#                 tmpdata = FontData(
#                     size_name,
#                     px.Font(f"assets/font/{file_name}"),
#                     int(data.split(" ")[1]),
#                 )
#                 cls._fontdata[size_name] = tmpdata
#             else:
#                 match size_name:
#                     case "small":
#                         cls._fontdata[size_name].height = 4
#                     case "basic":
#                         cls._fontdata[size_name].height = 9
#                     case "large":
#                         cls._fontdata[size_name].height = 13

#     @classmethod
#     def get_fontdata(cls, size_name: FONT_SIZE_NAME) -> FontData:
#         """フォント"""
#         return cls._fontdata[size_name]

# # フォント管理クラスは静的クラスとして初期化
# FontHandler.initialize()

# @classmethod
# def get_imagechip(cls) -> px.Image:
#     """画像チップ"""
#     return cls.image_chips

# # イメージチップは全共通の為モジュールレベルでロード
# _image_chips: px.Image = px.Image(0,0)#px.Image.from_image("gameutils/window/chip_window.bmp")


class Window:
    """汎用ウインドウクラス"""

    _chip_size: int = 8
    _image_chips: px.Image
    _max_msg_rows: int = 3

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
        # self.chip = WindowManager.get_imagechip()
        self.fontdata = FontManager.get_fontdata(font_size_name)
        # self.chip = _image_chips
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
        self.wait_frame = px.ceil(wait_sec * 30)
        self.frame_counter = 0
        self.text_list = []
        self.window_image = px.Image(self.width, self.height)

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
        # px.blt(self.x + (Xpos*G_.CHIP_PIXEL), self.y + (Ypos*G_.CHIP_PIXEL), G_.IMGIDX["CHIP"],
        #         32, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL )
        self.window_image.rect(
            self._chip_size,
            self._chip_size,
            self.width - (self._chip_size * 2),
            self.height - (self._chip_size * 2),
            self._image_chips.pget(7, 7),
        )

    def update(self):
        self.frame_counter += 1
        # menuモードのウインドウは基本的にupdateを実行しないが念の為
        if self.window_mode == "menu":
            return
        # waitモード時は待機フレーム数が過ぎると全終了
        if self.window_mode == "wait" and self.frame_counter <= self.wait_frame:
            return WindowAction.DISCARD
        # waitモード時は待機フレーム数の半分を過ぎるまでキー入力を受け付けない
        if self.window_mode == "wait" and self.frame_counter <= self.wait_frame // 2:
            return WindowAction.CONTINUE

        # 決定またはキャンセルキー処理
        # if WindowManager.is_pressed("decide", "once") or WindowManager.is_pressed("cancel", "once"):
        # if MenuInputHandler.is_pressed("decide") or MenuInputHandler.is_pressed("cancel"):
        # inp = WindowInputHandler.get()
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
                    self.x + self.width // 2 - 4,
                    self.y + self.height - 5,
                    self._image_chips,
                    35,
                    248,
                    5,
                    8,
                    colkey=0,
                    rotate=90,
                )

    # def drawText(self, x: int, y: int, text_list: list):
    #     for i, text in enumerate(text_list):
    #         px.text(x, y + (i * 16 + 2), text, px.COLOR_WHITE, font=self.font)
    #     return

    # def drawTextColor(self, x: int, y: int, text_list: list):
    #     for i, data in enumerate(text_list):
    #         px.text(x, y + (i * 16 + 2), data[0], data[1], font=self.font)
    #     return

    def drawText(self, x: int, y: int, text_list: list):
        for i, data in enumerate(text_list):
            try:
                textcolor = data[1]
            except IndexError:
                textcolor = px.COLOR_WHITE
            px.text(
                x,
                y + (i * int(self.fontdata.height * 1.5)),
                data[0],
                textcolor,
                font=self.font,
            )
        return

    def set_message(self, message_text):
        if self.window_mode == "menu":
            return
        self.text_list.append(message_text)
        while len(self.text_list) > self._max_msg_rows:
            self.text_list.pop(0)

    def draw_message(self):
        pos_x = self.x + self._chip_size
        pos_y = self.y + self._chip_size
        if self.window_mode == "page":
            text = self.text_list[0]
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
    action_args: tuple = field(default_factory=tuple)  # 関数に渡す引数（あれば）
    # is_disabled: bool = False                # (将来用) 選択不可フラグなどを足しても便利です


class Menu:
    """メニュー基底クラス"""

    # 固定メニュー項目データ読込
    file = "assets/data/menu_structure.json"
    path = check_file(file)
    assert (
        path is not None
    ), f"固定メニュー項目データの読み込みに失敗しました：file={file}"
    menu_item_data = read_json(path)
    _MENU_ITEM_CASHE: dict[str, list[list[dict[str, str]]]] = dict(menu_item_data)

    def __init__(
        self,
        font_size_name: FONT_SIZE_NAME,
        x: int,
        y: int,  # width: int, height: int,
        menu_shape: list[int],
        # menu_items: list[list[str]],
        # menu_items: list[MenuItem]|str
        menu_source: str | list[list[dict[str, str]]],
    ):
        # self, image_chips: px.Image, x: int, y: int, font_name):

        # 管理クラスへの参照
        # self.chip = get_imagechip()
        self.img_cursor = [16, 0, Window._chip_size, Window._chip_size]
        self.fontdata = FontManager.get_fontdata(font_size_name)
        self.font = self.fontdata.font
        self.cursor_row_offset = px.ceil((self.fontdata.height - Window._chip_size) / 2)
        # クラス個別パラメータ
        self.cursor_position: list[int] = [0, 0]
        self.menu_shape: list = menu_shape  # 横軸数,縦軸数
        # self.menu_items: list = menu_items  # 横軸テキスト[a,b,c],,,※縦軸数分
        if isinstance(menu_source, str):  # メニュー固定項目指定時
            # if type(menu_source) is str:
            tmp_menudata = self._MENU_ITEM_CASHE[menu_source]
        else:  # 動的指定
            tmp_menudata = menu_source  # 横軸テキスト[a,b,c],,,※縦軸数分

        self.menu_items: list[list[MenuItem]] = [
            [
                MenuItem(
                    item_label=data["id"],
                    # menu_action = getattr(self, data["action"]) if isinstance(data["action"], str) else data["action"],
                    menu_action=getattr(self, data["action"], None),
                    action_args=tuple(data.get("args", [])),
                )
                for data in row
            ]
            for row in tmp_menudata
        ]
        # 共通基本パラメータ
        (
            width,
            height,
        ) = self.calculate_windowsize()  # フォントサイズを元にウインドウサイズ算出
        adjusted_x = (
            x if x + width <= px.width else px.width - width
        )  # 右端からはみ出す場合を考慮
        # ウインドウ生成処理
        self.windows: dict[MENU_WINDOW_TYPE, Window] = {}
        self.windows["main"] = Window(
            font_size_name, adjusted_x, y, width, height, "menu"
        )

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
        self.column_x_pos: list[int] = []
        current_x = Window._chip_size  # 描画初期アドレスを枠のすぐ右に定義

        column_items = [list(col) for col in zip(*self.menu_items)]
        # for column_text in column_items:
        for column_data in column_items:
            # 現在のカラムのX座標を記録
            self.column_x_pos.append(current_x)

            if self.font:
                text_list = [item.item_label for item in column_data]
                max_column_textlen = self.font.text_width(
                    max(text_list, key=self.font.text_width)
                )
            else:
                # デフォルトフォントの場合の文字長は4ピクセル
                max_column_textlen = max([item.item_label for item in column_data]) * 4
            menuwidth += offset_cursor + max_column_textlen + offset_sepalete_col
            current_x += menuwidth

        # チップサイズで丸めて最終的な幅を算出
        menuwidth = (
            px.ceil((menuwidth + framesize) / Window._chip_size) * Window._chip_size
        )
        # menuwidth = px.ceil((current_x - offset_sepalete_col + Window.chip_size) / Window.chip_size) * Window.chip_size

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

    def update(self):
        """更新"""
        RC = self.key_check()
        return RC

    def key_check(self):
        """キー入力の確認と応答"""
        inp = WindowInputHandler.get()
        if self.move_cursor(inp):
            return WindowAction.CONTINUE
        # if MenuInputHandler.is_pressed("decide"):
        if inp.decide():
            return WindowAction.EXECUTE
        # if MenuInputHandler.is_pressed("cancel"):
        if inp.cancel():
            return WindowAction.CLOSE
        if self.individual_key_check(inp):
            pass

    def individual_key_check(self, inp: WindowInputWrapper):
        """メニュー個別のキー判定用"""
        pass

    def move_cursor(self, inp: WindowInputWrapper) -> bool:
        """キー入力に応じたカーソル移動とインデックス制御"""
        # if WindowManager.is_pressed("up", "hold"):
        # if MenuInputHandler.is_pressed("up"):
        if inp.up():
            self.cursor_position[1] = (self.cursor_position[1] - 1) % self.menu_shape[1]
            return True
        # if WindowManager.is_pressed("left", "hold"):
        # if MenuInputHandler.is_pressed("left"):
        if inp.left():
            self.cursor_position[0] = (self.cursor_position[0] - 1) % self.menu_shape[0]
            return True
        # if WindowManager.is_pressed("down", "hold"):
        # if MenuInputHandler.is_pressed("down"):
        if inp.down():
            self.cursor_position[1] = (self.cursor_position[1] + 1) % self.menu_shape[1]
            return True
        # if WindowManager.is_pressed("right", "hold"):
        # if MenuInputHandler.is_pressed("right"):
        if inp.right():
            self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]
            return True
        return False

    def exec_menu(self) -> Any:
        ...

    def draw(self):
        """描画"""
        for name, win in self.windows.items():
            win.draw()
            if name == "main":
                self.draw_main()

    def draw_main(self):
        """メニュー項目文字表示"""
        # for row in range(self.menu_shape[1]):
        #     for col in range(self.menu_shape[0]):
        #         # for i,_str in enumerate(self.menu_items[row][col]):

        #         #     px.text(self.windows["main"].x+(1+((1+1)*col+(self.menutext_length*2)*col)+(1+1+i*2))*G_.CHIP_PIXEL,
        #         #             self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL,
        #         #             _str, px.COLOR_WHITE, G_.JP_FONT)
        for row_idx, row in enumerate(self.menu_items):
            # for col_idx, text in enumerate(row):
            for col_idx, item in enumerate(row):
                text_x = (
                    self.windows["main"].x
                    + self.column_x_pos[col_idx]
                    + Window._chip_size
                )  # カーソルの右隣
                text_y = self.windows["main"].y + self.row_y_pos[row_idx]
                px.text(text_x, text_y, item.item_label, px.COLOR_WHITE, self.font)
        self.draw_cursor()

    def draw_cursor(self):
        """メニューカーソル表示"""
        # self.cursor_address = [self.menu_window.x +
        #                        #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
        #                        (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
        #                        *G_.CHIP_PIXEL - 2,
        #                        self.menu_window.y +
        #                        (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        # px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)
        pos_x, pos_y = self.cursor_position
        cursor_x = self.windows["main"].x + self.column_x_pos[pos_x]
        cursor_y = (
            self.windows["main"].y + self.row_y_pos[pos_y] + self.cursor_row_offset
        )
        px.blt(
            cursor_x,
            cursor_y,
            self.windows["main"]._image_chips,
            *self.img_cursor,
            colkey=px.COLOR_BLACK,
        )


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
