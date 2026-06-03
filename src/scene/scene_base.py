"""scene_base.py
scene系基底クラスおよびシーンスタックマネージャ
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from gameutils.lib.window import WindowManager


class BaseScene(ABC):
    """シーン基底クラス"""

    def __init__(self) -> None:
        """初期化：シーン別ウインドウマネージャ生成"""
        self.wndmgr = WindowManager()

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def draw(self) -> None:
        pass
