---
description: ROADMAP.md を全体生成・更新し、今すぐ実行すべき runx コマンドを優先順位付きで提示する
---

`roadmap` スキルの手順に従って実行してください。

## 生成内容

1. **プロジェクト全体像** — テキストフロー図（データソース → 各実験の依存関係）
2. **実験ステータス一覧** — 全実験の状態（✅/⚠️/❌/🔄）と備考
3. **投入順序** — 今すぐ実行すべき `runx` コマンドを理由コメント付きで優先順位順に列挙
4. **GRID ステータス表** — array 実験の model × dataset マトリクス
5. **依存関係図** — upstream の DAG
6. **実験詳細** — 各実験の入力・出力・GRID 数・upstream

## 特に注意する点
- `logs/{exp}/{job_id}/run_metadata.yaml` の status と `outputs/{exp}/*/completion.json` の両方を参照する
- udata / pstream のパスが `config.yml` の `upstream:` に登録されているか確認する
- 完了済み `runx` コマンドはコメントアウトして残す（履歴として）

生成後、ROADMAP.md をリポジトリルートに上書き保存する。
