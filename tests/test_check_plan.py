import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_plan', ROOT / 'scripts/check_plan.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PlanChecks(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / 'examples/plan.json').read_text())
        self.shot = self.plan['shots'][0]

    def test_valid_plan(self):
        self.assertEqual(module.check(self.plan)[0], [])

    def test_real_duration_mismatch(self):
        self.shot['node_duration'] = 10
        self.assertTrue(module.check(self.plan)[0])

    def test_timeline_gap_and_overlap(self):
        for value in (3, 5):
            with self.subTest(value=value):
                self.shot['beats'][1]['start'] = value
                self.assertTrue(module.check(self.plan)[0])

    def test_missing_media_binding(self):
        self.shot['references'] = ['A']
        self.assertTrue(module.check(self.plan)[0])

    def test_generation_in_preproduction(self):
        self.shot['status'] = 'running'
        self.assertTrue(module.check(self.plan)[0])

    def test_dialogue_overlap_requires_intent(self):
        self.shot['dialogue'][1]['start'] = 2
        self.assertTrue(module.check(self.plan)[0])
        self.shot['allow_overlap'] = True
        self.assertEqual(module.check(self.plan)[0], [])

    def test_malformed_input_is_diagnosed(self):
        for value in (None, [], {}, {'stage': 'script', 'shots': [None]}):
            with self.subTest(value=value):
                self.assertTrue(module.check(value)[0])

    def test_non_finite_time_rejected(self):
        self.shot['duration'] = float('nan')
        self.assertTrue(module.check(self.plan)[0])


if __name__ == '__main__':
    unittest.main()
