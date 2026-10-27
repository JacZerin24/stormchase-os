import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from email.message import Message
from pipelines.hrrr_subset import utc_cycle, source_url, parse_idx, choose, fetch_message

RUN = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)
IDX = ("1:0:d=2026102712:REFC:entire atmosphere:6 hour fcst:\n"
       "2:12:d=2026102712:TMP:2 m above ground:6 hour fcst:\n"
       "3:24:d=2026102712:DPT:2 m above ground:6 hour fcst:\n"
       "4:36:d=2026102712:UGRD:10 m above ground:6 hour fcst:\n")
class Fake:
    status = 206
    def __init__(self, data, content_range):
        self.data = data
        self.headers = Message()
        self.headers["Content-Range"] = content_range
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, count=1_000_000): return self.data[:count]

class HrrrTransportTests(unittest.TestCase):
    def test_cycle_and_valid_reference(self):
        self.assertEqual(utc_cycle("2026-10-27T12:00:00Z"), RUN)
        self.assertIn("/hrrr.t12z.wrfsfcf06.grib2", source_url(RUN, 6))
        for value in ["2026-10-27T12:00:00", "2026-10-27T12:20:00Z"]:
            with self.assertRaises(ValueError): utc_cycle(value)
    def test_idx_ranges(self):
        entries = parse_idx(IDX, RUN)
        item, end = choose(entries, "TMP", "2 m above ground")
        self.assertEqual((item.offset, end), (12, 23))
        self.assertIsNone(choose(entries,"UGRD","10 m above ground")[1])
        with self.assertRaises(ValueError): choose(entries,"VGRD","10 m above ground")
    def test_wrong_model_cycle_and_unsorted_idx(self):
        with self.assertRaises(ValueError): parse_idx(IDX, RUN.replace(hour=11))
        with self.assertRaises(ValueError): parse_idx(IDX.replace("3:24:", "3:2:"), RUN)
    @patch("pipelines.hrrr_subset.urlopen")
    def test_fail_closed_on_ignored_or_mismatched_range(self, get):
        data = b"GRIB" + b"xxxx" + b"7777"
        get.return_value=Fake(data, "bytes 12-23/200")
        result, _=fetch_message("https://example.test/file.grib2",12,23)
        self.assertEqual(result,data)
        get.return_value=Fake(data,"bytes 12-24/200")
        with self.assertRaises(ValueError):fetch_message("https://example.test/file.grib2",12,23)
        wrong=Fake(data,"bytes 12-23/200")
        wrong.status=200
        get.return_value=wrong
        with self.assertRaises(ValueError):fetch_message("https://example.test/file.grib2",12,23)
if __name__ == "__main__": unittest.main()
