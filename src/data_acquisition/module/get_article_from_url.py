import asyncio
import aiohttp
import trafilatura

from bs4 import BeautifulSoup
from datetime import datetime
from readability import Document

from typing import List, Dict, Any


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

async def fetch_full_article_by_url(
    url: str,
    timeout: int = 8,
    min_body_length: int = 50,
) -> Dict[str, Any]:
    """
    根据 URL 抓取新闻正文（直抓 + archive.ph 兜底）

    返回字段：
    - success: bool
    - title: str | None
    - body: str | None
    - authors: list[str]
    - published_at: datetime | None
    - method: str | None
    - confidence: float
    - error: str | None
    """

    result = {
        "success": False,
        "title": None,
        "body": None,
        "authors": [],
        "published_at": None,
        "method": None,
        "confidence": 0.0,
        "error": None,
    }

    async def _download(target_url: str) -> str | None:
        try:
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                async with session.get(target_url, timeout=timeout) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.text()
        except Exception:
            return None

    def _extract(html: str) -> tuple[str | None, float, str | None]:
        """
        返回 (body, confidence, method)
        """
        # --- trafilatura ---
        try:
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
            )
            if text and len(text.strip()) >= min_body_length:
                return text.strip(), 0.9, "direct"
        except Exception:
            pass

        # --- readability 兜底 ---
        try:
            doc = Document(html)
            content_html = doc.summary(html_partial=True)
            soup = BeautifulSoup(content_html, "lxml")
            text = soup.get_text(separator="\n").strip()
            if len(text) >= min_body_length:
                return text, 0.7, "direct+readability"
        except Exception:
            pass

        return None, 0.0, None

    # ======================
    # 1️⃣ 直抓
    # ======================
    html = await _download(url)
    if html:
        body, confidence, method = _extract(html)
        if body:
            result["body"] = body
            result["confidence"] = confidence
            result["method"] = method
            result["success"] = True
        else:
            result["error"] = "direct_extract_failed"
    else:
        result["error"] = "direct_fetch_failed"

    # ======================
    # 2️⃣ archive.ph 兜底
    # ======================
    if not result["success"]:

        archive_url = f"https://archive.ph/{url}"
        archive_html = await _download(archive_url)

        if archive_html and "wip" not in archive_url:
            body, confidence, method = _extract(archive_html)
            if body:
                result["body"] = body
                result["confidence"] = confidence * 0.85
                result["method"] = "archive"
                result["success"] = True
                result["error"] = None
        else:
            result["error"] = "archive_unavailable"

    # ======================
    # 3️⃣ title / author 提取
    # ======================
    if result["success"]:
        soup = BeautifulSoup(html or archive_html, "lxml")

        # title
        if soup.title and soup.title.string:
            result["title"] = soup.title.string.strip()

        # author（启发式）
        for key in ["author", "byline", "parsely-author"]:
            meta = soup.find("meta", attrs={"name": key})
            if meta and meta.get("content"):
                result["authors"] = [
                    a.strip() for a in meta["content"].split(",") if a.strip()
                ]
                break

    return result


if __name__ == "__main__":
    import asyncio

    test_url = "https://www.bloomberg.com/news/articles/2026-01-21/ex-bridgewater-executive-is-hired-by-florida-based-cv-advisors"
    async def main():
        article = await fetch_full_article_by_url(test_url)
        print(article)

    asyncio.run(main())