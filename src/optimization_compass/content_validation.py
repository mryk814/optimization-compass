from __future__ import annotations

from optimization_compass.content_models import ContentPage


def require_published_method_references(pages: list[ContentPage], known_methods: set[str]) -> None:
    for page in pages:
        if page.kind == "method" and page.method_id not in known_methods:
            raise ValueError(
                f"{page.content_id} references unknown canonical method: {page.method_id}"
            )
