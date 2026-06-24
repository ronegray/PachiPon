from .input_protocol import INPUT_MODE, TARGET_DEVICE, ACTION_NAME

# from .input_handler import InputHandler
from .input_system import (
    initialize_input,
    keybind,
    listener,
    is_pressed,
    get_keymap,
    save_config,
    load_keyconfig,
)
