---
description: runx 投入直前の品質ゲート。config.yml ↔ experiment.py の整合性、シード固定、グリッド探索数、および upstream 依存関係を検証する
---

## 実行コマンド

```bash
python3 -m lib.preflight_check
```

対象実験: $ARGUMENTS（指定なければ `experiments/latest` を使う）

## チェック内容
**A. config.yml ↔ experiment.py の整合性**
- 孤立キー（config.yml にあるが experiment.py で未参照）
- 未定義参照（experiment.py が読むが config.yml にないキー）
- マジックナンバー（設定ファイル外の数値リテラル）

**B. 再現性（シード固定）**
- `random / np / torch / cuda` の seed 設定
- DataLoader の `worker_init_fn` または `generator`
- `config.yml` に `seed:` キーがあるか

## 判定
- 🔴 ブロッカーがあれば修正してから再実行
- ✅ 問題なければ「preflight OK — `runx` 投入可」と報告
