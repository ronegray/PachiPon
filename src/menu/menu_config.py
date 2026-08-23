"""
メニューモジュール：コンフィグ（タイトル）
"""

import logging
from typing import Callable
import pyxel as px
import service_locater as di

from const import SoundID
from config import (
    CONF_VOLUME,
    CONF_DISP_SIZE,
    CONF_TEXT_SPEED,
    ASSIGNABLE_KEY_ACTIONS,
    KEYCODE_UNASSIGNABLE,
)
from gameutils.base import (
    BGM_CHANNELS,
    SE_INSTANT_CH,
    SE_SUSTAIN_CH,
    listener,
    keybind,
    unbind_action,
)
from gameutils.lib import (
    Window,
    Menu,
    MenuYesNo,
    MENU_ITEM_LIST,
    WindowAction,
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
        return RsltPush(
            MenuAssignKey, self.cursor_x, self.cursor_y, self.build_config_info
        )


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

        disp_conf, _ = selected_item.action_args
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

        text_conf, _ = selected_item.action_args
        di.ref.conf.text_speed = text_conf

        return RsltPop([self.build_config_info])


class MenuAssignKey(Menu):
    ...

    def __init__(self, x: int, y: int, build_config_info: Callable):
        # self.key_names = {getattr(px, name): name.replace("KEY_", "").replace("GAMEPAD1_", "")
        #                   for name in dir(px)
        #                   if name.startswith("KEY_") or name.startswith("GAMEPAD1_")
        # }
        self.build_config_info = build_config_info
        item_list = self.build_config_info()
        # super().__init__(px.width//2 -96 ,8, [3,7], item_list, 7, 5)
        row_offset = 2
        menu_pos_x, menu_pos_y = (
            x + Window._chip_size,
            y + Window._chip_size + row_offset,
        )
        menu_shape = [3, 4]
        super().__init__("basic", menu_pos_x, menu_pos_y, menu_shape, item_list)
        self.cursor_row_offset += 2

        # self.insMsgWnd  = Window(px.width//2 - (P_CHIP_SIZE*17)//2, px.height//1.5, P_CHIP_SIZE*17, P_CHIP_SIZE*5, 0)
        # # self.txtMsg     = Message(self.insMsgWnd.P_x+P_CHIP_SIZE, self.insMsgWnd.P_y+P_CHIP_SIZE*2, [self.prefix + self.InputName])
        # self.txtMsg     = Message(self.insMsgWnd.P_x+P_CHIP_SIZE, self.insMsgWnd.P_y+P_CHIP_SIZE*2, ["わりあてるキーをおしてください"])
        suggest_x, suggest_y = menu_pos_x, menu_pos_y + self.height
        suggest_w, suggest_h = 128, 24
        self.suggest_window = Window(
            "basic", suggest_x, suggest_y, suggest_w, suggest_h, "hold"
        )
        self.suggest_window.set_message(["割り当てるキーを押して下さい"])
        self.is_keylisten: bool = False

        self.cursor_position = [1, 1]

    def update(self) -> WindowAction:
        if self.is_keylisten:
            match self.cursor_position[0]:
                case 1:
                    target = "pad"
                case 2:
                    target = "kbd"
                case _:
                    target = "pad"
            response = listener(target)
            if response != (-999, -999):
                if response[0] in KEYCODE_UNASSIGNABLE:
                    di.ref.sndmgr.play_se_instant(SoundID.ERROR)
                    self.is_keylisten = False
                    return WindowAction.CONTINUE
                action_name = list(ASSIGNABLE_KEY_ACTIONS)[self.cursor_position[1] - 1]
                unbind_action(action_name, target)  # type: ignore
                keybind(action_name, *response, target)  # type: ignore
                items = self.build_config_info()
                self.build_menu_items(items)
                self.is_keylisten = False
            return WindowAction.CONTINUE

        """キー入力に応じたカーソル移動とインデックス制御"""

        def _move_cursor() -> bool:
            if self.inputkey.up():
                self.cursor_position[1] = (
                    self.cursor_position[1] - 1
                ) % self.menu_shape[1]
                if self.cursor_position[1] == 0:
                    self.cursor_position[1] = (
                        self.cursor_position[1] - 1
                    ) % self.menu_shape[1]
                return True
            if self.inputkey.left():
                self.cursor_position[0] = (
                    self.cursor_position[0] - 1
                ) % self.menu_shape[0]
                if self.cursor_position[0] == 0:
                    self.cursor_position[0] = (
                        self.cursor_position[0] - 1
                    ) % self.menu_shape[0]
                return True
            if self.inputkey.down():
                self.cursor_position[1] = (
                    self.cursor_position[1] + 1
                ) % self.menu_shape[1]
                if self.cursor_position[1] == 0:
                    self.cursor_position[1] = (
                        self.cursor_position[1] + 1
                    ) % self.menu_shape[1]
                return True
            if self.inputkey.right():
                self.cursor_position[0] = (
                    self.cursor_position[0] + 1
                ) % self.menu_shape[0]
                if self.cursor_position[0] == 0:
                    self.cursor_position[0] = (
                        self.cursor_position[0] + 1
                    ) % self.menu_shape[0]
                return True
            return False

        """キー入力の確認と応答"""
        if _move_cursor():
            self.se.play(self.ui_se["CURSOR_VERTICAL"])
        elif self.inputkey.decide():
            self.se.play(self.ui_se["DECIDE"])
            if self.is_keylisten is False:
                self.is_keylisten = True
            return WindowAction.EXECUTE
        elif self.inputkey.cancel():
            self.is_keylisten = False
            return WindowAction.CLOSE
        return WindowAction.CONTINUE

    def draw(self) -> None:
        super().draw()
        if self.is_keylisten:
            self.suggest_window.draw()
            self.suggest_window.draw_message()

    # def moveCursor(self):
    #     if inp.is_pressed("up", "hold"):
    #         px.flip()
    #         self.posCursor[1] -= 1
    #     if inp.is_pressed("left", "hold"):
    #         px.flip()
    #         self.posCursor[0] -= 1
    #     if inp.is_pressed("down", "hold"):
    #         px.flip()
    #         self.posCursor[1] += 1
    #     if inp.is_pressed("right", "hold"):
    #         px.flip()
    #         self.posCursor[0] += 1

    #     if self.posCursor[1] == 0:
    #         self.posCursor[1] = self.wndSize[1]
    #     if self.posCursor[1] == self.wndSize[1]:
    #         self.posCursor[1] = 1
    #     if self.posCursor[0] == 0:
    #         self.posCursor[0] = self.wndSize[0]
    #     if self.posCursor[0] == self.wndSize[0]:
    #         self.posCursor[0] = 1

    # def menuKeyConfig(self):
    #     if self.flgMsgWnd is False:
    #         self.flgMsgWnd = True
    #         return True
    #     else:
    #         target = "pad" if self.posCursor[0] % self.wndSize[0] == 0 else "kbd"
    #         response = inp.listener(target)
    #         if response:
    #             action_name = ASSIGNABLE_ACTIONS_INDEX[self.posCursor[1] % self.wndSize[1]]
    #             inp.keybind(action_name, *response, target)
    #             self.items = self.build_keyassign_matrix()

    #         return True

    # def draw(self):
    #     if self.flgCmd:
    #         self.insCmd.draw()
    #     else:
    #         self.drawMenu()
    #         if self.flgMsgWnd:
    #             self.insMsgWnd.draw()
    #             self.insMsgWnd.drawText(self.txtMsg.P_x, self.txtMsg.P_y, self.txtMsg.msg)
    #         # if self.flgMsgWnd2:
    #         #     self.insMsgWnd2.draw()
    #         #     self.insMsgWnd2.drawText(self.insMsgWnd2.P_x + ( self.insMsgWnd2.P_width//2 - (P_CHIP_SIZE*len(self.Msg2[0]))//2 ),
    #         #                              self.insMsgWnd2.P_height//2, self.Msg2)

    #         # self.drawMenu()
