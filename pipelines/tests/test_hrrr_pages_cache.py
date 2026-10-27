import unittest
from tempfile import TemporaryDirectory
from datetime import datetime,timedelta,timezone
from hashlib import sha256
from unittest.mock import patch
from pathlib import Path
import json
from pipelines.hrrr_pages_cache import catalog,verify,update

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

def synthetic(root,valid):
    folder=root/("candidate"+valid.strftime("%Y%m%d%H"));folder.mkdir()
    blob=b"dummy-unit-test-image"
    for name in ("older.png","newer.png","difference.png","older.tif","newer.tif"):
        (folder/name).write_bytes(blob+name.encode()+valid.isoformat().encode())
    sh=lambda name:sha256((folder/name).read_bytes()).hexdigest()
    iso=lambda t:t.isoformat(timespec="seconds").replace("+00:00","Z")
    q={"schema":"stormchase-hrrr-live-candidate/1","validAt":iso(valid),
       "latestRunAt":iso(valid-timedelta(hours=2)),"sourceIndexObservedAt":iso(valid),
       "images":[{"key":k,"file":k+".png","sha256":sh(k+".png"),
                  "cog":k+".tif","cogSha256":sh(k+".tif")} for k in ("older","newer")],
       "difference":{"file":"difference.png","sha256":sh("difference.png")},
       "calibratedSevereWeatherProbability":False}
    (folder/"candidate.json").write_text(json.dumps(q))
    return folder,q

class RetentionAndRollbackTests(unittest.TestCase):
    def test_seven_publications_keep_only_six_recent_hours(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/"cache";cache.mkdir()
            first=datetime(2026,10,27,12,tzinfo=timezone.utc)
            for i in range(7):
                valid=first+timedelta(hours=i)
                folder,data=synthetic(root,valid)
                with patch("pipelines.hrrr_pages_cache.checked_candidate",return_value=data):
                    current=update(cache,folder,valid+timedelta(minutes=5))
            self.assertEqual(len(current["snapshots"]),6)
            self.assertEqual(current["snapshots"][0]["validAt"],"2026-10-27T18:00:00Z")
            self.assertFalse((cache/"runs"/"20261027T12Z").exists())
            self.assertEqual(len(verify(cache)["snapshots"]),6)
    def test_older_publication_and_revision_cannot_replace_latest(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);cache=root/"cache";cache.mkdir()
            now=datetime(2026,10,27,21,tzinfo=timezone.utc)
            folder,q=synthetic(root,now)
            with patch("pipelines.hrrr_pages_cache.checked_candidate",return_value=q):
                update(cache,folder,now)
            old_folder,old_q=synthetic(root,now-timedelta(hours=1))
            with patch("pipelines.hrrr_pages_cache.checked_candidate",return_value=old_q):
                with self.assertRaisesRegex(ValueError,"Older model valid"):
                    update(cache,old_folder,now)
            altered=json.loads(json.dumps(q));altered["images"][0]["sha256"]="b"*64
            with patch("pipelines.hrrr_pages_cache.checked_candidate",return_value=altered):
                with self.assertRaisesRegex(ValueError,"collision"):
                    update(cache,folder,now+timedelta(minutes=1))
            self.assertEqual(verify(cache)["snapshots"][0]["validAt"],"2026-10-27T21:00:00Z")

if __name__=="__main__":unittest.main()
