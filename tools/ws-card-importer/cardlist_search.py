#!/usr/bin/env python3
"""Utilities for scraping the official Weiss Schwarz card search endpoint."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class CardSearchError(RuntimeError):
    """Raised when the card search crawler cannot fetch or parse data."""


@dataclass
class SearchConfig:
    base_url: str
    ajax_url: str
    method: str = "POST"
    action: str | None = None
    nonce: str | None = None
    pack_param: str = "pack[]"
    lang_param: str | None = None
    keyword_param: str | None = None
    page_param: str = "page"
    per_page_param: str | None = None
    per_page: int | None = None
    additional_params: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class SearchResult:
    info: dict[str, object]
    cards: list[object]


class CardSearchClient:
    """Crawler that mimics the logic used by https://ws-tcg.com/cardlist/search/."""

    def __init__(
        self,
        base_url: str = "https://ws-tcg.com/cardlist/search/",
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url
        self.user_agent = user_agent
        self.config = self._discover_config()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_cards(self, set_code: str, language: str | None = None) -> SearchResult:
        cards = self._fetch_cards_for_set(set_code, language or "en")
        if not cards:
            raise CardSearchError(f"No cards returned for set {set_code}")
        info = self._derive_series_info(cards, set_code)
        return SearchResult(info=info, cards=cards)

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    def _discover_config(self) -> SearchConfig:
        html = self._fetch_html(self.base_url)
        parser = _SearchPageParser()
        parser.feed(html)
        parser.close()
        config = parser.to_config(self.base_url)
        if not config.ajax_url:
            raise CardSearchError("Could not determine card search AJAX endpoint")
        return config

    def _fetch_html(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html"})
        try:
            with urlopen(request, timeout=30) as response:  # nosec: B310 - trusted domain
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as error:  # pragma: no cover - network branch
            raise CardSearchError(f"HTTP error {error.code} when loading {url}") from error
        except URLError as error:  # pragma: no cover - network branch
            raise CardSearchError(f"Failed to reach {url}: {error.reason}") from error

    # ------------------------------------------------------------------
    # Request orchestration
    # ------------------------------------------------------------------
    def _fetch_cards_for_set(self, set_code: str, language: str) -> list[object]:
        config = self.config
        results: list[object] = []
        page = 1
        expected_total: int | None = None

        while page <= 200:
            payload = self._build_payload(config, set_code, language, page)
            data = self._execute_request(config.ajax_url, payload)
            items = _extract_items(data)
            if not items:
                break
            results.extend(items)

            if expected_total is None:
                expected_total = _extract_int(data, ["total", "total_count", "totalCount", "count"])
            if expected_total is not None and len(results) >= expected_total:
                break

            if not self._has_next_page(config, data, page, len(items)):
                break
            page += 1

        return results

    def _build_payload(
        self,
        config: SearchConfig,
        set_code: str,
        language: str,
        page: int,
    ) -> list[tuple[str, str]]:
        payload: list[tuple[str, str]] = list(config.additional_params)

        if config.action:
            payload.append(("action", config.action))
        if config.nonce:
            payload.append(("nonce", config.nonce))

        keyword_param = config.keyword_param or "keyword"
        payload.append((keyword_param, ""))

        lang_param = config.lang_param or "lang"
        payload.append((lang_param, language))

        per_page = config.per_page or 50
        if config.per_page_param:
            payload.append((config.per_page_param, str(per_page)))
        else:
            payload.append(("per_page", str(per_page)))
            payload.append(("limit", str(per_page)))

        page_param = config.page_param or "page"
        payload.append((page_param, str(page)))

        payload.extend(self._encode_pack_values(config.pack_param, set_code))
        return payload

    def _encode_pack_values(self, pack_param: str | None, set_code: str) -> list[tuple[str, str]]:
        if not pack_param:
            pack_param = "pack[]"
        cleaned = set_code.strip()
        values = {cleaned}
        if "/" in cleaned:
            family, suffix = cleaned.split("/", 1)
            values.add(family)
            values.add(suffix)
        result: set[tuple[str, str]] = set()
        for value in values:
            if not value:
                continue
            result.add((pack_param, value))
            if pack_param.endswith("[]"):
                result.add((pack_param[:-2], value))
            else:
                result.add((pack_param + "[]", value))
            result.add(("pack[]", value))
            result.add(("set[]", value))
            result.add(("product[]", value))
        return sorted(result)

    def _execute_request(self, url: str, payload: list[tuple[str, str]]) -> object:
        data = urlencode(payload, doseq=True).encode("utf-8")
        request = Request(
            url,
            data=data,
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": self.base_url,
            },
        )
        try:
            with urlopen(request, timeout=30) as response:  # nosec: B310 - trusted host
                text = response.read().decode("utf-8", errors="replace")
        except HTTPError as error:  # pragma: no cover - network branch
            raise CardSearchError(f"Search request failed with HTTP {error.code}") from error
        except URLError as error:  # pragma: no cover - network branch
            raise CardSearchError(f"Could not reach search endpoint: {error.reason}") from error

        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise CardSearchError(f"Invalid JSON payload from card search: {error}") from error

    def _has_next_page(
        self,
        config: SearchConfig,
        data: object,
        page: int,
        page_size: int,
    ) -> bool:
        if not isinstance(data, dict):
            return False

        for key in ("hasNext", "has_next", "next"):
            value = data.get(key)
            if isinstance(value, bool):
                return value

        pager = data.get("pager")
        if isinstance(pager, dict):
            for key in ("hasNext", "has_next"):
                flag = pager.get(key)
                if isinstance(flag, bool):
                    return flag
            max_page = _extract_int(pager, ["max", "maxPage", "pageMax", "last", "totalPages"])
            if max_page is not None:
                return page < max_page

        max_page = _extract_int(data, ["maxPage", "max_page", "total_pages", "page_max"])
        if max_page is not None:
            return page < max_page

        per_page = config.per_page or page_size
        if page_size == 0:
            return False
        if per_page and page_size < per_page:
            return False
        return True

    def _derive_series_info(self, cards: list[object], set_code: str) -> dict[str, object]:
        info: dict[str, object] = {"setCode": set_code}
        candidates: Iterable[dict[str, object]] = (
            card
            for card in cards
            if isinstance(card, dict)
        )
        first_card = next(iter(candidates), None)
        if isinstance(first_card, dict):
            meta_candidates = [first_card]
            meta = first_card.get("meta")
            if isinstance(meta, dict):
                meta_candidates.append(meta)
            for candidate in meta_candidates:
                if "name" not in info:
                    name = _first_non_empty(
                        candidate,
                        [
                            "pack_name",
                            "set_name",
                            "series_name",
                            "product_name",
                            "title",
                            "packTitle",
                        ],
                    )
                    if name:
                        info["name"] = name
                code = _first_non_empty(
                    candidate,
                    [
                        "pack_code",
                        "set_code",
                        "series_code",
                        "product_code",
                        "pack",
                    ],
                )
                if code:
                    info["setCode"] = code
                release = _first_non_empty(
                    candidate,
                    ["release", "release_date", "releaseDate", "date"],
                )
                if release:
                    info["release"] = release
        return info


class _SearchPageParser(HTMLParser):
    """Extract configuration values embedded in the card search HTML."""

    def __init__(self) -> None:
        super().__init__()
        self._in_form = False
        self._form_depth = 0
        self._ajax_url: str | None = None
        self._action: str | None = None
        self._nonce: str | None = None
        self._pack_param: str | None = None
        self._lang_param: str | None = None
        self._keyword_param: str | None = None
        self._page_param: str | None = None
        self._per_page_param: str | None = None
        self._per_page: int | None = None
        self._additional: list[tuple[str, str]] = []
        self._capture_script = False
        self._script_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr = {key: (value or "") for key, value in attrs}
        if tag == "form":
            identifier = (attr.get("id") or "") + " " + (attr.get("class") or "")
            action = attr.get("action", "")
            if "search" in identifier.lower() or "cardlist" in action:
                self._in_form = True
                self._form_depth = 1
            elif self._in_form:
                self._form_depth += 1
        elif self._in_form and tag == "input":
            name = attr.get("name")
            if not name:
                return
            value = attr.get("value", "")
            input_type = attr.get("type", "text").lower()
            if input_type == "hidden" and value:
                if "nonce" in name and not self._nonce:
                    self._nonce = value
                    return
                if name == "action" and not self._action:
                    self._action = value
                    return
                self._additional.append((name, value))
            if ("pack" in name or "series" in name) and value and "/" in value and not self._pack_param:
                self._pack_param = name
            if "lang" in name and not self._lang_param:
                self._lang_param = name
            if "keyword" in name and not self._keyword_param:
                self._keyword_param = name
            if "page" in name and not self._page_param:
                self._page_param = name
            if ("per_page" in name or "limit" in name) and not self._per_page_param:
                self._per_page_param = name
                if value.isdigit():
                    self._per_page = int(value)
        elif self._in_form and tag == "select":
            name = attr.get("name")
            if not name:
                return
            if "lang" in name and not self._lang_param:
                self._lang_param = name
            if ("per_page" in name or "limit" in name) and not self._per_page_param:
                self._per_page_param = name
        elif tag == "script":
            self._capture_script = True
            self._script_chunks = []

    def handle_endtag(self, tag: str):
        if tag == "form" and self._in_form:
            self._form_depth -= 1
            if self._form_depth <= 0:
                self._in_form = False
        elif tag == "script" and self._capture_script:
            self._capture_script = False
            self._parse_script("".join(self._script_chunks))

    def handle_data(self, data: str):
        if self._capture_script:
            self._script_chunks.append(data)

    def _parse_script(self, data: str) -> None:
        if not data.strip():
            return
        if not self._ajax_url:
            ajax_match = _regex_first(
                [
                    r"https?://[^\"']*admin-ajax\.php",
                    r"['\"](/wp/[^'\"]*admin-ajax\.php)['\"]",
                ],
                data,
            )
            if ajax_match:
                self._ajax_url = ajax_match
        if not self._action:
            value = _regex_first(
                [
                    r"action[\"']?\s*[:=]\s*[\"']([a-zA-Z0-9_:-]+)[\"']",
                    r"['\"]action['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._action = value
        if not self._nonce:
            value = _regex_first(
                [
                    r"nonce[\"']?\s*[:=]\s*[\"']([a-zA-Z0-9]+)[\"']",
                    r"['\"]nonce['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._nonce = value
        if not self._pack_param:
            value = _regex_first(
                [
                    r"pack(?:Param|Name)?[\"']?\s*[:=]\s*[\"']([^'\"]+)[\"']",
                    r"['\"]packParam['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._pack_param = value
        if not self._lang_param:
            value = _regex_first(
                [
                    r"lang(?:uage)?Param[\"']?\s*[:=]\s*[\"']([^'\"]+)[\"']",
                    r"['\"]lang['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._lang_param = value
        if not self._keyword_param:
            value = _regex_first(
                [
                    r"keywordParam[\"']?\s*[:=]\s*[\"']([^'\"]+)[\"']",
                    r"['\"]keyword['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._keyword_param = value
        if not self._page_param:
            value = _regex_first(
                [
                    r"pageParam[\"']?\s*[:=]\s*[\"']([^'\"]+)[\"']",
                    r"['\"]page['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._page_param = value
        if not self._per_page_param:
            value = _regex_first(
                [
                    r"per(?:Page|_page|PageParam)[\"']?\s*[:=]\s*[\"']([^'\"]+)[\"']",
                    r"['\"]per_page['\"]\s*:\s*['\"]([^'\"]+)['\"]",
                ],
                data,
            )
            if value:
                self._per_page_param = value
        if not self._per_page:
            per_page_str = _regex_first(
                [
                    r"per[_ ]?page[\"']?\s*[:=]\s*([0-9]+)",
                    r"['\"]per_page['\"]\s*:\s*([0-9]+)",
                ],
                data,
            )
            if per_page_str and per_page_str.isdigit():
                self._per_page = int(per_page_str)

    def to_config(self, base_url: str) -> SearchConfig:
        ajax_url = self._ajax_url or ""
        if ajax_url.startswith("/"):
            ajax_url = urljoin(base_url, ajax_url)
        return SearchConfig(
            base_url=base_url,
            ajax_url=ajax_url,
            action=self._action,
            nonce=self._nonce,
            pack_param=self._pack_param or "pack[]",
            lang_param=self._lang_param,
            keyword_param=self._keyword_param,
            page_param=self._page_param or "page",
            per_page_param=self._per_page_param,
            per_page=self._per_page,
            additional_params=self._additional,
        )


def _extract_items(data: object) -> list[object]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "cards", "list", "data", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = value.get("items") or value.get("list") or value.get("rows")
                if isinstance(nested, list):
                    return nested
    return []


def _extract_int(source: object, keys: Iterable[str]) -> int | None:
    if not isinstance(source, dict):
        return None
    for key in keys:
        value = source.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if isinstance(value, dict):
            nested = _extract_int(value, keys)
            if nested is not None:
                return nested
    return None


def _first_non_empty(source: dict[str, object], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _regex_first(patterns: Iterable[str], data: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, data)
        if match:
            group = match.group(1) if match.groups() else match.group(0)
            if group:
                return group
    return None


__all__ = [
    "CardSearchClient",
    "CardSearchError",
    "SearchConfig",
    "SearchResult",
]
