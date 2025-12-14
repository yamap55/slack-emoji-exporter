# slack-emoji-exporter

Slackから全ての絵文字をエクスポートする

## 事前準備

- python: 3.12.3で動作確認済み

```
python --version
```

- 依存ライブラリインストール

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Slack OAuth Token取得
  - [Your Apps](https://api.slack.com/apps/) -> Create New App
    - From scratch
    - App Name: 適切な値
    - workspace: 適切なWorkspace
    - OAuth & Permissions -> Scopes -> Bot Token Scopes
    - `emoji:read` を追加
    - install workspace
    - 表示された Bot User OAuth Token をコピー

## 実行

```
export SLACK_BOT_TOKEN=xoxb-xxxxxxx
python main.py
```

※取得された絵文字はemojisフォルダに出力されます
