import pystac_client
from dataclasses import dataclass


STAC_CATALOG = "https://planetarycomputer.microsoft.com/api/stac/v1"

SOURCE_PRIORITY = ["cop-dem-glo-30", "cop-dem-glo-90"]

SOURCE_QUALITY = {
    "cop-dem-glo-30": 0.95,
    "cop-dem-glo-90": 0.85,
}


@dataclass
class DEMSource:
    collection: str
    item_id: str
    asset_href: str
    resolution_m: int
    quality_score: float


def select_best_source(bbox: list[float]) -> DEMSource:
    client = pystac_client.Client.open(STAC_CATALOG)

    for collection in SOURCE_PRIORITY:
        try:
            results = client.search(
                bbox=bbox,
                collections=[collection],
                max_items=1
            ).item_collection()

            if len(results) == 0:
                continue

            item = results[0]
            asset_href = item.assets.get("data") or item.assets.get("elevation")

            if asset_href is None:
                continue

            resolution = 30 if "glo-30" in collection else 90

            return DEMSource(
                collection=collection,
                item_id=item.id,
                asset_href=asset_href.href,
                resolution_m=resolution,
                quality_score=SOURCE_QUALITY[collection]
            )

        except Exception:
            continue

    raise RuntimeError(f"No DEM source found for bbox {bbox}")