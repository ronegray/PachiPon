"""command_cast_spell.py

EntityCommand系の具象例。

このファイルには本来 entity.py / effect_manager.py 等、別モジュールに
切り出すべきクラスもサンプルの都合上まとめて置いている
（コメントでその旨を明記する）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from command._command_protocol import CommandState, DisplayInfo, Phase, wait_for_confirm


# --------------------------------------------------------------------------
# 本来は entity.py に置くクラス。
# 「変更の責務はクラス自身にある」の実践として、HP/MPの増減は
# Entity自身のメソッド経由で行い、Command側からの直接代入は行わない。
# --------------------------------------------------------------------------
@dataclass
class Entity:
    name: str
    hp: int
    max_hp: int
    mp: int
    max_mp: int

    def consume_mp(self, cost: int) -> bool:
        """MPを消費する。不足していれば消費せずFalseを返す。
        消費可否のルールはここに一元化されており、Command側で
        `if cost > entity.mp` のような判定を再実装する必要はない。
        """
        if cost > self.mp:
            return False
        self.mp -= cost
        return True

    def apply_damage(self, amount: int) -> int:
        """ダメージを受ける。HPが0未満にならないという不変条件を守りつつ、
        実際に与えられたダメージ量を返す（Command側はこの戻り値だけを見て
        メッセージを組み立てればよく、Entityの内部を覗く必要がない）。
        """
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual

    @property
    def is_down(self) -> bool:
        return self.hp <= 0


# --------------------------------------------------------------------------
# 本来は effect_protocol.py / skill_master.json / effect_manager.py に
# 分かれる部分。サンプルでは辞書1つで簡略化している。
# --------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class SpellData:
    name: str
    mp_cost: int
    power: int
    sound_id: str


_SPELL_TABLE: dict[str, SpellData] = {
    "fire": SpellData(name="ファイア", mp_cost=4, power=18, sound_id="snd_fire"),
    "heal": SpellData(name="ヒール", mp_cost=3, power=-20, sound_id="snd_heal"),
}


def _play_sound(sound_id: str) -> None:
    """効果音を鳴らす。drawがスキップされても取りこぼさないよう、
    必ずupdate側からのみ呼び出すこと。実プロジェクトでは
    pyxel.play(...) 等に置き換える。
    """
    print(f"[sound] play {sound_id}")


class Situation(Enum):
    FIELD = auto()
    BATTLE = auto()


@dataclass(frozen=True, slots=True)
class EntityContext:
    """状況／実行者／対象、をまとめて運ぶContext。
    『行動』だけはContextのデータではなく、生成するConcreteCommandクラス
    そのものの型によって表現される。
    """

    situation: Situation
    actor: Entity
    targets: list[Entity]


class CommandCastSpell:
    """呪文使用コマンド（EntityCommand系）。"""

    def __init__(self, ctx: EntityContext, spell_id: str) -> None:
        # MP不足チェックはここでは行わない。
        # 「このコマンドを生成してよいか」はClient側（メニュー処理等）が
        # 生成前に判断済みという前提に立つ。
        self._ctx = ctx
        self._spell_id = spell_id
        self._state = CommandState(phase=Phase.PENDING)
        self._actual_amounts: list[
            int
        ] = []  # コマンド固有の詳細はフラグとして個別に持つ

    # --- CommandEntityProtocol の要求 -------------------------------------
    @property
    def actor(self) -> Entity:
        return self._ctx.actor

    @property
    def targets(self) -> list[Entity]:
        return self._ctx.targets

    # --- CommandProtocol の要求 ---------------------------------------------
    def update(self) -> CommandState:
        if self._state.phase is Phase.PENDING:
            self._apply_effect()
            self._state.phase = Phase.AWAITING_ACK
        elif self._state.phase is Phase.AWAITING_ACK:
            if wait_for_confirm():
                self._state.phase = Phase.DONE

        return self._state

    def draw(self) -> DisplayInfo | None:
        # 自分のdisplay_infoを返すだけ。新たな計算は一切行わない。
        return self._state.display_info

    # --- 内部処理 -------------------------------------------------------
    def _apply_effect(self) -> None:
        """初回updateでのみ呼ばれる。旧コードのexec()に相当する処理を
        ここに統合している。"""
        spell = _SPELL_TABLE[self._spell_id]

        ok = self._ctx.actor.consume_mp(spell.mp_cost)
        assert ok, "MP不足のCommandは生成前に弾かれている前提"

        for target in self._ctx.targets:
            actual = target.apply_damage(spell.power)
            self._actual_amounts.append(actual)

        # 効果音は一度きりの副作用なので、必ずupdate側で発火させる。
        _play_sound(spell.sound_id)

        message = f"{self._ctx.actor.name}の{spell.name}！"
        if len(self._ctx.targets) == 1:
            target = self._ctx.targets[0]
            sub = f"{target.name}に{self._actual_amounts[0]}のダメージ"
            if target.is_down:
                sub += "（戦闘不能）"
        else:
            sub = " / ".join(
                f"{t.name}に{a}"
                for t, a in zip(self._ctx.targets, self._actual_amounts)
            )

        self._state.display_info = DisplayInfo(message=message, sub_message=sub)
