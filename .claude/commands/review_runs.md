---
description: 投入済み実験のバリアント完了状況を集計し、ROADMAP.md と plan.md を更新する
---

`review-runs` スキルの手順に従って実行してください。

対象実験: $ARGUMENTS（指定なければ `experiments/latest` を使う）

## 手順の概要
1. `outputs/{exp}/*/completion.json` から job_id と status を収集
2. `logs/{exp}/[0-9]*/run_metadata.yaml` から Slurm レベルの状況を集計
3. GRID ステータス表（model × dataset）を生成
4. 失敗・欠損バリアントを列挙して再投入コマンドを提示
5. `experiments/{exp}/plan.md` の `## 実行状況` に追記
6. `ROADMAP.md` の該当実験行を最新状態に更新

失敗ジョブがあれば `/debug_exp` の実行を促す。**自動再投入はしない。**
