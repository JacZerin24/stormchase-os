import unittest
from datetime import datetime,timezone
from pipelines.hrrr_convective import FIELDS,descriptor,select,inspect
from pipelines.hrrr_subset import parse_idx
RUN=datetime(2026,10,27,17,tzinfo=timezone.utc)
IDX=('1:0:d=2026102717:REFC:entire atmosphere:3 hour fcst:\n'
     '2:120:d=2026102717:MXUPHL:5000-2000 m above ground:2-3 hour max fcst:\n'
     '3:280:d=2026102717:APCP:surface:0-3 hour acc fcst:\n'
     '4:550:d=2026102717:APCP:surface:2-3 hour acc fcst:\n'
     '5:830:d=2026102717:DPT:2 m above ground:3 hour fcst:\n')
class CatalogTests(unittest.TestCase):
 def test_scope(self):
  for name in ['refc','uh25_max','uh02_max','cape_sb','cin_ml180','srh01','hgt500','u250','t850','apcp_1h','apcp_since_run']:
   self.assertIn(name,FIELDS)
  self.assertGreaterEqual(len(FIELDS),60)
 def test_different_time_meanings(self):
  self.assertEqual(descriptor(FIELDS['refc'],3),'3 hour fcst')
  self.assertEqual(descriptor(FIELDS['uh25_max'],3),'2-3 hour max fcst')
  self.assertEqual(descriptor(FIELDS['uh25_min'],3),'2-3 hour min fcst')
  self.assertEqual(descriptor(FIELDS['apcp_since_run'],3),'0-3 hour acc fcst')
  self.assertEqual(descriptor(FIELDS['apcp_1h'],3),'2-3 hour acc fcst')
 def test_exact_step_and_APCP_selection(self):
  rows=parse_idx(IDX,RUN)
  x=select(rows,FIELDS['uh25_max'],3)
  self.assertEqual((x['start'],x['end'],x['intervalStartLead']),(120,279,2))
  self.assertEqual(select(rows,FIELDS['apcp_since_run'],3)['start'],280)
  self.assertEqual(select(rows,FIELDS['apcp_1h'],3)['start'],550)
 def test_missing_is_not_silently_substituted(self):
  rows=parse_idx(IDX,RUN)
  self.assertEqual(select(rows,FIELDS['uh02_max'],3)['status'],'missing')
  self.assertEqual(select(rows,FIELDS['uh25_max'],2)['status'],'missing')
 def test_ambiguous_fails_closed(self):
  duplicate=IDX.replace('2:120:d=','2:120:d=') # add a duplicate with valid offsets
  duplicate=('1:0:d=2026102717:REFC:entire atmosphere:3 hour fcst:\n'
             '2:120:d=2026102717:REFC:entire atmosphere:3 hour fcst:\n'
             '3:280:d=2026102717:TMP:2 m above ground:3 hour fcst:\n')
  self.assertEqual(select(parse_idx(duplicate,RUN),FIELDS['refc'],3)['status'],'ambiguous')
 def test_realistic_report_semantics(self):
  report=inspect(RUN,3,['refc','uh25_max','apcp_1h'],fetcher=lambda _:IDX)
  self.assertEqual(report['indexVerified'],3)
  self.assertIsNone(report['firstPublicationAt'])
  self.assertFalse(report['decoded'])
if __name__=='__main__':unittest.main()
