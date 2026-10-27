import unittest
from datetime import datetime,timedelta,timezone
from pipelines.hrrr_state import blank,merge
from pipelines.hrrr_inventory import iso
RUN=datetime(2026,10,27,17,tzinfo=timezone.utc)
def report(at,state="inventory_observed",run=RUN,lead=2):
    item={"state":state,"runAt":iso(run),"leadHours":lead}
    if state=="inventory_observed":
        item.update(validAt=iso(run+timedelta(hours=lead)),
                    sourceLastModified=iso(at-timedelta(minutes=10)),sourceETag="etag")
    return {"schema":"stormchase-hrrr-inventory/1","checkedAt":iso(at),
            "attempts":[{"runs":[item]}]}
class HistoricalObservationTests(unittest.TestCase):
    def test_first_positive_not_rewritten(self):
        t=datetime(2026,10,27,19,tzinfo=timezone.utc)
        a=merge(blank(),report(t))
        b=merge(a,report(t+timedelta(hours=1)))
        rec=next(iter(b["records"].values()))
        self.assertEqual(rec["firstObservedIndexAt"],iso(t))
        self.assertEqual(rec["lastObservedIndexAt"],iso(t+timedelta(hours=1)))
        self.assertIsNone(rec["indexBecameObservableBetween"])
    def test_only_prior_404_bounds_observed_visibility(self):
        t=datetime(2026,10,27,18,tzinfo=timezone.utc)
        absent=merge(blank(),report(t,"not_found"))
        seen=merge(absent,report(t+timedelta(minutes=30)))
        rec=next(iter(seen["records"].values()))
        self.assertEqual(rec["indexBecameObservableBetween"],
                         [iso(t),iso(t+timedelta(minutes=30))])
        self.assertEqual(seen["availabilityWindowBoundedRecords"],1)
    def test_network_failure_not_treated_as_confirmed_absence(self):
        t=datetime(2026,10,27,18,tzinfo=timezone.utc)
        bad=merge(blank(),report(t,"source_error"))
        seen=merge(bad,report(t+timedelta(minutes=30)))
        self.assertIsNone(next(iter(seen["records"].values()))["indexBecameObservableBetween"])
    def test_out_of_order_update_rejected(self):
        t=datetime(2026,10,27,19,tzinfo=timezone.utc)
        prior=merge(blank(),report(t))
        with self.assertRaisesRegex(ValueError,"out-of-order"):
            merge(prior,report(t-timedelta(hours=1)))
    def test_old_records_expire_under_retention(self):
        t=datetime(2026,10,27,18,tzinfo=timezone.utc)
        prior=merge(blank(),report(t))
        recent=report(t+timedelta(days=6),run=RUN+timedelta(days=6))
        merged=merge(prior,recent)
        self.assertEqual(merged["recordsRetained"],1)
    def test_invalid_valid_time_never_recorded(self):
        r=report(datetime(2026,10,27,19,tzinfo=timezone.utc))
        r["attempts"][0]["runs"][0]["validAt"]="2026-01-01T00:00:00Z"
        with self.assertRaises(ValueError):merge(blank(),r)
if __name__=="__main__":unittest.main()
