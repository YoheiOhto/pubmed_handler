---
description: 前回の実験状態を確認して作業を再開する（/roadmap に委譲）
---

`roadmap` スキルの手順に従って ROADMAP.md を最新化し、現在の状況を報告してください。

$ARGUMENTS に実験 ID が指定されていれば、その実験の詳細も合わせて確認する。

## 確認する内容
```bash
squeue --me
git status
git branch
```

その後 `roadmap` スキルを実行して以下を報告する：
- 実行中のジョブ（squeue の結果）
- 完了・失敗した実験（ROADMAP.md の実験ステータス一覧）
- **今すぐ実行できる runx コマンド**（投入順序セクション）

特定の実験が指定された場合は `logs/{exp}/latest/run_metadata.yaml` と `logs/{exp}/latest/slurm.out` の末尾も合わせて確認する。
