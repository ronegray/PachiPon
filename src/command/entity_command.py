"""
エンティティコマンドモジュール
"""

import logging
from typing import Generator, cast
from dataclasses import dataclass
import pyxel as px
from const import SoundID, APP_FPS
from gameutils.base import is_pressed
from gameutils.lib import Window, WindowAction

# from helper import diceroll, upper_int
from helper import upper_int
from entity import EntityContext, Enemy, Party  # , WeakType  # , Character
from skill import SkillTargetType, DebuffType  # , SkillID
from item import ItemTargetType  # , StackPool  # , ItemState  # , WeaponType
import service_locater as di
from . import CommandBaseSequence, SeqSubCmd  # , CommandPhase
from .effect_command import (
    efx_diceroll,
    # efx_physical_attack,
    # efx_damage_shake,
    # efx_monster_dead,
    # efx_skill_attack,
)


# ロギング設定
logger = logging.getLogger(__name__)


class CommandBaseEntity(CommandBaseSequence):
    """エンティティが実行者となるコマンドの基底クラス"""

    def __init__(self, ctx: EntityContext, wnd: Window, *args, **kwargs) -> None:
        """初期化：コンテキストの引継"""
        super().__init__(wnd, *args, **kwargs)
        self._ctx: EntityContext = ctx


@dataclass
class CommandPackage:
    """Command選択結果のメニュー⇔シーン間受け渡し用パッケージ"""

    selected_action: type[CommandBaseEntity] | None = None
    target_type: SkillTargetType | ItemTargetType | None = None
    selected_args: dict | None = None


class PartyDefeated(CommandBaseSequence):
    """パーティー全滅時処理"""

    def _sequence(self) -> Generator[list, None, None]:
        # フェード用背景画像コピー
        bg = self.args[0]
        w, h = px.width, px.height
        fade_bgimage = px.Image(w, h)
        fade_bgimage.blt(0, 0, bg, 0, 0, w, h)
        # 背景&BGMフェード
        i = 1
        di.ref.sndmgr.stop_music_fadeout(APP_FPS * 5)
        while True:
            self.display_info.graphic_command = [
                lambda alpha=i: bg.dither(alpha),
                lambda: bg.cls(0),
                lambda: bg.blt(0, 0, fade_bgimage, 0, 0, px.width, px.height),
            ]
            i -= 0.015
            if i < 0:
                if di.ref.sndmgr.get_fade_state():
                    # エネミーリストのクリア
                    self.args[1].clear()
                    break
            yield [SeqSubCmd.WAIT, 0]
        # 全滅BGM再生
        di.ref.sndmgr.request_bgm("defeat")
        messages = [
            ["やられたョ！", "　　♰ 全員　死亡 ♰ "],
            [SeqSubCmd.WAIT, 3],
            ["", "・・・慌てる事はありません"],
            [SeqSubCmd.WAIT, 2],
            ["", "あなたに再び立ち上がり、戦う力を与えましょう"],
            [SeqSubCmd.WAIT, 2],
            ["", "啓示を得た者がそこを訪れ、王城へと連れ帰ってくれます"],
            [SeqSubCmd.WAIT, 2],
            ["", "彼の地でゆっくり傷を癒やすとよいでしょう"],
            [""],
            [""],
            [""],
            [SeqSubCmd.WAIT, 2],
            ["これだけの業を振るったのです"],
            [SeqSubCmd.WAIT, 3],
            ["", "少しの供物を頂いておきますよ？"],
        ]
        for msg in messages:
            if is_pressed("cancel"):
                break
            yield msg

        # お供え物
        # di.ref.sndmgr.play_se_instant(SoundID.ITEM_LOST)
        yield [SeqSubCmd.SE_INSTANT, SoundID.ITEM_LOST]
        offering_foods = di.ref.pt._pt_foods // 2
        di.ref.pt.lost_foods(offering_foods)
        offering_golds = int(di.ref.pt._pt_golds * 0.1)
        di.ref.pt.spend_gold(offering_golds)

        # イベントポイントの待機化
        penalty_turns = max(1, int(di.ref.pt.average_level // 10))
        di.ref.map.defeated_penalty(penalty_turns)

        yield from self._wait_finish()

        # スタート地点へ戻る
        di.ref.pt.set_current_point("p01")
        di.ref.pt._pt_is_moving = False
        di.ref.pt.set_current_route()
        di.ref.pt._field_sprite._is_moving = False

        di.ref.scnmgr.change_scene("map")

        return


class GrantReward(CommandBaseEntity):
    """戦闘報酬獲得イベント（エンティティ関連）"""

    def _sequence(self) -> Generator[list, None, None]:
        enemy_list = cast(list[Enemy], self._ctx.targets)
        pt: Party = self.args[0]

        # ここで勝利SEとBGMロード
        px.stop()
        # px.play(self.se_ch, SoundID.BATTLE_VICTORY, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.BATTLE_VICTORY)
        yield [SeqSubCmd.SE_SUSTAIN, SoundID.BATTLE_VICTORY]
        yield ["敵との戦闘に　勝利した！！"]
        yield [""]
        # yield [SeqSubCmd.WAIT, "1"]  # 勝利SEの長さを文字で返す

        # お金
        reward_gold = sum([enemy.eparam.gold for enemy in enemy_list])
        pt.earn_gold(reward_gold)
        yield [f"パーティーは　{upper_int(reward_gold)}ゴールド　の儲け"]

        # 経験値はメンバー人数割りで死亡者も全員獲得
        reward_exp = sum([enemy.param.exp for enemy in enemy_list])
        num = pt.get_member_count()
        for member in pt.get_allmember():
            getexp = px.ceil(reward_exp / num)
            member.gain_exp(getexp)
            yield [f"{member.param.name}は　経験値{upper_int(getexp)}　を稼いだ！"]

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()


class CharacterInitialHPMP(CommandBaseEntity):
    """キャラメイク時の初期HPとMPの決定"""

    def _sequence(self) -> Generator[list, None, None]:
        effect = di.ref.efxdice
        roll_frames = 60
        # yield ["初期ＨＰとＭＰの最大値を決定します"]
        # yield ["ＨＰサイコロの数は、２＋耐久ボーナス値"]
        yield ["初期ＨＰとＭＰの最大値を決定します", "ＨＰサイコロの数は、２＋耐久ボーナス値"]
        dices = 2 + self._ctx.actor.bonus_end
        effect.start(dices, roll_frames)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
            # self.display_info.graphic_command = effect.get_draw_commands()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield [SeqSubCmd.WAIT, 0]
        max_hp = effect.total + self._ctx.actor.endurance
        yield [f"最大ＨＰは {max_hp} になりました"]
        self._ctx.actor.param.max_hp = max_hp
        self._ctx.actor.param.hp = max_hp

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # self.display_info.target.update_indicator(False)

        yield ["", "ＭＰサイコロの数は、１＋魔力ボーナス値"]
        dices = 1 + self._ctx.actor.bonus_arc
        effect.start(dices, roll_frames)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
            # self.display_info.graphic_command = effect.get_draw_commands()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield [SeqSubCmd.WAIT, 0]
        max_mp = effect.total + self._ctx.actor.bonus_arc
        yield [f"最大ＭＰは {max_mp} になりました"]
        self._ctx.actor.param.max_mp = max_mp
        self._ctx.actor.param.mp = max_mp

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()


class CharacterLevelup(CommandBaseEntity):
    """レベルアップメッセージと効果音"""

    def _sequence(self) -> Generator[list, None, None]:
        # px.play(self.se_ch, SoundID.LEVEL_UP, resume=True)
        # di.ref.sndmgr.play_se_sustain(SoundID.LEVEL_UP)
        yield [SeqSubCmd.SE_INSTANT, SoundID.LEVEL_UP]
        yield [f"{self._ctx.actor.param.name}は　レベルアップ！！", ""]
        return


class CharacterGainHPMP(CommandBaseEntity):
    """レベルアップによるHPとMPの上昇"""

    def _sequence(self) -> Generator[list, None, None]:
        yield ["ＨＰの上昇値を決定します", "Ｌｅｔ’ｓ　ｄｉｃｅｒｏｌｌ！"]
        val = yield from efx_diceroll(self.display_info, 1)  # type: ignore
        gain = val + self._ctx.actor.bonus_end
        yield [f"ＨＰが{gain} 増えました！"]
        self._ctx.actor.param.max_hp += gain
        self._ctx.actor.param.hp += gain

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # self.display_info.target.update_indicator(False)

        yield ["", "ＭＰの上昇値を決定します"]
        val = yield from efx_diceroll(self.display_info, 1)  # type: ignore
        gain = val + self._ctx.actor.bonus_arc
        yield [f"ＭＰが{gain} 増えました！"]
        self._ctx.actor.param.max_mp += gain
        self._ctx.actor.param.mp += gain

        # self.display_info.target.update_indicator(True)
        # while self.display_info.target.update() == WindowAction.CONTINUE:
        #     yield [SeqSubCmd.WAIT, 0]
        # self.display_info.target.update_indicator(False)
        yield from self._wait_finish()

        return


class DebuffRecoverCheck(CommandBaseEntity):
    """ターン終了時のデバフ回復チェック"""

    def _sequence(self) -> Generator[list, None, None]:
        yield [SeqSubCmd.WAIT, 0]
        self.step_wait = -1
        debuff_name = {
            DebuffType.REDUCE_DICEVALUE: "呪詛",
            DebuffType.POISON_DAMAGE: "中毒",
            DebuffType.STONE_HOLD: "石化",
            DebuffType.FALL_ASLEEP: "睡眠",
            DebuffType.DISTURB_MIND: "混乱",
            DebuffType.CHARM_PERSON: "魅了",
            DebuffType.INITIATIVE_ZERO: "転倒",
        }
        for member in self._ctx.allies:
            recover = member.recoverroll()
            if len(recover) > 0:
                for debuff_id in recover:
                    yield [f"{member.param.name}は {debuff_name[debuff_id]}状態から回復した"]
                self.display_info.target.update_indicator(True)
                while self.display_info.target.update() == WindowAction.CONTINUE:
                    yield [SeqSubCmd.WAIT, 0]
                self.display_info.target.update_indicator(False)
        return
