# Active Context - PachiPon

## 現在の作業内容
- `src/event/event_protocol.py` の定義に従い、`doc/仕様.md` の「ランダムイベントのタイプ」および「ランダムイベントの内容」を定義した `src/assets/data/event_master.json` を作成する。

## 直近の決定事項
- `event_master.json` は `src/assets/data/event_master.json` として作成する。
- JSONフォーマットは `Event` データクラス（`event_type`, `event_id`, `event_name`, `event_value`）に正確に一致させる。
- `event_type` および `event_id` は文字列で定義し、読みやすさと管理性を高める。
- `event_value` にはダイスの個数や最大脅威度などの整数値を格納する。
