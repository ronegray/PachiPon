"""
メニューモジュール：コンフィグ（タイトル）
"""

import logging
from typing import Callable
import pyxel as px
import service_locater as di

# from const import SoundID
from config import CONF_VOLUME, CONF_DISP_SIZE, CONF_TEXT_SPEED
from gameutils.base import BGM_CHANNELS, SE_INSTANT_CH, SE_SUSTAIN_CH  # , get_keymap
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
    # def __init__(self):
    #     self.key_names = {getattr(px, name): name.replace("KEY_", "").replace("GAMEPAD1_", "")
    #                       for name in dir(px)
    #                       if name.startswith("KEY_") or name.startswith("GAMEPAD1_")
    #     }

    #     item_list = self.build_keyassign_matrix()
    #     super().__init__(px.width//2 -96 ,8, [3,7], item_list, 7, 5)
    #     # self.prefix     = "なまえ　：　"
    #     # self.InputName  = ""
    #     self.insMsgWnd  = Window(px.width//2 - (P_CHIP_SIZE*17)//2, px.height//1.5, P_CHIP_SIZE*17, P_CHIP_SIZE*5, 0)
    #     # self.txtMsg     = Message(self.insMsgWnd.P_x+P_CHIP_SIZE, self.insMsgWnd.P_y+P_CHIP_SIZE*2, [self.prefix + self.InputName])
    #     self.txtMsg     = Message(self.insMsgWnd.P_x+P_CHIP_SIZE, self.insMsgWnd.P_y+P_CHIP_SIZE*2, ["わりあてるキーをおしてください"])

    #     self.flgMsgWnd2 = False
    #     self.Parent = Parent
    #     self.posCursor = [1,1]

    # @classmethod
    # def build_keyassign_matrix(cls) -> list:
    #     item_list = [["アクション","ゲームパッド","キーボード"]]
    #     self.keymap_pad = {action_name: self.key_names.get(keymaps["code"],
    #                                                    f"Unknown({keymaps["code"]})")
    #                    for action_name, keymaps in get_keymap("pad").items()}
    #     self.keymap_kbd = {action_name: self.key_names.get(keymaps["code"],
    #                                                    f"Unknown({keymaps["code"]})")
    #                    for action_name, keymaps in get_keymap("kbd").items()}
    #     for action_key, action_name_id in ASSIGNABLE_ACTIONS_INDEX.items():
    #         item_list += [[ASSIGNABLE_ACTIONS[action_name_id],
    #                    self.keymap_pad[action_key], self.keymap_kbd[action_key]]]
    #         print(item_list)

    #     return item_list

    # def update(self):
    #     if self.flgMsgWnd:
    #         if self.posCursor[0] % self.wndSize[0] == 1:
    #             target = "pad"
    #         elif self.posCursor[0] % self.wndSize[0] == 2:
    #             target = "kbd"
    #         response = inp.listener(target)
    #         if response:
    #             action_name = list(ASSIGNABLE_ACTIONS_INDEX.keys())[(self.posCursor[1]-1) % self.wndSize[1]]
    #             inp.keybind(action_name, *response, target)
    #             self.items = self.build_keyassign_matrix()
    #             self.flgMsgWnd = False
    #         return True

    #     if inp.is_pressed("decide"):
    #         px.play(3,SNDEFX["pi"], resume=True)
    #         if self.flgMsgWnd is False:
    #             self.flgMsgWnd = True
    #             return True

    #     if inp.is_pressed("cancel"):
    #         px.play(3,SNDEFX["pi"], resume=True)
    #         self.flgMsgWnd = False
    #         return False
    #         self.Parent.now_scene = SCENE_STATUS["Title"]

    #     self.moveCursor()
    #     return True

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
