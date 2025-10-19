#!/usr/bin/env python3
"""Helpers for scraping individual Weiss Schwarz card detail pages."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener
from urllib.request import ProxyHandler

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

CARD_PAGE_URL_TEMPLATE = "https://ws-tcg.com/cardlist/?cardno={card_code}{lang_suffix}"


class CardPageFetchError(RuntimeError):
    """Raised when a card detail page cannot be downloaded or parsed."""


@dataclass
class CardPageDetails:
    """Structured data extracted from a card detail page."""

    title: str | None
    effect: str | None
    image_url: str | None


class CardPageFetcher:
    """Downloader that fetches card detail pages and extracts metadata."""

    def __init__(self, *, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self.user_agent = user_agent
        self._cache: dict[tuple[str, str], CardPageDetails] = {}
        # Explicitly disable proxies so corporate MITM proxies do not break scraping.
        self._opener = build_opener(ProxyHandler({}))

    def fetch(self, card_code: str, *, language: str = "ja") -> CardPageDetails:
        key = (card_code, language)
        if key in self._cache:
            return self._cache[key]

        url = build_card_page_url(card_code, language)
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://ws-tcg.com/cardlist/search/",
            },
        )
        try:
            with self._opener.open(request, timeout=30) as response:  # nosec: B310 - trusted host
                html_text = response.read().decode("utf-8", errors="replace")
        except HTTPError as error:  # pragma: no cover - depends on remote server
            raise CardPageFetchError(f"HTTP {error.code} when fetching {url}") from error
        except URLError as error:  # pragma: no cover - network branch
            raise CardPageFetchError(f"Failed to fetch {url}: {error.reason}") from error

        title = extract_title(html_text)
        effect = extract_effect(html_text)
        image_url = extract_image_url(html_text)
        details = CardPageDetails(title=title, effect=effect, image_url=image_url)
        if not any((title, effect, image_url)):
            raise CardPageFetchError("Card detail page did not contain parsable data")
        self._cache[key] = details
        return details


def build_card_page_url(card_code: str, language: str) -> str:
    encoded_code = quote(card_code, safe="/-")
    lang = (language or "").strip().lower()
    if not lang or lang in {"ja", "jp", "japanese"}:
        lang_suffix = "&l"
    else:
        lang_suffix = "&l=" + quote(lang, safe="")
    return CARD_PAGE_URL_TEMPLATE.format(card_code=encoded_code, lang_suffix=lang_suffix)


def extract_title(html_text: str) -> str | None:
    patterns = [
        r"<th[^>]*>\s*カード名\s*</th>\s*<td[^>]*>(.*?)</td>",
        r"<div[^>]+class=\"[^\"]*(?:cardDetail__name|cardname|card_name)[^\"]*\"[^>]*>(.*?)</div>",
        r"<p[^>]+class=\"[^\"]*(?:cardDetail__name|cardname|card_name)[^\"]*\"[^>]*>(.*?)</p>",
        r"<meta[^>]+property=\"og:title\"[^>]+content=\"([^\"]+)\"",
    ]
    return _first_clean_match(patterns, html_text)


def extract_effect(html_text: str) -> str | None:
    patterns = [
        r"<th[^>]*>\s*カードテキスト\s*</th>\s*<td[^>]*>(.*?)</td>",
        r"<th[^>]*>\s*テキスト\s*</th>\s*<td[^>]*>(.*?)</td>",
        r"<div[^>]+class=\"[^\"]*(?:cardDetail__text|cardtext|card_txt|textArea)[^\"]*\"[^>]*>(.*?)</div>",
        r"<section[^>]+class=\"[^\"]*cardText[^\"]*\"[^>]*>(.*?)</section>",
        r"<p[^>]+class=\"[^\"]*(?:cardDetail__text|cardtext|card_txt|textArea)[^\"]*\"[^>]*>(.*?)</p>",
    ]
    text = _first_clean_match(patterns, html_text)
    if not text:
        return None
    # Normalise consecutive ability separators and whitespace.
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_image_url(html_text: str) -> str | None:
    patterns = [
        r"<meta[^>]+property=\"og:image\"[^>]+content=\"([^\"]+)\"",
        r"<img[^>]+src=\"([^\"]+)\"[^>]+class=\"[^\"]*(?:cardImage|card-image|card_img)[^\"]*\"",
        r"<img[^>]+class=\"[^\"]*(?:cardImage|card-image|card_img)[^\"]*\"[^>]+src=\"([^\"]+)\"",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
        if match:
            return _normalise_url(match.group(1))
    return None


def _first_clean_match(patterns: list[str], html_text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
        if match:
            raw = match.group(1)
            cleaned = _clean_html(raw)
            if cleaned:
                return cleaned
    return None


def _clean_html(snippet: str) -> str:
    snippet = snippet.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    snippet = re.sub(r"<(script|style)[^>]*>.*?</\\1>", "", snippet, flags=re.IGNORECASE | re.DOTALL)
    snippet = re.sub(r"<[^>]+>", "", snippet)
    text = html.unescape(snippet)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _normalise_url(url: str) -> str:
    if not url:
        return url
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    return url


__all__ = [
    "CardPageDetails",
    "CardPageFetchError",
    "CardPageFetcher",
    "build_card_page_url",
]
