import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,timezone
from pipelines.hrrr_live_pack import produce,validate_stage

NOW=datetime(2026,10,27,21,tzinfo=timezone.utc)
class LivePackTests(unittest.TestCase):
    def test_failure_does_not_leave_publishable_candidate(self):
        with TemporaryDirectory() as t:
            out=Path(t)/"asset"
            def invalid(dest,now):
                dest.mkdir()
                (dest/"manifest.json").write_text('{"schema":"wrong"}')
            with self.assertRaises(ValueError):produce(out,NOW,stage_fn=invalid)
            self.assertFalse(out.exists())
    def test_existing_artifacts_never_silently_overwritten(self):
        with TemporaryDirectory() as t:
            out=Path(t)/"asset"
            out.mkdir()
            with self.assertRaises(FileExistsError):produce(out,NOW)
    def test_incomplete_file_set_cannot_pass(self):
        with TemporaryDirectory() as t:
            p=Path(t)
            (p/"manifest.json").write_text('{"schema":"stormchase-hrrr-staged-pair/1","status":"staged_experimental_not_published","operational":false,"automaticallyPublished":false,"crs":"EPSG:4326","bounds":[-103,33,-94,39.4],"width":225,"height":160,"validAt":"2026-10-27T21:00:00Z","products":[]}')
            with self.assertRaises(ValueError):validate_stage(p,NOW)
if __name__=="__main__":unittest.main()
