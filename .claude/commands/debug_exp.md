---
description: 失敗した実験のトリアージ・根本原因の特定・修正・記録を行う
---

`debug-experiment` スキルの手順に従って実行してください。

対象実験: $ARGUMENTS（指定なければ `experiments/latest` を使う）

## 調査の流れ

### Step 0. クイックトリアージ（30秒）
`outputs/{exp}/*/completion.json` の job_id から状況を把握し、以下で方針を決める：

| 状況 | → |
|------|---|
| TIMEOUT / OOM | `run_slurm.sh` の `--time`/`--mem` を1.5倍に修正 |
| slurm.out なし | `run_slurm.sh` の `#SBATCH` 設定を確認 |
| Python エラー | Step 1 へ（詳細調査） |

### Step 1. 出力 → metadata → ログ → 実行コマンドの順で辿る
```
outputs/{exp}/{variant}/completion.json  ← job_id
        ↓
logs/{exp}/{job_id}/
    ├── command.sh        ← ★ 最初に確認（実際に渡された引数）
    ├── run_metadata.yaml ← status / exit_code
    └── slurm.out         ← エラーログ
```

### Step 2–5. 仮説消去
リソース → 環境 → データ → コード → 設定の順で原因を絞り込む。

### Step 6. 修正・記録
- `edit_file` で修正（1ファイル・1箇所ずつ）
- `experiments/{exp}/plan.md` にデバッグ記録を追記
- `ROADMAP.md` の備考列を更新
- 修正後の `runx` コマンドを提示（**自動再投入はしない**）
