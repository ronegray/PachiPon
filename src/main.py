"""main.py
ゲームアプリケーション起動モジュール
- Pyxelの起動処理に必要な値の設定
"""
from game import GameApp
from bootstrap import ipl

# ロギング設定
import logging

logger = logging.getLogger(__name__)

# アプリケーション環境準備処理
ipl()

# ゲームアプリ起動
logger.info("launch the game application.")
GameApp()
