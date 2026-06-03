"""logger.py
ロギング設定モジュール
debug.logに情報を出力　※非assetの為アセットIDマッピングは行わない
"""
import logging


def setup_logging(log_level: int):
    if "Level" in logging.getLevelName(log_level):
        log_level = logging.CRITICAL
    # ルートロガー（全てのロガーの親）の設定を行う
    logging.basicConfig(
        # level=logging.INFO,
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("debug.log", encoding="utf-8"),  # ファイル出力
            logging.StreamHandler(),  # コンソール出力
        ],
    )
