# python-automation

## プロジェクト概要

Pythonによる自動化スクリプト群を管理するリポジトリです。

## 開発環境

- Python 3.x
- 依存パッケージは `requirements.txt` で管理

## Git 運用ルール

### 基本方針

- **コードを変更するたびに必ずGitHubへプッシュすること**
- コミットは変更の単位を小さく保ち、意図が明確なメッセージを付けること

### リポジトリ

- GitHub URL: https://github.com/test-cloud-2026/python-automation.git
- デフォルトブランチ: `main`

### コミット・プッシュ手順

コードを変更した後は、毎回以下を実行すること：

```bash
git add <変更ファイル>
git commit -m "変更内容を簡潔に記述"
git push origin main
```

### コミットメッセージ規則

| プレフィックス | 用途 |
|---|---|
| `feat:` | 新機能追加 |
| `fix:` | バグ修正 |
| `refactor:` | リファクタリング |
| `docs:` | ドキュメント変更 |
| `chore:` | ビルド・設定変更 |

例: `feat: CSVファイルを自動処理するスクリプトを追加`

### ブランチ戦略

- `main`: 常に動作する状態を保つ
- 大きな機能追加は feature ブランチで開発し、動作確認後に main へマージ

## コーディング規約

- PEP 8 に準拠すること
- 関数・クラスには docstring を記載すること
- 機密情報（APIキー、パスワードなど）はコードにハードコードせず `.env` を使用し、`.gitignore` に追加すること

## .gitignore 対象

- `__pycache__/`, `*.pyc`
- `.env`
- `venv/`, `.venv/`
- `*.log`
