"""
アクションコマンドモジュール
CommandProtocol
└CommandBaseSequence
 └CommandBaseEntity
  └CommandBaseActionを継承する、EntityContextが行動する処理

"""

import logging
from typing import Generator
from const import SoundID
from gameutils.lib import Menu, Window, WindowAction

from skill import SkillDef
from item import StackPool, ItemDef
import service_locater as di
from . import SeqSubCmd, CommandBaseAction


# ロギング設定
logger = logging.getLogger(__name__)


class learn_skill(CommandBaseAction):
    """スキルを取得"""

    def _sequence_action(self) -> Generator[list, None, None]:
        # コマンドパッケージから取得するスキル情報
        item_def: ItemDef = self.kwargs["sel_cmd_dict"]["item_def"]

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", "習得スキルを選択してください"]

        # 習得対象スキルリストの生成
        self.skill_list = []
        self.menu_shape = [0, 0]
        self.generate_item_list(int(item_def.effect_value))

        # スキル選択メニュー
        pos_x, pos_y = 128, 16
        menu_width = 104
        menu_select_learn_skill = Menu("basic", pos_x, pos_y, self.menu_shape, self.skill_list, menu_width)
        # スキル詳細ウインドウ
        info_height = 8 + (16 * 3) + 8  # 上枠＋フォント分16px + 下枠
        info_pos = (
            menu_select_learn_skill.x,
            menu_select_learn_skill.y + menu_select_learn_skill.height + 1,
        )
        info_size = (menu_select_learn_skill.width, info_height)
        wnd_skill_info = Window("basic", *info_pos, *info_size, "sub")

        # キー待ち時の入力を一回捨てる
        yield [SeqSubCmd.WAIT, 0]

        # スタックに追加せずメニュー動作
        rc = menu_select_learn_skill.update()
        while rc == WindowAction.CONTINUE:
            self.change_target_item(menu_select_learn_skill, wnd_skill_info)
            self.display_info.graphic_command = [
                lambda menu=menu_select_learn_skill: menu.draw(),
                lambda window=wnd_skill_info: window.draw(),
                lambda window=wnd_skill_info: window.draw_message(),
            ]
            yield [SeqSubCmd.WAIT, 0]
            rc = menu_select_learn_skill.update()

        if rc == WindowAction.EXECUTE:
            self.display_info.graphic_command = None
            yield [SeqSubCmd.SE_SUSTAIN, SoundID.USEITEM]
            pos_x, pos_y = menu_select_learn_skill.cursor_position
            selected_item = menu_select_learn_skill.menu_items[pos_y][pos_x]
            self.ctx.target.skills.learn_skill(selected_item.action_args[1])
            yield [f"{self.ctx.target.param.name}は　スキルを習得した"]
            # アイテム消費（キャンセルの場合を考慮）
            pl_stack: StackPool = self.kwargs["sel_cmd_dict"]["source"]
            pl_stack.remove(item_def.def_id)

        # キー待ち
        yield from self.wait_finish()

    def generate_item_list(self, rank: int):
        """メニュー項目リストの生成：スキル"""
        target = self.ctx.target
        tmplist = di.ref.sklrps.get_def_by_rank(rank)

        self.item_count = len(tmplist)
        if self.item_count <= 0:
            self.skill_list = [[{"id": "該当なし", "action": "None", "args": ["習得可能なスキルがない"]}]]
        else:
            tmp_item_list = [
                [
                    {
                        "id": skill_def.name,
                        "action": "None",
                        "args": [skill_def, skill_id],
                    }
                ]
                for skill_id, skill_def in tmplist.items()
                # ターゲットの習得済スキルは一覧に出さない
                if skill_id not in target.skills.get_learned_skill_id()
            ]
            if len(tmp_item_list) <= 0:
                self.skill_list = [[{"id": "該当なし", "action": "None", "args": ["習得可能なスキルがない"]}]]
            else:
                self.skill_list = tmp_item_list.copy()

        self.menu_shape = [min(len(tmplist), 1), len(self.skill_list)]

    def set_description_string(self, menu: Menu, window: Window):
        """詳細ウインドウに表示する文字列を設定"""
        item_desc = self.get_item_desc()
        text_area_width = window.width - (Window._chip_size * 2)
        message_list = []
        i = start_row = 0

        for desc_string in item_desc:
            for i in range(0, len(desc_string) + 1):
                if (
                    window.fontdata.font.text_width(  # type: ignore
                        desc_string[start_row : i + 1]
                    )
                    > text_area_width
                ):
                    message_list.append(desc_string[start_row:i])
                    start_row = i
            # 最後の残りを結合
            message_list.append(desc_string[start_row:i])
        window.set_message(message_list)

    def get_item_desc(self) -> list[str]:
        skill_def = self.target_item[0]["args"][0]
        if isinstance(skill_def, SkillDef):
            desc = skill_def.description  # type: ignore
        else:
            desc = "習得していない"
        return [desc]

    def change_target_item(self, menu: Menu, window: Window):
        """選択アイテムを示す内部情報の変更"""

        self.target_item = self.skill_list[menu.cursor_position[1]]
        self.set_description_string(menu, window)
