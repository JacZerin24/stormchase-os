import unittest
from datetime import datetime,timezone
from pipelines.hrrr_convective_render import window_contract
RUN=datetime(2026,10,27,17,tzinfo=timezone.utc)
class UHScientificSemantics(unittest.TestCase):
 def test_strict_three_contiguous_hourly_maxima(self):
  intervals=window_contract([1,2,3],RUN)
  self.assertEqual(intervals[0],('2026-10-27T17:00:00Z','2026-10-27T18:00:00Z'))
  self.assertEqual(intervals[-1],('2026-10-27T19:00:00Z','2026-10-27T20:00:00Z'))
 def test_missing_hour_or_overlap_cannot_claim_contiguous_swath(self):
  for invalid in ([1,3],[1,2,2],[2,1],[0,1]):
   with self.assertRaises(ValueError):window_contract(invalid,RUN)
if __name__=='__main__':unittest.main()
