# Progress - PachiPon

## 完了済み
- `src` 配下（`gameutils` 除く）の数値キーを持つ辞書の調査と抽出、および `数値キー辞書.md` への書き出し。
- `src` 配下の複数クラス（メニュークラス群）における変数名とコンストラクタ記述順の調査・統一。
  - `MenuSelectFieldTarget`, `MenuUseItem`, `MenuBattle`, `MenuField`, `MenuSelectItemCategory`, `MenuSelectSkillBattle`, `MenuSelectSkillField` 等のすべてのメニュークラスにおいて、 `EntityContext` の引数名およびインスタンス変数名を `ctx` / `self.ctx` に完全に統一。
  - 各メニュークラスのコンストラクタ記述順の妥当性を評価。順序変更により動作が壊れる `MenuSelectFieldTarget` については、順序を変更しない判断（現状維持）を決定・実装。

## 未着手
- なし

## 既知の問題
- なし
