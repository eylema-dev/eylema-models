import copy
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import decision_catalog as d
ROOT = pathlib.Path(__file__).resolve().parents[2]


class DecisionCatalogTests(unittest.TestCase):
    def setUp(self):
        self.cat = json.loads((ROOT / 'catalog/qwen3-reranker-0.6b.v1.json').read_text())
        self.profile = json.loads((ROOT / 'contracts/decision-score.v1.json').read_text())
        self.ops = json.loads((ROOT / 'contracts/qwen3-reranker-operators.v1.json').read_text())
        self.reference = json.loads((ROOT / 'contracts/decision-score-reference.v1.json').read_text())

    def check(self):
        d.validate(self.cat, self.profile, self.ops, self.reference)

    def test_actual_catalog_source_and_eyl_are_pinned(self):
        d.check_catalog(ROOT)
        self.assertEqual(self.cat['manifest']['source_commit'], 'e61197ed45024b0ed8a2d74b80b4d909f1255473')
        self.assertEqual(self.profile['head']['yes_token_id'], 9693)
        self.assertEqual(self.profile['head']['no_token_id'], 2152)
        self.assertFalse(self.cat['evidence']['weights_downloaded'])
        self.assertEqual(self.cat['manifest']['rights']['license_component'], 'README.md')

    def test_frozen_multiquestion_values_choice_ties_and_missing(self):
        self.check()
        for case in self.reference['cases']:
            with self.subTest(case=case['id']):
                self.assertEqual(d.reference_output(case['questions']), case['expected'])
        reasons = {row['reason'] for case in self.reference['cases'] for row in case['expected']}
        self.assertTrue({'chosen', 'tie', 'below_floor', 'insufficient_margin', 'missing_score'} <= reasons)

    def test_bool_float_versions_head_ids_and_limits_fail(self):
        for mutate in [lambda c: c['manifest'].update(revision=True), lambda c: c['manifest']['profiles'][0].update(version=True), lambda c: c['manifest']['configuration'].update(context_limit=4096.0)]:
            cat = copy.deepcopy(self.cat)
            mutate(cat)
            with self.assertRaises(ValueError):
                d.validate(cat, self.profile, self.ops, self.reference)
        self.profile['head']['yes_token_id'] = 9693.0
        with self.assertRaises(ValueError):
            self.check()

    def test_head_prompt_semantic_operator_and_reference_drift_fail(self):
        for target, mutate in [('profile', lambda x: x['head'].update(no_token_id=9693)), ('profile', lambda x: x['prompt'].update(system='changed')), ('profile', lambda x: x['decision'].update(min_probability='0.50')), ('ops', lambda x: x['operators'].pop()), ('reference', lambda x: x['cases'][0]['expected'][0].update(choice='other'))]:
            values = dict(cat=copy.deepcopy(self.cat), profile=copy.deepcopy(self.profile), ops=copy.deepcopy(self.ops), reference=copy.deepcopy(self.reference))
            mutate(values[target])
            with self.assertRaises(ValueError):
                d.validate(**values)

    def test_source_rights_unknown_fields_and_false_support_fail(self):
        for mutate in [lambda c: c['manifest'].update(source_commit='a' * 40), lambda c: c['manifest']['rights'].update(status='unresolved'), lambda c: c['manifest']['rights'].update(license_component='LICENSE'), lambda c: c['manifest'].update(permissions=['train']), lambda c: c['evidence'].update(local_support='accepted'), lambda c: c['evidence'].update(weights_downloaded=True), lambda c: c['evidence'].update(fallback='external')]:
            cat = copy.deepcopy(self.cat)
            mutate(cat)
            with self.assertRaises(ValueError):
                d.validate(cat, self.profile, self.ops, self.reference)

    def test_questions_options_duplicates_nonfinite_and_bounds_fail(self):
        valid = [{'id': 'q', 'options': [{'id': 'a', 'delta': '2'}, {'id': 'b', 'delta': '-2'}]}]
        bads = [[], valid * 5, [{'id': 'q', 'options': valid[0]['options'] * 3}], [{'id': 'q', 'options': [valid[0]['options'][0]] * 2}], [{'id': 'q', 'options': [{'id': 'a', 'delta': 'NaN'}]}], [{'id': 'q', 'options': [{'id': 'a', 'delta': '33'}]}], [{'id': 'q', 'options': [{'id': 'a', 'delta': 2.0}]}], [{'id': 'q', 'options': [{'id': 'a', 'delta': True}]}], [{'id': 'bad id', 'options': valid[0]['options']}]]
        for value in bads:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    d.reference_output(value)

    def test_bounded_loader_duplicate_keys_and_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            p = root / 'bad.json'
            p.write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):
                d.load(p)
            p.write_bytes(b' ' * 65537)
            with self.assertRaises(ValueError):
                d.load(p)
            link = root / 'link.json'
            link.symlink_to(p)
            with self.assertRaises(ValueError):
                d.load(link)

    def test_actual_json_eyl_byte_drift_fails(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            for name in ['catalog', 'contracts']:
                shutil.copytree(ROOT / name, root / name)
            p = root / 'catalog/qwen3-reranker-0.6b.v1.eyl'
            p.write_bytes(p.read_bytes() + b'\x00')
            with self.assertRaises(ValueError):
                d.check_catalog(root)


if __name__ == '__main__':
    unittest.main()
