"""
Commandクラス群用プロトコルモジュール

Commandクラスはゲーム内の意思決定に従った処理を実行する
Commandクラス自身および利用側の処理で必要とする取り決めについて
本モジュールでまとめる

"""

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Callable
from gameutils.lib import Window


class CommandPhase(IntEnum):
    """Commandの大まかな実行状態。ConcreteCommand固有の詳細状態は個別実装する事"""

    SYN = auto()
    SYNACK = auto()
    ACK = auto()
    FINACK = auto()
    FIN = auto()


class CommandType(IntEnum):
    """コマンドの種類"""

    SYSTEM = auto()
    ATTACK = auto()
    SPELL = auto()
    ITEM = auto()
    ESCAPE = auto()
    ENEMY_ATTACK = auto()
    ENEMY_SKILL = auto()


@dataclass(slots=True)
class DisplayInfo:
    """Commandクラスのdrawメソッドが返す、描画内容の指示"""

    target: Window  # メッセージ出力先
    message: list[str] = field(default_factory=list)
    is_change: bool = False  # 内容が変更されたかどうか
    graphic_command: list[Callable] | None = None


class CommandContext:
    """コンテキストの型ベース用クラス"""

    ...
