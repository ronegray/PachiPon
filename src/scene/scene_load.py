import pyxel as px
from gameutils.base import is_pressed, get_filelist, read_json  # , check_file, read_bin
from gameutils.lib import Window, WindowAction
from assets.asset_map import AssetID, AssetMap
import service_locater as di
from helper import upper_str, upper_int_spaced, upper_int_zeroed, format_leftright
from entity import PlayerSprite
from . import BaseScene


class SceneBaseSavedata(BaseScene):
    # カーソルイメージアドレス
    _img_cursor = [16, 0, Window._chip_size, Window._chip_size]
    # データウインドウ描画数
    _max_draw_datas: int = 5

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # データファイルの中身を読み込んで辞書化
        self.savedatas: list[dict] = []
        savedata_pathlist = get_filelist(AssetMap.get_assetpath(AssetID.SAVEDATA_DIR))
        if savedata_pathlist is None:
            return
        for i, path in enumerate(savedata_pathlist):
            self.savedatas.append({"data": read_json(path)})
            self.savedatas[i]["img"] = None
            str_line = ["", "", ""]

            # データウインドウ描画内容生成
            dat = self.savedatas[i]["data"]
            str_line = ["", "", ""]
            datano = "オートセーブ" if i == 0 else "データ" + upper_int_zeroed(i, 2)
            savetime = upper_str(dat["savetime"][:-6])
            str_line[0] = format_leftright(datano, savetime, 60)

            charimg_size = 16
            padding = 3
            img = px.Image(len(dat["chars"]) * (charimg_size + padding), charimg_size)
            img.rect(0, 0, img.width, img.height, px.COLOR_GREEN)
            for ci, chara in enumerate(dat["chars"]):
                tmp_sprite = PlayerSprite(0, 0, chara[0]["sprite_type"])
                img.blt(
                    padding + ci * (charimg_size + padding),
                    0,
                    tmp_sprite.img,
                    0,
                    0,
                    charimg_size,
                    charimg_size,
                )

            turn = f"ターン：{upper_int_spaced(dat["pt"]["turns"], 4)}"
            point = f"現在地：{di.ref.map.get_point(dat["pt"]["point"]).name}"  # type: ignore
            str_line[2] = "　" * 9 + turn + "　　" + point

            self.savedatas[i]["img"] = img
            self.savedatas[i]["str_line"] = str_line

            # self.data_windows[i].set_message(str_line)

        self.max_data_count: int = max(2, len(self.savedatas))
        # カーソル関連
        self.data_index: int = 0  # ターゲットデータのインデックス
        self.cursor_index: int = 0  # 画面上の何個目のデータを指すか(0~draw_datas)
        # データ表示ウインドウリスト
        self.data_windows: list[Window] = []
        self.draw_start_index: int = 0
        datwnd_x, datwnd_y = 0, 0
        datwnd_w, datwnd_h = px.width, 48
        # y_offset = 0
        for i in range(self._max_draw_datas):
            # ウインドウインスタンス生成＆イメージ用変数
            self.data_windows.append(
                Window("basic", datwnd_x, datwnd_y + datwnd_h * i, datwnd_w, datwnd_h, "view")
            )
            # y_offset += datwnd_h

        """9/16朝　データウインドウは５個に限定して、表示するデータを保持するクラスを定義してウインドウに直接持たせているデータをそちらに移し、描画時に対象データをウインドウに描画
        位置合わせの方法やデータを設定するか単に上書き描画だけするかは考える
        """

        # for i in range(self.max_data_count):
        #     # ウインドウインスタンス生成＆イメージ用変数
        #     # self.data_windows.append(
        #     #     Window("basic", datwnd_x, datwnd_y + y_offset,
        #     #            datwnd_w, datwnd_h, "view")
        #     # )
        #     # y_offset += datwnd_h
        #     self.data_windows[i].img = None
        #     # ウインドウ別メッセージ設定
        #     dat = self.savedatas[i]
        #     str_line = ["","",""]
        #     # savetime = ""
        #     # for s in dat["savetime"][:-6]:
        #     #     savetime += upper_str(s)
        #     # savetime = upper_str(dat["savetime"])
        #     #
        #     datano = "オートセーブ" if i == 0 else "データ"+upper_int_zeroed(i,2)
        #     savetime = upper_str(dat["savetime"][:-6])
        #     str_line[0] = format_leftright(datano, savetime, 60)

        #     charimg_size = 16
        #     padding = 3
        #     self.data_windows[i].img = px.Image(
        #         len(dat["chars"]) * (charimg_size + padding), charimg_size
        #     )
        #     self.data_windows[i].img.rect(0,0,
        #                                   self.data_windows[i].img.width,
        #                                   self.data_windows[i].img.height, px.COLOR_GREEN)
        #     for ci, chara in enumerate(dat["chars"]):
        #         tmp_sprite = PlayerSprite(0,0, chara[0]["sprite_type"])
        #         self.data_windows[i].img.blt(padding + ci * (charimg_size + padding), 0,
        #                                      tmp_sprite.img, 0,0, charimg_size,charimg_size)

        #     turn = f"ターン：{upper_int_spaced(dat["pt"]["turns"], 4)}"
        #     point = f"現在地：{di.ref.map.get_point(dat["pt"]["point"]).name}" # type: ignore
        #     # str_line[2] = format_leftright(" ", point, 60)
        #     str_line[2] = "　" * 9 + turn + "　　" + point

        #     self.data_windows[i].set_message(str_line)
        self.set_datawindow()

    def set_datawindow(self) -> None:
        """データウインドウに表示する内容を設定／更新"""
        # for i_target in range(self.draw_start_index,
        #                       self.draw_start_index + self._max_draw_datas):
        #     self.data_windows[i_target].set_message(self.savedatas[i_target]["str_line"])
        #     canvas = self.data_windows[i_target]
        #     img = self.savedatas[i_target]["img"]
        #     draw_x, draw_y = 8, 24
        #     canvas.window_image.rect(draw_x, draw_y, img.width, img.height, px.COLOR_NAVY)
        #     canvas.window_image.blt(draw_x, draw_y, img,
        #                             0,0, img.width,img.height, px.COLOR_GREEN)
        draw_x, draw_y = 8, 24
        for i, wnd in enumerate(self.data_windows):
            targetdata_index = i + self.draw_start_index
            wnd.set_message(self.savedatas[targetdata_index]["str_line"])
            img = self.savedatas[targetdata_index]["img"]
            wnd.window_image.rect(draw_x, draw_y, img.width, img.height, px.COLOR_NAVY)
            wnd.window_image.blt(draw_x, draw_y, img, 0, 0, img.width, img.height, px.COLOR_GREEN)

    def update(self) -> None:
        for wnd in self.data_windows:
            if wnd.update() != WindowAction.CONTINUE:
                return

        if is_pressed("up"):
            self.data_index = (self.data_index - 1) % self.max_data_count
            # # if self.cursor_index == 0:
            # #     self.draw_start_index -= 1
            # #     self.set_datawindow()
            # # else:
            # #     self.cursor_index -= 1
            max_draw_index = self._max_draw_datas - 1
            # if self.data_index == max_draw_index:
            #     self.cursor_index = max_draw_index
            #     self.draw_start_index = self.data_index - self.max_data_count
            #     self.set_datawindow()
            # elif self.cursor_index == 0:
            #     self.draw_start_index -= 1
            #     self.set_datawindow()
            # else:
            #     self.cursor_index -= 1
            if self.cursor_index == 0:
                if self.draw_start_index == 0:
                    self.cursor_index = max_draw_index
                    self.draw_start_index = self.max_data_count - self._max_draw_datas
                    self.set_datawindow()
                else:
                    self.draw_start_index -= 1
                    self.set_datawindow()
            else:
                self.cursor_index -= 1

        elif is_pressed("down"):
            self.data_index = (self.data_index + 1) % self.max_data_count
            # if self.data_index == 0:
            #     self.cursor_index = 0
            # elif self.cursor_index < self._draw_datas:
            #     self.cursor_index += 1
            # else:
            #     pass
            max_draw_index = self._max_draw_datas - 1
            if self.data_index == 0:
                self.cursor_index = self.draw_start_index = 0
                self.set_datawindow()
            elif self.cursor_index == max_draw_index:
                self.draw_start_index += 1
                self.set_datawindow()
            else:
                self.cursor_index += 1

    def draw(self) -> None:
        for i, wnd in enumerate(self.data_windows):
            wnd.draw()
            wnd.draw_message(offset_y=-4)

        px.blt(
            3,
            20 + self.cursor_index * 48,
            self.data_windows[0]._image_chips,
            *self._img_cursor,
            colkey=px.COLOR_BLACK,
        )
        return
        # 以下デバッグ用
        y = 0
        for dat in self.savedatas:
            img = dat["img"]
            px.blt(0, 0 + y, img, 0, 0, img.width, img.height, px.COLOR_GREEN)
            y += 24


class SceneLoaddata(SceneBaseSavedata):
    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # # データファイルの中身を読み込んで辞書化
        # self.savedatas: list = []
        # savedata_pathlist = get_filelist(AssetMap.get_assetpath(AssetID.SAVEDATA_DIR))
        # if savedata_pathlist is None:
        #     return
        # for path in savedata_pathlist:
        #     self.savedatas.append(read_json(path))
        # self.max_data_count: int = max(2, len(self.savedatas))
        # # カーソル関連
        # self.data_index: int = 0 # ターゲットデータのインデックス
        # self.cursor_index: int = 0 # 画面上の何個目のデータを指すか(0~draw_datas)
        # # データ表示ウインドウリスト
        # self.data_windows: list[Window] = []
        # datwnd_x, datwnd_y = 0, 0
        # datwnd_w, datwnd_h = px.width, 48
        # # y_offset = 0
        # for i in range(self._draw_datas):
        #     # ウインドウインスタンス生成＆イメージ用変数
        #     self.data_windows.append(
        #         Window("basic", datwnd_x, datwnd_y + datwnd_h * i,
        #                datwnd_w, datwnd_h, "view")
        #     )
        #     # y_offset += datwnd_h

        # """9/16朝　データウインドウは５個に限定して、表示するデータを保持するクラスを定義してウインドウに直接持たせているデータをそちらに移し、描画時に対象データをウインドウに描画
        # 位置合わせの方法やデータを設定するか単に上書き描画だけするかは考える
        # """

        # for i in range(self._draw_datas):
        #     # ウインドウインスタンス生成＆イメージ用変数
        #     # self.data_windows.append(
        #     #     Window("basic", datwnd_x, datwnd_y + y_offset,
        #     #            datwnd_w, datwnd_h, "view")
        #     # )
        #     # y_offset += datwnd_h
        #     self.data_windows[i].img = None
        #     # ウインドウ別メッセージ設定
        #     dat = self.savedatas[i]
        #     str_line = ["","",""]
        #     # savetime = ""
        #     # for s in dat["savetime"][:-6]:
        #     #     savetime += upper_str(s)
        #     # savetime = upper_str(dat["savetime"])
        #     #
        #     datano = "オートセーブ" if i == 0 else "データ"+upper_int_zeroed(i,2)
        #     savetime = upper_str(dat["savetime"][:-6])
        #     str_line[0] = format_leftright(datano, savetime, 60)

        #     charimg_size = 16
        #     padding = 3
        #     self.data_windows[i].img = px.Image(
        #         len(dat["chars"]) * (charimg_size + padding), charimg_size
        #     )
        #     self.data_windows[i].img.rect(0,0,
        #                                   self.data_windows[i].img.width,
        #                                   self.data_windows[i].img.height, px.COLOR_GREEN)
        #     for ci, chara in enumerate(dat["chars"]):
        #         tmp_sprite = PlayerSprite(0,0, chara[0]["sprite_type"])
        #         self.data_windows[i].img.blt(padding + ci * (charimg_size + padding), 0,
        #                                      tmp_sprite.img, 0,0, charimg_size,charimg_size)

        #     turn = f"ターン：{upper_int_spaced(dat["pt"]["turns"], 4)}"
        #     point = f"現在地：{di.ref.map.get_point(dat["pt"]["point"]).name}" # type: ignore
        #     # str_line[2] = format_leftright(" ", point, 60)
        #     str_line[2] = "　" * 9 + turn + "　　" + point

        #     self.data_windows[i].set_message(str_line)

    def update(self) -> None:
        # for wnd in self.data_windows:
        #     if wnd.update() != WindowAction.CONTINUE:
        #         return

        # if is_pressed("up"):
        #     self.data_index = (self.data_index - 1) % self.max_data_count
        #     self.cursor_index = self.cursor_index - 1 if self.cursor_index > 0 else self.cursor_index
        # elif is_pressed("down"):
        #     self.data_index = (self.data_index + 1) % self.max_data_count
        #     if self.data_index == 0:
        #         self.cursor_index = 0
        #     elif self.cursor_index < self._draw_datas:
        #         self.cursor_index += 1
        #     else:
        #         pass
        super().update()

    def draw(self) -> None:
        # for i, wnd in enumerate(self.data_windows):
        #     if i <= self._draw_datas or i <= self._draw_datas + self.data_index - self.cursor_index:
        #         wnd.draw()
        #         wnd.draw_message(offset_y=-4)
        #         px.blt(wnd.x + 8, wnd.y + 24, wnd.img, 0,0,wnd.img.width,wnd.img.height, px.COLOR_GREEN)
        #     px.blt(
        #         3,
        #         20+self.cursor_index*48,
        #         self.data_windows[0]._image_chips,
        #         *self._img_cursor,
        #         colkey=px.COLOR_BLACK,
        #     )
        super().draw()
