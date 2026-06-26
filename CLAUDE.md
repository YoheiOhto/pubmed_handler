# CLAUDE.md

このプロジェクトはSlurmベースの実験管理システム（template-daily-research-experiments）で運用されています。
詳細および共通ルールは `AGENTS.md` を参照してください。

---

## 1. オンボーディング情報 (Onboarding Information)
- **技術スタック**: Python (==3.12.*), `uv`による環境管理, Slurm / PBS (Miyabi) スケジューラ（Apptainerコンテナ）
- **ディレクトリ構成**: `experiments/` (実験コード), `outputs/` (実行出力), `logs/` (ジョブログ), `lib/` (共通ライブラリ)
- **主要コマンド**:
  - `make create_exp name=<名前>` : 新規実験作成 (ID自動採番)
  - `runx <id>` : ジョブ投入 (sbatch経由)
  - `lsx` : ジョブステータス確認
  - `make preflight` : 実験コードと設定の事前検証
  - `make log_clean` : ジョブログの整理
  - `make clean_failed` : 失敗・Orphanedログの削除
  - `uv run pytest tests/unit/ -v` : 単体テスト実行

---

## 2. コードベースから推論できないルール (Non-inferrable Rules)
- **粒度ルール: 1実験 = 1フェーズ**: 複数フェーズを1つの実験ディレクトリに混在させない。
- **実行ルール: 1ジョブ = 1原子単位**: `experiment.py` 内で可変次元をループさせない。複数組み合わせの実行は `runx --array` を使用する。
- **時間の余裕**: ジョブ投入時間 (`--time` / `DEFAULT_TIME`) は見積りの **1.5〜2倍** を確保する（TIMEOUTは全損のため）。
- **データ形式**: 前処理・実験結果等のすべての永続化データは **Parquet形式 (`.parquet`)** に統一する。
- **`udata/`データの upstream 登録**: `udata/` のデータを参照する場合は `plan.md` および `config.yml` の `upstream:` に明記する。

---

## 3. 明確な禁止事項 (Explicit Prohibitions)
- **特定ディレクトリの直接編集禁止**: `scripts/`, `tools/`, `templates/` の編集禁止。
- **データ・出力の直接書き込み禁止**: `outputs/` や `data/` への直接コピー・移動は禁止（必ず `experiment.py` から出力する）。
- **一括実行の禁止**: `for / while` ループを用いてシェル上でジョブを一括投入・実行することは禁止。
- **1ファイル200行制限**: `experiments/` または `lib/` 以下の Python コードは**1ファイル200行以内**に収める。200行超のファイルは hook によりブロックされる。
- **ブランチルール**: `main` / `master` ブランチへの直接の編集・コミット・チェックアウトは禁止。
  作業は `work/xxx` ブランチで行い、完了時は `gfinish` で集約 → ユーザーに `gpush` を依頼。
  `git checkout -b` / `git switch -c`（ブランチ作成）、`git branch -D`（強制削除）も禁止。
  `git merge` は `machine/*` ブランチ上のみ許可（`gfinish` 用）。

---

## 4. エスカレーションのルール (Escalation Rules)
- **ユーザー承認を必ず取る場面 (自律実行禁止)**:
  - ジョブの投入・キャンセル (`runx`, `sbatch`, `srun`, `cancelx`)
  - パッケージの追加・同期 (`make setup`, `make uv_sync`, `uv add`)
  - Gitリモート操作 (`git push`, `git rebase` の提案)、`gstart` / `gpush` の実行依頼
  - 複数フェーズに跨る実験、あるいは重大な設計変更
  - `outputs/` 以下の個別ディレクトリ削除、`make log_clean`、`make clean_failed`
- **エラー修正ループの上限**: ローカルでの修正・再実行ループは**最大5回**まで。5回で解決しない場合は強行せず、試行履歴を整理してユーザーに報告し、指示を仰ぐ。
