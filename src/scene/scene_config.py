"""
シーンモジュール：コンフィグ

- コンフィグメニューの表示
- 現在のコンフィグ設定値の表示
  - 呼び出しメニューに応じたコマンドの生成
"""

import logging
from dataclasses import asdict
import pyxel as px
from assets.asset_map import AssetID, AssetMap
from gameutils.base import get_keymap, check_file, write_json
from gameutils.lib import Window, WindowAction

# from helper import upper_str
import service_locater as di
from menu import MenuSelectConfigTarget
from config import CONF_VOLUME, CONF_DISP_SIZE, CONF_TEXT_SPEED, ASSIGNABLE_KEY_ACTIONS
from . import BaseScene


# ロギング設定
logger = logging.getLogger(__name__)


class SceneConfig(BaseScene):
    """コンフィグ設定シーン"""

    def __init__(self):
        super().__init__()
        self.situation = "system"
        # 設定情報表示ウインドウ
        info_x, info_y = 0, 0
        info_w, info_h = px.width, px.height
        self.window_config_info = Window(
            "basic", info_x, info_y, info_w, info_h, "hold"
        )
        self.config_info: list[str] = []
        self.keybind: list[list[str]] = []

        # 画面タイトルウインドウ
        title_x, title_y = 0, 0
        title_w, title_h = px.width, 24
        self.window_titlebar = Window(
            "large", title_x, title_y, title_w, title_h, "hold"
        )
        self.window_titlebar.set_message(["　　　　　システムコンフィグ"])

        # pyxel標準キー定義名
        self.key_names = {
            getattr(px, name): name.replace("KEY_", "")
            .replace("GAMEPAD1_", "")
            .replace("BUTTON_", "")
            for name in dir(px)
            if name.startswith("KEY_") or name.startswith("GAMEPAD1_")
        }
        # コンフィグ情報テキスト生成
        self.build_config_info()

        # コンフィグ項目選択メニュー
        self.wndmgr.push_stack(
            MenuSelectConfigTarget,
            self.window_titlebar.y + title_h,
            self.build_config_info,
        )

        """前シーンのBGMを引き継ぐ為設定不要"""

    def update(self) -> None:
        if (
            self.wndmgr.update() in (WindowAction.DISCARD, WindowAction.CLOSE)
            and self.wndmgr.has_stack is False
        ):
            di.ref.scnmgr.previous_scene(False)

    def build_config_info(self) -> list:
        """描画用のコンフィグ現在設定情報文字列を生成"""
        self.config_info.clear()
        self.keybind.clear()

        # 設定
        self.config_info.append(
            f"ＢＧＭ音量　：{CONF_VOLUME[di.ref.conf.vol_bgm]["label"]}"
        )
        self.config_info.append(
            f"効果音音量　：{CONF_VOLUME[di.ref.conf.vol_se]["label"]}"
        )
        self.config_info.append(
            f"画面サイズ　：{CONF_DISP_SIZE[di.ref.conf.display_size]["label"]}"
        )
        fulsc = "する" if di.ref.conf.is_fullscreen else "しない"
        self.config_info.append(f"全画面表示　：{fulsc}")
        self.config_info.append(
            f"文字送り待ち：{CONF_TEXT_SPEED[di.ref.conf.text_speed]["label"]}"
        )
        curpos = "記憶" if di.ref.conf.is_memory_cursor else "初期化"
        self.config_info.append(f"カーソル位置：{curpos}")
        cutin_dice = "表示する" if di.ref.conf.is_cutin_dice else "非表示"
        self.config_info.append(f"ダイス演出　：{cutin_dice}")
        self.config_info.append("キー割り当て：")
        # # キーアサイン
        # self.keybind = [
        #     # ["キー割り当て：", " ", " "],
        #     ["アクション", "パッド", "キー"],
        # ]
        # # keymap_pad = {
        # #     action_name: self.key_names.get(
        # #         keymaps["code"], f"Unknown({keymaps["code"]})"
        # #     )
        # #     for action_name, keymaps in get_keymap("pad").items()
        # # }
        # # logger.debug(get_keymap("pad"))
        # # keymap_kbd = {
        # #     action_name: self.key_names.get(
        # #         keymaps["code"], f"Unknown({keymaps["code"]})"
        # #     )
        # #     for action_name, keymaps in get_keymap("kbd").items()
        # # }
        # # logger.debug(get_keymap("kbd"))

        # keymap_pad = {
        #     action_name: self.key_names.get(
        #         keymaps[0]["code"], f"Unknown({keymaps[0]["code"]})"
        #     )
        #     for action_name, keymaps in get_keymap("pad").items()
        #     if action_name in ASSIGNABLE_KEY_ACTIONS
        # }
        # keymap_kbd = {
        #     action_name: self.key_names.get(
        #         keymaps[0]["code"], f"Unknown({keymaps[0]["code"]})"
        #     )
        #     for action_name, keymaps in get_keymap("kbd").items()
        #     if action_name in ASSIGNABLE_KEY_ACTIONS
        # }
        # for action_key, action_name in ASSIGNABLE_KEY_ACTIONS.items():
        #     self.keybind += [
        #         [
        #             action_name,
        #             upper_str(keymap_pad[action_key]),
        #             upper_str(keymap_kbd[action_key]),
        #         ]
        #     ]
        keyassign = self.build_keyassign_matrix()

        # 情報作成時＝データ内容変更時と捉えて、データ内容をファイルに出力
        path = check_file(AssetMap.get_assetpath(AssetID.SYSCONFIG), "w")
        if path is None:
            raise SystemError("コンフィグファイルが出力出来ません")
        write_json(path, asdict(di.ref.conf))

        return keyassign

    def build_keyassign_matrix(self) -> list:
        # キーアサイン
        self.keybind = [
            ["アクション", "パッド", "キー"],
        ]
        keymap_pad = {
            action_name: self.key_names.get(
                keymaps[0]["code"], f"Unknown({keymaps[0]["code"]})"
            )
            for action_name, keymaps in get_keymap("pad").items()
            if action_name in ASSIGNABLE_KEY_ACTIONS
        }
        keymap_kbd = {
            action_name: self.key_names.get(
                keymaps[0]["code"], f"Unknown({keymaps[0]["code"]})"
            )
            for action_name, keymaps in get_keymap("kbd").items()
            if action_name in ASSIGNABLE_KEY_ACTIONS
        }
        for action_key, action_name in ASSIGNABLE_KEY_ACTIONS.items():
            self.keybind += [
                [
                    action_name,
                    # upper_str(keymap_pad[action_key]),
                    # upper_str(keymap_kbd[action_key]),
                    (keymap_pad[action_key]),
                    (keymap_kbd[action_key]),
                ]
            ]
        return self.keybind

    def draw_config_info(self) -> None:
        """事前に生成したコンフィグ現在設定情報を描画"""
        x = 104
        y = self.window_titlebar.y + self.window_titlebar.height + Window._chip_size - 1
        for txt in self.config_info:
            px.text(x, y, txt, px.COLOR_WHITE, self.window_config_info.font)
            y += 13
        # y += 32
        x = 104
        for name, pad, kbd in self.keybind:
            px.text(x, y, name, px.COLOR_WHITE, self.window_config_info.font)
            px.text(x + 92, y, pad, px.COLOR_WHITE, self.window_config_info.font)
            px.text(x + 124, y, kbd, px.COLOR_WHITE, self.window_config_info.font)
            y += px.ceil(self.window_config_info.fontdata.height * 1.25)

    def draw(self) -> None:
        self.window_config_info.draw()
        self.draw_config_info()
        self.window_titlebar.draw()
        self.window_titlebar.draw_message()
        self.wndmgr.draw()
