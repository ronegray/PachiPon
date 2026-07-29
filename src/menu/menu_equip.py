"""menu_equip.py
メニューモジュール：装備変更
- 変更する装備スロット（部位）を選択
- 選択したスロットに合致するアイテムの一覧から、装備を変更
- 変更処理は選択ユーザが保持するequipments.Equipsクラスの責務として実行
"""

import logging
import pyxel as px
from const import SoundID
import service_locater as di
from gameutils.lib import Menu, Window, ExecResult, RsltPush, RsltPop, RsltContinue
from item import ItemState, ItemType
from entity import EquipSlot
from helper import upper_int_format, format_leftright


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectEquipSlot(Menu):
    """装備スロット選択メニュー"""

    def __init__(self, parent: Menu) -> None:
        # 情報表示ウインドウのサイズ
        param_w, param_h = 128, 136  # ステータス
        equip_w, equip_h = 128, 88  # 装備
        padding = 2
        pos_x = parent.x + Window._chip_size
        pos_y = parent.y + Window._chip_size

        menu_pos = (pos_x, pos_y + param_h + padding)
        menu_shape = [1, 6]  # 武器、防具、アクセx2、消耗品x2の6スロット
        self.item_list: list = []
        self.member_index: int = di.ref.pt.get_top_index()
        self.generate_item_list()

        # メニュー本体は装備一覧がわ
        super().__init__(
            "basic", *menu_pos, menu_shape, self.item_list, equip_w, equip_h
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

        self.windows["sub"] = Window("basic", pos_x, pos_y, param_w, param_h, "once")
        self.build_status()

    def generate_item_list(self):
        """メニューアイテム生成"""
        self.item_list.clear()
        member = di.ref.pt.get_member(self.member_index)
        # 装備項目の構築
        slots = [
            (EquipSlot.WEAPON, "武　器"),
            (EquipSlot.GUARDER, "防　具"),
            (EquipSlot.ACCESSORY_1, "装飾１"),
            (EquipSlot.ACCESSORY_2, "装飾２"),
            (EquipSlot.CONSUME_1, "消費１"),
            (EquipSlot.CONSUME_2, "消費２"),
        ]
        for slot, label in slots:
            pooled_item = member.equipments.get_slot(slot)
            if pooled_item is None:
                item_name = "なし"
            else:
                _, plent = pooled_item
                item_name = plent.ins.param.name
            self.item_list.append(
                [
                    {
                        "id": f"{label}： {item_name}",
                        "action": "equip_item",
                        "args": [slot],
                    }
                ]
            )

    def build_status(self) -> None:
        """ステータス表示内容の構築（ステータスのみ）"""
        member = di.ref.pt.get_member(self.member_index)
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

        result = selected_item.menu_action(*selected_item.action_args)
        return result

    def equip_item(self, slot: EquipSlot) -> RsltPush:
        return RsltPush(MenuEquip, slot, self.member_index, self.windows["sub"])

    def individual_update(self) -> None:
        """クラス固有の更新処理"""

        def update_list():
            self.generate_item_list()
            self.build_menu_items(self.item_list)
            self.build_status()

        if self.inputkey.left():
            px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
            self.member_index = (self.member_index - 1) % di.ref.pt.get_member_count()
            update_list()
        if self.inputkey.right():
            px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
            self.member_index = (self.member_index + 1) % di.ref.pt.get_member_count()
            update_list()

    def move_cursor(self) -> bool:
        """キー入力に応じたカーソル移動とインデックス制御"""
        if self.inputkey.up():
            self.cursor_position[1] = (self.cursor_position[1] - 1) % self.menu_shape[1]
            return True
        # if self.inputkey.left():
        #     self.cursor_position[0] = (self.cursor_position[0] - 1) % self.menu_shape[0]
        #     return True
        if self.inputkey.down():
            self.cursor_position[1] = (self.cursor_position[1] + 1) % self.menu_shape[1]
            return True
        # if self.inputkey.right():
        #     self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]
        #     return True
        return False


class MenuEquip(Menu):
    """消耗品アイテム表示・選択用メニュー"""

    _list_rows: int = 10
    pagelabel_size = 4 * 5  # 4ptフォント5文字
    # 装備項目の構築
    _filter = {
        EquipSlot.WEAPON: ItemType.WEAPON,
        EquipSlot.GUARDER: ItemType.GUARDER,
        EquipSlot.ACCESSORY_1: ItemType.ORNAMENT,
        EquipSlot.ACCESSORY_2: ItemType.ORNAMENT,
        EquipSlot.CONSUME_1: ItemType.CONSUME,
        EquipSlot.CONSUME_2: ItemType.CONSUME,
    }

    def __init__(self, slot: EquipSlot, member_index: int, parent: Menu):
        """データ取得と表示ウインドウの再定義"""
        self.member = di.ref.pt.get_member(member_index)
        offset = 2
        pos_x = parent.x + parent.width + offset
        pos_y = parent.y
        w = 104
        self.item_list: list = []
        self.itemlist_index: int = 0
        self.inventory_count: int = 0
        # self.filter_cursor: int = 0
        # self.filter_name: list[str] = ["", "COMSUME", "LEGEND"]
        # self.filter_types = ConsumeGrade
        self.slot = slot
        self.slot_filter = self._filter[slot]
        if self.slot_filter == ItemType.CONSUME:
            self.func_gen_item = self.generate_item_list_consume
            self.func_equip = self.member.equipments.equip_on_consume
        else:
            self.func_gen_item = self.generate_item_list
            self.func_equip = self.member.equipments.equip_on_pool
        # # self.list_rows: int = 10
        # # self.inventory_count: int = 0
        self.func_gen_item()
        super().__init__(
            "basic",
            pos_x,
            pos_y,
            [1, len(self.item_list[self.itemlist_index])],
            self.item_list[self.itemlist_index],
            w,
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        self.windows["sub"] = Window(
            "basic",
            pos_x,
            pos_y + self.windows["main"].height + 1,
            self.windows["main"].width,
            64,
            "sub",
        )
        self.is_push_left: int = 0
        self.is_push_right: int = 0
        # # # self.target_item = self.item_list[0][0]
        self.change_target_item()
        # super().__init__()

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        # self.member.equipments.equip_off(self.slot)
        if self.inventory_count <= 0:
            return RsltContinue()
        elif self.slot_filter == ItemType.CONSUME:
            px.play(self.se_ch, SoundID.CHANGE_EQUIP, resume=True)
            self.member.equipments.equip_on_consume(
                self.slot, selected_item.action_args[0]
            )
        else:
            iid = selected_item.action_args[1]
            plent = di.ref.pl_item.get(iid)
            if plent is None:
                errmsg = f"プールからのアイテム取得に失敗しました：ID={iid}"
                logger.critical(errmsg, exc_info=True)
                raise ValueError(errmsg)
            px.play(self.se_ch, SoundID.CHANGE_EQUIP, resume=True)
            self.member.equipments.equip_on_pool(self.slot, (iid, plent))
            self.member.update_bonus()

        now_scene = di.ref.scnmgr.get_now_scene()
        i = 1
        while True:
            parent = now_scene.wndmgr.get_stack(i)
            if isinstance(parent, MenuSelectEquipSlot):
                break
            i += 1
        parent.generate_item_list()
        parent.build_menu_items(parent.item_list)
        parent.build_status()
        # parent.menu_items = parent.item_list

        # if selected_item.menu_action is None:
        #     errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
        #     logger.critical(errmsg, exc_info=True)
        #     raise ValueError(errmsg)

        # logger.info(
        #     f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        # )

        # result = selected_item.menu_action(*selected_item.action_args)
        # return result

        return RsltPop([])

    def generate_item_list(self):
        """アイテムリストの生成"""
        # tmplist = di.ref.pl_stack.get_by_state(ItemState.BAG)
        # filteredlist = self._get_filtered_list(tmplist)
        tmplist = di.ref.pl_item.get_by_state(ItemState.BAG)
        # filteredlist = [
        #     {item_[0]: item_[1]}
        #     for item_ in tmplist.items()
        #     if item_[0] & 0xFF00 != ItemType.KEY_ITEM
        # ]
        filteredlist = [
            [
                {
                    "id": items_.ins.param.name,
                    "action": "None",
                    # "args": items_.ins.param.description,
                    "args": [items_.ins.param.def_id, iid],
                }
            ]
            for iid, items_ in tmplist.items()
            # if items_.ins.param.def_id & 0xFF00 == self.slot_filter
            if items_.ins.param.item_type == self.slot_filter
        ]

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            # if self.filter_name == "":
            #     self.item_list = [[{"id": "なし", "action": "None"}]]
            # else:
            self.item_list = [[[{"id": "該当なし", "action": "None", "args": [""]}]]]
        else:
            # tmp_item_list = [[{"id":f"{di.ref.itemmgr.get_def(key).name} x {val}",
            #                    "action":"use_item", "args":[key]}]
            #                  for key,val in filteredlist.items() if val > 0]
            # self.item_list = [tmp_item_list[i:i+self.list_rows]
            #                   for i in range(0, self.inventory_count, self.list_rows)]
            self.item_list = [
                filteredlist[i : i + self._list_rows]
                for i in range(0, self.inventory_count, self._list_rows)
            ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def generate_item_list_consume(self):
        """アイテムリストの生成"""
        filteredlist = di.ref.pl_stack.get_by_state(ItemState.BAG)

        self.inventory_count = len(filteredlist)
        if self.inventory_count <= 0:
            self.item_list = [[[{"id": "該当なし", "action": "None", "args": [""]}]]]
        else:
            tmp_item_list = [
                [
                    {
                        # "id": f"{di.ref.itemrps.get_def(key).name} x {val}",  # type:ignore
                        "id": format_leftright(
                            di.ref.pl_stack.get_def(key).name,  # type: ignore
                            f"ｘ{upper_int_format(val,2)}",
                        ),
                        "action": "use_item",
                        "args": [key],
                    }
                ]
                for key, val in filteredlist.items()
                if val > 0
            ]
            self.item_list = [
                tmp_item_list[i : i + self._list_rows]
                for i in range(0, self.inventory_count, self._list_rows)
            ]

        # ページインデックスが範囲外にならないよう補正
        if self.itemlist_index >= len(self.item_list):
            self.itemlist_index = len(self.item_list) - 1
        self.menu_shape = [1, len(self.item_list[self.itemlist_index])]

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""
        self.target_item = (  # type:ignore
            self.item_list[self.itemlist_index][self.cursor_position[1]]
        )
        self.set_description_string()

    def remap_itemlist(self):
        self.build_menu_items(self.item_list[self.itemlist_index])
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0, 0]

    def get_item_desc(self) -> list[str]:
        # return self.target_item[0]["args"]
        item_def = di.ref.itemrps.get_def(self.target_item[0]["args"][0])
        if item_def is None:
            # errmsg = f"アイテム定義情報の取得に失敗しました：ID={item_def}"
            # logger.critical(errmsg, exc_info=True)
            # raise ValueError(errmsg)
            return ["何も持っていない"]
        match item_def.item_type:
            case ItemType.CONSUME:
                return [f"{item_def.description}"]
            case ItemType.WEAPON:
                expect_dmg = item_def.hitdice * 4
                # perf_txt = f"攻撃性能:{expect_dmg:>2}"
                perf_txt = f"攻撃:{upper_int_format(expect_dmg, 2)}"
            case ItemType.GUARDER:
                perf_txt = (
                    # f"防御性能:{item_def.defvalue} 魔法阻害:{item_def.magpenalty}"
                    f"防御:{upper_int_format(item_def.defvalue, 2)} 魔法阻害:{upper_int_format(item_def.magpenalty, 1)}"
                )
            case ItemType.ORNAMENT:
                perf_txt = "特殊な効果をもつ飾り"
            case _:
                perf_txt = ""
        return [f"{perf_txt}", f"{item_def.description}"]

    def set_description_string(self):
        """詳細ウインドウに表示する文字列を設定"""
        item_desc = self.get_item_desc()
        text_area_width = self.windows["sub"].width - (Window._chip_size * 2)
        message_list = []
        start_row = 0

        for desc_string in item_desc:
            for i in range(0, len(desc_string) + 1):
                if (
                    self.windows["sub"].fontdata.font.text_width(  # type:ignore
                        desc_string[start_row : i + 1]
                    )
                    > text_area_width
                ):
                    message_list.append(desc_string[start_row:i])
                    start_row = i
            # 最後の残りを結合
            message_list.append(desc_string[start_row:i])  # type:ignore
        self.windows["sub"].set_message(message_list)

    def individual_update(self):
        """クラス固有の更新処理"""
        # 左右キーでのリスト内容切替
        if len(self.item_list) > 1:
            if self.inputkey.left():
                px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
                self.itemlist_index = (self.itemlist_index - 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                self.is_push_left = 1
                return
            if self.inputkey.right():
                px.play(self.se_ch, SoundID.PAGE_ARROW, resume=True)
                self.itemlist_index = (self.itemlist_index + 1) % len(self.item_list)
                self.remap_itemlist()
                self.change_target_item()
                self.is_push_right = 1

    def move_cursor(self) -> bool:
        """カーソル移動時に詳細ウインドウの内容を書き換える"""
        result = super().move_cursor()
        if result:
            self.change_target_item()
        return result

    def draw_main(self) -> None:
        """ページ表示の追加"""
        super().draw_main()
        x = self.x + self.width - (self.pagelabel_size + Window._chip_size)
        y = self.y
        px.rect(
            x,
            y,
            self.pagelabel_size,
            Window._chip_size,
            self.windows["main"]._image_chips.pget(7, 7),
        )
        px.text(
            x,
            y,
            f"{self.itemlist_index + 1:02}/{len(self.item_list):02}",
            px.COLOR_WHITE,
        )
