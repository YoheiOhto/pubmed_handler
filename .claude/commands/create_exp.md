---
description: 承認済みの計画書をもとに実験ディレクトリを作成し、計画書を dir 配下へ移動して実装を開始する
---

前提: `/plan-experiment` で `experiments/<NNNN>_<name>.md` の計画書が作成・承認済みであること。
未作成なら先に `/plan-experiment $ARGUMENTS` を案内する。

## ステップ1: 実験ディレクトリを作成
```bash
make create_exp name=$ARGUMENTS
```

## ステップ2: 作成されたディレクトリを特定
```bash
CREATED=$(basename "$(readlink -f experiments/latest)")
echo "created: $CREATED"
```

## ステップ3: 計画書を dir 配下へ移動（plan.md にリネーム）
top-level の計画書（`experiments/<NNNN>_<name>.md`）を、作成された dir 配下へ移す。
ID がずれても名前一致で拾えるようにする。
```bash
SAFE_NAME=$(echo "$ARGUMENTS" | tr ' /' '__' | tr -cd '[:alnum:]_-')
PLAN=$(ls experiments/*_"${SAFE_NAME}".md 2>/dev/null | head -n1)
if [ -n "$PLAN" ]; then
  mv "$PLAN" "experiments/${CREATED}/plan.md"
  echo "moved plan -> experiments/${CREATED}/plan.md"
else
  echo "⚠ 計画書が見つかりません。/plan-experiment を先に実行してください。"
fi
```

## ステップ4: plan.md に沿って実装
`experiments/${CREATED}/` の `experiment.py` / `config.yml` / `run_slurm.sh` を計画書どおりに実装する。
- plan.md の「実行計画」「リソース見積」を run_slurm.sh に反映する（--time は余裕を持たせる）。
- 実装の際は、Pythonコードが1ファイル200行を超えないように注意する（超えそうな場合は `lib/` への共通化を行う）。