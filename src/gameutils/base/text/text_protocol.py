"""font_protocol.py
フォント利用側とのインタフェース

- ウインドウ／メニューのスタック追加時の指定パラメータを管理
- ウインドウ／メニュー操作後の戻り値の指定パラメータを管理
"""
from typing import Literal


FONT_SIZE_NAME = Literal["small", "basic", "large"]
