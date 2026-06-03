# from typing import Callable
# import pyxel as px


# class InputHandler:
#     """入力制御クラス"""
#     # 操作名ごとにデフォルト実装を定義
#     _input_handlers: dict[str, Callable[[], bool]] = {
#         "up": lambda: px.btnp(px.KEY_UP, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_UP, 12, 6),
#         "down": lambda: px.btnp(px.KEY_DOWN, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_DOWN, 12, 6),
#         "left": lambda: px.btnp(px.KEY_LEFT, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_LEFT, 12, 6),
#         "right": lambda: px.btnp(px.KEY_RIGHT, 12, 6) or px.btnp(px.GAMEPAD1_BUTTON_DPAD_RIGHT, 12, 6),
#         "decide": lambda: px.btnp(px.KEY_RETURN) or px.btnp(px.GAMEPAD1_BUTTON_A),
#         "cancel": lambda: px.btnp(px.KEY_ESCAPE) or px.btnp(px.GAMEPAD1_BUTTON_B),
#     }

#     @classmethod
#     def set_input_handler(cls, action: str, handler: Callable[[], bool]) -> None:
#         """入力制御の更新（外部入力モジュール利用時のコンフィグ反映を想定）"""
#         cls._input_handlers[action] = handler

#     @classmethod
#     def is_pressed(cls, action: str) -> bool:
#         """キー入力判定関数"""
#         handler = cls._input_handlers[action]
#         return handler() if handler else False
