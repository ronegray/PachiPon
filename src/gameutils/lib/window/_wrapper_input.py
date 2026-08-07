"""wrapper_input.py
Windowパッケージが必要とする入力関数をラップするインタフェース
- 入力関数を集約するクラス
- 外部入力機能不使用時のデフォルト設定関数
"""

from typing import Callable
from dataclasses import dataclass, field
import pyxel as px


@dataclass
class WindowInputWrapper:
    """windowパッケージが必要とする入力関数の集約"""

    up: Callable[[], bool] = field(default=lambda: False)
    down: Callable[[], bool] = field(default=lambda: False)
    left: Callable[[], bool] = field(default=lambda: False)
    right: Callable[[], bool] = field(default=lambda: False)
    decide: Callable[[], bool] = field(default=lambda: False)
    cancel: Callable[[], bool] = field(default=lambda: False)
    other1: Callable[[], bool] = field(default=lambda: False)
    other2: Callable[[], bool] = field(default=lambda: False)
    start: Callable[[], bool] = field(default=lambda: False)
    select: Callable[[], bool] = field(default=lambda: False)
    LS: Callable[[], bool] = field(default=lambda: False)
    RS: Callable[[], bool] = field(default=lambda: False)


def set_default_pyxel_input() -> WindowInputWrapper:
    """外部入力機能を使わない場合のデフォルト定義（オプション）"""
    _hold_frames, _repeat_frames = 12, 6
    return WindowInputWrapper(
        up=lambda: (
            px.btnp(px.KEY_UP, _hold_frames, _repeat_frames)
            or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP, _hold_frames, _repeat_frames)
        ),
        down=lambda: (
            px.btnp(px.KEY_DOWN, _hold_frames, _repeat_frames)
            or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN, _hold_frames, _repeat_frames)
        ),
        left=lambda: (
            px.btnp(px.KEY_LEFT, _hold_frames, _repeat_frames)
            or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT, _hold_frames, _repeat_frames)
        ),
        right=lambda: (
            px.btnp(px.KEY_RIGHT, _hold_frames, _repeat_frames)
            or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT, _hold_frames, _repeat_frames)
        ),
        decide=lambda: px.btnp(px.KEY_Z) or px.btnp(px.GAMEPAD1_BUTTON_A),
        cancel=lambda: px.btnp(px.KEY_X) or px.btnp(px.GAMEPAD1_BUTTON_B),
        other1=lambda: px.btnp(px.KEY_C) or px.btnp(px.GAMEPAD1_BUTTON_X),
        other2=lambda: px.btnp(px.KEY_V) or px.btnp(px.GAMEPAD1_BUTTON_Y),
        start=lambda: px.btnp(px.KEY_RETURN) or px.btnp(px.GAMEPAD1_BUTTON_START),
        select=lambda: px.btnp(px.KEY_SHIFT) or px.btnp(px.GAMEPAD1_BUTTON_BACK),
        LS=lambda: px.btnp(px.KEY_LSHIFT) or px.btnp(px.GAMEPAD1_BUTTON_LEFTSHOULDER),
        RS=lambda: px.btnp(px.KEY_RSHIFT) or px.btnp(px.GAMEPAD1_BUTTON_RIGHTSHOULDER),
    )
