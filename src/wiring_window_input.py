"""
アプリケーション層専用モジュール。

window パッケージ（WindowInputHandler / Menu 等）は input_system を知らず、
input_system は window パッケージを知らない。両者の存在を知って良いのは
「利用する立場」であるアプリケーション層のみ、という位置づけで本モジュールを置く。

役割:
- Menu側のアクション語彙（up/down/left/right/decide/cancel/action/menu/start/select/LS/RS）
  と input_system側のACTION_NAME語彙（同上、ただしaction→other1, menu→other2）の対応表を
  一箇所に集約する。
- is_pressed() を薄くラップし、mode をそのまま透過するクロージャを生成する。
  is_pressedはmodeが渡されるたびに最新の_bindings_pad/_bindings_kbdを参照するため、
  設定画面でのキー再割当(keybind/unbind_action)が起きても本モジュールの再呼び出しは不要。

呼び出しタイミング:
- ゲーム起動時、load_keyconfig()（または initialize_input()）の直後に1回呼べば良い。
  以降、キーコンフィグ画面でのリバインドがあっても再配線は不要。

# NOTE: 実際のパッケージ構成に合わせて import パスを調整すること。
"""
from typing import get_args
from gameutils import INPUT_MODE, ACTION_NAME, InputHandler
from gameutils.lib import WindowInputHandler
from gameutils.base import is_pressed

# # Menu側のアクション名 → input_system側のACTION_NAMEの対応表
# _ACTION_NAME_MAP: dict[str, ACTION_NAME] = {
#     "up": "up",
#     "down": "down",
#     "left": "left",
#     "right": "right",
#     "decide": "decide",
#     "cancel": "cancel",
#     "action": "action",
#     "menu": "menu",
#     "start": "start",
#     "select": "select",
#     "LS": "LS",
#     "RS": "RS",
# }


def _adapt(action_name: ACTION_NAME) -> InputHandler:
    """is_pressedをmode透過のまま呼び出す薄いクロージャを生成する

    ここでキー割当の内容そのものは一切保持しない。呼ばれるたびに
    is_pressed() 経由で最新の _bindings_pad / _bindings_kbd を参照するため、
    リバインド後の再配線が不要になる。
    """
    # input_system_action = _ACTION_NAME_MAP[menu_action_name]
    action_default_mode = "hold" if action_name in ("up", "down", "left", "right") else "once"

    def handler(mode: INPUT_MODE = action_default_mode) -> bool:
        return is_pressed(action_name, mode)

    return handler


def wire_window_input_from_input_system() -> None:
    """input_system経由の判定へ切り替える

    ゲーム起動時、load_keyconfig()（または initialize_input()）の直後に
    1回呼び出せば良い。設定画面でのキー再割当があっても、
    このメソッドを再度呼び出す必要はない。
    """
    WindowInputHandler.update_window_input({name: _adapt(name) for name in get_args(ACTION_NAME)})
