"""window_protocol.py
ウインドウ・メニュークラスおよび管理クラスの利用側とのインタフェース

- ウインドウ／メニューのスタック追加時の指定パラメータを管理
- ウインドウ／メニュー操作後の戻り値の指定パラメータを管理
"""

from enum import Enum, auto
from typing import Literal


WINDOW_MODE = Literal["once", "wait", "page", "menu", "sub", "hold", "view"]
MENU_WINDOW_TYPE = Literal["main", "sub", "sub2", "sub3"]
SE_CHANNEL = 7


class WindowAction(Enum):
    """メニュー／ウインドウ操作時の応答リスト"""

    CONTINUE = auto()  # 現在状態の継続
    CLOSE = auto()  # 一つ戻る (pop)
    DISCARD = auto()  # 全て破棄して閉じる (初期化)
    EXECUTE = auto()  # 選択処理を実行
    NOTHING = auto()  # メニュースタックが存在しない状態
