---
description: 完了した実験の結果を集計・比較し、仮説の支持/棄却を判定する（/summarize-results に委譲）
---

`summarize-results` スキルの手順に従って実行してください。

対象実験: $ARGUMENTS（指定なければ `experiments/latest` を使う）

## 実施内容
1. `outputs/{exp}/*/results.parquet`（または `results.json`）を収集
2. `plan.md` の `## 評価指標` / `## 成功基準` を参照して突合
3. バリアント間のランキング表を生成
4. 仮説の **支持 / 棄却 / 未決** を判定して `plan.md` に追記
5. `ROADMAP.md` の当該実験行を `✅ 完了` に更新
6. `sacct` でリソース実績を取得し、次回の推奨 `--time`/`--mem` を算出

複数実験を比較したい場合は実験 ID をスペース区切りで指定する（例: `/eval_summary 0001 0003 0005`）。
