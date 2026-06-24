"""
ゲームアプリケーション起動モジュール
- Pyxelの起動処理に必要な値の設定
"""

import logging
from game import GameApp
from bootstrap import ipl

# アプリケーション環境準備処理
ipl()

# ロギング設定
logger = logging.getLogger(__name__)

# ゲームアプリ起動
logger.info("launch the game application.")
GameApp()
