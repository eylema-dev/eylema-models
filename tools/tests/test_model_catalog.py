import copy, json, pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import model_catalog as m
ROOT = pathlib.Path(__file__).resolve().parents[2]

class CatalogTests(unittest.TestCase):

    def setUp(self):
        self.catalog = json.loads((ROOT / 'catalog/qwen3-0.6b.v1.json').read_text())
        self.roles = json.loads((ROOT / 'contracts/role-interfaces.v1.json').read_text())
        self.ops = json.loads((ROOT / 'contracts/qwen3-operators.v1.json').read_text())

    def check(self):
        m.validate_catalog(self.catalog, self.roles, self.ops)

    def test_json_eyl_drift_fails(self):
        m.check_catalog(ROOT)
        with tempfile.TemporaryDirectory() as td:
            import shutil
            r = pathlib.Path(td)
            for name in ['catalog', 'contracts']:
                shutil.copytree(ROOT / name, r / name)
            p = r / 'catalog/qwen3-0.6b.v1.eyl'
            p.write_bytes(p.read_bytes() + b'\x00')
            with self.assertRaisesRegex(ValueError, 'EYL drift'):
                m.check_catalog(r)

    def test_role_model_identity_not_interchangeable(self):
        self.catalog['manifest']['profiles'][0]['input_units'] = 'milliseconds.v1'
        with self.assertRaisesRegex(ValueError, 'role interface'):
            self.check()

    def test_nine_optional_roles_do_not_assign_every_role(self):
        self.check()
        self.assertEqual(len(self.roles['roles']), 9)
        self.assertEqual({p['role'] for p in self.catalog['manifest']['profiles']}, {'reasoning', 'planning', 'specialist'})
        self.assertTrue(all((r['default_assignment'] is None for r in self.roles['roles'])))

    def test_unsupported_local_cannot_claim_accepted_or_external_fallback(self):
        for key in ['accepted', 'can_execute', 'permissions', 'verified_weights']:
            cat = copy.deepcopy(self.catalog)
            cat['manifest'][key] = True
            with self.assertRaises(ValueError):
                m.validate_catalog(cat, self.roles, self.ops)
        self.catalog['evidence']['local_support'] = 'accepted'
        with self.assertRaisesRegex(ValueError, 'support'):
            self.check()

    def test_operator_digest_or_preprocessing_drift_fails(self):
        self.ops['operators'][0]['semantics'] = 'changed normalization'
        with self.assertRaisesRegex(ValueError, 'operator'):
            self.check()
        self.ops = json.loads((ROOT / 'contracts/qwen3-operators.v1.json').read_text())
        self.catalog['manifest']['profiles'][0]['preprocessing'] = 'other.v1'
        with self.assertRaisesRegex(ValueError, 'role interface'):
            self.check()

    def test_component_bounds_unknown_keys_and_rights_fail(self):
        for change in [lambda d: d['components'][0].update(name='../config.json'), lambda d: d['components'][0].update(size=True), lambda d: d['components'][0].update(sha256='0' * 64), lambda d: d['rights'].update(status='unresolved'), lambda d: d['rights'].update(source_commit='a' * 40), lambda d: d['configuration'].update(context_limit=40961)]:
            cat = copy.deepcopy(self.catalog)
            change(cat['manifest'])
            with self.assertRaises(ValueError):
                m.validate_catalog(cat, self.roles, self.ops)

    def test_advertised_weight_hash_not_local_byte_verification(self):
        self.check()
        c = next((c for c in self.catalog['manifest']['components'] if c['name'] == 'model.safetensors'))
        self.assertEqual(c['digest_source'], 'publisher_advertised')
        self.assertFalse(self.catalog['evidence']['weights_downloaded'])
        self.assertFalse(self.catalog['evidence']['tokenizer_json_byte_verified'])
        self.catalog['evidence']['weights_downloaded'] = True
        with self.assertRaisesRegex(ValueError, 'weight'):
            self.check()

class DuplicateJsonTests(unittest.TestCase):

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / 'duplicate.json'
            p.write_text('{"accepted":false,"accepted":true}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                m.load(p)

class ReviewRegressionTests(unittest.TestCase):
    setUp = CatalogTests.setUp

    def test_boolean_versions_and_float_special_tokens_are_rejected(self):
        for change in [lambda d: d['manifest'].update(revision=True), lambda d: d['manifest']['profiles'][0].update(version=True), lambda d: d['evidence']['special_tokens'].update(bos_token_id=151643.0)]:
            cat = copy.deepcopy(self.catalog)
            change(cat)
            with self.assertRaises(ValueError):
                m.validate_catalog(cat, self.roles, self.ops)

    def test_paired_measured_template_digest_or_length_drift_is_rejected(self):
        for change in [lambda d: (d['manifest']['configuration'].update(template_sha256='a' * 64), d['evidence'].update(template_sha256='a' * 64)), lambda d: d['evidence'].update(template_bytes=4169)]:
            cat = copy.deepcopy(self.catalog)
            change(cat)
            with self.assertRaisesRegex(ValueError, 'template'):
                m.validate_catalog(cat, self.roles, self.ops)

    def test_native_semantic_identifier_domain_is_enforced(self):
        import hashlib
        roles = copy.deepcopy(self.roles)
        cat = copy.deepcopy(self.catalog)
        roles['roles'][1]['interface']['input_schema'] = 'invalid id with spaces'
        cat['manifest']['profiles'][0]['input_schema'] = 'invalid id with spaces'
        b = (json.dumps(roles, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()
        component = next((c for c in cat['manifest']['components'] if c['name'] == 'role-interfaces.v1.json'))
        component.update(size=len(b), sha256=hashlib.sha256(b).hexdigest())
        with self.assertRaisesRegex(ValueError, 'role interface'):
            m.validate_catalog(cat, roles, self.ops)
