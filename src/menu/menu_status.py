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
    def __init__(self, parent: Menu):
        # 情報表示ウインドウのサイズ
        param_w, param_h = 128, 136  # ステータス
        equip_w, equip_h = 128, 88  # 装備
        skill_w, skill_h = 104, 144  # 習得スキル
        padding = 2
        pos_x = parent.x + Window._chip_size
        pos_y = parent.y + Window._chip_size

        self.windows: dict[MENU_WINDOW_TYPE, Window] = {}
        self.windows["sub"] = Window("basic", pos_x, pos_y, param_w, param_h, "once")
        self.windows["sub2"] = Window(
            "basic",
            pos_x,
            pos_y + param_h + padding,
            equip_w,
            equip_h,
            "once",
        )
        self.windows["sub3"] = Window(
            "basic",
            pos_x + param_w + padding,
            pos_y,
            skill_w,
            skill_h,
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

        # メインステータス
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
        self.windows["sub"].text_list = [status_lines]

        # 装備項目の構築
        slots = [
            (EquipSlot.WEAPON, "武　器"),
            (EquipSlot.GUARDER, "防　具"),
            (EquipSlot.ACCESSORY_1, "装飾１"),
            (EquipSlot.ACCESSORY_2, "装飾２"),
            (EquipSlot.CONSUME_1, "消費１"),
            (EquipSlot.CONSUME_2, "消費２"),
        ]
        equip_lines = ""
        for slot, label in slots:
            pooled_item = member.equipments.get_slot(slot)
            if pooled_item is None:
                skill_name = "なし"
            else:
                _, plent = pooled_item
                skill_name = plent.ins.param.name
            equip_lines += f"　{label}： {skill_name}\n"
        self.windows["sub2"].text_list = [equip_lines]

        # スキル項目の構築
        skill_lines = ""
        for id in member.skills.get_learned_skills():
            skill = di.ref.sklmgr.get_def(id)
            if skill is None:
                skill_name = "なし"
            else:
                skill_name = skill.name
            skill_lines += f"　{skill_name}\n"
        self.windows["sub3"].text_list = [skill_lines]

    def update(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.inputkey.decide() or self.inputkey.cancel():
            return WindowAction.DISCARD
        if self.inputkey.left():
            self.member_index = (self.member_index - 1) % di.ref.pt.get_member_count()
            self.build_status()
        if self.inputkey.right():
            self.member_index = (self.member_index + 1) % di.ref.pt.get_member_count()
            self.build_status()
        return WindowAction.CONTINUE
