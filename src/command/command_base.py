"""
Command系基底クラス

コマンド関連クラスの契約となる抽象クラス
"""

# from __future__ import annotations
from abc import ABC, abstractmethod
from . import CommandPhase, DisplayInfo


class CommandBase(ABC):
    """コマンド基底クラス"""

    phase: CommandPhase

    @abstractmethod
    def update(self) -> CommandPhase:
        ...

    @abstractmethod
    def draw(self) -> DisplayInfo:
        ...
