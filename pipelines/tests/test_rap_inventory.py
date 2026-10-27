import unittest
from datetime import datetime,timedelta,timezone
from email.message import Message
from unittest.mock import patch
from pipelines.rap_inventory import source_url,survey,probe,parse_rap_index

NOW=datetime(2026,10,27,20,40,tzinfo=timezone.utc)
class Resp:
    status=200
    def __init__(self,data):
        self.data=data.encode()
        self.headers=Message()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data[:n]
class RAPSurveyTests(unittest.TestCase):
    def test_official_rap_directory_filename_rollover(self):
        run=datetime(2026,10,27,23,tzinfo=timezone.utc)
        self.assertIn("rap.20261027/rap.t23z.awp130bgrbf02.grib2.idx",source_url(run,2))
        with self.assertRaises(ValueError):source_url(run,25)
    def test_fallback_to_previous_cycle_without_imputing_newest(self):
        calls=[]
        def check(run,lead):
            calls.append(run.hour)
            return {"state":"index_observed_only" if len(calls)==2 else "not_found",
                    "runAt":run.isoformat(),"leadHours":lead}
        out=survey(NOW,check)
        self.assertEqual(out["status"],"inventory_observed")
        self.assertEqual(calls,[18,17])
        self.assertIsNone(out["sourcePublicationAt"])
    def test_empty_source_does_not_become_forecast(self):
        out=survey(NOW,lambda run,lead:{"state":"not_found"})
        self.assertIsNone(out["selected"])
        self.assertFalse(out["liveProductEnabled"])
    def test_actual_nomads_dotted_submessages_and_repeated_offset(self):
        run=datetime(2026,10,27,18,tzinfo=timezone.utc)
        idx=("1:0:d=2026102718:PRES:1 hybrid level:2 hour fcst:\n"
             "15.1:100:d=2026102718:UGRD:1 hybrid level:2 hour fcst:\n"
             "15.2:100:d=2026102718:VGRD:1 hybrid level:2 hour fcst:\n"
             "16:400:d=2026102718:TMP:2 m above ground:2 hour fcst:\n"
             "17:1000:d=2026102718:DPT:2 m above ground:2 hour fcst:\n")
        start,end,count,shared,record=parse_rap_index(idx,run,2)
        self.assertEqual((start,end,count,shared,record),(400,999,5,False,"16"))
    def test_multi_submessage_target_is_not_silently_isolated(self):
        run=datetime(2026,10,27,18,tzinfo=timezone.utc)
        idx=("1:0:d=2026102718:REFC:entire atmosphere:2 hour fcst:\n"
             "2.1:100:d=2026102718:TMP:2 m above ground:2 hour fcst:\n"
             "2.2:100:d=2026102718:DPT:2 m above ground:2 hour fcst:\n"
             "3:500:d=2026102718:UGRD:10 m above ground:2 hour fcst:\n")
        self.assertTrue(parse_rap_index(idx,run,2)[3])

    @patch("pipelines.rap_inventory.urlopen")
    def test_actual_idx_schema(self,urlopen):
        idx=("1:0:d=2026102718:REFC:entire atmosphere:2 hour fcst:\n"
             "2:12:d=2026102718:TMP:2 m above ground:2 hour fcst:\n"
             "3:360:d=2026102718:DPT:2 m above ground:2 hour fcst:\n")
        urlopen.return_value=Resp(idx)
        r=probe(datetime(2026,10,27,18,tzinfo=timezone.utc))
        self.assertEqual(r["state"],"index_observed_only")
        self.assertEqual(r["estimatedFieldBytes"],348)
    @patch("pipelines.rap_inventory.urlopen")
    def test_bad_idx_is_explicit_failure(self,urlopen):
        urlopen.return_value=Resp("malformed index")
        r=probe(datetime(2026,10,27,18,tzinfo=timezone.utc))
        self.assertEqual(r["state"],"invalid_inventory")
if __name__=="__main__":unittest.main()
