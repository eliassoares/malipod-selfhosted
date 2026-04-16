from __future__ import annotations

from app.schemas.subscription import SubscriptionItem, SubscriptionRenderPayload
from app.services.subscription_formats import SubscriptionFormatService


def test_subscription_format_service_renders_jsonp_payload() -> None:
    service = SubscriptionFormatService()

    rendered = service.render(
        SubscriptionRenderPayload(
            items=[SubscriptionItem(url="https://example.com/feed.xml", title="Feed")],
            format="json",
            jsonp="callback",
        )
    )

    assert rendered.media_type == "application/javascript"
    assert rendered.content == (
        'callback([{"url": "https://example.com/feed.xml", "title": "Feed"}]);'
    )


def test_subscription_format_service_renders_plaintext_in_order() -> None:
    service = SubscriptionFormatService()

    rendered = service.render(
        SubscriptionRenderPayload(
            items=[
                SubscriptionItem(url="https://example.com/one.xml"),
                SubscriptionItem(url="https://example.com/two.xml"),
            ],
            format="txt",
        )
    )

    assert rendered.media_type == "text/plain; charset=utf-8"
    assert (
        rendered.content == "https://example.com/one.xml\nhttps://example.com/two.xml\n"
    )


def test_subscription_format_service_parses_opml_outlines() -> None:
    service = SubscriptionFormatService()

    parsed = service.parse_upload(
        "opml",
        b"""<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <body>
    <outline text="Feed One" xmlUrl="https://example.com/feed-1.xml" />
    <outline title="Feed Two" xmlUrl="https://example.com/feed-2.xml" />
  </body>
</opml>
""",
    )

    assert [item.url for item in parsed] == [
        "https://example.com/feed-1.xml",
        "https://example.com/feed-2.xml",
    ]
    assert [item.title for item in parsed] == ["Feed One", "Feed Two"]
