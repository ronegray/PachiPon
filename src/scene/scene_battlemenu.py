"""
シーンモジュール：バトルメニュー

シーン：バトルのサブモジュールとして、
バトルメニューで作成した結果をコマンド化する機能を提供
"""
import logging

# from typing import Callable
import pyxel as px

# from gameutils.base import check_file, read_string
from gameutils.lib import WindowAction  # Window, WindowAction, WindowInputHandler

# from const import ENEMY_ID_BASE
import service_locater as di

# from helper import diceroll
# from field_map import Route
# from entity import Enemy, EntityParam, EnemyParam, BaseSprite, ActionPattern, Character
from . import BaseScene, SceneBattle
import command.entity_command as e_cmd

# from command.system_command import BattleStartEffect
# from entity import EntityBase, EntityContext
from menu import MenuBattle

# ロギング設定
logger = logging.getLogger(__name__)


class SceneBattleMenu(BaseScene):
    """バトルシーン"""

    # _disp_addr_center: int = 128  # エネミースプライト配置のセンター位置
    # _sprite_under: int = 160
    # _status_width: int = 80
    # _status_height: int = 48
    # _enemy_name_suffix: list = ["Ａ", "Ｂ", "Ｃ", "Ｄ", "Ｅ", "Ｆ"]
    # _enemy_commands: dict[ActionPattern, type[e_cmd.CommandBaseEntity]] = {
    #     ActionPattern.ATTACK: e_cmd.Attack,
    #     ActionPattern.ESCAPE: e_cmd.EnemyEscape,
    #     ActionPattern.SKILL: e_cmd.UseSkill,
    #     ActionPattern.SPECIAL: e_cmd.EnemySpecial,
    #     ActionPattern.DEFEND: e_cmd.DefenceMode,
    # }

    # def __init__(self, actor:Character, enemy_list:list[Enemy], battle_command: dict, message_window:Window, parent_draw: Callable):
    def __init__(self) -> None:
        super().__init__()
        self.situation = "battle"

        # self.actor = actor
        # self.enemy_list = enemy_list
        # self.battle_commands = battle_command
        # self.message_window = message_window
        # self.parent_draw = parent_draw

        # # # バトルでは決定キーの入力を連打状態に更新する
        # # # バトルシーンから抜ける際に復旧関数で元に戻す
        # # _hold_frames, _repeat_frames = 4, 2
        # # WindowInputHandler._wrapper.decide = lambda: px.btnp(
        # #     px.KEY_Z, _hold_frames, _repeat_frames
        # # ) or px.btnp(px.GAMEPAD1_BUTTON_A, _hold_frames, _repeat_frames)

        # # メニュー未生成の場合は作成する
        # # 逆順メンバーリストを生成
        # # member_list = di.ref.pt.get_active_member()
        # # # logger.info(f"order member list {member_list}",)
        # # member_list.reverse()

        # # ここで作るコンテキストのターゲットはダミー。メニュー内で更新する。
        # _ctx = self.build_context(
        #     self.actor, self.actor, di.ref.pt.get_allmember(), self.enemy_list
        # )

        # logger.info(f"source context {ctx}")
        parent_scene = di.ref.scnmgr.get_now_scene()
        if not isinstance(parent_scene, SceneBattle):
            errmsg = (
                f"想定外のシーンから呼び出されました：{parent_scene.__class__.__name__}"
            )
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)
        battle_data = parent_scene.transfer_battledata()
        (
            self.context,
            self.battle_commands,
            self.message_window,
            # self.parent_draw,
            self.bgimage,
        ) = battle_data
        # キャンセル後の再実行時を考慮して担当キャラの入力済コマンドがあれば削除
        self.battle_commands.pop(self.context.actor.id, None)

        # self.wndmgr.push_stack(
        #     MenuBattle,
        #     self.context,
        #     # member_list,
        #     self.battle_commands,
        #     self.message_window,
        # )
        self.command_package = e_cmd.CommandPackage()
        self.wndmgr.push_stack(MenuBattle, self.context, self.command_package)

    def load_bgm(self) -> None:
        """シーン切替時のBGMロード"""
        """暫定処理：BGMロード"""
        pass

    def update(self):
        """更新処理
        - 戦闘終了フラグ時は戦闘報酬コマンド発行
        - 生存エネミーが0の場合に戦闘終了フラグON
        - コマンドスタックがある場合はコマンド処理へ抜ける
          - ない場合は生存PTメンバー分のコマンド生成をループ実行
          - コマンド数が揃ったらエネミー側コマンドと行動順を決定してコマンドスタック追加
        """

        # # コマンドリストにアクティブメンバー数のコマンドが揃うまでループ
        # if len(self.battle_commands.keys()) < di.ref.pt.get_active_member_count():
        #     if self.wndmgr.has_stack:
        #         self.wndmgr.update()

        # 基本的にメニューを回す
        # 完了またはキャンセル時の処理は
        is_submenu_open = self.wndmgr.stack_count > 1
        result = self.wndmgr.update()
        # サブメニューオープン時は確定処理を行わない
        if is_submenu_open:
            return
        match result:
            # case WindowAction.NOTHING:
            #     pass
            case WindowAction.CLOSE:
                """バトルメニューキャンセル時"""
                if self.context.actor.id > 0:
                    self.battle_commands.pop(self.context.actor.id - 1)
                di.ref.scnmgr.previous_scene(False)
            case WindowAction.NOTHING:
                """バトルメニュー決定完了時"""
                if self.command_package.selected_action is None:
                    errmsg = "コマンドが未定義です"
                    logger.critical(errmsg, exc_info=True)
                    raise TypeError(errmsg)
                cmd = self.command_package.selected_action
                self.battle_commands[self.context.actor.id] = cmd(
                    self.context,
                    self.message_window,
                    self.command_package.selected_args,
                )
                di.ref.scnmgr.previous_scene(False)
            # case WindowAction.CONTINUE:
            #     pass
            # case WindowAction.EXECUTE:
            #     pass
            # case WindowAction.NOTHING:
            #     pass
            # case _:
            #     pass

        """
        バトルメニューシーンを呼ぶ
        　コマンドの器は渡す
        　シーン内メニューでコマンドを作る
        　メニューは終わったらPOPする
        　　コマンドの器に生成したコマンドを定義する
        """

    def draw(self):
        """描画処理
        - 背景＝親画面（SceneBattleのdraw関数）
        - バトルメニュー
        """
        # 背景描画
        # self.parent_draw()
        px.dither(0.3)
        px.blt(0, 0, self.bgimage, 0, 0, self.bgimage.width, self.bgimage.height)
        # px.dither(0.5)
        # px.rect(0,0,px.width,px.height,px.COLOR_NAVY)
        px.dither(1)
        self.wndmgr.draw()

    # def build_context(
    #     self,
    #     actor: EntityBase,
    #     target: EntityBase,
    #     ally_list: list,
    #     target_list: list,
    # ) -> EntityContext:
    #     """エンティティコマンド用コンテキスト生成"""
    #     ctx = EntityContext(
    #         situation=self.situation,
    #         actor=actor,
    #         target=target,
    #         allies=ally_list,
    #         targets=target_list,
    #         # pending_command=None
    #     )
    #     return ctx
