"""main.py
ゲームアプリケーション起動モジュール
- Pyxelの起動処理に必要な値の設定
"""
from game import GameApp
from logger import setup_logging

# ロギング設定
import logging

logger = logging.getLogger(__name__)

# ログ設定の初期化
setup_logging(logging.DEBUG)
logger.info("log setup finished successfully.")


logger.info("launch the game application.")
GameApp()
