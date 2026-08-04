"""
メニューモジュール：レベルアップ
"""

import logging
import pyxel as px
import service_locater as di
from const import SoundID, BONUS_POINT, BASE_PARAM, INITIAL_MAX_PARAM
from helper import upper_int_format, format_leftright
from gameutils.base import check_file, read_json
from gameutils.lib import (
    Menu,
    # MENU_ITEM_LIST,
    Window,
    MenuYesNo,
    WindowAction,
    ExecResult,
    RsltPush,
)
from assets.asset_map import AssetID, AssetMap
from entity import Character  # , EntityParam


# ロギング設定
logger = logging.getLogger(__name__)


class MenuCharaMake(Menu):
    def __init__(self, hero: Character) -> None:
        path = check_file(AssetMap.get_assetpath(AssetID.DATA_PARAM))
        if path is None:
            errmsg = "パラメータ詳細ファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)
        self.param_desc: list[str] = read_json(path)

        self.bonus_max = BONUS_POINT  # 振り分け可能ポイント
        self.assigned = 0  # 振り分け済ポイント

        self.hero = hero
        # メニューウインドウのサイズ
        gain_w = 128  # 上昇項目選択
        menu_pos_x, menu_pos_y = Window._chip_size, 76
        menu_shape = [1, 5]
        super().__init__(
            "basic", menu_pos_x, menu_pos_y, menu_shape, "MenuLevelup", gain_w
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        # ボーナスポイント現在値
        bonus_w, bonus_h = 104, 24
        offset = 2
        self.windows["sub"] = Window(
            "basic",
            self.x + self.width + offset,
            self.y - bonus_h,
            bonus_w,
            bonus_h,
            "once",
        )
        self.set_bonuspoint_string()

        # パラメータ項目説明ウインドウ
        param_w = 104
        self.windows["sub2"] = Window(
            "basic", self.x + self.width + offset, self.y, param_w, self.height, "once"
        )
        self.set_description_string()

        # YesNoダイアログ応答内容
        self.ans: dict[str, bool | None] = {"answer": None, "finished": False}

    def set_bonuspoint_string(self) -> None:
        """残りボーナスポイント表示"""
        self.windows["sub"].set_message(
            [f"残りポイント：{upper_int_format(self.bonus_max - self.assigned, 2)}"]
        )

    def set_description_string(self) -> None:
        """詳細ウインドウに表示する文字列を設定"""
        item_desc = self.param_desc[self.cursor_position[1]]
        text_area_width = self.windows["sub2"].width - (Window._chip_size * 2)
        message_list = []
        start_row = 0
        for desc_string in item_desc:
            for i in range(0, len(desc_string) + 1):
                if (
                    self.windows["sub2"].fontdata.font.text_width(  # type: ignore
                        desc_string[start_row : i + 1]
                    )
                    > text_area_width
                ):
                    message_list.append(desc_string[start_row:i])
                    start_row = i
            # 最後の残りを結合
            message_list.append(desc_string[start_row:i])  # type: ignore
        self.windows["sub2"].set_message(message_list)

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

        result = selected_item.menu_action()
        return result

    def ask_confirm(self) -> RsltPush:
        return RsltPush(
            MenuYesNo,
            self.ans,
            [
                "パラメータ設定は これでよろしいですか？",
                "よろしければ ＨＰ・ＭＰの算出を開始します",
            ],
        )

    def move_cursor(self) -> bool:
        """キー入力に応じたカーソル移動とインデックス制御"""
        if self.inputkey.up():
            px.play(self.se_ch, SoundID.CURSOR_VERTICAL, resume=True)
            self.cursor_position[1] = (self.cursor_position[1] - 1) % self.menu_shape[1]
            self.set_description_string()
            return True
        if self.inputkey.left():
            is_assigned = False
            match self.cursor_position[1]:
                case 0:
                    if self.hero.param.strength > BASE_PARAM:
                        is_assigned = True
                        self.hero.param.strength -= 1
                case 1:
                    if self.hero.param.arcane > BASE_PARAM:
                        is_assigned = True
                        self.hero.param.arcane -= 1
                case 2:
                    if self.hero.param.endurance > BASE_PARAM:
                        is_assigned = True
                        self.hero.param.endurance -= 1
                case 3:
                    if self.hero.param.speed > BASE_PARAM:
                        is_assigned = True
                        self.hero.param.speed -= 1
                case 4:
                    if self.hero.param.luck > BASE_PARAM:
                        is_assigned = True
                        self.hero.param.luck -= 1
            if is_assigned:
                px.play(self.se_ch, SoundID.DECIDE, resume=True)
                self.assigned = max(0, self.assigned - 1)
                self.set_bonuspoint_string()
            else:
                px.play(self.se_ch, SoundID.ERROR, resume=True)

            return True
        if self.inputkey.down():
            px.play(self.se_ch, SoundID.CURSOR_VERTICAL, resume=True)
            self.cursor_position[1] = (self.cursor_position[1] + 1) % self.menu_shape[1]
            self.set_description_string()
            return True
        if self.inputkey.right():
            if self.assigned < self.bonus_max:
                is_assigned = False
                match self.cursor_position[1]:
                    case 0:
                        if self.hero.param.strength < INITIAL_MAX_PARAM:
                            is_assigned = True
                            self.hero.param.strength += 1
                    case 1:
                        if self.hero.param.arcane < INITIAL_MAX_PARAM:
                            is_assigned = True
                            self.hero.param.arcane += 1
                    case 2:
                        if self.hero.param.endurance < INITIAL_MAX_PARAM:
                            is_assigned = True
                            self.hero.param.endurance += 1
                    case 3:
                        if self.hero.param.speed < INITIAL_MAX_PARAM:
                            is_assigned = True
                            self.hero.param.speed += 1
                    case 4:
                        if self.hero.param.luck < INITIAL_MAX_PARAM:
                            is_assigned = True
                            self.hero.param.luck += 1
                if is_assigned:
                    px.play(self.se_ch, SoundID.DECIDE, resume=True)
                    self.assigned = min(self.bonus_max, self.assigned + 1)
                    self.set_bonuspoint_string()
                else:
                    px.play(self.se_ch, SoundID.ERROR, resume=True)
            else:
                px.play(self.se_ch, SoundID.ERROR, resume=True)
            # self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]
            return True
        return False

    def key_check(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.move_cursor():
            pass
        elif self.inputkey.decide():
            if self.bonus_max == self.assigned:
                px.play(self.se_ch, SoundID.DECIDE, resume=True)
                return WindowAction.EXECUTE
            else:
                px.play(self.se_ch, SoundID.ERROR, resume=True)
        elif self.inputkey.cancel():
            di.ref.scnmgr.previous_scene()
        return WindowAction.CONTINUE

    def update(self) -> WindowAction:
        """更新"""
        if self.ans["finished"]:
            if self.ans["answer"]:
                # self.target.append(self.menu_items[self.cursor_position[1]][0].action_args[0])
                return WindowAction.CLOSE
            elif self.ans["answer"] is False:
                self.ans["finished"] = False
                self.ans["answer"] = None
                self.assigned = 0
                self.hero.param.strength = BASE_PARAM
                self.hero.param.arcane = BASE_PARAM
                self.hero.param.endurance = BASE_PARAM
                self.hero.param.speed = BASE_PARAM
                self.hero.param.luck = BASE_PARAM
                self.set_bonuspoint_string()
                return WindowAction.CONTINUE
        RC = self.key_check()
        return RC

    def draw(self) -> None:
        super().draw()
        member = self.hero
        for i, y in enumerate(self.row_y_pos):
            match i:
                case 0:
                    param = f"{
                        format_leftright(
                            upper_int_format(member.strength, 2),
                            f'（＋{upper_int_format(member.bonus_str, 1)}）',
                            14,
                        )
                    }"
                case 1:
                    param = f"{
                        format_leftright(
                            upper_int_format(member.arcane, 2),
                            f'（＋{upper_int_format(member.bonus_arc, 1)}）',
                            14,
                        )
                    }"
                case 2:
                    param = f"{
                        format_leftright(
                            upper_int_format(member.endurance, 2),
                            f'（＋{upper_int_format(member.bonus_end, 1)}）',
                            14,
                        )
                    }"
                case 3:
                    param = f"{
                        format_leftright(
                            upper_int_format(member.speed, 2),
                            f'（＋{upper_int_format(member.bonus_spd, 1)}）',
                            14,
                        )
                    }"
                case 4:
                    param = f"{
                        format_leftright(
                            upper_int_format(member.luck, 2),
                            f'（＋{upper_int_format(member.bonus_lck, 1)}）',
                            14,
                        )
                    }"
            px.text(
                self.width - self.font.text_width(param) - Window._chip_size,  # type: ignore
                y + self.height - self.cursor_row_offset,
                param,  # type: ignore
                px.COLOR_WHITE,
                self.font,
            )  # type: ignore
        self.windows["sub2"].draw_message()
