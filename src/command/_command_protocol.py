"""command_protocol.py

Commandの実行契約（Protocol）を定義するモジュール。

設計方針（これまでの議論のまとめ）:
- execute()という1回完結の呼び出しは存在しない。Pyxelはフレーム単位でしか
  処理が進まないため、update()/draw()という2つのメソッドの組み合わせ自体が
  「execute」の実体になる。
- Commandは自分の実行状態（Phase）と表示内容（DisplayInfo）を自分自身で持つ。
  update()はその両方を進行させ、draw()は「今の状態を見せるだけ」の
  冪等な処理に徹する（drawはPyxelの高負荷時にスキップされ得るため、
  状態の進行や効果音のような一度きりの副作用を絶対に持たせない）。
- CommandEntityProtocol / CommandSystemProtocol は、Contextの形が異なる
  2系統を型として書き分けるためのものであり、CommandManager（Invoker）は
  これらを一切区別しない。CommandManagerが見るのはCommandProtocolのみ。
  どちらの系統のCommandを生成するかは、生成側（Client）がコーディング時点で
  自明に把握している前提（動的な判定は行わない）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class Phase(Enum):
    """Commandの大まかな実行状態。コマンド固有の詳細はこのEnumに含めず、
    各ConcreteCommand側の属性（フラグ）として個別に持たせる。"""

    PENDING = auto()  # 未実行：生成直後、まだ一度もupdateが進行していない
    AWAITING_ACK = auto()  # 効果適用済み・確認待ち：表示内容を見せてユーザの入力を待つ
    DONE = auto()  # 完了：Invokerはこの状態を見てpopしてよい


@dataclass(frozen=True, slots=True)
class DisplayInfo:
    """draw()が返す、冪等な表示用データ。
    効果音などの「一度きりの副作用」はここに含めない（update側で発火させる）。
    """

    message: str
    sub_message: str | None = None


@dataclass(slots=True)
class CommandState:
    """update()が返す、Commandの現在の実行状態。"""

    phase: Phase
    display_info: DisplayInfo | None = None


class CommandProtocol(Protocol):
    """全Commandが満たすべき最小の契約。CommandManagerはこの型としてのみ
    Commandを扱い、これ以上の情報を一切要求しない。"""

    def update(self) -> CommandState:
        """1フレーム分、状態を進行させる。
        初回呼び出し（phase==PENDING時）で実際の効果適用を行う
        （旧コードのexec()に相当する処理はここに統合する）。
        効果音のような一度きりの副作用も必ずここで発火させる。
        """
        ...

    def draw(self) -> DisplayInfo | None:
        """現在保持しているdisplay_infoを返すだけの、副作用のない処理。
        drawフレームがスキップされても進行に一切影響しないことが必須。
        """
        ...


class CommandEntityProtocol(CommandProtocol, Protocol):
    """状況／実行者／行動／対象、のうち実行者(Entity)を伴う系統。
    CommandManagerはこの型を意識しない。ターン進行ロジックなど、
    『実行者が誰か』を本当に必要とする別の構成要素のためだけに存在する。
    """

    @property
    def actor(self) -> object:
        """行動の実行者（Entity）。"""
        ...

    @property
    def targets(self) -> list[object]:
        """行動の対象（Entityのリスト）。"""
        ...


class CommandSystemProtocol(CommandProtocol, Protocol):
    """実行者(Entity)を伴わない系統（セーブ／ロード／コンフィグ／ショップ等）。
    対象（システムリソース）はあるが、実行者という概念を持たない。
    """

    @property
    def target(self) -> object:
        """操作対象となるシステムリソース。"""
        ...


def wait_for_confirm() -> bool:
    """確認入力（決定キー等）が押されたかどうか。
    EntityCommand/SystemCommandの両方から共通で使う、確認待ちフェーズ用の
    小さな共有ユーティリティ。実プロジェクトでは pyxel.btnp(...) 等に置き換える。
    ここではサンプル用にダミー実装を提供する。
    """
    return True
