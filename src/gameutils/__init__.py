"""gameutilsパッケージ
ゲーム開発で使用頻度の高い機能をまとめたライブラリ
- ライブラリ内で使用するリソースの定義
"""

from .libconfig import ResourcePath
from .input_protocol import (
    INPUT_MODE,
    TARGET_DEVICE,
    ACTION_NAME,
    is_action_name,
    InputHandler,
)
