import os
import time
import requests
from pathlib import Path
from urllib.parse import urlparse

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
API_URL = "https://slack.com/api/emoji.list"
OUTPUT_DIR = "emojis"

HEADERS = {
    "Authorization": f"Bearer {SLACK_TOKEN}",
}

RATE_LIMIT_SLEEP = 0.3  # 秒

CONTENT_TYPE_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def fetch_emoji_list() -> dict:
    """
    Slack APIから全件の絵文字リストを取得
    """
    r = requests.get(API_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    
    if not data.get("ok"):
        raise RuntimeError(data)
    
    return data.get("emoji", {})


def resolve_alias(name: str, emoji_map: dict, visited=None) -> str:
    """
    alias を再帰的に解決し、最終的な URL を返す
    """
    if visited is None:
        visited = set()

    if name in visited:
        raise RuntimeError(f"Alias loop detected: {name}")

    if name not in emoji_map:
        raise RuntimeError(f"Emoji '{name}' not found in emoji map")

    visited.add(name)
    value = emoji_map[name]

    if value.startswith("alias:"):
        target = value.split("alias:", 1)[1]
        return resolve_alias(target, emoji_map, visited)

    return value


def get_extension(url: str) -> str:
    path = urlparse(url).path
    ext = Path(path).suffix
    return ext if ext else ".img"


def sanitize_filename(name: str) -> str:
    """ファイル名に使用できない文字を置換"""
    # Windows/Linux/Macで使用できない文字を置換
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    safe_name = name
    for char in invalid_chars:
        safe_name = safe_name.replace(char, "_")
    return safe_name


def download_image(name: str, url: str, retry_count: int = 0):
    """
    画像をダウンロードする
    
    Args:
        name: 絵文字名
        url: 画像URL
        retry_count: リトライ回数（429エラー用）
    """
    safe_name = sanitize_filename(name)

    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 429:
        if retry_count >= 5:
            raise RuntimeError(f"Rate limit exceeded after {retry_count} retries for {name}")
        time.sleep(2)
        return download_image(name, url, retry_count + 1)

    r.raise_for_status()

    content_type = r.headers.get("Content-Type", "").split(";", 1)[0]
    ext = CONTENT_TYPE_TO_EXT.get(content_type)

    # Content-Typeが不明な場合はURLから拡張子を推測
    if not ext:
        ext = get_extension(url)

    path = Path(OUTPUT_DIR) / f"{safe_name}{ext}"

    if path.exists():
        return

    with open(path, "wb") as f:
        f.write(r.content)

    time.sleep(RATE_LIMIT_SLEEP)


def main():
    if not SLACK_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN is not set")

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    emoji_map = fetch_emoji_list()
    # from itertools import islice # 10件だけ取得する場合
    # emoji_map = islice(emoji_map, 10)

    resolved = {}
    for name in emoji_map:
        try:
            url = resolve_alias(name, emoji_map)
            resolved[name] = url
        except Exception as e:
            print(f"[WARN] {name}: {e}")

    total = len(list(emoji_map))
    print(f"Total entries       : {total}")
    print(f"Resolved image URLs : {len(set(resolved.values()))}")

    total_downloads = len(resolved)
    for idx, (name, url) in enumerate(resolved.items()):
        if idx % 100 == 0 or idx == total_downloads:
            print(f"Downloading images: {idx + 1}/{total_downloads}")
        try:
            download_image(name, url)
        except Exception as e:
            print(f"[ERROR] {name}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
