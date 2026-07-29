"""
メニューモジュール：レベルアップ
"""

import logging
import pyxel as px

# import service_locater as di
# from const import SoundID
from helper import upper_int_format, format_leftright
from gameutils.lib import (
    Menu,
    Window,
    MenuYesNo,
    WindowAction,
    ExecResult,
    RsltPush,
)
from entity import Character  # , EntityParam


# ロギング設定
logger = logging.getLogger(__name__)


class MenuLevelup(Menu):
    def __init__(self, member: Character, target: list[str]) -> None:
        self.member = member
        # 情報表示ウインドウのサイズ
        param_w, param_h = 128, 136  # ステータス
        gain_w = 128  # 上昇項目選択
        padding = 2
        pos_x = Window._chip_size
        pos_y = Window._chip_size

        menu_pos = (pos_x, pos_y + param_h + padding)
        menu_shape = [1, 5]  #

        # メニュー本体はパラメータ側
        super().__init__("basic", *menu_pos, menu_shape, "MenuLevelup", gain_w)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.windows["sub"] = Window("basic", pos_x, pos_y, param_w, param_h, "once")
        self.build_status()

        self.ans: dict[str, bool | None] = {"answer": None, "finished": False}
        self.target: list[str] = target

    def build_status(self) -> None:
        """ステータス表示内容の構築（ステータスのみ）"""
        member = self.member
        param = member.param

        status_lines = f"{param.name}"
        status_lines += f"\nレベル： {upper_int_format(param.level,2)}"
        status_lines += f"\n経験値： {upper_int_format(param.exp,6)}"
        status_lines += f"\nＨ　Ｐ： {upper_int_format(param.hp, 3)}／{upper_int_format(param.max_hp, 3)}"
        status_lines += f"\nＭ　Ｐ： {upper_int_format(param.mp, 3)}／{upper_int_format(param.max_mp, 3)}"
        status_lines += f"\n筋　力： {format_leftright(
                upper_int_format(member.strength, 3),
                f"（＋{upper_int_format(member.bonus_str,1)}）",
                18)}"
        status_lines += f"\n魔　力： {format_leftright(
                upper_int_format(member.arcane, 3),
                f"（＋{upper_int_format(member.bonus_str,1)}）",
                18)}"
        status_lines += f"\n耐　久： {format_leftright(
                upper_int_format(member.endurance, 3),
                f"（＋{upper_int_format(member.bonus_end,1)}）",
                18)}"
        status_lines += f"\n速　度： {format_leftright(
                upper_int_format(member.speed, 3),
                f"（＋{upper_int_format(member.bonus_spd,1)}）",
                18)}"
        status_lines += f"\n幸　運： {format_leftright(
                upper_int_format(member.luck, 3),
                f"（＋{upper_int_format(member.bonus_lck,1)}）",
                18)}"

        self.windows["sub"].message_list = [status_lines]

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

    def update(self) -> WindowAction:
        """更新"""
        if self.ans["finished"]:
            if self.ans["answer"]:
                self.target.append(
                    self.menu_items[self.cursor_position[1]][0].action_args[0]
                )
                return WindowAction.CLOSE
            elif self.ans["answer"] is False:
                self.ans["answer"] = None
        RC = self.key_check()
        return RC

    def individual_update(self):
        """MenuYesNoからの戻り値に応じた処理"""

    def ask_confirm(self) -> RsltPush:
        return RsltPush(
            MenuYesNo,
            self.ans,
            [
                f"成長させるパラメータは『{self.menu_items[self.cursor_position[1]][0].item_label}』でよろしいですか？"
            ],
        )

    def key_check(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.move_cursor():
            px.play(self.se_ch, self.ui_se["CURSOR_VERTICAL"], resume=True)
        elif self.inputkey.decide():
            px.play(self.se_ch, self.ui_se["DECIDE"], resume=True)
            return WindowAction.EXECUTE
        return WindowAction.CONTINUE
