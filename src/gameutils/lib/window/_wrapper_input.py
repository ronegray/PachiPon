"""wrapper_input.py
Windowパッケージが必要とする入力関数をラップするインタフェース

- 入力関数を集約するクラス（WindowInputWrapper）
- 外部入力機能不使用時のデフォルト設定関数（set_default_pyxel_input）

設計方針:
- 本モジュールは pyxel 以外の外部ライブラリ（input_system 等）を一切知らない。
  Windowパッケージを単体のライブラリとして成立させるための依存回避。
- 各ハンドラは Callable[[INPUT_MODE], bool] とし、once/keep/hold を
  呼び出し側（Menu等の利用側コード）が都度選べるようにする。
  例: カーソル移動は hold で長押しリピート、決定/キャンセルは once のまま。
"""

# from typing import Literal, Callable
from dataclasses import dataclass, field

import pyxel as px
from gameutils import InputHandler, INPUT_MODE


# INPUT_MODE = Literal["once", "keep", "hold"]

_ANALOG_THRESHOLD_XY = 0x3FFF  # アナログレバー閾値
_HOLD_FRAMES = 9  # キーリピートまでの長押しフレーム数
_REPEAT_FRAMES = 3  # キーリピート間隔フレーム数


# def _make_handler(*sources: int | tuple[int, int]) -> Callable[[INPUT_MODE], bool]:
def _make_handler(*sources: int | tuple[int, int]) -> InputHandler:
    """デジタルキー/ボタンとアナログ軸(符号付き)を混在させて判定するハンドラを生成する

    Args:
        sources: 各要素は以下のいずれか
            - int: デジタルキー/ボタンコード（px.KEY_*, px.GAMEPAD1_BUTTON_*）
            - tuple[int, int]: (アナログ軸コード, 符号) のペア。
              符号は+1または-1で、スティックのどちら向きをこの方向として扱うかを表す。

    Returns:
        Callable[[INPUT_MODE], bool]: mode("once"/"keep"/"hold")を受け取り、
        いずれかのソースが条件を満たせばTrueを返す判定関数。
    """
    digital_codes = tuple(s for s in sources if isinstance(s, int))
    analog_sources = tuple(s for s in sources if isinstance(s, tuple))
    # アナログ軸ごとに独立したframe_countを保持（holdのリピート判定に必要）
    frame_counts: dict[tuple[int, int], int] = {src: 0 for src in analog_sources}

    def _check_analog(code: int, sign: int, mode: INPUT_MODE) -> bool:
        val = px.btnv(code)
        is_active = (val * sign) > _ANALOG_THRESHOLD_XY
        count = frame_counts[(code, sign)]

        if mode == "keep":
            return is_active

        if is_active:
            count += 1
            frame_counts[(code, sign)] = count
            # 1フレーム目はどちらもTrue
            if count == 1:
                return True
            # once：2フレーム目以降は常にFalse
            if mode == "once":
                return False
            # hold：hold期間を超え、かつrepeat間隔ごとにTrue
            if mode == "hold" and count > _HOLD_FRAMES:
                if (count - _HOLD_FRAMES) % _REPEAT_FRAMES == 0:
                    return True
        else:
            # キー入力停止（閾値を下回る）でリセット
            frame_counts[(code, sign)] = 0

        return False

    def handler(mode: INPUT_MODE = "once") -> bool:
        # デジタル側：pyxel内部が押下継続フレーム数を管理しているため、
        # or短絡評価があっても後続コードの状態には影響しない
        digital_hit = False
        for code in digital_codes:
            if mode == "keep":
                digital_hit = digital_hit or px.btn(code)
            elif mode == "hold":
                digital_hit = digital_hit or px.btnp(
                    code, hold=_HOLD_FRAMES, repeat=_REPEAT_FRAMES
                )
            else:  # "once"
                digital_hit = digital_hit or px.btnp(code)

        # アナログ側：frame_countを自前保持しているため、
        # 短絡評価で呼び出しが飛ぶとカウンタが崩れる。必ず全ソースを評価してからany()。
        analog_results = [
            _check_analog(code, sign, mode) for code, sign in analog_sources
        ]

        return digital_hit or any(analog_results)

    return handler


@dataclass
class WindowInputWrapper:
    """windowパッケージが必要とする入力関数の集約

    各フィールドは Callable[[INPUT_MODE], bool]。
    デフォルト引数 mode="once" を持たせているため、
    呼び出し側は従来通り引数無し(self.inputkey.up())でも動作し、
    holdでリピート判定したい箇所だけ self.inputkey.up("hold") のように指定できる。
    """

    # up: Callable[[INPUT_MODE], bool] = field(default=lambda mode="hold": False)
    # down: Callable[[INPUT_MODE], bool] = field(default=lambda mode="hold": False)
    # left: Callable[[INPUT_MODE], bool] = field(default=lambda mode="hold": False)
    # right: Callable[[INPUT_MODE], bool] = field(default=lambda mode="hold": False)
    # decide: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # cancel: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # action: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # menu: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # start: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # select: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # LS: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)
    # RS: Callable[[INPUT_MODE], bool] = field(default=lambda mode="once": False)

    up: InputHandler = field(default=lambda mode="hold": False)
    down: InputHandler = field(default=lambda mode="hold": False)
    left: InputHandler = field(default=lambda mode="hold": False)
    right: InputHandler = field(default=lambda mode="hold": False)
    decide: InputHandler = field(default=lambda mode="once": False)
    cancel: InputHandler = field(default=lambda mode="once": False)
    action: InputHandler = field(default=lambda mode="once": False)
    menu: InputHandler = field(default=lambda mode="once": False)
    start: InputHandler = field(default=lambda mode="once": False)
    select: InputHandler = field(default=lambda mode="once": False)
    LS: InputHandler = field(default=lambda mode="once": False)
    RS: InputHandler = field(default=lambda mode="once": False)


def set_default_pyxel_input() -> WindowInputWrapper:
    """外部入力機能を使わない場合のデフォルト定義（オプション）

    移動系(up/down/left/right)は、個別カスタマイズを許さない代わりに
    WASD・カーソルキー・D-pad・アナログスティックを常時すべて有効にする。

    注意: AXIS_LEFTYの符号方向はpyxel/実機依存のため実測確認が必要。
          ここでは "スティックを上に倒す = 負の値" と仮定している。
    """
    return WindowInputWrapper(
        up=_make_handler(
            px.KEY_UP,
            px.KEY_W,
            px.GAMEPAD1_BUTTON_DPAD_UP,
            (px.GAMEPAD1_AXIS_LEFTY, -1),
        ),
        down=_make_handler(
            px.KEY_DOWN,
            px.KEY_S,
            px.GAMEPAD1_BUTTON_DPAD_DOWN,
            (px.GAMEPAD1_AXIS_LEFTY, 1),
        ),
        left=_make_handler(
            px.KEY_LEFT,
            px.KEY_A,
            px.GAMEPAD1_BUTTON_DPAD_LEFT,
            (px.GAMEPAD1_AXIS_LEFTX, -1),
        ),
        right=_make_handler(
            px.KEY_RIGHT,
            px.KEY_D,
            px.GAMEPAD1_BUTTON_DPAD_RIGHT,
            (px.GAMEPAD1_AXIS_LEFTX, 1),
        ),
        decide=_make_handler(px.KEY_Z, px.GAMEPAD1_BUTTON_A),
        cancel=_make_handler(px.KEY_X, px.GAMEPAD1_BUTTON_B),
        action=_make_handler(px.KEY_C, px.GAMEPAD1_BUTTON_X),
        menu=_make_handler(px.KEY_V, px.GAMEPAD1_BUTTON_Y),
        start=_make_handler(px.KEY_RETURN, px.GAMEPAD1_BUTTON_START),
        select=_make_handler(px.KEY_SHIFT, px.GAMEPAD1_BUTTON_BACK),
        LS=_make_handler(
            px.KEY_LSHIFT,
            px.GAMEPAD1_BUTTON_LEFTSHOULDER,
            px.KEY_LEFT,
            px.GAMEPAD1_BUTTON_DPAD_LEFT,
        ),
        RS=_make_handler(
            px.KEY_RSHIFT,
            px.GAMEPAD1_BUTTON_RIGHTSHOULDER,
            px.KEY_RIGHT,
            px.GAMEPAD1_BUTTON_DPAD_RIGHT,
        ),
    )
