# Active Context - PachiPon

## 現在の作業内容
- `src` 配下の `.py` ファイルを対象に、同様の複数クラスがある際にコンストラクタ内の記述順を検証し、同じ利用法・型の変数名について最も短い名前（`ctx`）に統一。
  - 対象：`src/menu/` 配下の全メニュークラス。
  - 結果：`MenuSelectFieldTarget` と `MenuUseItem` などの引数名 `context` を、他のメニュークラスと合わせて `ctx` に統一。
  - さらに、クラスインスタンスの変数名も `self.context` から **`self.ctx`** へと統一いたしました。
  - 記述順については、`MenuSelectFieldTarget` が親クラスの初期化前に依存データ（`self.ctx`, `self.target_type`）の代入を必須とするため、順序変更を行わずに現状維持（処理結果に影響するため）。

## 直近の決定事項
- クラス間での `EntityContext` 引数名、およびインスタンス変数名を最も短い `ctx` へ完全に統一。
- 順序変更によって動作不全（エラー）を起こす `MenuSelectFieldTarget` の `super().__init__` 呼び出し順はあえて変更しない。
