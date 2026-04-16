from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.schemas.subscription import (
    SubscriptionItem,
    SubscriptionJsonUpload,
    SubscriptionRenderPayload,
    SubscriptionRenderResult,
)


@dataclass(slots=True)
class ImportedSubscription:
    url: str
    title: str | None = None


class SubscriptionFormatService:
    @staticmethod
    def _escape_xml(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def parse_upload(self, format_name: str, body: bytes) -> list[ImportedSubscription]:
        if format_name == "json":
            return self._parse_json(body)
        if format_name == "opml":
            return self._parse_opml(body)
        if format_name == "txt":
            return self._parse_txt(body)
        raise ValueError("format must be one of json, opml, txt")

    def render(self, payload: SubscriptionRenderPayload) -> SubscriptionRenderResult:
        if payload.format == "json":
            content = [item.model_dump(exclude_none=True) for item in payload.items]
            if payload.jsonp:
                return SubscriptionRenderResult(
                    media_type="application/javascript",
                    content=f"{payload.jsonp}({json.dumps(content)});",
                )
            return SubscriptionRenderResult(
                media_type="application/json",
                content=content,
            )
        if payload.format == "opml":
            return SubscriptionRenderResult(
                media_type="application/xml",
                content=self._render_opml(payload.items),
            )
        if payload.format == "txt":
            return SubscriptionRenderResult(
                media_type="text/plain; charset=utf-8",
                content=self._render_txt(payload.items),
            )
        raise ValueError("format must be one of json, opml, txt")

    def _parse_json(self, body: bytes) -> list[ImportedSubscription]:
        try:
            payload = SubscriptionJsonUpload.model_validate_json(body)
        except Exception as exc:  # pragma: no cover - pydantic error text enough
            raise ValueError("request body must be valid subscription JSON") from exc
        return [ImportedSubscription(url=url) for url in payload.to_urls()]

    def _parse_txt(self, body: bytes) -> list[ImportedSubscription]:
        text = body.decode("utf-8")
        return [
            ImportedSubscription(url=line)
            for line in (candidate.strip() for candidate in text.splitlines())
            if line
        ]

    def _parse_opml(self, body: bytes) -> list[ImportedSubscription]:
        text = body.decode("utf-8")
        if "<opml" not in text.lower():
            raise ValueError("request body must be valid OPML")
        items: list[ImportedSubscription] = []
        outline_matches = re.findall(
            r"<outline\b([^>]*)/?>",
            text,
            flags=re.IGNORECASE,
        )
        for attributes in outline_matches:
            attr_map = dict(
                re.findall(r'([A-Za-z_:][\w:.-]*)\s*=\s*"([^"]*)"', attributes)
            )
            url = attr_map.get("xmlUrl", "").strip()
            if not url:
                continue
            title = attr_map.get("title") or attr_map.get("text")
            items.append(
                ImportedSubscription(
                    url=url,
                    title=title.strip() if title else None,
                )
            )
        return items

    def _render_txt(self, items: list[SubscriptionItem]) -> str:
        if not items:
            return ""
        return "\n".join(item.url for item in items) + "\n"

    def _render_opml(self, items: list[SubscriptionItem]) -> str:
        outlines: list[str] = []
        for item in items:
            label = item.title or item.url
            attrs = [
                'type="rss"',
                f'xmlUrl="{self._escape_xml(item.url)}"',
                f'text="{self._escape_xml(label)}"',
                f'title="{self._escape_xml(label)}"',
            ]
            if item.website:
                attrs.append(f'htmlUrl="{self._escape_xml(item.website)}"')
            outlines.append(f"    <outline {' '.join(attrs)} />")
        outline_block = "\n".join(outlines)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<opml version="1.0">\n'
            "  <head>\n"
            "    <title>Malipod subscriptions</title>\n"
            "  </head>\n"
            "  <body>\n"
            f"{outline_block}\n"
            "  </body>\n"
            "</opml>"
        )
