from dataclasses import dataclass  # , field
from enum import IntEnum, auto


class EventType(IntEnum):
    """イベントの種類
    - NORMAL：ノーマル（中マイナスと中プラスが半々、効果はそれなり
    - SAFETY：セーフティ（弱マイナス１つ、他は弱プラス
    - GAMBLE：ハイリターン（強プラス１つ、他は強マイナス
    - BATTLE：ボス戦
    """

    NORMAL = auto()
    SAFETY = auto()
    GAMBLE = auto()
    BATTLE = auto()


class EventID(IntEnum):
    """イベント内容の一覧"""

    # good
    INCREASE_HP = auto()  # HP増
    INCREASE_MP = auto()  # MP増
    INCREASE_GOLD = auto()  # おかね増
    INCREASE_FOOD = auto()  # 食糧増
    FLGEVENT1_A = auto()  # フラグイベントStep1
    FLGEVENT1_B = auto()  # フラグイベントStep1
    FLGEVENT1_C = auto()  # フラグイベントStep1
    GET_POTION = auto()  # 低級消耗品増
    MEET_ALLY = auto()  # 仲間ゲット
    FLGEVENT2_D = auto()  # フラグイベントStep2
    FLGEVENT2_E = auto()  # フラグイベントStep2
    FLGEVENT2_F = auto()  # フラグイベントStep2
    GET_HIPOTION = auto()  # 高級消耗品増
    FLGEVENT3_G = auto()  # フラグイベントStep3
    FLGEVENT3_H = auto()  # フラグイベントStep3

    # bad
    DECREASE_HP = auto()  # HP減
    DECREASE_MP = auto()  # MP減
    DECREASE_GOLD = auto()  # おかね減
    DECREASE_FOOD = auto()  # 食糧減
    LOST_POTION = auto()  # 低級消耗品減
    SURPRISE_BATTLE = auto()  # 強制戦闘
    LOST_HIPOTION = auto()  # 高級消耗品減

    # boss
    CROWN = auto()  # 宝冠の守護者　破魔に弱い
    MIRROR = auto()  # 神鏡の守護者　衝撃に弱い
    CEPTER = auto()  # 王笏の守護者　精神に弱い
    GRAIL = auto()  # 聖杯の守護者　呪毒に弱い
    SATAN = auto()  # 魔王
    KING = auto()  # 人間の王


@dataclass
class Event:
    """データファイルから読み込むイベント情報定義"""

    event_type: EventType
    event_id: EventID
    event_name: str  # イベント表示名
    event_value: int  # ダイス値や脅威度等の値
