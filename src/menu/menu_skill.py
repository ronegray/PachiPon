"""
メニューモジュール：スキル使用

- 使用するスキルを選択
- 使用スキルのターゲットを選択
"""

import logging
from typing import Callable
import service_locater as di
from gameutils.lib import Menu, Window, ExecResult, RsltContinue, RsltPush

# from item import ItemState, ItemType
# from entity import EquipSlot
from skill import SkillID, SkillDef
import command.entity_command as e_cmd


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectSkill(Menu):
    """アイテム用メニュー基本クラス"""

    _list_rows: int = 10
    pagelabel_size = 4 * 5  # 4ptフォント5文字

    def __init__(self, ctx_builder: Callable):
        """使用するスキルを選択データ取得と表示ウインドウの再定義"""
        self.buid_context = ctx_builder
        namewindow_height = Window._chip_size + 16
        # padding = 2
        menu_pos = (80, Window._chip_size + namewindow_height)
        skill_w, skill_h = 104, 144  # 習得スキル
        self.skill_list: list = []
        self.member_index: int = di.ref.pt.get_top_index()
        self.generate_item_list()
        super().__init__(
            "basic",
            *menu_pos,
            [1, len(self.skill_list)],
            self.skill_list,
            # px.width - x - Window._chip_size,
            skill_w,
            skill_h,
        )
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応
        self.windows["sub"] = Window(
            "basic",
            menu_pos[0],
            menu_pos[1] + self.height + 1,
            self.width,
            64,
            "sub",
        )
        self.windows["sub2"] = Window(
            "basic",
            menu_pos[0],
            menu_pos[1] - namewindow_height,
            self.width,
            namewindow_height,
            "sub",
        )
        self.is_push_left: int = 0
        self.is_push_right: int = 0
        self.change_target_item()
        self.set_actor_name()

    def change_target_item(self):
        """選択アイテムを示す内部情報の変更"""
        self.target_item = self.skill_list[self.cursor_position[1]]
        self.set_description_string()

    def remap_itemlist(self):
        self.build_menu_items(self.skill_list)
        self.menu_shape[1] = len(self.menu_items)
        self.cursor_position = [0, 0]

    def set_actor_name(self):
        member = di.ref.pt.get_member(self.member_index)
        self.windows["sub2"].set_message([member.param.name])

    def set_description_string(self):
        """詳細ウインドウに表示する文字列を設定"""
        item_desc = self.get_item_desc()
        text_area_width = self.windows["sub"].width - (Window._chip_size * 2)
        message_list = []
        i = start_row = 0
        # for i in range(0, len(item_desc) + 1):
        #     if (
        #         self.windows["sub"].fontdata.font.text_width(
        #             item_desc[start_row : i + 1]
        #         )
        #         > text_area_width
        #     ):
        #         message_list.append(item_desc[start_row:i])
        #         start_row = i
        for desc_string in item_desc:
            for i in range(0, len(desc_string) + 1):
                if (
                    self.windows["sub"].fontdata.font.text_width(  # type: ignore
                        desc_string[start_row : i + 1]
                    )
                    > text_area_width
                ):
                    message_list.append(desc_string[start_row:i])
                    start_row = i
            # 最後の残りを結合
            message_list.append(desc_string[start_row:i])
        self.windows["sub"].set_message(message_list)

    def individual_update(self) -> None:
        """クラス固有の更新処理"""

        # 左右キーでのリスト内容切替
        # if len(self.skill_list) > 1:
        #     if self.inputkey.left():
        #         self.member_index = (self.member_index - 1) % len(self.skill_list)
        #         self.remap_itemlist()
        #         self.change_target_item()
        #         self.is_push_left = 1
        #         return
        #     if self.inputkey.right():
        #         self.member_index = (self.member_index + 1) % len(self.skill_list)
        #         self.remap_itemlist()
        #         self.change_target_item()
        #         self.is_push_right = 1
        def update_list():
            self.generate_item_list()
            self.build_menu_items(self.skill_list)
            self.remap_itemlist()
            self.change_target_item()
            self.set_actor_name()
            # self.build_status()

        if self.inputkey.left():
            self.member_index = (self.member_index - 1) % di.ref.pt.get_member_count()
            update_list()
        if self.inputkey.right():
            self.member_index = (self.member_index + 1) % di.ref.pt.get_member_count()
            update_list()

    def move_cursor(self) -> bool:
        """カーソル移動時に詳細ウインドウの内容を書き換える"""
        result = super().move_cursor()
        if result:
            self.change_target_item()
        return result

    # def draw_main(self) -> None:
    #     """ページ表示の追加"""
    #     super().draw_main()
    #     x = self.x + self.width - (self.pagelabel_size + Window._chip_size)
    #     y = self.y
    #     px.rect(
    #         x,
    #         y,
    #         self.pagelabel_size,
    #         Window._chip_size,
    #         self.windows["main"]._image_chips.pget(7, 7),
    #     )
    #     px.text(
    #         x, y, f"{self.member_index+1:02}/{len(self.skill_list):02}", px.COLOR_WHITE
    #     )

    def generate_item_list(self):
        """スキルリストの生成"""
        member = di.ref.pt.get_member(self.member_index)
        tmplist = member.skills.get_learned_skills()

        self.inventory_count = len(tmplist)
        if self.inventory_count <= 0:
            self.skill_list = [[{"id": "該当なし", "action": "None", "args": [""]}]]
        else:
            # tmp_item_list = [
            #     [
            #         {
            #             "id": f"{di.ref.sklmgr.get_def(key).name} {di.ref.sklmgr.get_def(key).cost}",
            #             "action": "use_skill",
            #             "args": [key],
            #         }
            #     ]
            #     for key in tmplist
            # ]
            tmp_item_list = []
            for id in tmplist:
                skill_def = di.ref.sklmgr.get_def(id)
                if skill_def is None or skill_def.target_type & 0b0010 != 0b0010:
                    continue
                tmp_item_list.append(
                    [
                        {
                            "id": f"{skill_def.name} [{skill_def.cost}]",
                            "action": "select_target",
                            "args": [skill_def.def_id],
                        }
                    ]
                )
            if len(tmp_item_list) <= 0:
                self.skill_list = [[{"id": "該当なし", "action": "None", "args": [""]}]]
            else:
                # self.skill_list = [
                #     tmp_item_list[i : i + self._list_rows]
                #     for i in range(0, self.inventory_count, self._list_rows)
                # ]
                self.skill_list = tmp_item_list[0:]

        # # ページインデックスが範囲外にならないよう補正
        # if self.member_index >= len(self.skill_list):
        #     self.member_index = len(self.skill_list) - 1
        self.menu_shape = [1, len(self.skill_list)]

    def get_item_desc(self) -> list[str]:
        item_def = di.ref.sklmgr.get_def(self.target_item[0]["args"][0])
        return [""] if item_def is None else [item_def.description]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        selected_item = self.menu_items[pos_y][pos_x]
        logger.info(selected_item)

        if selected_item.menu_action is None:
            return RsltContinue()

        logger.info(
            f"選択メニュー実行：{self.menu_items[self.cursor_position[1]][0].item_label}"
        )
        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def select_target(self, skill_id: SkillID) -> ExecResult:
        """使用するスキルIDを引き渡してターゲット選択メニューを呼び出し"""
        # item_name = di.ref.sklmgr.get_def(skill_id).name
        # print(f"{skill_id} {item_name}")
        # self.windows["sub"].add_message(f"{item_name} をつかった")

        skill_def = di.ref.sklmgr.get_def(skill_id)

        return RsltPush(
            MenuSelectSkillTarget, self.buid_context, self.member_index, skill_def
        )


class MenuSelectSkillTarget(Menu):
    """スキル使用対象を選択し、スキルコマンドを発行"""

    def __init__(self, ctx_builder: Callable, actor_id: int, skill_def: SkillDef):
        # actor = di.ref.pt.get_member(actor_id)
        self._ctx = ctx_builder(actor_id=actor_id)
        self.skill_def = skill_def
        menu_pos = (160, 160)
        menu_shape = [1, di.ref.pt.get_member_count()]
        menu_items = [
            [
                {
                    "id": f"{member.param.name}",
                    "action": "use_skill",
                    "args": [[member]],
                }
            ]
            for member in di.ref.pt.get_allmember()
        ]
        if skill_def.target_type & 0b0001 == 0b0001:
            self.target = di.ref.pt.get_allmember()
            self.use_skill(self.target)
        else:
            self.target: list = []
        super().__init__("basic", *menu_pos, menu_shape, menu_items)
        self.cursor_row_offset += 2

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

        # return WindowAction.DISCARD
        # return RsltContinue()
        return result

    def use_skill(self, member: list) -> None:
        """スキルコマンドを発行し、コマンドマネージャに登録"""
        # コンテキスト内容確定
        # if len(self.target) <= 0:
        #     # self.target = [self.menu_items[self.cursor_position[1]]]
        #     self.target =
        self._ctx.allies = member
        # コマンド判定
        cmd = getattr(e_cmd, self.skill_def.effect_func)
        if cmd is None:
            errmsg = f"コマンド関数が定義されていません：{self.skill_def.effect_func}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        cast_skill = cmd(self._ctx, self.skill_def)
        di.ref.cmdmgr.push_command(cast_skill)
