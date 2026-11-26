from enum import IntEnum, auto


# fmt: off
class FlagID(IntEnum):
    CROWN        = auto() # ラスボス対策 # 魔法ロールを下げる
    MIRROR       = auto() # ラスボス対策 # 特殊攻撃を封じる
    CEPTER       = auto() # ラスボス対策 # 攻撃ロールを下げる
    GRAIL        = auto() # ラスボス対策 # HP自動回復を封じる
    JADEEYE      = auto() # イベントA イベントD,Fの起点
    CROSS        = auto() # イベントB イベントD,Eの起点 B+C = E
    CRYSTALROD   = auto() # イベントC イベントE,Fの起点 C+A = F
    DRAGONFANG   = auto() # イベントD A+Bで発生 武器イベントの条件
    TARISMAN     = auto() # イベントE B+Cで発生 武器／防具イベントの条件
    HOLYSHROUD   = auto() # イベントF C+Aで発生 防具イベントの条件
    SACREDWEAPON = auto() # イベントG D+Eで発生 武器イベント
    HOLYGUARD    = auto() # イベントH E+Fで発生 防具イベント
    SLAY_SATAN   = auto() # 魔王討伐
    BIGBAD       = auto() # 裏ボスルート開通
# fmt: on


class FlagManager:
    def __init__(self) -> None:
        self._flags: set[FlagID] = set()

    def set_flag(self, flag: FlagID) -> None:
        self._flags.add(flag)

    def unset_flag(self, flag: FlagID) -> None:
        self._flags.discard(flag)

    def is_set(self, flag: FlagID) -> bool:
        return flag in self._flags

    def check_all(self, flags: set[FlagID]) -> bool:
        """複数フラグが全部立っているか(AND)"""
        return flags <= self._flags

    def check_any(self, flags: set[FlagID]) -> bool:
        """複数フラグのどれかが立っているか(OR)"""
        return bool(flags & self._flags)

    def save_flags(self) -> list[str]:
        return [flag.name for flag in self._flags]

    def load_flags(self, flag_names: list[str]) -> None:
        """名前からFlagの値を引き当てる"""
        self._flags = {FlagID[name] for name in flag_names if name in FlagID.__members__}
