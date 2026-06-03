#!/usr/bin/env python3
"""
books.toscrape.com から書籍タイトル・価格・在庫状況を収集し Markdown に保存する
"""

import logging
import random
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
USER_AGENT = "python-scraper/1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraping.log", encoding="utf-8"),
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


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"接続エラー: {url} - {e}")
        sys.exit(1)
    except requests.exceptions.Timeout as e:
        logger.error(f"タイムアウトエラー: {url} - {e}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPエラー: {url} - {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"リクエストエラー: {url} - {e}")
        sys.exit(1)


def random_wait() -> None:
    wait = random.uniform(1, 3)
    logger.info(f"  次のリクエストまで {wait:.2f} 秒待機")
    time.sleep(wait)


def parse_books(soup: BeautifulSoup) -> List[Dict[str, str]]:
    books = []
    for article in soup.select("article.product_pod"):
        title_tag = article.select_one("h3 > a")
        price_tag = article.select_one("p.price_color")
        avail_tag = article.select_one("p.availability")

        books.append(
            {
                "title": title_tag["title"] if title_tag else "N/A",
                "price": price_tag.get_text(strip=True) if price_tag else "N/A",
                "availability": avail_tag.get_text(strip=True) if avail_tag else "N/A",
            }
        )
    return books


def next_page_url(soup: BeautifulSoup, current_url: str) -> Optional[str]:
    btn = soup.select_one("li.next > a")
    if not btn:
        return None
    return urljoin(current_url, btn["href"])


def save_markdown(books: List[Dict[str, str]], path: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 書籍リスト",
        "",
        f"取得日時: {now}  ",
        f"総件数: {len(books)} 件  ",
        "",
        "| タイトル | 価格 | 在庫状況 |",
        "|---|---|---|",
    ]
    for b in books:
        title = b["title"].replace("|", "｜")
        lines.append(f"| {title} | {b['price']} | {b['availability']} |")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"Markdown に保存しました: {path}")


def main() -> None:
    logger.info("スクレイピングを開始します")

    rp = load_robots(BASE_URL)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    all_books: List[Dict[str, str]] = []
    current_url: Optional[str] = BASE_URL
    page_num = 1

    while current_url:
        if not can_fetch(rp, current_url):
            logger.warning(f"robots.txt によりアクセス禁止のためスキップ: {current_url}")
            break

        logger.info(f"ページ {page_num} を取得: {current_url}")
        soup = fetch_page(current_url, session)
        if soup is None:
            break

        books = parse_books(soup)
        all_books.extend(books)
        logger.info(f"  {len(books)} 件取得（累計: {len(all_books)} 件）")

        current_url = next_page_url(soup, current_url)
        page_num += 1

        if current_url:
            random_wait()

    logger.info(f"全 {len(all_books)} 件の書籍情報を取得しました")

    date_str = datetime.now().strftime("%Y%m%d")
    output_path = f"books_{date_str}.md"
    save_markdown(all_books, output_path)

    logger.info("完了")


if __name__ == "__main__":
    main()
