"""
イベント情報管理モジュール
- マスタ定義ファイルの情報を保持
- 指定したEventTypeとEventIDのイベント情報を提供
"""

import logging
from gameutils.base import check_file, read_json
from assets.asset_map import AssetID, AssetMap
from .event_protocol import EventType, EventID, Event

# ロギング設定
logger = logging.getLogger(__name__)


class EventManager:
    _master_def: dict[tuple[EventType, EventID], Event]
    _master_list: list[Event]

    def __init__(self) -> None:
        """JSONファイルを読み込んでイベント定義を初期化する"""
        path_check = AssetMap.get_assetpath(AssetID.DATA_EVENT)
        json_path = check_file(path_check)
        if json_path:
            json_data = read_json(json_path)
        else:
            errmsg = "イベント定義データファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        EventManager._master_def = {}
        EventManager._master_list = []

        for item in json_data:
            type_str = item.get("event_type")
            id_str = item.get("event_id")

            if hasattr(EventType, type_str) and hasattr(EventID, id_str):
                event_type = EventType[type_str]
                event_id = EventID[id_str]

                event = Event(
                    event_type=event_type,
                    event_id=event_id,
                    event_name=item.get("event_name", "Unknown"),
                    event_value=item.get("event_value", 0),
                )

                EventManager._master_def[(event_type, event_id)] = event
                EventManager._master_list.append(event)
            else:
                if not hasattr(EventType, type_str):
                    logger.warning(f"Warning: EventType.{type_str} is not defined.")
                if not hasattr(EventID, id_str):
                    logger.warning(f"Warning: EventID.{id_str} is not defined.")

    @classmethod
    def get_def(cls, event_type: EventType, event_id: EventID) -> Event | None:
        """指定されたEventTypeとEventIDのイベント定義を取得する"""
        return cls._master_def.get((event_type, event_id))

    @classmethod
    def get_all_definitions(cls) -> list[Event]:
        """すべてのイベント定義を取得する"""
        return cls._master_list

    @classmethod
    def get_defs_by_type(cls, event_type: EventType) -> list[Event]:
        """指定されたイベント種類のすべてのイベント定義を取得する"""
        return [evt for evt in cls._master_list if evt.event_type == event_type]
