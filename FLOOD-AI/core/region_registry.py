"""
RegionRegistry: manages all geographic regions being monitored.
Each region maps to a cluster of grid cells in the engine output.
Supports add_region(), get_region(), list_regions().
"""
from typing import Dict, List, Optional
from core.schemas import RegionConfig


class RegionRegistry:
    def __init__(self):
        self._regions: Dict[str, RegionConfig] = {}

    def register(self, region: RegionConfig):
        self._regions[region.region_id] = region

    def get(self, region_id: str) -> Optional[RegionConfig]:
        return self._regions.get(region_id)

    def all(self) -> List[RegionConfig]:
        return list(self._regions.values())

    def ids(self) -> List[str]:
        return list(self._regions.keys())

    def count(self) -> int:
        return len(self._regions)

    def remove(self, region_id: str):
        self._regions.pop(region_id, None)

    def clear(self):
        self._regions.clear()

    def get_downstream(self, region_id: str) -> List[RegionConfig]:
        region = self.get(region_id)
        if not region:
            return []
        return [self._regions[rid] for rid in region.downstream_ids if rid in self._regions]

    def get_upstream(self, region_id: str) -> List[RegionConfig]:
        region = self.get(region_id)
        if not region:
            return []
        return [self._regions[rid] for rid in region.upstream_ids if rid in self._regions]


registry = RegionRegistry()