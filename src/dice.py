"""dice.py
ダイスロールモジュール
- ダイスロール実行時の処理定義
"""

import pyxel as px


def diceroll(dice_num: int) -> int:
    """指定した数d6を振った結果を返す"""
    return px.rndi(dice_num, dice_num * 6)
