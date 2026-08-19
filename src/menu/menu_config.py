"""
メニューモジュール：コンフィグ（タイトル）
"""

import logging
from typing import Callable
import pyxel as px
import service_locater as di

# from const import SoundID
from config import CONF_VOLUME, CONF_DISP_SIZE, CONF_TEXT_SPEED
from gameutils.base import BGM_CHANNELS, SE_INSTANT_CH, SE_SUSTAIN_CH
from gameutils.lib import (
    Window,
    Menu,
    MenuYesNo,
    MENU_ITEM_LIST,
    ExecResult,
    RsltPush,
    RsltPop,
)

# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectConfigTarget(Menu):
    """コンフィグ項目選択メニュー"""

    def __init__(self, y: int, build_config_info: Callable) -> None:
        self.build_config_info = build_config_info
        menu_pos = (0, y)
        menu_shape = [1, 8]
        super().__init__("basic", *menu_pos, menu_shape, self.__class__.__name__)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.ans_fullsc: dict[str, bool | None] = {"answer": None, "finished": False}
        self.ans_curpos: dict[str, bool | None] = {"answer": None, "finished": False}
        self.ans_cutind: dict[str, bool | None] = {"answer": None, "finished": False}

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

    def individual_update(self) -> None:
        if self.ans_fullsc["finished"]:
            di.ref.conf.is_fullscreen = True if self.ans_fullsc["answer"] else False
            px.fullscreen(di.ref.conf.is_fullscreen)
            self.ans_fullsc["finished"] = False
            self.build_config_info()
        if self.ans_curpos["finished"]:
            di.ref.conf.is_memory_cursor = True if self.ans_curpos["answer"] else False
            self.ans_curpos["finished"] = False
            self.build_config_info()
        if self.ans_cutind["finished"]:
            di.ref.conf.is_cutin_dice = True if self.ans_cutind["answer"] else False
            self.ans_cutind["finished"] = False
            self.build_config_info()

    def set_vol_bgm(self):
        return RsltPush(
            MenuConfigVolume, self.cursor_x, self.cursor_y, 0, self.build_config_info
        )

    def set_vol_se(self):
        return RsltPush(
            MenuConfigVolume, self.cursor_x, self.cursor_y, 1, self.build_config_info
        )

    def set_dispsize(self):
        return RsltPush(
            MenuConfigDisplaySize, self.cursor_x, self.cursor_y, self.build_config_info
        )

    def set_fullscreen(self):
        # return RsltPush(MenuYesNo)
        return RsltPush(
            MenuYesNo,
            self.ans_fullsc,
            ["全画面モードに設定しますか？"],
        )

    def set_textspeed(self):
        return RsltPush(
            MenuConfigTextSpeed, self.cursor_x, self.cursor_y, self.build_config_info
        )

    def set_cursorpos(self):
        # return RsltPush(MenuYesNo)
        return RsltPush(
            MenuYesNo,
            self.ans_curpos,
            ["戦闘時のカーソル位置を記憶しますか？"],
        )

    def set_cutin_dice(self):
        # return RsltPush(MenuYesNo)
        return RsltPush(
            MenuYesNo,
            self.ans_cutind,
            ["ダイスロール演出を表示しますか？"],
        )

    def assign_key(self):
        return RsltPush(MenuAssignKey)


class MenuConfigVolume(Menu):
    def __init__(self, x: int, y: int, target: int, build_config_info: Callable):
        self.build_config_info = build_config_info
        # 0=bgm 1=se
        if target not in (0, 1):
            target = 0
        self.target = target
        self.item_list: MENU_ITEM_LIST = []
        self.generate_item_list()
        row_offset = 2
        super().__init__(
            "basic",
            x + Window._chip_size,
            y + Window._chip_size + row_offset,
            self.menu_shape,
            self.item_list,
        )

    def generate_item_list(self):
        """メニューアイテム生成"""
        for dict_ in CONF_VOLUME.values():
            self.item_list.append(
                [
                    {
                        "id": f"{dict_["label"]}",
                        "action": f"{dict_["action"]}",
                        "args": dict_["args"],
                    }
                ]
            )
        self.menu_shape = [1, len(self.item_list)]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        # if selected_item.menu_action is None:
        #     errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
        #     logger.critical(errmsg, exc_info=True)
        #     raise ValueError(errmsg)

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )

        # result = selected_item.menu_action(*selected_item.action_args)
        # return result
        vol_conf, vol_factor = selected_item.action_args
        match self.target:
            case 0:
                di.ref.conf.vol_bgm = vol_conf
                di.ref.sndmgr.set_basegain_factor(vol_factor, BGM_CHANNELS)
            case 1:
                di.ref.conf.vol_se = vol_conf
                di.ref.sndmgr.set_basegain_factor(
                    vol_factor, (SE_INSTANT_CH, SE_SUSTAIN_CH)
                )

        return RsltPop([self.build_config_info])


class MenuConfigDisplaySize(Menu):
    def __init__(self, x: int, y: int, build_config_info: Callable):
        self.build_config_info = build_config_info
        self.item_list: MENU_ITEM_LIST = []
        self.generate_item_list()
        row_offset = 2
        super().__init__(
            "basic",
            x + Window._chip_size,
            y + Window._chip_size + row_offset,
            self.menu_shape,
            self.item_list,
        )

    def generate_item_list(self):
        """メニューアイテム生成"""
        for dict_ in CONF_DISP_SIZE.values():
            self.item_list.append(
                [
                    {
                        "id": f"{dict_["label"]}",
                        "action": f"{dict_["action"]}",
                        "args": dict_["args"],
                    }
                ]
            )
        self.menu_shape = [1, len(self.item_list)]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )

        disp_conf, disp_factor = selected_item.action_args
        di.ref.conf.display_size = disp_conf

        return RsltPop([self.build_config_info])


class MenuConfigTextSpeed(Menu):
    def __init__(self, x: int, y: int, build_config_info: Callable):
        self.build_config_info = build_config_info
        self.item_list: MENU_ITEM_LIST = []
        self.generate_item_list()
        row_offset = 2
        super().__init__(
            "basic",
            x + Window._chip_size,
            y + Window._chip_size + row_offset,
            self.menu_shape,
            self.item_list,
        )

    def generate_item_list(self):
        """メニューアイテム生成"""
        for dict_ in CONF_TEXT_SPEED.values():
            self.item_list.append(
                [
                    {
                        "id": f"{dict_["label"]}",
                        "action": f"{dict_["action"]}",
                        "args": dict_["args"],
                    }
                ]
            )
        self.menu_shape = [1, len(self.item_list)]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )

        text_conf, text_factor = selected_item.action_args
        di.ref.conf.text_speed = text_conf

        return RsltPop([self.build_config_info])


class MenuAssignKey(Menu):
    ...
