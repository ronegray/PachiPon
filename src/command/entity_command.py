"""
エンティティコマンドモジュール
CommandProtocol
└CommandBaseSequence
 └CommandBaseEntityを継承する、EntityContextを処理対象とするもの
"""

import logging
from typing import Generator, cast

import pyxel as px
from const import SoundID
from helper import upper_int
from entity import Enemy, Party
from skill import DebuffType
import service_locater as di
from . import CommandBaseEntity, SeqSubCmd
from .effect_command import efx_diceroll


# ロギング設定
logger = logging.getLogger(__name__)


class GrantReward(CommandBaseEntity):
    """戦闘報酬獲得イベント（エンティティ関連）"""

    def _sequence(self) -> Generator[list, None, None]:
        enemy_list = cast(list[Enemy], self.ctx.targets)
        pt: Party = self.kwargs["party"]

        # ここで勝利SEとBGMロード
        px.stop()
        yield [SeqSubCmd.SE_SUSTAIN, SoundID.BATTLE_VICTORY]
        yield ["敵との戦闘に　勝利した！！"]
        yield [""]

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

        yield from self.wait_finish()


class CharacterInitialHPMP(CommandBaseEntity):
    """キャラメイク時の初期HPとMPの決定"""

    def _sequence(self) -> Generator[list, None, None]:
        effect = di.ref.efxdice
        roll_frames = 60
        yield ["初期ＨＰとＭＰの最大値を決定します", "ＨＰサイコロの数は、２＋耐久ボーナス値"]
        dices = 2 + self.ctx.actor.bonus_end
        effect.start(dices, roll_frames)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield [SeqSubCmd.WAIT, 0]
        max_hp = effect.total + self.ctx.actor.endurance
        yield [f"最大ＨＰは {max_hp} になりました"]
        self.ctx.actor.param.max_hp = max_hp
        self.ctx.actor.param.hp = max_hp

        yield ["", "ＭＰサイコロの数は、１＋魔力ボーナス値"]
        dices = 1 + self.ctx.actor.bonus_arc
        effect.start(dices, roll_frames)
        if not di.ref.conf.is_cutin_dice:
            effect.skip()
        while effect.is_rolling:
            effect.update()
            self.display_info.graphic_command = effect.get_draw_commands()
            yield [SeqSubCmd.WAIT, 0]
        max_mp = effect.total + self.ctx.actor.bonus_arc
        yield [f"最大ＭＰは {max_mp} になりました"]
        self.ctx.actor.param.max_mp = max_mp
        self.ctx.actor.param.mp = max_mp

        yield from self.wait_finish()


class CharacterLevelup(CommandBaseEntity):
    """レベルアップメッセージと効果音"""

    def _sequence(self) -> Generator[list, None, None]:
        yield [SeqSubCmd.SE_INSTANT, SoundID.LEVEL_UP]
        yield [f"{self.ctx.actor.param.name}は　レベルアップ！！", ""]
        return


class CharacterGainHPMP(CommandBaseEntity):
    """レベルアップによるHPとMPの上昇"""

    def _sequence(self) -> Generator[list, None, None]:
        yield ["ＨＰの上昇値を決定します", "Ｌｅｔ’ｓ　ｄｉｃｅｒｏｌｌ！"]
        val = yield from efx_diceroll(self.display_info, 1)  # type: ignore
        gain = val + self.ctx.actor.bonus_end
        yield [f"ＨＰが{gain} 増えました！"]
        self.ctx.actor.param.max_hp += gain
        self.ctx.actor.param.hp += gain

        yield ["", "ＭＰの上昇値を決定します"]
        val = yield from efx_diceroll(self.display_info, 1)  # type: ignore
        gain = val + self.ctx.actor.bonus_arc
        yield [f"ＭＰが{gain} 増えました！"]
        self.ctx.actor.param.max_mp += gain
        self.ctx.actor.param.mp += gain

        yield from self.wait_finish()

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
        for member in self.ctx.allies:
            recover = member.recoverroll()
            if len(recover) > 0:
                for debuff_id in recover:
                    yield [f"{member.param.name}は {debuff_name[debuff_id]}状態から回復した"]
                self.display_info.target.update_indicator(True)
                yield from self.wait_finish()
        return
