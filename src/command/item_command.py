"""
アイテムコマンドモジュール
"""

import logging
from typing import Generator, cast
from dataclasses import dataclass

# import pyxel as px
from const import SoundID
from gameutils.lib import Menu, Window, WindowAction
from helper import diceroll, upper_int
from entity import EntityContext, Character  # , Enemy, Party, Character
from skill import SkillTargetType, SkillDef
from item import ItemTargetType, StackPool, ItemDef  # , ItemState  # , WeaponType
import service_locater as di
from . import CommandBaseSequence, CommandPhase
# from .effect_command import efx_diceroll, efx_physical_attack, efx_damage_shake, efx_monster_dead

# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseItem(CommandBaseSequence):
    """エンティティが実行者となるコマンドの基底クラス"""

    def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        super().__init__(wnd, *args, **kwargs)
        self._ctx: EntityContext = ctx

    def _check_actor_alive(self) -> bool:
        """行動前の行動可否チェック"""
        if self._ctx.actor.is_alive:
            return True
        else:
            self.step_wait = 0
            return False

    def _check_living_targets(self) -> list:
        """行動前の対象生存チェック"""
        # 生存しているターゲットだけをリストアップ
        living_targets = [t for t in self._ctx.targets if t.is_alive]
        # ターゲットが全て生存していない場合は終了
        if not living_targets:
            self.phase = CommandPhase.FIN
            self.step_wait = 0
            return []
        return living_targets


@dataclass
class CommandPackage:
    """Command選択結果のメニュー⇔シーン間受け渡し用パッケージ"""

    selected_action: type[CommandBaseItem] | None = None
    target_type: SkillTargetType | ItemTargetType | None = None
    selected_args: dict | None = None


class heal_hp(CommandBaseItem):
    """HP回復アイテム"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = cast(Character, self._ctx.actor)
        else:
            return

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [
            f"{actor.param.name}は　{target.param.name}に",
            f"　{item_def.name} を 使用した",
        ]

        # アイテム消費
        if self._ctx.situation == "battle":
            slot = self.args[0]["slot"]
            actor.equipments.use_consume(slot)
        else:
            pl_stack = cast(StackPool, self.args[0]["pl_stack"])
            # pl_stack.remove(item_def.def_id, ItemState.BAG, 1)
            pl_stack.remove(item_def.def_id)

        # 回復ロール
        if item_def.effect_value:
            healing = target.param.max_hp
        else:
            healing = diceroll(actor.param.level)

        if self._ctx.situation == "battle":
            yield [""]

        # run_effectに相当：メッセージ表示後にダメージ適用
        real_heal = target.increase_hp(healing)
        # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＨＰが　回復した"]


class heal_mp(CommandBaseItem):
    """MP回復アイテム"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = cast(Character, self._ctx.actor)
        else:
            return

        # 生存ターゲットチェック
        living_targets = self._check_living_targets()
        if not living_targets:
            return
        # 現在のターゲットが生存していればそれを使う、そうでなければリストの先頭を使う
        current = self._ctx.target
        target = current if current.is_alive else living_targets[0]

        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [
            f"{actor.param.name}は　{target.param.name}に",
            f"　{item_def.name} を 使用した",
        ]

        # アイテム消費
        if self._ctx.situation == "battle":
            slot = self.args[0]["slot"]
            actor.equipments.use_consume(slot)
        else:
            pl_stack = cast(StackPool, self.args[0]["pl_stack"])
            # pl_stack.remove(item_def.def_id, ItemState.BAG, 1)
            pl_stack.remove(item_def.def_id)

        # 回復ロール
        if item_def.effect_value:
            healing = target.param.max_hp
        else:
            healing = diceroll(actor.param.level)

        if self._ctx.situation == "battle":
            yield [""]

        # run_effectに相当：メッセージ表示後にダメージ適用
        real_heal = target.increase_mp(healing)
        # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        yield [f"{target.param.name}は {upper_int(real_heal)} のＭＰが　回復した"]


class torchlight(CommandBaseItem):
    """たいまつ"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", " "]

        # アイテム消費
        pl_stack = cast(StackPool, self.args[0]["pl_stack"])
        pl_stack.remove(item_def.def_id)

        # PT単位効果付与
        di.ref.pt.set_pt_efx(item_def.effect_id)
        di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
        yield [
            "パーティはダンジョン探索が可能になった",
            "ダンジョンのイベントポイントでイベント実行できます",
            f"一度実行すると{item_def.name}の効果は消失します",
        ]

        # キー待ち
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class escape_battle(CommandBaseItem):
    """戦闘離脱"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # 最初に必ず生死チェック
        if self._check_actor_alive():
            actor = cast(Character, self._ctx.actor)
        else:
            return

        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", " "]

        # アイテム消費
        if self._ctx.situation == "battle":
            slot = self.args[0]["slot"]
            actor.equipments.use_consume(slot)
        else:
            pl_stack = cast(StackPool, self.args[0]["pl_stack"])
            # pl_stack.remove(item_def.def_id, ItemState.BAG, 1)
            pl_stack.remove(item_def.def_id)

        # PT単位効果付与
        di.ref.pt.set_pt_efx(item_def.effect_id)
        di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
        if self._ctx.situation == "battle":
            yield ["ドロン！戦闘から離脱した！"]
            return
        else:
            yield [
                "パーティは次のエンカウント時に",
                f"{item_def.name}の効果で戦闘を回避します",
                f"一度エンカウントすると{item_def.name}の効果は消失します",
            ]

        # # run_effectに相当：メッセージ表示後にダメージ適用
        # real_heal = target.increase_mp(healing)
        # # px.play(self.se_ch, SoundID.RECOVER, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.RECOVER)
        # yield [f"{target.param.name}は {upper_int(real_heal)} のＭＰが　回復した"]

        # キー待ち
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class reduce_negative(CommandBaseItem):
    """マイナス選択肢でダイス振り直し"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", " "]

        # アイテム消費
        pl_stack = cast(StackPool, self.args[0]["pl_stack"])
        pl_stack.remove(item_def.def_id)

        # PT単位効果付与
        di.ref.pt.set_pt_efx(item_def.effect_id + str(item_def.effect_value))
        di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
        yield [
            "次に発生するランダムイベントの候補から",
            f"{upper_int(int(item_def.effect_value))}個のマイナス選択肢を除外します",
            f"一度実行すると{item_def.name}の効果は消失します",
        ]

        # キー待ち
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class dice_plus(CommandBaseItem):
    """ダイスロール時のダイスをプラス"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", " "]

        # アイテム消費
        pl_stack = cast(StackPool, self.args[0]["pl_stack"])
        pl_stack.remove(item_def.def_id)

        # PT単位効果付与
        di.ref.pt.set_pt_efx(item_def.effect_id + str(item_def.effect_value))
        di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
        yield [
            "次に行うダイスロール時に、一度だけ",
            f"ダイスを{upper_int(int(item_def.effect_value))}個追加します",
            f"一度実行すると{item_def.name}の効果は消失します",
        ]

        # キー待ち
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class food_plus(CommandBaseItem):
    """食糧を追加"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", " "]

        # アイテム消費
        pl_stack = cast(StackPool, self.args[0]["pl_stack"])
        pl_stack.remove(item_def.def_id)

        # PT単位効果付与
        val = int(item_def.effect_value)
        di.ref.pt.earn_foods(val)
        di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
        yield [f"食糧が{val}増えた！"]

        # キー待ち
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)


class learn_skill(CommandBaseItem):
    """スキルを取得"""

    def _sequence(self) -> Generator[list[str], None, None]:
        # コマンドパッケージから取得するスキル情報
        item_def = cast(ItemDef, self.args[0]["item_def"])

        # ファーストメッセージ
        yield [f"{item_def.name} を 使用した", "習得スキルを選択してください"]

        # 習得対象スキルリストの生成
        self.skill_list = []
        self.menu_shape = [0, 0]
        self.generate_item_list(int(item_def.effect_value))

        # スキル選択メニュー
        pos_x, pos_y = 128, 16
        menu_width = 104
        menu_select_learn_skill = Menu(
            "basic", pos_x, pos_y, self.menu_shape, self.skill_list, menu_width
        )
        # スキル詳細ウインドウ
        info_height = 8 + (16 * 3) + 8  # 上枠＋フォント分16px + 下枠
        info_pos = (
            menu_select_learn_skill.x,
            menu_select_learn_skill.y + menu_select_learn_skill.height + 1,
        )
        info_size = (menu_select_learn_skill.width, info_height)
        wnd_skill_info = Window("basic", *info_pos, *info_size, "sub")
        # self.change_target_item(menu_select_learn_skill, wnd_skill_info)

        # キー待ち時の入力を一回捨てる
        yield [self.WAIT, "0"]

        # スタックに追加せずメニュー動作
        rc = menu_select_learn_skill.update()
        while rc == WindowAction.CONTINUE:
            self.change_target_item(menu_select_learn_skill, wnd_skill_info)
            self.display_info.graphic_command = [
                lambda menu=menu_select_learn_skill: menu.draw(),
                lambda window=wnd_skill_info: window.draw(),
                lambda window=wnd_skill_info: window.draw_message(),
            ]
            yield [self.WAIT, "0"]
            rc = menu_select_learn_skill.update()

        if rc == WindowAction.EXECUTE:
            self.display_info.graphic_command = None
            di.ref.sndmgr.play_se_sustain(SoundID.USEITEM)
            pos_x, pos_y = menu_select_learn_skill.cursor_position
            selected_item = menu_select_learn_skill.menu_items[pos_y][pos_x]
            self._ctx.target.skills.learn_skill(selected_item.action_args[1])
            yield [f"{self._ctx.target.param.name}は　スキルを習得した"]
            # アイテム消費（キャンセルの場合を考慮）
            pl_stack = cast(StackPool, self.args[0]["pl_stack"])
            pl_stack.remove(item_def.def_id)

        # キー待ち
        self.display_info.target.update_indicator(True)
        while self.display_info.target.update() == WindowAction.CONTINUE:
            yield [self.WAIT, "0"]
        self.display_info.target.update_indicator(False)

    def generate_item_list(self, rank: int):
        """メニュー項目リストの生成：スキル"""
        target = self._ctx.target
        tmplist = di.ref.sklrps.get_def_by_rank(rank)

        self.item_count = len(tmplist)
        if self.item_count <= 0:
            self.skill_list = [
                [{"id": "該当なし", "action": "None", "args": ["習得可能なスキルがない"]}]
            ]
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
                self.skill_list = [
                    [{"id": "該当なし", "action": "None", "args": ["習得可能なスキルがない"]}]
                ]
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
