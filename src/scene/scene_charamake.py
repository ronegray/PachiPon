"""
シーンモジュール：キャラメイク
"""

import logging
import pyxel as px
from helper import upper_int_format, format_leftright
from gameutils.lib import Window
from assets.asset_map import AssetID, AssetMap
import service_locater as di
from entity import PlayerSprite, Character, EntityContext
from menu import MenuCharaMake
import command.entity_command as e_cmd

from . import BaseScene

# ロギング設定
logger = logging.getLogger(__name__)


class SceneCharaMake(BaseScene):
    def __init__(self):
        super().__init__()
        self.situation = "system"
        # 背景イメージ設定
        self.bgimage = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_TITLE))
        self.bgpos = (
            (px.width - self.bgimage.width) // 2,
            (px.height - self.bgimage.height) // 2,
        )

        # キャラクターのベースデータ作成
        self.param = di.ref.scnmgr.get_now_scene().param  # type: ignore
        self.charaimage: px.Image = px.Image.from_image(
            AssetMap.get_assetpath(AssetID.IMAGE_CHARA)
        )
        self.sprite = PlayerSprite(0, 0, self.charaimage)
        self.hero = Character(id=0, param=self.param, sprite=self.sprite)

        # メッセージ用ウインドウの生成
        message_pos = (0, 184)
        message_size = (px.width, 72)
        self.message_window = Window("basic", *message_pos, *message_size, "once")
        self.message_window.update_row_max(self.message_window._max_msg_rows + 1)
        self.message_window.set_message(
            [
                "各パラメータに３～１８の範囲でポイントを割り振り",
                "主人公の能力を決定してください",
                "（各パラメータの説明は右のミニウインドウ）",
                "全ポイント割振後に決定キーを押してください",
            ]
        )

        # パラメータ用ウインドウの生成
        param_pos = (Window._chip_size, Window._chip_size)
        param_size = (128, 136)
        self.param_window = Window("basic", *param_pos, *param_size, "once")
        self.build_status()

        # メニュー生成
        self.wndmgr.push_stack(MenuCharaMake, self.hero)

    def build_status(self) -> None:
        """ステータス表示内容の構築（ステータスのみ）"""
        member = self.hero
        param = member.param

        status_lines = f"{param.name}"
        status_lines += f"\nレベル： {upper_int_format(param.level, 2)}"
        status_lines += f"\n経験値： {upper_int_format(param.exp, 6)}"
        status_lines += f"\nＨ　Ｐ： {upper_int_format(param.hp, 3)}／{upper_int_format(param.max_hp, 3)}"
        status_lines += f"\nＭ　Ｐ： {upper_int_format(param.mp, 3)}／{upper_int_format(param.max_mp, 3)}"
        status_lines += f"\n筋　力： {
            format_leftright(
                upper_int_format(member.strength, 3),
                f'（＋{upper_int_format(member.bonus_str, 1)}）',
                18,
            )
        }"
        status_lines += f"\n魔　力： {
            format_leftright(
                upper_int_format(member.arcane, 3),
                f'（＋{upper_int_format(member.bonus_str, 1)}）',
                18,
            )
        }"
        status_lines += f"\n耐　久： {
            format_leftright(
                upper_int_format(member.endurance, 3),
                f'（＋{upper_int_format(member.bonus_end, 1)}）',
                18,
            )
        }"
        status_lines += f"\n速　度： {
            format_leftright(
                upper_int_format(member.speed, 3),
                f'（＋{upper_int_format(member.bonus_spd, 1)}）',
                18,
            )
        }"
        status_lines += f"\n幸　運： {
            format_leftright(
                upper_int_format(member.luck, 3),
                f'（＋{upper_int_format(member.bonus_lck, 1)}）',
                18,
            )
        }"
        self.param_window.message_list = [status_lines]

    def update(self):
        """更新処理"""
        if di.ref.cmdmgr.is_empty:
            if self.wndmgr.has_stack:
                self.wndmgr.update()
            else:
                self.build_status()
                ctx = EntityContext(
                    situation=self.situation,
                    actor=self.hero,
                    target=self.hero,
                    allies=[],
                    targets=[],
                )
                cmd = e_cmd.CharacterInitialHPMP(ctx, self.message_window)
                self.hero.equip_default()
                di.ref.pt.add_ptmember(self.hero)
                di.ref.pt.set_field_sprite()
                di.ref.cmdmgr.push_command(cmd)
                di.ref.cmdmgr.set_on_empty(
                    lambda: di.ref.scnmgr.change_scene("opening")
                )

    def draw(self):
        """描画処理"""
        px.blt(
            *self.bgpos,
            self.bgimage,
            0,
            0,
            self.bgimage.width,
            self.bgimage.height,
            colkey=px.COLOR_BLACK,
        )
        self.param_window.draw()
        self.param_window.draw_message()
        self.message_window.draw()
        self.message_window.draw_message()

        if di.ref.cmdmgr.is_empty:
            if self.wndmgr.has_stack:
                self.wndmgr.draw()
