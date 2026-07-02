"""scene_base.py
scene系基底クラスおよびシーンスタックマネージャ
"""

# from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal
from gameutils.lib.window import WindowManager


SITUATION = Literal["field", "battle", "system"]


class BaseScene(ABC):
    """シーン基底クラス"""

    situation: SITUATION = "system"

    def __init__(self) -> None:
        """初期化：シーン別ウインドウマネージャ生成"""
        self.wndmgr = WindowManager()

    @abstractmethod
    def update(self) -> None:
        ...

    @abstractmethod
    def draw(self) -> None:
        ...
