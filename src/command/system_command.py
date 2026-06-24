"""
システムコマンドモジュール
"""

from gameutils.lib import Window
from . import CommandBase, DisplayInfo


class CommandBaseSystem(CommandBase):
    """システムに対するユーザ操作を表すコマンドの基底クラス"""

    def __init__(self, target_window: Window, *args, **kwargs) -> None:
        """初期化：コンテキストは利用しない"""

        self.display_info: DisplayInfo = DisplayInfo(target_window, [])
