import unittest
from unittest.mock import patch
from tools.noaa_source_smoke import summarize_spc, summarize_nws

class SmokeReportTests(unittest.TestCase):
    @patch("tools.noaa_source_smoke.request_json")
    def test_spc_report_is_only_aggregate(self, getter):
        getter.side_effect = [
            ({"count": 1}, {"http_status": 200}),
            ({"type": "FeatureCollection", "features": [
                {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": []},
                 "properties": {"dn": 4, "valid": "2026-10-27T12:00:00Z", "issue": "example"}}
            ]}, {"http_status": 200})
        ]
        report = summarize_spc(1)
        self.assertEqual(report["provider_count"], 1)
        self.assertEqual(report["dn_values"], ["4"])
        self.assertNotIn("features", report)
    @patch("tools.noaa_source_smoke.request_json")
    def test_nws_report_has_no_raw_alert_identity(self, getter):
        getter.return_value = ({"type": "FeatureCollection", "features": [
            {"type": "Feature", "id": "private-id-test", "geometry": None,
             "properties": {"event": "Tornado Warning", "sent": "2026-10-27T18:00:00Z"}}
        ]}, {"http_status": 200})
        report = summarize_nws("Tornado Warning")
        self.assertEqual(report["null_geometry_count"], 1)
        self.assertNotIn("private-id-test", str(report))
    @patch("tools.noaa_source_smoke.request_json")
    def test_disallow_cross_event_false_success(self, getter):
        getter.return_value = ({"type": "FeatureCollection", "features": [
            {"id": "a", "properties": {"event": "Flood Warning"}, "geometry": None}
        ]}, {"http_status": 200})
        with self.assertRaisesRegex(ValueError, "unexpected events"):
            summarize_nws("Tornado Warning")

if __name__ == "__main__":
    unittest.main()
