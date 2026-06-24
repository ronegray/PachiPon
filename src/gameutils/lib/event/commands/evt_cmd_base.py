"""event_command_base.py
イベント制御コマンド定義の基底データクラス
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Generator

# updateジェネレータの型エイリアス
generator_type_command = Generator[None, None, None]


@dataclass
class EventCommand:
    # runner: Callable[..., Generator]
    runner: Callable  # 即時: 普通の関数 / 待機: ジェネレータ関数
    drawer: Callable | None = None  # 待機のみ： 普通の描画用関数
    is_instant: bool = False  # 即時命令はTrue
