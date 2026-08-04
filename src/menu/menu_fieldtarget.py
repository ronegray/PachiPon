import logging
import pyxel as px
from gameutils.lib import Menu, MENU_ITEM_LIST, ExecResult, RsltDiscard, RsltContinue
from entity import EntityContext, EntityBase
from skill import SkillTargetType


# ロギング設定
logger = logging.getLogger(__name__)


class MenuSelectFieldTarget(Menu):
    def __init__(self, ctx: EntityContext, target_type: SkillTargetType):
        self.ctx: EntityContext = ctx
        self.target_type: SkillTargetType = target_type
        self.item_list: MENU_ITEM_LIST = []
        self.generate_item_list()

        menu_pos = (px.width // 2, px.height // 2)
        super().__init__("basic", *menu_pos, self.menu_shape, self.item_list)
        self.cursor_row_offset += 2  # k8x12Sの縦長分対応

    def generate_item_list(self):
        """メニュー項目リストの生成：ターゲット"""
        # 対象リストの振り分け
        match self.target_type:
            case SkillTargetType.ALLY:
                target_list = self.ctx.allies
            case SkillTargetType.ALLIES:
                target_list = self.ctx.allies
            case SkillTargetType.SELF:  # 単体対象オブジェクトはリスト化が必要
                target_list = [self.ctx.actor]
            case SkillTargetType.ALL:
                target_list = self.ctx.targets + self.ctx.allies
            case _:
                target_list = self.ctx.targets

        menu_cols = 1
        enemy_count = len(target_list)
        if enemy_count <= 0:
            errmsg = "ターゲット対象リストが空の状態です"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        else:
            # tmp_item_list = [
            self.item_list = [
                [
                    {
                        "id": f"{target.param.name.ljust(9, '　')}",
                        "action": "set_target",
                        "args": [target],
                    }
                ]
                for target in target_list
                if target.is_alive
            ]

            # tmp_list = []
            # cnt = 0
            # for i, tmp_item in enumerate(tmp_item_list):
            #     if i % menu_cols == 0:
            #         tmp_list = [].copy()
            #     tmp_list.append(tmp_item[0])
            #     if len(tmp_list) == menu_cols:
            #         self.item_list.append(tmp_list.copy())
            #         cnt += 2
            # if len(tmp_item_list) != cnt:
            #     # list[list[dict[str, str]]]
            #     self.item_list.append(tmp_list.copy())

        self.menu_shape = [menu_cols, len(self.item_list)]

    def exec_menu(self) -> ExecResult:
        """選択メニュー項目の処理を実行"""
        pos_x, pos_y = self.cursor_position
        try:
            selected_item = self.menu_items[pos_y][pos_x]
        except IndexError:
            # 空データを選択した時はスルー
            return RsltContinue()
        # logger.info(selected_item)

        if selected_item.menu_action is None:
            errmsg = f"メニューアクション関数が定義されていません：{selected_item.item_label}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)

        result = selected_item.menu_action(*selected_item.action_args)

        return result

    def set_target(self, target: EntityBase) -> ExecResult:
        """コンテキストにターゲットを設定"""
        self.ctx.target = target
        return RsltDiscard()
