import unittest
from datetime import datetime,timezone,timedelta
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

from pipelines.hrrr_inventory import (
    discover,inspect_index,target_valid_times,iso,INDEX_MAX_BYTES
)

RUN=datetime(2026,10,27,18,tzinfo=timezone.utc)
def ok(run,lead):
    return {"state":"inventory_observed","runAt":iso(run),"leadHours":lead,
            "validAt":iso(run+timedelta(hours=lead)),"estimatedMessageBytes":800000}
def notfound(run,lead):
    return {"state":"not_found","runAt":iso(run),"leadHours":lead}

class FakeResponse:
    status=200
    headers=Message()
    def __init__(self,text):
        self.body=text.encode()
        self.headers=Message()
        self.headers["Last-Modified"]="Tue, 27 Oct 2026 19:00:00 GMT"
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.body[:n]

class HRRRDiscoveryTests(unittest.TestCase):
    def test_utc_rollover_and_nonfuture_latest(self):
        dt=datetime(2026,10,27,23,45,tzinfo=timezone.utc)
        self.assertEqual(target_valid_times(dt,3),[
            datetime(2026,10,28,0,tzinfo=timezone.utc),
            datetime(2026,10,27,23,tzinfo=timezone.utc),
            datetime(2026,10,27,22,tzinfo=timezone.utc)])
        with self.assertRaises(ValueError):
            target_valid_times(datetime(2026,10,27,23,45))
    def test_uses_newest_both_verified_not_only_one(self):
        now=datetime(2026,10,27,19,35,tzinfo=timezone.utc)
        def probe(run,lead):
            if run==datetime(2026,10,27,17,tzinfo=timezone.utc) and lead==3:
                return notfound(run,lead)
            return ok(run,lead)
        d=discover(now,probe,max_candidates=3)
        self.assertEqual(d["status"],"pair_inventory_observed")
        self.assertEqual(d["selected"]["validAt"],"2026-10-27T19:00:00Z")
        self.assertEqual([r["leadHours"] for r in d["selected"]["runs"]],[3,2])
        self.assertEqual(d["probeCount"],4)
        self.assertIsNone(d["actualUpstreamFirstPublicationAt"])
        self.assertFalse(d["operationalForChaseDecisions"])
    def test_no_pair_explicit_degraded(self):
        d=discover(RUN,notfound,max_candidates=2)
        self.assertEqual(d["status"],"no_verified_pair")
        self.assertIsNone(d["selected"])
        self.assertEqual(d["probeCount"],4)
    def test_refuses_bogus_run_valid(self):
        def corrupted(run,lead):return {**ok(run,lead),"validAt":"2026-01-01T00:00:00Z"}
        with self.assertRaisesRegex(ValueError,"mismatch"):
            discover(RUN,corrupted,max_candidates=1)
    @patch("pipelines.hrrr_inventory.urlopen")
    def test_actual_idx_fields_and_bounded_byte_range(self, urlopen):
        idx=("1:0:d=2026102718:REFC:entire atmosphere:2 hour fcst:\n"
             "2:16:d=2026102718:TMP:2 m above ground:2 hour fcst:\n"
             "3:360:d=2026102718:DPT:2 m above ground:2 hour fcst:\n")
        urlopen.return_value=FakeResponse(idx)
        d=inspect_index(RUN,2)
        self.assertEqual(d["state"],"inventory_observed")
        self.assertEqual(d["estimatedMessageBytes"],344)
        self.assertEqual(d["sourceLastModified"],"2026-10-27T19:00:00Z")
        self.assertEqual(d["validAt"],"2026-10-27T20:00:00Z")
        self.assertFalse(d["messageTransferred"])
    @patch("pipelines.hrrr_inventory.urlopen")
    def test_http_404_does_not_claim_data_exists(self,urlopen):
        urlopen.side_effect=HTTPError("https://example.test/index",404,"Not Found",{},None)
        self.assertEqual(inspect_index(RUN,2)["state"],"not_found")
    @patch("pipelines.hrrr_inventory.urlopen")
    def test_bad_index_cannot_be_selected(self,urlopen):
        urlopen.return_value=FakeResponse("bad index line\n")
        self.assertEqual(inspect_index(RUN,2)["state"],"invalid_index")

if __name__=="__main__":
    unittest.main()
