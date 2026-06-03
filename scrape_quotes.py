#!/usr/bin/env python3
"""
Playwright を使って quotes.toscrape.com/js から名言・著者名を収集する
"""

import logging
import random
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://quotes.toscrape.com/"
START_PATH = "/js"
USER_AGENT = "python-scraper/1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraping_quotes.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def load_robots(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    rp.set_url(robots_url)
    try:
        rp.read()
        logger.info(f"robots.txt を読み込みました: {robots_url}")
    except Exception as e:
        logger.warning(f"robots.txt の読み込みに失敗しました（アクセス許可として続行）: {e}")
    return rp


def can_fetch(rp: RobotFileParser, url: str) -> bool:
    return rp.can_fetch(USER_AGENT, url)


def random_wait() -> None:
    wait = random.uniform(1, 3)
    logger.info(f"  次のリクエストまで {wait:.2f} 秒待機")
    time.sleep(wait)


def parse_quotes(page: Page) -> List[Dict[str, str]]:
    """JS レンダリング完了を待ってから名言を抽出する"""
    page.wait_for_selector("div.quote", timeout=15000)
    quotes = []
    for el in page.query_selector_all("div.quote"):
        text_el = el.query_selector("span.text")
        author_el = el.query_selector("small.author")
        quotes.append(
            {
                "text": text_el.inner_text() if text_el else "N/A",
                "author": author_el.inner_text() if author_el else "N/A",
            }
        )
    return quotes


def next_page_url(page: Page) -> Optional[str]:
    btn = page.query_selector("li.next > a")
    if not btn:
        return None
    href = btn.get_attribute("href")
    return urljoin(BASE_URL, href) if href else None


def save_markdown(quotes: List[Dict[str, str]], path: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 名言リスト",
        "",
        f"取得日時: {now}  ",
        f"総件数: {len(quotes)} 件  ",
        "",
    ]
    for i, q in enumerate(quotes, 1):
        lines += [
            f"## {i}. {q['author']}",
            "",
            f"> {q['text']}",
            "",
        ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"Markdown に保存しました: {path}")


def main() -> None:
    logger.info("スクレイピングを開始します")

    rp = load_robots(BASE_URL)
    start_url = urljoin(BASE_URL, START_PATH)

    if not can_fetch(rp, start_url):
        logger.error(f"robots.txt によりアクセスが禁止されています: {start_url}")
        sys.exit(1)

    date_str = datetime.now().strftime("%Y%m%d")
    md_path = f"quotes_{date_str}.md"
    png_path = f"quotes_{date_str}.png"

    all_quotes: List[Dict[str, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        current_url: Optional[str] = start_url
        page_num = 1
        screenshot_taken = False

        while current_url:
            if not can_fetch(rp, current_url):
                logger.warning(f"robots.txt によりアクセス禁止のためスキップ: {current_url}")
                break

            logger.info(f"ページ {page_num} を取得: {current_url}")

            try:
                page.goto(current_url, wait_until="networkidle", timeout=30000)
            except PlaywrightError as e:
                logger.error(f"接続エラー: {current_url} - {e}")
                browser.close()
                sys.exit(1)

            # 1ページ目のみスクリーンショット（JS レンダリング完了後）
            if not screenshot_taken:
                try:
                    page.wait_for_selector("div.quote", timeout=15000)
                except PlaywrightError:
                    pass
                page.screenshot(path=png_path, full_page=True)
                logger.info(f"スクリーンショットを保存しました: {png_path}")
                screenshot_taken = True

            try:
                quotes = parse_quotes(page)
            except PlaywrightError as e:
                logger.error(f"パースエラー（セレクタが見つかりません）: {e}")
                browser.close()
                sys.exit(1)

            all_quotes.extend(quotes)
            logger.info(f"  {len(quotes)} 件取得（累計: {len(all_quotes)} 件）")

            current_url = next_page_url(page)
            page_num += 1

            if current_url:
                random_wait()

        browser.close()

    logger.info(f"全 {len(all_quotes)} 件の名言を取得しました")
    save_markdown(all_quotes, md_path)
    logger.info("完了")


if __name__ == "__main__":
    main()
