"""Development-only offline catalog audit/encoding. No model engine or authority."""
import argparse, hashlib, json, pathlib, re, struct
HEADER = b'EYL\x01\x00\x01\x00'
ROLES = {'perception', 'reasoning', 'planning', 'decision', 'policy', 'world_model', 'specialist', 'critic', 'representation'}
FIELDS = {'format', 'id', 'revision', 'source_repository', 'source_commit', 'architecture', 'artifact_format', 'numeric_format', 'quantization', 'components', 'operators', 'rights', 'configuration', 'profiles'}
IFACE = {'role', 'version', 'input_schema', 'output_schema', 'input_units', 'output_units', 'preprocessing', 'action_semantics', 'state_reset'}
CONFIG = {'config_component', 'weights_component', 'tokenizer_component', 'tokenizer_config_component', 'template_sha256', 'preprocessing_component', 'operators_component', 'dimensions', 'batch_size', 'context_limit', 'max_new_tokens'}
SOURCE = 'https://huggingface.co/Qwen/Qwen3-0.6B'
COMMIT = 'c1899de289a04d12100db370d81485cdf75e47ca'
UPSTREAM = {'config.json': (726, '660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd', 'audit_measured_small_bytes'), 'LICENSE': (11343, '832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e', 'audit_measured_small_bytes'), 'tokenizer_config.json': (9732, 'd5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101', 'audit_measured_small_bytes'), 'model.safetensors': (1503300328, 'f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b', 'publisher_advertised'), 'tokenizer.json': (11422654, 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4', 'publisher_advertised')}

def require(ok, why):
    if not ok:
        raise ValueError(why)

def obj(value, keys, why):
    require(type(value) is dict and set(value) == set(keys), why)

def uint(v):
    return type(v) is int and 0 < v <= 2 ** 64 - 1

def digest(v, n=64):
    return type(v) is str and bool(re.fullmatch('[0-9a-f]{' + str(n) + '}', v)) and (v != '0' * n)

def name(v):
    return type(v) is str and bool(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,127}', v))

def text(v):
    return type(v) is str and 0 < len(v.encode()) <= 1024 and (not any((ord(c) < 32 or ord(c) == 127 for c in v)))

def canonical(v):
    return (json.dumps(v, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()

def _value(v, key=''):
    if key in {'source_commit', 'sha256', 'spec_sha256', 'template_sha256'} and v is not None:
        require(digest(v, 40 if key == 'source_commit' else 64), 'digest')
        v = bytes.fromhex(v)
    if v is None:
        return b'\x00'
    if type(v) is bool:
        return b'\x02' if v else b'\x01'
    if type(v) is int:
        require(0 <= v < 2 ** 64, 'integer')
        return b'\x04' + struct.pack('>Q', v)
    if type(v) is bytes:
        return b'\x05' + struct.pack('>I', len(v)) + v
    if type(v) is str:
        b = v.encode()
        require(len(b) <= 4096, 'text bound')
        return b'\x06' + struct.pack('>I', len(b)) + b
    if type(v) is list:
        return b'\x07' + struct.pack('>I', len(v)) + b''.join((_value(x) for x in v))
    require(type(v) is dict, 'value type')
    items = sorted(v.items(), key=lambda kv: kv[0].encode())
    data = b'\x08' + struct.pack('>I', len(items))
    for k, x in items:
        b = k.encode()
        require(0 < len(b) <= 96, 'key bound')
        data += struct.pack('>I', len(b)) + b + _value(x, k)
    return data

def encode_manifest(value):
    wire = HEADER + _value(value)
    require(len(wire) <= 32768, 'manifest bound')
    return wire

def validate_catalog(cat, roles, ops):
    obj(cat, {'manifest', 'evidence'}, 'catalog fields')
    d = cat['manifest']
    e = cat['evidence']
    obj(d, FIELDS, 'manifest fields')
    require(d['format'] == 'model-profile.v1' and d['id'] == 'qwen3-0.6b' and (d['revision'] == 1), 'manifest identity')
    require(d['source_repository'] == SOURCE and d['source_commit'] == COMMIT, 'immutable source')
    require(d['architecture'] == 'qwen3-dense.v1' and d['artifact_format'] == 'safetensors.v1' and (d['numeric_format'] == 'bfloat16') and (d['quantization'] == 'none'), 'unsupported baseline profile')
    require(type(d['components']) is list and 1 <= len(d['components']) <= 64, 'component count')
    components = {}
    total = 0
    for c in d['components']:
        obj(c, {'name', 'size', 'sha256', 'digest_source'}, 'component fields')
        require(name(c['name']) and c['name'] not in components and uint(c['size']) and digest(c['sha256']) and (c['digest_source'] in {'publisher_advertised', 'audit_measured_small_bytes'}), 'component identity')
        total += c['size']
        require(total <= 2 ** 64 - 1, 'component sum overflow')
        components[c['name']] = c
    require(set(components) == set(UPSTREAM) | {'qwen3-operators.v1.json', 'role-interfaces.v1.json'}, 'component set')
    for n, want in UPSTREAM.items():
        c = components[n]
        require((c['size'], c['sha256'], c['digest_source']) == want, 'upstream component identity')
    for n, data, why in [('qwen3-operators.v1.json', ops, 'operator'), ('role-interfaces.v1.json', roles, 'role interface')]:
        b = canonical(data)
        c = components[n]
        require((c['size'], c['sha256'], c['digest_source']) == (len(b), hashlib.sha256(b).hexdigest(), 'audit_measured_small_bytes'), why + ' component drift')
    r = d['rights']
    obj(r, {'publisher', 'source_repository', 'source_commit', 'license_id', 'license_component', 'status'}, 'rights fields')
    require(r == {'publisher': 'Qwen', 'source_repository': SOURCE, 'source_commit': COMMIT, 'license_id': 'Apache-2.0', 'license_component': 'LICENSE', 'status': 'publisher_terms_pinned'}, 'rights unresolved or foreign')
    obj(roles, {'format', 'roles', 'authority'}, 'role document')
    require(roles['format'] == 'role-interfaces.v1' and type(roles['roles']) is list and (len(roles['roles']) == 9), 'nine roles')
    registry = {}
    for r in roles['roles']:
        obj(r, {'interface', 'domains', 'default_assignment'}, 'role fields')
        p = r['interface']
        obj(p, IFACE, 'role interface fields')
        require(p['role'] in ROLES and p['role'] not in registry and (p['version'] == 1) and all((text(p[k]) for k in IFACE - {'version'})), 'role interface identity')
        require(r['default_assignment'] is None and type(r['domains']) is list and r['domains'] and all((text(x) for x in r['domains'])), 'optional role intent')
        registry[p['role']] = p
    require(set(registry) == ROLES, 'nine unique roles')
    require(type(d['profiles']) is list and len(d['profiles']) == 3 and ({p['role'] for p in d['profiles']} == {'reasoning', 'planning', 'specialist'}), 'intended profiles')
    for p in d['profiles']:
        require(p == registry[p['role']], 'role interface mismatch')
    require(type(d['operators']) is list and 1 <= len(d['operators']) <= 64, 'operators')
    require(ops['format'] == 'qwen3-operators.v1' and ops['source_model_commit'] == COMMIT, 'operator source')
    spec = components['qwen3-operators.v1.json']['sha256']
    expected = [{'id': o['id'], 'spec_sha256': spec} for o in ops['operators']]
    require(d['operators'] == expected and len({o['id'] for o in expected}) == len(expected), 'operator identity')
    c = d['configuration']
    obj(c, CONFIG, 'configuration fields')
    for k in ['config_component', 'weights_component', 'tokenizer_component', 'tokenizer_config_component', 'preprocessing_component', 'operators_component']:
        require(c[k] in components, 'configuration reference')
    require(c['config_component'] == 'config.json' and c['weights_component'] == 'model.safetensors' and (c['tokenizer_component'] == 'tokenizer.json') and (c['tokenizer_config_component'] == 'tokenizer_config.json') and (c['preprocessing_component'] == 'role-interfaces.v1.json') and (c['operators_component'] == 'qwen3-operators.v1.json'), 'configuration role binding')
    dims = c['dimensions']
    require(dims == {'hidden_size': 1024, 'intermediate_size': 3072, 'layers': 28, 'attention_heads': 16, 'kv_heads': 8, 'head_dim': 128, 'vocab_size': 151936, 'context_capacity': 40960} and all((uint(v) for v in dims.values())), 'configuration dimensions')
    require(c['batch_size'] == 1 and c['context_limit'] == 4096 and (c['max_new_tokens'] == 128) and all((uint(c[k]) for k in ['batch_size', 'context_limit', 'max_new_tokens'])), 'configuration workload')
    require(digest(c['template_sha256']) and c['template_sha256'] == e['template_sha256'], 'template identity')
    expected_e = {'local_support', 'fallback', 'weights_downloaded', 'tokenizer_json_byte_verified', 'source_config_sha256', 'tokenizer_config_sha256', 'template_sha256', 'template_bytes', 'template_intent', 'special_tokens', 'core_contract_revision', 'core_contract_module_sha256', 'owned_contract_components', 'upstream_reference', 'artifact_verification'}
    obj(e, expected_e, 'evidence fields')
    require(e['local_support'] == 'unsupported' and e['fallback'] == 'fail', 'support is not execution')
    require(e['weights_downloaded'] is False and e['tokenizer_json_byte_verified'] is False, 'weight/tokenizer byte verification not run')
    require(e['source_config_sha256'] == UPSTREAM['config.json'][1] and e['tokenizer_config_sha256'] == UPSTREAM['tokenizer_config.json'][1] and digest(e['core_contract_revision'], 40) and digest(e['core_contract_module_sha256']), 'audit source pins')
    require(e['owned_contract_components'] == ['qwen3-operators.v1.json', 'role-interfaces.v1.json'] and e['upstream_reference'] == {'repository': ops['reference_repository'], 'commit': ops['reference_commit'], 'files_sha256': ops['reference_files_sha256']}, 'audit operator provenance')
    require(e['template_intent'] == {'enable_thinking': False, 'add_generation_prompt': True, 'execution': 'not_run'} and e['special_tokens'] == {'bos_token_id': 151643, 'eos_token_id': 151645, 'tokenizer_class': 'Qwen2Tokenizer'} and uint(e['template_bytes']), 'template and special token intent')
    encode_manifest(d)

def load(path):
    require(not path.is_symlink(), 'symlink catalog')
    raw = path.read_bytes()
    require(len(raw) <= 65536, 'catalog file bound')

    def unique(pairs):
        d = {}
        for k, v in pairs:
            require(k not in d, 'duplicate JSON key')
            d[k] = v
        return d
    return json.loads(raw, object_pairs_hook=unique)

def check_catalog(root):
    cat = load(root / 'catalog/qwen3-0.6b.v1.json')
    roles = load(root / 'contracts/role-interfaces.v1.json')
    ops = load(root / 'contracts/qwen3-operators.v1.json')
    validate_catalog(cat, roles, ops)
    for n, obj_ in [('role-interfaces.v1.json', roles), ('qwen3-operators.v1.json', ops)]:
        require((root / 'contracts' / n).read_bytes() == canonical(obj_), 'contract JSON bytes drift')
    p = root / 'catalog/qwen3-0.6b.v1.eyl'
    require(not p.is_symlink() and p.read_bytes() == encode_manifest(cat['manifest']), 'EYL drift')
    return cat
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    if args.write:
        cat = load(root / 'catalog/qwen3-0.6b.v1.json')
        validate_catalog(cat, load(root / 'contracts/role-interfaces.v1.json'), load(root / 'contracts/qwen3-operators.v1.json'))
        (root / 'catalog/qwen3-0.6b.v1.eyl').write_bytes(encode_manifest(cat['manifest']))
    check_catalog(root)
    print('PASS: pinned catalog, nine optional roles, exact EYL metadata; local model execution unsupported/not_run')
