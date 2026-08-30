---
description: lib/REVIEW_CODES.md の「未対応」候補を選んで lib/ に実装し、重複している各 experiment.py を lib/ 参照に置き換える
---

`consolidate-lib` スキルの手順に従って実行してください。

対象候補: $ARGUMENTS（関数名を指定。未指定なら lib/REVIEW_CODES.md の未対応候補一覧を表示してユーザーに選ばせる）

## 実施内容
1. `lib/REVIEW_CODES.md` から対象候補の詳細（出現箇所・提案シグネチャ）を読む
2. 各 `experiment.py` の実装を比較して統合版シグネチャを確定
3. `lib/<module>.py` に関数を実装（1ファイル200行制限に注意）
4. 各 `experiment.py` の重複実装を `from lib.<module> import <func>` に置き換え
5. `lib/REVIEW_CODES.md` の当該候補のステータスを `✅ 対応済み` に更新
6. `git add lib/ experiments/` → `git commit -m "refactor: consolidate <func> into lib/<module>"`

**1候補ずつ実施する。** 複数指定された場合は1つ完了後に次を提案する。
