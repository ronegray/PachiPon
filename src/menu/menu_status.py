"""menu_status.py
メニューモジュール：ステータス
"""
import logging
import service_locater as di
from gameutils.lib import (
    Menu,
    Window,
    MENU_WINDOW_TYPE,
    WindowAction,
    WindowInputHandler,
)
from entity import EquipSlot


# ロギング設定
logger = logging.getLogger(__name__)


class MenuStatus(Menu):
    def __init__(self):
        # パラメータ、装備品のウインドウサイズ
        param_w, param_h = 128, 136
        equip_w, equip_h = 128, 88
        # 現在のシーンのWindowManagerを取得
        wndmgr = di.ref.scnmgr.get_now_scene().wndmgr
        parent = wndmgr.get_stack(1)
        padding = 2
        pos_x = parent.x + parent.width + padding
        pos_y = padding

        self.windows: dict[MENU_WINDOW_TYPE, Window] = {}
        self.windows["sub"] = Window("basic", pos_x, pos_y, param_w, param_h, "once")
        self.windows["sub2"] = Window(
            "basic",
            self.windows["sub"].x,
            self.windows["sub"].y + self.windows["sub"].height + padding,
            equip_w,
            equip_h,
            "once",
        )
        # デフォルト表示は先頭メンバー
        self.member_index: int = di.ref.pt.get_top_index()
        self.build_status()

        self.inputkey = WindowInputHandler.get()

    def build_status(self) -> None:
        """ステータス表示内容の構築（装備含む）"""
        member = di.ref.pt.get_member(self.member_index)
        param = member.base_param

        # 装備項目の構築
        slots = [
            (EquipSlot.WEAPON, "武　器"),
            (EquipSlot.GUARDER, "防　具"),
            (EquipSlot.ACCESSORY_1, "装飾１"),
            (EquipSlot.ACCESSORY_2, "装飾２"),
            (EquipSlot.CONSUME_1, "消費１"),
            (EquipSlot.CONSUME_2, "消費２"),
        ]

        status_lines = f"{param.name}"
        status_lines += f"\nレベル： {param.level:2}"
        status_lines += f"\n経験値： {param.exp:5}"
        status_lines += f"\nＨ　Ｐ： {param.hp:3}／{param.max_hp:3}"
        status_lines += f"\nＭ　Ｐ： {param.mp:3}／{param.max_mp:3}"
        status_lines += f"\n筋　力： {member.strength:3}(+{member.bonus_str})"
        status_lines += f"\n魔　力： {member.arcane:3}(+{member.bonus_arc})"
        status_lines += f"\n耐　久： {member.endurance:3}(+{member.bonus_end})"
        status_lines += f"\n速　度： {member.speed:3}(+{member.bonus_spd})"
        status_lines += f"\n幸　運： {member.luck:3}(+{member.bonus_lck})"
        equip_lines = ""
        for slot, label in slots:
            pooled_item = member.equipments.get_slot(slot)
            if pooled_item is None:
                item_name = "なし"
            else:
                _, plent = pooled_item
                item_name = plent.ins.param.name
            equip_lines += f"　{label}： {item_name}\n"

        self.windows["sub"].text_list = [status_lines]
        self.windows["sub2"].text_list = [equip_lines]

    def update(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.inputkey.decide() or self.inputkey.cancel():
            return WindowAction.DISCARD
        if self.inputkey.left():
            self.member_index = (self.member_index - 1) % di.ref.pt.get_members()
            self.build_status()
        if self.inputkey.right():
            self.member_index = (self.member_index + 1) % di.ref.pt.get_members()
            self.build_status()
        return WindowAction.CONTINUE
