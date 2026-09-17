from enum import IntEnum, auto


# fmt: off
class Flag(IntEnum):
    CROWN        = auto()  # ラスボス対策 # 魔法ロールを下げる
    MIRROR       = auto()  # ラスボス対策 # 特殊攻撃を封じる
    CEPTER       = auto()  # ラスボス対策 # 攻撃ロールを下げる
    GRAIL        = auto()  # ラスボス対策 # HP自動回復を封じる
    JADEEYE      = auto()  # イベントA イベントD,Fの起点
    CROSS        = auto()  # イベントB イベントD,Eの起点 B+C = E
    CRYSTALROD   = auto()  # イベントC イベントE,Fの起点 C+A = F
    DRAGONFANG   = auto()  # イベントD A+Bで発生 武器イベントの条件
    TARISMAN     = auto()  # イベントE B+Cで発生 武器／防具イベントの条件
    HOLYSHROUD   = auto()  # イベントF C+Aで発生 防具イベントの条件
# fmt: on


class FlagManager:
    def __init__(self) -> None:
        self._flags: set[Flag] = set()

    def set_flag(self, flag: Flag) -> None:
        self._flags.add(flag)

    def unset_flag(self, flag: Flag) -> None:
        self._flags.discard(flag)

    def is_set(self, flag: Flag) -> bool:
        return flag in self._flags

    def check_all(self, flags: set[Flag]) -> bool:
        """複数フラグが全部立っているか(AND)"""
        return flags <= self._flags

    def check_any(self, flags: set[Flag]) -> bool:
        """複数フラグのどれかが立っているか(OR)"""
        return bool(flags & self._flags)

    # def toggle(self, flag: Flag) -> None:
    #     self.set_flag(flag, not self.get_flag(flag))

    def save_data(self) -> list[str]:
        return [flag.name for flag in self._flags]

    def load_data(self, flag_names: list[str]) -> None:
        """名前からFlagの値を引き当てる"""
        self._flags = {Flag[name] for name in flag_names if name in Flag.__members__}
