"""Give the same profile control more tables, guarded by actual Linux RSS."""

import os
from pathlib import Path

from indexed_profiles import IndexedProfiles


class ResourceProfiles(IndexedProfiles):
    def __init__(self, *args, resource_statistics=None, **kwargs):
        self.resource_statistics = resource_statistics if resource_statistics is not None else {}
        self.rss_budget_bytes = 3 * 1024**3
        self.rss_checked_max_bytes = self.merge_calls = self.sample_calls = 0
        self.resource_statistics.update(rss_budget_bytes=self.rss_budget_bytes)
        self.page_bytes = os.sysconf("SC_PAGE_SIZE")
        super().__init__(*args, max_cells=10000000, max_transitions=30000000, **kwargs)

    def combine(self, left, right):
        self.merge_calls += 1
        if self.merge_calls % 4096 == 0:
            self.check_rss()
        return super().combine(left, right)

    def check_rss(self):
        rss = int(Path("/proc/self/statm").read_text().split()[1]) * self.page_bytes
        self.rss_checked_max_bytes = max(self.rss_checked_max_bytes, rss)
        self.resource_statistics.update(rss_checked_max_bytes=self.rss_checked_max_bytes)
        if rss > self.rss_budget_bytes:
            raise TimeoutError("profile RSS budget; unresolved")

    def sample(self, rng, end=None):
        self.sample_calls += 1
        if self.sample_calls % 256 == 0:
            self.check_rss()
        return super().sample(rng, end)
