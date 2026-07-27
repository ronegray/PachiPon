"""menu_status.py
メニューモジュール：ステータス
"""

import logging
import pyxel as px
import service_locater as di
from const import SoundID
from helper import upper_int_format, format_leftright
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
    def __init__(self, parent: Menu) -> None:
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
        param = member.param

        # メインステータス
        # status_lines = f"{param.name}"
        # status_lines += f"\nレベル： {param.level:2}"
        # status_lines += f"\n次まで： {member.next_exp:5}"
        # status_lines += f"\nＨ　Ｐ： {param.hp:3}／{param.max_hp:3}"
        # status_lines += f"\nＭ　Ｐ： {param.mp:3}／{param.max_mp:3}"
        # status_lines += f"\n筋　力： {member.strength:3}(+{member.bonus_str})"
        # status_lines += f"\n魔　力： {member.arcane:3}(+{member.bonus_arc})"
        # status_lines += f"\n耐　久： {member.endurance:3}(+{member.bonus_end})"
        # status_lines += f"\n速　度： {member.speed:3}(+{member.bonus_spd})"
        # status_lines += f"\n幸　運： {member.luck:3}(+{member.bonus_lck})"
        status_lines = f"{param.name}"
        status_lines += f"\nレベル： {upper_int_format(param.level, 2)}"
        status_lines += f"\n次まで： {upper_int_format(member.next_exp, 1)}"
        status_lines += f"\nＨ　Ｐ： {upper_int_format(param.hp, 3)}／{upper_int_format(param.max_hp, 3)}"
        status_lines += f"\nＭ　Ｐ： {upper_int_format(param.mp, 3)}／{upper_int_format(param.max_mp, 3)}"
        status_lines += (
            # f"\n筋　力： {upper_int_format(member.strength,2)} （＋{upper_int_format(member.bonus_str,1)}）"
            f"\n筋　力： {format_leftright(
                upper_int_format(member.strength,2),
                f"（＋{upper_int_format(member.bonus_str,1)}）",
                18)}"
        )
        # status_lines += f"\n魔　力： {upper_int_format(member.arcane,2)} （＋{upper_int_format(member.bonus_arc,1)}）"
        # status_lines += (
        #     f"\n耐　久： {upper_int_format(member.endurance,2)} （＋{upper_int_format(member.bonus_end,1)}）"
        # )
        # status_lines += f"\n速　度： {upper_int_format(member.speed,2)} （＋{upper_int_format(member.bonus_spd,1)}）"
        # status_lines += f"\n幸　運： {upper_int_format(member.luck,2)} （＋{upper_int_format(member.bonus_lck,1)}）"
        status_lines += f"\n魔　力： {format_leftright(
                upper_int_format(member.arcane,2),
                f"（＋{upper_int_format(member.bonus_str,1)}）",
                18)}"
        status_lines += f"\n耐　久： {format_leftright(
                upper_int_format(member.endurance,2),
                f"（＋{upper_int_format(member.bonus_end,1)}）",
                18)}"
        status_lines += f"\n速　度： {format_leftright(
                upper_int_format(member.speed,2),
                f"（＋{upper_int_format(member.bonus_spd,1)}）",
                18)}"
        status_lines += f"\n幸　運： {format_leftright(
                upper_int_format(member.luck,2),
                f"（＋{upper_int_format(member.bonus_lck,1)}）",
                18)}"

        self.windows["sub"].message_list = [status_lines]

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
        self.windows["sub2"].message_list = [equip_lines]

        # スキル項目の構築
        skill_lines = ""
        # for id in member.skills.get_learned_skill_id():
        #     skill = di.ref.sklmgr.get_def(id)
        #     if skill is None:
        #         skill_name = "なし"
        #     else:
        #         skill_name = skill.name
        #     skill_lines += f"　{skill_name}\n"
        for skill_def in member.skills.get_learned_skill_def("system"):
            skill_lines += f"　{skill_def.name}\n"

        self.windows["sub3"].message_list = [skill_lines]

    def update(self) -> WindowAction:
        """キー入力の確認と応答"""
        if self.inputkey.decide() or self.inputkey.cancel():
            return WindowAction.DISCARD
        if self.inputkey.left():
            px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
            self.member_index = (self.member_index - 1) % di.ref.pt.get_member_count()
            self.build_status()
        if self.inputkey.right():
            px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
            self.member_index = (self.member_index + 1) % di.ref.pt.get_member_count()
            self.build_status()
        return WindowAction.CONTINUE
