import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from pipelines.hrrr_inventory import iso
from pipelines.hrrr_stage import check_pair,stage

NOW=datetime(2026,10,27,19,38,tzinfo=timezone.utc)
VALID=datetime(2026,10,27,20,tzinfo=timezone.utc)
def inventory(valid=VALID,checked=NOW):
    runs=[]
    for lead in (3,2):
        init=valid-timedelta(hours=lead)
        runs.append({"state":"inventory_observed","field":"TMP:2 m above ground",
                     "runAt":iso(init),"leadHours":lead,"validAt":iso(valid),
                     "estimatedMessageBytes":1000000,"byteStart":100,
                     "byteEndInclusive":1000099,"source_index":"https://example.test/file.idx"})
    return {"schema":"stormchase-hrrr-inventory/1",
            "status":"pair_inventory_observed","checkedAt":iso(checked),
            "selected":{"validAt":iso(valid),"runs":runs}}

class StagingTests(unittest.TestCase):
    def test_two_cycles_one_valid_time(self):
        valid,runs=check_pair(inventory(),NOW)
        self.assertEqual(valid,iso(VALID))
        self.assertEqual([r["leadHours"] for r in runs],[3,2])
    def test_stale_or_no_inventory_fails_closed(self):
        with self.assertRaises(ValueError):check_pair({"status":"no_verified_pair"},NOW)
        with self.assertRaises(ValueError):
            check_pair(inventory(valid=VALID-timedelta(hours=4)),NOW)
        with self.assertRaises(ValueError):
            check_pair(inventory(checked=NOW-timedelta(minutes=15)),NOW)
    def test_future_lookup_not_acceptable(self):
        with self.assertRaises(ValueError):
            check_pair(inventory(checked=NOW+timedelta(minutes=30)),NOW)
    def test_wrong_lead_rejected(self):
        bad=inventory();bad["selected"]["runs"][1]["leadHours"]=4
        with self.assertRaises(ValueError):check_pair(bad,NOW)
    def test_bad_byte_offset_never_reaches_renderer(self):
        with TemporaryDirectory() as tmp:
            def bad_acquire(run,lead,param,level,path):
                return {"status":"transport_verified_not_decoded",
                        "sha256":"a"*64,
                        "forecast_reference_at":iso(run),
                        "forecast_lead_hours":lead,
                        "valid_at":iso(run+timedelta(hours=lead)),
                        "byte_start":101,"byte_end_inclusive":1000099,"bytes":1000000}
            def forbidden(*args):raise AssertionError("No render on changed source")
            p=Path(tmp)/"out"
            with self.assertRaisesRegex(ValueError,"changed between"):
                stage(p,NOW,discover_fn=lambda now:inventory(),
                      acquire_fn=bad_acquire,render_fn=forbidden)
            self.assertFalse(p.exists())
    def test_no_output_overwrite(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"out";p.mkdir()
            with self.assertRaises(FileExistsError):stage(p,NOW)
if __name__=="__main__":unittest.main()
