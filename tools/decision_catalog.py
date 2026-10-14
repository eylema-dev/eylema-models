"""Offline development audit/reference oracle. No model engine or task authority."""
import argparse
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import hashlib
import json
import pathlib
import re
import model_catalog as base

SOURCE = 'https://huggingface.co/Qwen/Qwen3-Reranker-0.6B'
COMMIT = 'e61197ed45024b0ed8a2d74b80b4d909f1255473'
UPSTREAM = {'config.json': (727, 'd479c427a9ca5295218063d4f9aca4f297ab4ac27487cca7af42c84643d51ef0', 'audit_measured_small_bytes'), 'README.md': (14742, '5bba8c734f6dd3ae48317b4139317e45a7fce48fc55e15670b23a0dd15492ab6', 'audit_measured_small_bytes'), 'tokenizer_config.json': (9706, '253153d0738ceb4c668d2eff957714dd2bea0b56de772a9fdccd96cbf517e6a0', 'audit_measured_small_bytes'), 'vocab.json': (2776833, 'ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910', 'audit_measured_small_bytes'), 'model.safetensors': (1191588280, '27cd75a405b9c1b46b59abfd88aaa209e6fed2a1972cde9b70e7659537c5e65b', 'publisher_advertised'), 'tokenizer.json': (11422654, 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4', 'publisher_advertised')}
CONTRACT_HASHES = {'decision-score.v1.json': '4b0991f34f552dac9c695675d625ba575efbd2d787623cacfa9dacc8461c5250', 'qwen3-reranker-operators.v1.json': '7b3ab7d55b1159ee368b07dc954c5bc0b0ac63c0755e774236bee853fec2a802', 'decision-score-reference.v1.json': '64b3b13cf1f5395eb080671461a1ecaa3b3df1c4509afe0798e2b18a61438f2c'}
PROMPT_SHA256 = 'c91af212ad3548b6a9f87c8b54901bb171e2f596e7d61f666634e44fc690a637'
PROMPT_BYTES = 236

require = base.require
obj = base.obj
canonical = base.canonical

def load(path):
    require(not path.is_symlink(), 'symlink input')
    with path.open('rb') as stream:
        raw = stream.read(65537)
    require(len(raw) <= 65536, 'input byte bound')
    def unique(pairs):
        values = {}
        for key, value in pairs:
            require(key not in values, 'duplicate JSON key')
            values[key] = value
        return values
    return json.loads(raw, object_pairs_hook=unique)

def ident(value):
    return type(value) is str and bool(re.fullmatch(r'[A-Za-z0-9_:.-]{1,64}', value))

def reference_output(questions):
    require(type(questions) is list and 1 <= len(questions) <= 4, 'question count')
    result, seen, pairs = [], set(), 0
    with localcontext() as context:
        context.prec = 80
        for question in questions:
            obj(question, {'id', 'options'}, 'question fields')
            require(ident(question['id']) and question['id'] not in seen, 'question identity')
            seen.add(question['id'])
            options = question['options']
            require(type(options) is list and 1 <= len(options) <= 4, 'option count')
            pairs += len(options)
            require(pairs <= 16, 'pair count')
            scores, option_ids = [], set()
            for option in options:
                obj(option, {'id', 'delta'}, 'option fields')
                require(ident(option['id']) and option['id'] not in option_ids, 'option identity')
                option_ids.add(option['id'])
                delta = option['delta']
                if delta is None:
                    scores.append(dict(option_id=option['id'], raw_delta=None, probability=None, score_micros=None, yes_no=None))
                    continue
                require(type(delta) is str and bool(re.fullmatch(r'-?[0-9]{1,2}(?:\.[0-9]{1,24})?', delta)), 'finite bounded delta text')
                number = Decimal(delta)
                require(abs(number) <= 32, 'delta extent')
                # Stable two-label sigmoid form; independent frozen oracle uses 1/(1+exp(-delta)).
                if number >= 0:
                    probability = Decimal(1) / (Decimal(1) + (-number).exp())
                else:
                    positive = number.exp()
                    probability = positive / (Decimal(1) + positive)
                micros = int((probability * 1000000).to_integral_value(rounding=ROUND_HALF_EVEN))
                scores.append(dict(option_id=option['id'], raw_delta=delta, probability=format(probability, '.24f'), score_micros=micros, yes_no=micros >= 500000))
            choice = None
            if any(row['score_micros'] is None for row in scores):
                reason = 'missing_score'
            else:
                ranked = sorted(scores, key=lambda row: row['score_micros'], reverse=True)
                best = ranked[0]['score_micros']
                second = ranked[1]['score_micros'] if len(ranked) > 1 else 0
                if len(ranked) > 1 and best == second:
                    reason = 'tie'
                elif best < 750000:
                    reason = 'below_floor'
                elif best - second < 100000:
                    reason = 'insufficient_margin'
                else:
                    choice, reason = ranked[0]['option_id'], 'chosen'
            result.append(dict(question_id=question['id'], scores=scores, choice=choice, status='chosen' if reason == 'chosen' else 'abstain', reason=reason))
    return result

def validate(cat, profile, ops, reference):
    obj(cat, {'manifest', 'evidence'}, 'catalog fields')
    for name, data in [('decision-score.v1.json', profile), ('qwen3-reranker-operators.v1.json', ops), ('decision-score-reference.v1.json', reference)]:
        require(hashlib.sha256(canonical(data)).hexdigest() == CONTRACT_HASHES[name], 'frozen contract/reference drift')
    d, e = cat['manifest'], cat['evidence']
    obj(d, base.FIELDS, 'manifest fields')
    require(d['format'] == 'model-profile.v1' and d['id'] == 'qwen3-reranker-0.6b' and type(d['revision']) is int and d['revision'] == 1, 'manifest identity')
    require(d['source_repository'] == SOURCE and d['source_commit'] == COMMIT, 'source identity')
    require(d['architecture'] == 'qwen3-dense.v1' and d['artifact_format'] == 'safetensors.v1' and d['numeric_format'] == 'bfloat16' and d['quantization'] == 'none', 'source profile')
    require(type(d['components']) is list and len(d['components']) == len(UPSTREAM) + len(CONTRACT_HASHES), 'component count')
    components, total = {}, 0
    for component in d['components']:
        obj(component, {'name', 'size', 'sha256', 'digest_source'}, 'component fields')
        require(base.name(component['name']) and component['name'] not in components and base.uint(component['size']) and base.digest(component['sha256']), 'component identity')
        total += component['size']
        require(total <= 2**64 - 1, 'component sum overflow')
        components[component['name']] = component
    require(set(components) == set(UPSTREAM) | set(CONTRACT_HASHES), 'component set')
    for name, wanted in UPSTREAM.items():
        component = components[name]
        require((component['size'], component['sha256'], component['digest_source']) == wanted, 'pinned source component')
    for name, data in [('decision-score.v1.json', profile), ('qwen3-reranker-operators.v1.json', ops), ('decision-score-reference.v1.json', reference)]:
        component = components[name]
        require((component['size'], component['sha256'], component['digest_source']) == (len(canonical(data)), CONTRACT_HASHES[name], 'audit_measured_small_bytes'), 'owned contract component')
    require(d['rights'] == {'publisher':'Qwen', 'source_repository':SOURCE, 'source_commit':COMMIT, 'license_id':'Apache-2.0', 'license_component':'README.md', 'status':'publisher_terms_pinned'}, 'publisher declaration not permissions')
    require(type(d['profiles']) is list and len(d['profiles']) == 1, 'one optional decision profile')
    interface = d['profiles'][0]
    obj(interface, base.IFACE, 'role fields')
    require(type(interface['version']) is int and interface == profile['interface'] and all(base.identifier(interface[key]) for key in base.IFACE - {'version'}), 'role semantic identity')
    expected_ops = [{'id':op['id'], 'spec_sha256':CONTRACT_HASHES['qwen3-reranker-operators.v1.json']} for op in ops['operators']]
    require(d['operators'] == expected_ops and len({op['id'] for op in expected_ops}) == len(expected_ops), 'operator identity')
    c = d['configuration']
    obj(c, base.CONFIG, 'configuration fields')
    require(c == {'config_component':'config.json', 'weights_component':'model.safetensors', 'tokenizer_component':'tokenizer.json', 'tokenizer_config_component':'tokenizer_config.json', 'template_sha256':PROMPT_SHA256, 'preprocessing_component':'decision-score.v1.json', 'operators_component':'qwen3-reranker-operators.v1.json', 'dimensions':{'hidden_size':1024, 'intermediate_size':3072, 'layers':28, 'attention_heads':16, 'kv_heads':8, 'head_dim':128, 'vocab_size':151669, 'context_capacity':40960}, 'batch_size':1, 'context_limit':4096, 'max_new_tokens':1}, 'configuration source/workload')
    require(all(base.uint(value) for value in c['dimensions'].values()) and all(base.uint(c[key]) for key in ['batch_size','context_limit','max_new_tokens']), 'configuration uint types')
    expected_e = {'local_support','fallback','weights_downloaded','tokenizer_json_byte_verified','vocab_bytes_measured','license_file_present','license_evidence','publisher_parameter_count','parameter_count_origin','source_config_sha256','tokenizer_config_sha256','vocab_sha256','template_sha256','template_bytes','template_kind','yes_token_id','no_token_id','core_contract_revision','core_contract_module_sha256','owned_contract_components','numeric_reference','model_execution','native_numeric_acceptance','calibrated_confidence'}
    obj(e, expected_e, 'evidence fields')
    require(e['local_support'] == 'unsupported' and e['fallback'] == 'fail' and e['model_execution'] == e['native_numeric_acceptance'] == 'not_run', 'execution unsupported/not_run')
    require(e['weights_downloaded'] is False and e['tokenizer_json_byte_verified'] is False and e['calibrated_confidence'] is False and e['license_file_present'] is False and e['vocab_bytes_measured'] is True, 'actual evidence flags')
    require(e['license_evidence'] == 'pinned_README_publisher_declaration_not_project_authority' and e['parameter_count_origin'] == 'publisher_advertised_metadata_not_weight_byte_audit' and type(e['publisher_parameter_count']) is int and e['publisher_parameter_count'] == 595776512, 'license/parameter provenance')
    require(e['source_config_sha256'] == UPSTREAM['config.json'][1] and e['tokenizer_config_sha256'] == UPSTREAM['tokenizer_config.json'][1] and e['vocab_sha256'] == UPSTREAM['vocab.json'][1], 'measured source pins')
    require(e['template_sha256'] == c['template_sha256'] == PROMPT_SHA256 and type(e['template_bytes']) is int and e['template_bytes'] == PROMPT_BYTES and e['template_kind'] == 'first_party_render_template_utf8_hash; full rendering contract component-hashed; actual model quality not_run', 'authored prompt identity')
    require(type(e['yes_token_id']) is int and type(e['no_token_id']) is int and e['yes_token_id'] == 9693 and e['no_token_id'] == 2152, 'head token identity')
    require(base.digest(e['core_contract_revision'],40) and e['core_contract_module_sha256'] == '7249070555c0fa72fcd2bd509574636f4295b67396c6cb22bd5409787ed6783e', 'owned core source pin')
    require(e['owned_contract_components'] == ['decision-score.v1.json','qwen3-reranker-operators.v1.json','decision-score-reference.v1.json'] and e['numeric_reference'] == 'synthetic_own_Decimal80_and_publisher_reported_delta_conversion_not_inference', 'reference provenance')
    for case in reference['cases']:
        require(reference_output(case['questions']) == case['expected'], 'frozen numerical reference mismatch')
    base.encode_manifest(d)

def check_catalog(root):
    cat = load(root/'catalog/qwen3-reranker-0.6b.v1.json')
    names = ['decision-score.v1.json','qwen3-reranker-operators.v1.json','decision-score-reference.v1.json']
    docs = [load(root/'contracts'/name) for name in names]
    validate(cat, *docs)
    for name, data in zip(names, docs):
        require((root/'contracts'/name).read_bytes() == canonical(data), 'canonical contract bytes')
    path = root/'catalog/qwen3-reranker-0.6b.v1.eyl'
    require(not path.is_symlink(), 'symlink EYL')
    with path.open('rb') as stream:
        wire = stream.read(32769)
    require(len(wire) <= 32768 and wire == base.encode_manifest(cat['manifest']), 'EYL drift')
    return cat

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.parse_args()
    check_catalog(pathlib.Path(__file__).resolve().parents[1])
    print('PASS: pinned decision-score catalog/reference/EYL; no model inference, calibrated confidence or authority')
