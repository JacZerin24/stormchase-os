import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from pipelines.hrrr_pages_cache import catalog,verify

class PagesCacheTests(unittest.TestCase):
    def test_empty_optional_cache_when_publisher_has_never_run(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(catalog(Path(tmp))["snapshots"],[])
    def test_rejects_malicious_paths_or_unverified_catalog(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"latest.json").write_text(json.dumps({
                "schema":"stormchase-hrrr-pages-catalog/1",
                "snapshots":[{"id":"../evil","manifest":"../evil","validAt":"2026-10-27T21:00:00Z"}],
                "forecastSkillVerified":False
            }))
            with self.assertRaises(ValueError):verify(root)
    def test_blocks_large_or_falsely_verified_cache(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"latest.json").write_text(json.dumps({
                "schema":"stormchase-hrrr-pages-catalog/1",
                "snapshots":[],"forecastSkillVerified":True}))
            with self.assertRaises(ValueError):catalog(root)
if __name__=="__main__":unittest.main()
