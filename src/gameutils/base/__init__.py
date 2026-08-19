"""gameutils.baseパッケージ
gameutilsライブラリ内でも使用される共通基本機能
"""

# from .asset import AssetID, AssetManager
from .file import (
    check_file,
    read_string,
    write_string,
    read_json,
    write_json,
    read_bin,
    write_bin,
)
from .input import (
    INPUT_MODE,
    TARGET_DEVICE,
    ACTION_NAME,
    initialize_input,
    keybind,
    listener,
    is_pressed,
    get_keymap,
    save_config,
    load_keyconfig,
)
from .text import FONT_SIZE_NAME, FontManager, shadowed_text
from .sound import SoundManager, ToneManager, BGM_CHANNELS, SE_INSTANT_CH, SE_SUSTAIN_CH
