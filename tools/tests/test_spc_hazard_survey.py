import unittest
from unittest.mock import patch
from tools.spc_hazard_survey import LAYERS, survey_layer

class SPCSourceContractTests(unittest.TestCase):
    def test_layer_semantics_separate_intensity_from_probability(self):
        self.assertEqual(LAYERS[2],("Day 1","tornado","conditional intensity"))
        self.assertEqual(LAYERS[3],("Day 1","tornado","occurrence probability"))
        self.assertEqual(LAYERS[18],("Day 3","severe","conditional intensity"))
        self.assertEqual(LAYERS[19],("Day 3","severe","occurrence probability"))
    @patch("tools.spc_hazard_survey.read_json")
    def test_carries_source_labels_without_interpreting_codes(self,read):
        read.side_effect=[
            {"count":1},
            {"features":[{"attributes":{"dn":2,"label":"5%","label2":"sample label",
                                      "valid":"202610281200"}}]}
        ]
        r=survey_layer(3)
        self.assertEqual(r["fields"]["dn"],["2"])
        self.assertEqual(r["fields"]["label"],["5%"])
        self.assertIn("UNVERIFIED",r["interpretation"])
    @patch("tools.spc_hazard_survey.read_json")
    def test_empty_valid_current_product_is_not_fabricated(self,read):
        read.side_effect=[{"count":0},{"features":[]}]
        r=survey_layer(18)
        self.assertEqual(r["polygon_count"],0)
        self.assertEqual(r["fields"]["dn"],[])
    @patch("tools.spc_hazard_survey.read_json")
    def test_source_count_mismatch_is_error(self,read):
        read.side_effect=[{"count":1},{"features":[{"attributes":{}},{"attributes":{}}]}]
        with self.assertRaises(ValueError):survey_layer(3)
if __name__=="__main__":unittest.main()
