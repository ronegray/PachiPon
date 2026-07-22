# System Patterns - PachiPon

## アーキテクチャ判断
- **データ駆動設計**: ゲーム内イベントやエネミー、アイテムの定義を JSON 形式のマスタファイルに分離することで、プログラム本体を変更することなくデータ調整や追加を容易にする。
- **データ構造の一貫性**: `src/event/event_protocol.py` の `Event` dataclass の構造を忠実に反映したJSONスキーマを採用。
  - `event_type`: `EventType` Enumの文字列名（`SAFETY`, `NORMAL`, `GAMBLE`）
  - `event_id`: `EventID` Enumの文字列名（`INCREASE_HP`, `SURPRISE_BATTLE` など）
  - `event_name`: 表示用のローカライズ名
  - `event_value`: パラメータ値（ダイスの個数、固定増減数、最大脅威度など）
