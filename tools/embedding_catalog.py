"""Offline development embedding metadata/reference audit, never a model engine."""
import argparse, hashlib, json, pathlib, re
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import model_catalog as base
require, obj, canonical = base.require, base.obj, base.canonical
SOURCE='https://huggingface.co/Qwen/Qwen3-Embedding-0.6B'
COMMIT='97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3'
PREFIX='Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:'
UPSTREAM={'config.json': [727, 'b5bf1f51fc45be473a54718cef92448d90a1be001bf9b9a44b8c7f10a19feaa9', 'audit_measured_small_bytes'], 'README.md': [17237, 'c34d9b7e5a267ad3fdd13227a253686bc90844ff4744a2a6a86c7c905e3d06f3', 'audit_measured_small_bytes'], 'tokenizer_config.json': [9706, '253153d0738ceb4c668d2eff957714dd2bea0b56de772a9fdccd96cbf517e6a0', 'audit_measured_small_bytes'], 'vocab.json': [2776833, 'ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910', 'audit_measured_small_bytes'], 'pooling-config.json': [313, '37bf193fa101f19101bfad9c31d3eb0f786e247b7b1e5cb7f007d730eed1ddbd', 'audit_measured_small_bytes'], 'modules.json': [349, '84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf', 'audit_measured_small_bytes'], 'config_sentence_transformers.json': [215, '10667c72ddb772627bf1780cb7f86af8e2ae0032b8c243c731172064105c6961', 'audit_measured_small_bytes'], 'model.safetensors': [1191586416, '0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd', 'publisher_advertised'], 'tokenizer.json': [11423705, 'def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a', 'publisher_advertised']}
SOURCE_PATHS={'config.json': 'config.json', 'README.md': 'README.md', 'tokenizer_config.json': 'tokenizer_config.json', 'vocab.json': 'vocab.json', 'pooling-config.json': '1_Pooling/config.json', 'modules.json': 'modules.json', 'config_sentence_transformers.json': 'config_sentence_transformers.json', 'model.safetensors': 'model.safetensors', 'tokenizer.json': 'tokenizer.json'}
CONTRACT_HASHES={'embedding-profile.v1.json': 'e6d110994e216a22b6f4bcccab0489f11aebb2409b8a619339f60b39c7be5475', 'qwen3-embedding-operators.v1.json': '4ead3403d77fbbc5d33e301d36c27019312359f5843810a160dc1338e17b7eff', 'embedding-reference.v1.json': '44e72d935c6da6d086e2c5c2462f60c8c1cc162aab7b696a25d4ba79341c783d'}
CONFIGURATION={'config_component': 'config.json', 'weights_component': 'model.safetensors', 'tokenizer_component': 'tokenizer.json', 'tokenizer_config_component': 'tokenizer_config.json', 'template_sha256': '9fab7feb99edb69f560d85cf1bb849dd556c37f383d0336574f78f1303e90740', 'preprocessing_component': 'embedding-profile.v1.json', 'operators_component': 'qwen3-embedding-operators.v1.json', 'dimensions': {'hidden_size': 1024, 'intermediate_size': 3072, 'layers': 28, 'attention_heads': 16, 'kv_heads': 8, 'head_dim': 128, 'vocab_size': 151669, 'context_capacity': 32768}, 'batch_size': 1, 'context_limit': 4096, 'max_new_tokens': 1}
EVIDENCE={'local_support': 'unsupported', 'fallback': 'fail', 'weights_downloaded': False, 'tokenizer_json_byte_verified': False, 'vocab_bytes_measured': True, 'source_component_paths': {'config.json': 'config.json', 'README.md': 'README.md', 'tokenizer_config.json': 'tokenizer_config.json', 'vocab.json': 'vocab.json', 'pooling-config.json': '1_Pooling/config.json', 'modules.json': 'modules.json', 'config_sentence_transformers.json': 'config_sentence_transformers.json', 'model.safetensors': 'model.safetensors', 'tokenizer.json': 'tokenizer.json'}, 'license_file_present': False, 'license_evidence': 'pinned_README_publisher_declaration_not_project_authority', 'publisher_parameter_count': 595776512, 'parameter_count_origin': 'publisher_advertised_metadata_not_weight_byte_audit', 'query_prefix_sha256': '9fab7feb99edb69f560d85cf1bb849dd556c37f383d0336574f78f1303e90740', 'query_prefix_bytes': 91, 'document_prefix_sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'core_contract_revision': 'a863e8bd68e9be23ab3f326c53a9ae875b9a270b', 'core_contract_module_sha256': '7249070555c0fa72fcd2bd509574636f4295b67396c6cb22bd5409787ed6783e', 'owned_contract_components': ['embedding-profile.v1.json', 'qwen3-embedding-operators.v1.json', 'embedding-reference.v1.json'], 'numeric_reference': 'synthetic_own_Decimal80_direct_sqrt_reference_not_inference', 'model_execution': 'not_run', 'native_numeric_acceptance': 'not_run', 'en_tr_quality': 'not_run'}

def raw_bytes(path,limit=65536):
 require(not path.is_symlink(),'symlink input')
 with path.open('rb') as stream: raw=stream.read(limit+1)
 require(len(raw)<=limit,'input byte bound')
 return raw

def load(path):
 def unique(pairs):
  values={}
  for key,value in pairs:
   require(key not in values,'duplicate JSON key');values[key]=value
  return values
 return json.loads(raw_bytes(path),object_pairs_hook=unique)

def ident(value):return type(value) is str and bool(re.fullmatch(r'[A-Za-z0-9_:.-]{1,64}',value))

def scalar(value):
 require(type(value) is str and bool(re.fullmatch(r'-?[0-9]{1,7}(?:\.[0-9]{1,24})?',value)),'finite bounded scalar text')
 number=Decimal(value);require(abs(number)<=1000000,'scalar extent');return number

def pool_normalize(rows,mask):
 require(type(rows) is list and 1<=len(rows)<=4,'position count')
 require(type(mask) is list and len(mask)==len(rows) and all(type(x) is int and x in [0,1] for x in mask),'binary mask')
 selected=[i for i,x in enumerate(mask) if x==1]
 require(selected and selected==list(range(selected[0],selected[-1]+1)) and (selected[0]==0 or selected[-1]==len(mask)-1),'contiguous left/right mask')
 require(all(type(row) is list and len(row)==1024 for row in rows),'dimension1024')
 with localcontext() as context:
  context.prec=80
  parsed=[[scalar(x) for x in row] for row in rows];vector=parsed[selected[-1]]
  scale=max(abs(x) for x in vector);require(scale>0,'zero norm')
  normalized=[x/scale for x in vector];root=sum(x*x for x in normalized).sqrt()
  require(scale*root>Decimal('0.000000000001'),'epsilon norm')
  return [x/root for x in normalized]

def render_text(mode,text):
 require(mode in ['query','document'],'query/document mode')
 require(type(text) is str and bool(text) and all(ord(x)>=32 or x in ['\n','\t'] for x in text) and '\x7f' not in text,'nonempty UTF8 data')
 require(not re.search(r'<\|[^<>]*\|>',text),'reserved control token')
 result=(PREFIX if mode=='query' else '')+text
 require(len(result.encode('utf-8'))<=16384,'rendered UTF8 bound')
 return result

def expand(row):
 obj(row,{'head','tail_zeros'},'compact fields')
 require(type(row['head']) is list and 1<=len(row['head'])<=4 and type(row['tail_zeros']) is int and len(row['head'])+row['tail_zeros']==1024,'compact dimension')
 return row['head']+['0']*row['tail_zeros']

def reference_output(queries,documents):
 require(type(queries) is list and 1<=len(queries)<=4 and type(documents) is list and 1<=len(documents)<=4,'query/document count')
 output={'query_vectors':[],'document_vectors':[],'rankings':[]};arrays=[]
 with localcontext() as context:
  context.prec=80
  for entries,kind in [(queries,'query_vectors'),(documents,'document_vectors')]:
   seen=set();vectors=[]
   for entry in entries:
    obj(entry,{'id','positions','mask'},'reference entry fields');require(ident(entry['id']) and entry['id'] not in seen,'reference identity');seen.add(entry['id'])
    require(type(entry['positions']) is list and 1<=len(entry['positions'])<=4,'position count')
    vector=pool_normalize([expand(row) for row in entry['positions']],entry['mask']);vectors.append(vector)
    output[kind].append({'id':entry['id'],'vector':{'head':[format(x,'.24f') for x in vector[:4]],'tail_zeros':1020}})
   arrays.append(vectors)
  for entry,query in zip(queries,arrays[0]):
   scores=[]
   for document,vector in zip(documents,arrays[1]):
    dot=sum(x*y for x,y in zip(query,vector));require(abs(dot)<=Decimal(1)+Decimal('1e-70'),'cosine numerical bound');dot=max(Decimal(-1),min(Decimal(1),dot))
    scores.append({'document_id':document['id'],'cosine':format(dot,'.24f'),'score_micros':int((dot*1000000).to_integral_value(rounding=ROUND_HALF_EVEN))})
   scores.sort(key=lambda row:(-row['score_micros'],row['document_id']));groups=[];previous=None
   for score in scores:
    if groups and score['score_micros']==previous:groups[-1].append(score['document_id'])
    else:groups.append([score['document_id']])
    previous=score['score_micros']
   output['rankings'].append({'query_id':entry['id'],'scores':scores,'groups':groups,'tied':any(len(group)>1 for group in groups)})
 return output

def validate(cat,profile,ops,reference):
 obj(cat,{'manifest','evidence'},'catalog fields')
 for name,value in [('embedding-profile.v1.json',profile),('qwen3-embedding-operators.v1.json',ops),('embedding-reference.v1.json',reference)]:
  require(hashlib.sha256(canonical(value)).hexdigest()==CONTRACT_HASHES[name],'frozen contract/reference drift')
 d,e=cat['manifest'],cat['evidence'];obj(d,base.FIELDS,'manifest fields')
 require(d['format']=='model-profile.v1' and d['id']=='qwen3-embedding-0.6b' and type(d['revision']) is int and d['revision']==1,'manifest identity')
 require(d['source_repository']==SOURCE and d['source_commit']==COMMIT,'source identity')
 require(d['architecture']=='qwen3-dense.v1' and d['artifact_format']=='safetensors.v1' and d['numeric_format']=='bfloat16' and d['quantization']=='none','source profile')
 require(type(d['components']) is list and len(d['components'])==len(UPSTREAM)+len(CONTRACT_HASHES),'component count');components={};total=0
 for component in d['components']:
  obj(component,{'name','size','sha256','digest_source'},'component fields')
  require(base.name(component['name']) and component['name'] not in components and base.uint(component['size']) and base.digest(component['sha256']),'component identity')
  total+=component['size'];require(total<=2**64-1,'component byte sum');components[component['name']]=component
 require(set(components)==set(UPSTREAM)|set(CONTRACT_HASHES),'component set')
 for name,wanted in UPSTREAM.items():
  row=components[name];require([row['size'],row['sha256'],row['digest_source']]==wanted,'pinned source component')
 for name,value in [('embedding-profile.v1.json',profile),('qwen3-embedding-operators.v1.json',ops),('embedding-reference.v1.json',reference)]:
  row=components[name];require((row['size'],row['sha256'],row['digest_source'])==(len(canonical(value)),CONTRACT_HASHES[name],'audit_measured_small_bytes'),'owned component identity')
 require(d['rights']=={'publisher':'Qwen','source_repository':SOURCE,'source_commit':COMMIT,'license_id':'Apache-2.0','license_component':'README.md','status':'publisher_terms_pinned'},'rights not authority')
 require(type(d['profiles']) is list and len(d['profiles'])==1,'one representation profile');interface=d['profiles'][0];obj(interface,base.IFACE,'role fields')
 require(type(interface['version']) is int and interface==profile['interface'] and all(base.identifier(interface[k]) for k in base.IFACE-{'version'}),'role semantic identity')
 expected=[{'id':row['id'],'spec_sha256':CONTRACT_HASHES['qwen3-embedding-operators.v1.json']} for row in ops['operators']]
 require(d['operators']==expected and len({row['id'] for row in expected})==len(expected),'operator identity')
 c=d['configuration'];obj(c,base.CONFIG,'configuration fields');require(c==CONFIGURATION,'configuration/source/workload')
 require(all(base.uint(x) for x in c['dimensions'].values()) and all(base.uint(c[k]) for k in ['batch_size','context_limit','max_new_tokens']),'configuration uint types')
 obj(e,set(EVIDENCE),'evidence fields')
 # Type equality prevents bool/int/float masquerading and support/authority drift.
 for key,wanted in EVIDENCE.items():
  require(type(e[key]) is type(wanted) and e[key]==wanted,'pinned evidence/provenance')
 for case in reference['cases']:require(reference_output(case['queries'],case['documents'])==case['expected'],'frozen numeric reference mismatch')
 for case in reference['text_fixtures']:require(render_text(case['mode'],case['text'])==case['expected'],'frozen UTF8/prefix mismatch')
 base.encode_manifest(d)

def check_catalog(root):
 cat=load(root/'catalog/qwen3-embedding-0.6b.v1.json');names=['embedding-profile.v1.json','qwen3-embedding-operators.v1.json','embedding-reference.v1.json'];docs=[load(root/'contracts'/name) for name in names];validate(cat,*docs)
 for name,doc in zip(names,docs):require(raw_bytes(root/'contracts'/name)==canonical(doc),'canonical contract bytes')
 require(raw_bytes(root/'catalog/qwen3-embedding-0.6b.v1.eyl',32768)==base.encode_manifest(cat['manifest']),'EYL drift')
 return cat

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.parse_args();check_catalog(pathlib.Path(__file__).resolve().parents[1]);print('PASS: pinned embedding catalog/EYL/synthetic reference; no model inference, Turkish quality or authority')
