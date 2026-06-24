"""
ロギング設定モジュール

debug.logに情報を出力する為の設定ファイル
※非assetの為アセットIDマッピングは行わない
"""

import logging
import logging.handlers

LOG_FILENAME = "debug.log"


def setup_logging(log_level: int):
    if "Level" in logging.getLevelName(log_level):
        log_level = logging.CRITICAL
    # ルートロガー（全てのロガーの親）の設定を行う
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILENAME, encoding="utf-8"),  # ファイル出力
            logging.StreamHandler(),  # コンソール出力
            logging.handlers.RotatingFileHandler(
                LOG_FILENAME, maxBytes=1048576, backupCount=5
            ),
        ],
    )
