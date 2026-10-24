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

    def test_valid_detailed_plan(self):
        self.assertEqual(module.check(self.plan)[0], [])

    def test_real_duration_and_ratio_mismatch(self):
        for name, value in [('node_duration', 10), ('node_duration', True), ('node_ratio', '9:16')]:
            with self.subTest(name=name):
                plan = copy.deepcopy(self.plan)
                plan['shots'][0][name] = value
                self.assertTrue(module.check(plan)[0])

    def test_timeline_gap_overlap_and_bounds(self):
        for value in (2, 4, -1, 16):
            with self.subTest(value=value):
                plan = copy.deepcopy(self.plan)
                plan['shots'][0]['subshots'][1]['start'] = value
                self.assertTrue(module.check(plan)[0])
        self.shot['subshots'][-1]['end'] = 14
        self.assertTrue(module.check(self.plan)[0])

    def test_missing_directing_details(self):
        for field in module.DETAIL_FIELDS:
            with self.subTest(field=field):
                plan = copy.deepcopy(self.plan)
                plan['shots'][0]['subshots'][0][field] = '  '
                self.assertTrue(module.check(plan)[0])

    def test_only_continuity_characters_require_media(self):
        self.shot['references'] = ['A']
        self.assertTrue(module.check(self.plan)[0])
        self.shot['continuity_required'] = ['A']
        self.assertEqual(module.check(self.plan)[0], [])
        self.shot['continuity_required'] = []
        self.shot['references'] = []
        self.assertEqual(module.check(self.plan)[0], [])

    def test_unknown_continuity_character(self):
        self.shot['continuity_required'] = ['stranger']
        self.assertTrue(module.check(self.plan)[0])

    def test_generation_in_preproduction(self):
        self.shot['status'] = 'running'
        self.assertTrue(module.check(self.plan)[0])

    def test_dialogue_overlap_requires_boolean_intent(self):
        self.shot['dialogue'][1]['start'] = 2
        self.assertTrue(module.check(self.plan)[0])
        self.shot['allow_overlap'] = 'false'
        self.assertTrue(module.check(self.plan)[0])
        self.shot['allow_overlap'] = True
        self.assertEqual(module.check(self.plan)[0], [])

    def test_dialogue_speaker_and_bounds(self):
        for name, value in [('speaker', 'unknown'), ('speaker', []), ('end', 16), ('start', -1), ('text', '')]:
            with self.subTest(name=name, value=value):
                plan = copy.deepcopy(self.plan)
                plan['shots'][0]['dialogue'][0][name] = value
                self.assertTrue(module.check(plan)[0])

    def test_empty_cast_and_dialogue_supported(self):
        for field in ('characters', 'references', 'continuity_required', 'dialogue'):
            self.shot[field] = []
        self.assertEqual(module.check(self.plan)[0], [])

    def test_audio_explicit_but_user_can_override_defaults(self):
        self.plan['audio'] = {'bgm': True, 'subtitles': True}
        self.assertEqual(module.check(self.plan)[0], [])
        self.plan['audio']['bgm'] = 'false'
        self.assertTrue(module.check(self.plan)[0])

    def test_legacy_beats_are_readable_without_forced_refs(self):
        legacy = {'stage': 'preproduction', 'shots': [{
            'id': 'old', 'duration': 15, 'status': 'draft',
            'characters': ['A'], 'references': [],
            'beats': [{'start': 0, 'end': 15, 'action': 'A walks.'}],
        }]}
        errors, warnings = module.check(legacy)
        self.assertEqual(errors, [])
        self.assertTrue(warnings)

    def test_duplicate_clip_ids(self):
        self.plan['shots'].append(copy.deepcopy(self.shot))
        self.assertTrue(module.check(self.plan)[0])

    def test_non_finite_time_rejected(self):
        for value in (float('nan'), float('inf'), 10 ** 400, True, 0, '15'):
            with self.subTest(value=value):
                self.shot['duration'] = value
                self.assertTrue(module.check(self.plan)[0])

    def test_malformed_inputs_are_diagnosed(self):
        for value in (None, [], {}, {'schema_version': []}, {'stage': 'script', 'shots': [None]}):
            with self.subTest(value=value):
                self.assertTrue(module.check(value)[0])
        for name in ('characters', 'references', 'continuity_required', 'subshots', 'dialogue'):
            for value in (None, 'wrong', [None], [{}]):
                with self.subTest(name=name, value=value):
                    plan = copy.deepcopy(self.plan)
                    plan['shots'][0][name] = value
                    self.assertTrue(module.check(plan)[0])


if __name__ == '__main__':
    unittest.main()
