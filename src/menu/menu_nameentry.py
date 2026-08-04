"""menu_nameentry.py
メニューモジュール：名前入力

"""

import logging
import pyxel as px
from gameutils.base import check_file, read_json, FontManager, shadowed_text
from gameutils.lib import Menu, Window, WindowAction  # , WindowInputHandler
from const import APP_FPS, SoundID
from assets.asset_map import AssetID, AssetMap
import service_locater as di
from entity import EntityParam


# ロギング設定
logger = logging.getLogger(__name__)


class MenuNameEntry(Menu):
    def __init__(self, param: EntityParam):
        # 名前引き渡し用キャラクタパラメータ
        self.param = param

        path = check_file(AssetMap.get_assetpath(AssetID.DATA_LETTER))
        if path is not None:
            self.name_chars = read_json(path)
        else:
            errmsg = "文字定義ファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)
        menu_pos = (8, 8)
        menu_shape = [11, 9]
        super().__init__("basic", *menu_pos, menu_shape, self.name_chars[0])

        self.max_name_length = 8
        self.prefix = "名前　：　"
        self.input_name_string = ""
        self.name_string = self.prefix + self.input_name_string
        # self.is_need_redraw = True
        self.warning_counter: int = 0  # 注意メッセージの表示中カウンタ
        self.warning_frames: int = APP_FPS * 3  # 注意メッセージの表示フレーム数
        self.warning_message: str = ""  # 注意メッセージの内容
        self.warning_fontdata = FontManager.get_fontdata("large")
        if self.warning_fontdata.font is None:
            errmsg = "日本語フォントデータが定義されていません"
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)

        # 名前表示ウインドウ
        name_w, name_h = 208, 24
        self.windows["sub"] = Window(
            "large",
            # px.width // 2 - name_w // 2,
            (px.width - name_w) // 2,
            # (self.windows["main"].y + self.windows["main"].height + Window._chip_size),
            (self.y + self.height + Window._chip_size),
            name_w,
            name_h,
            "sub",
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

    def individual_update(self) -> None:
        # 名前文字列を更新
        if (
            px.frame_count % APP_FPS < APP_FPS // 2
            or len(self.input_name_string) == self.max_name_length
        ):
            self.windows["sub"].set_message([self.name_string])
        else:
            self.windows["sub"].set_message([self.name_string + "＿"])
        # 注意メッセージ表示カウンタ更新
        if self.warning_counter > 0:
            self.warning_counter -= 1

    def key_check(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.move_cursor():
            px.play(self.se_ch, SoundID.CURSOR_VERTICAL, resume=True)
        elif self.inputkey.decide():
            px.play(self.se_ch, SoundID.DECIDE, resume=True)
            self.add_letter()
        elif self.inputkey.cancel():
            px.play(self.se_ch, SoundID.CANCEL, resume=True)
            self.delete_letter()
        return WindowAction.CONTINUE

    def add_letter(self) -> None:
        """入力名前文字列の末尾に追加"""
        # self.is_need_redraw = True
        # SE "pi"
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        match selected_item.item_label:
            case "ED":
                if len(self.input_name_string) <= 0:
                    self.warning_counter = self.warning_frames
                    self.warning_message = "名前が入力されていません"
                    return
                else:
                    # di.ref.scnmgr.change_scene("map")
                    # di.ref.scnmgr._stacks[-1].wndmgr.pop_stack()
                    self.param.name = self.input_name_string
                    di.ref.scnmgr.next_scene("charamake")
                    return
            case "片":
                self.build_menu_items(self.name_chars[1])
                return
            case "英":
                self.build_menu_items(self.name_chars[2])
                return
            case "平":
                self.build_menu_items(self.name_chars[0])
                return
        tmpStr = self.input_name_string + selected_item.item_label
        if len(tmpStr) > self.max_name_length:
            self.warning_message = "名前の文字数は８文字が上限です"
            # SE "don"
            self.warning_counter = self.warning_frames
            return
        else:
            self.input_name_string += selected_item.item_label

        self.name_string = self.prefix + self.input_name_string

    def delete_letter(self) -> None:
        """入力名前文字列の末尾を削除"""
        if len(self.input_name_string) == 0:
            di.ref.scnmgr.previous_scene(False)
            return
        else:
            tmpStr = self.input_name_string[:-1]
            self.input_name_string = tmpStr
            self.name_string = self.prefix + self.input_name_string

    def draw(self):
        super().draw()
        shadowed_text(
            self.windows["sub"].x,
            self.windows["sub"].y + self.windows["sub"].height + self.cursor_row_offset,
            "決定キー：文字入力　キャンセルキー：文字削除\nED：名前確定",
            px.COLOR_LIGHT_BLUE,
            self.windows["main"].font,
        )
        if self.warning_counter > 0:
            msglen = (
                0
                if self.warning_fontdata.font is None
                else self.warning_fontdata.font.text_width(self.warning_message)
            )
            msg_pos_x = (px.width - msglen) / 2
            msg_pos_y = px.height - (self.warning_fontdata.height * 3)
            backoffset = 4
            # px.dither(0.9)
            px.rect(
                msg_pos_x - backoffset,
                msg_pos_y - backoffset,
                msglen + (backoffset * 2),
                self.warning_fontdata.height + (backoffset * 2),
                px.COLOR_BLACK,
            )
            # px.dither(1)
            shadowed_text(
                msg_pos_x,
                msg_pos_y,
                self.warning_message,
                px.COLOR_RED,
                self.warning_fontdata.font,
                px.COLOR_PURPLE,
            )
