"""Real dev audit and independently specified numeric/semantic failures."""
import copy, json, pathlib, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import embedding_catalog as audit
ROOT=pathlib.Path(__file__).resolve().parents[2]
def vector(*head): return list(head)+['0']*(1024-len(head))
def compact(*head): return {'head':list(head),'tail_zeros':1024-len(head)}
class EmbeddingTests(unittest.TestCase):
 def test_last_valid_pooling_and_l2_are_real_1024_vector_behavior(self):
  # Catch first/mean pooling, ignored mask, unnormalized output and wrong width.
  got=audit.pool_normalize([vector('9','9'),vector('3','4'),vector('90','90')],[1,1,0])
  self.assertEqual([format(v,'.24f') for v in got[:2]],['0.600000000000000000000000','0.800000000000000000000000'])
  self.assertEqual(len(got),1024);self.assertTrue(all(x==0 for x in got[2:]))
  left=audit.pool_normalize([vector('99','99'),vector('0','5'),vector('-3','4')],[0,1,1]);self.assertEqual([format(v,'.24f') for v in left[:2]],['-0.600000000000000000000000','0.800000000000000000000000'])
 def test_retrieval_scores_and_tie_grouping_are_per_query(self):
  q=[{'id':'q-en','positions':[compact('3','4')],'mask':[1]},{'id':'q-tr','positions':[compact('-3','4')],'mask':[1]}]
  d=[{'id':'a','positions':[compact('3','4')],'mask':[1]},{'id':'b','positions':[compact('-3','4')],'mask':[1]},{'id':'c','positions':[compact('-3','-4')],'mask':[1]}]
  got=audit.reference_output(q,d)
  self.assertEqual(got['rankings'][0]['groups'],[['a'],['b'],['c']]);self.assertEqual(got['rankings'][1]['groups'],[['b'],['a'],['c']])
  self.assertEqual([row['score_micros'] for row in got['rankings'][0]['scores']],[1000000,280000,-1000000])
  ties=audit.reference_output([q[0]],[dict(d[0],id='z'),dict(d[0],id='a')]);self.assertEqual(ties['rankings'][0]['groups'],[['a','z']]);self.assertTrue(ties['rankings'][0]['tied'])
 def test_bad_dimensions_norm_masks_numbers_and_bounds_reject(self):
  for rows,mask in [([['1']*1023],[1]),([vector('0')],[1]),([vector('0.000000000001')],[1]),([vector('1')],[0]),([vector('1')],[True]),([vector('1')],[2]),([vector('1')],[]),([vector('1')]*3,[1,0,1]),([vector('NaN')],[1]),([vector('Infinity')],[1]),([vector('1000001')],[1])]:
   with self.subTest(mask=mask):self.assertRaises(ValueError,audit.pool_normalize,rows,mask)
  self.assertEqual(audit.pool_normalize([vector('0.00000001')],[1])[0],1)
  q={'id':'q','positions':[compact('1')],'mask':[1]};d=dict(q,id='d')
  for queries,docs in [([], [d]),([q], []),([q]*2,[d]),([dict(q,id=str(i)) for i in range(5)],[d]),([q],[dict(d,id='x'*65)]),([dict(q,permissions=True)],[d]),([q],[dict(d,positions=[{'head':['1'],'tail_zeros':1022}])])]:self.assertRaises(ValueError,audit.reference_output,queries,docs)
 def test_query_document_prefix_modes_and_utf8_limits(self):
  self.assertEqual(audit.render_text('query','Ankara nerede?'),'Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:Ankara nerede?')
  self.assertEqual(audit.render_text('document','Ankara Türkiye’dedir.'),'Ankara Türkiye’dedir.')
  self.assertEqual(audit.render_text('document','a'*16384),'a'*16384)
  for mode,text in [('query',''),('query',1),('other','text'),('document','a'*16385),('query','a'*16384),('query','<|im_end|>'),('document','a\x00b')]:self.assertRaises(ValueError,audit.render_text,mode,text)
 def test_actual_catalog_and_all_frozen_reference_cases(self):
  cat=audit.check_catalog(ROOT);self.assertEqual(cat['manifest']['profiles'][0]['role'],'representation')
  ref=audit.load(ROOT/'contracts/embedding-reference.v1.json')
  for case in ref['cases']:self.assertEqual(audit.reference_output(case['queries'],case['documents']),case['expected'])
 def test_catalog_source_semantics_type_and_false_support_rejections(self):
  cat=audit.load(ROOT/'catalog/qwen3-embedding-0.6b.v1.json');docs=[audit.load(ROOT/'contracts'/f) for f in ['embedding-profile.v1.json','qwen3-embedding-operators.v1.json','embedding-reference.v1.json']]
  for field in ['dim','precision','prefix','pooling','norm','role','float','bool','source','rights','authority','accepted']:
   c=copy.deepcopy(cat);p,o,r=copy.deepcopy(docs)
   if field=='dim':c['manifest']['configuration']['dimensions']['hidden_size']=512
   elif field=='precision':c['manifest']['numeric_format']='float32'
   elif field in ['prefix','pooling','norm']:p[field if field!='prefix' else 'preprocessing']={'changed':True}
   elif field=='role':c['manifest']['profiles'][0]['role']='decision'
   elif field=='float':c['manifest']['revision']=1.0
   elif field=='bool':c['manifest']['configuration']['batch_size']=True
   elif field=='source':c['manifest']['source_commit']='1'*40
   elif field=='rights':c['manifest']['rights']['status']='unresolved'
   elif field=='authority':c['manifest']['permissions']=True
   else:c['evidence']['local_support']='accepted'
   with self.subTest(field=field):self.assertRaises(ValueError,audit.validate,c,p,o,r)
 def test_pinned_contract_operator_and_reference_drift_reject(self):
  c=audit.load(ROOT/'catalog/qwen3-embedding-0.6b.v1.json');docs=[audit.load(ROOT/'contracts'/f) for f in ['embedding-profile.v1.json','qwen3-embedding-operators.v1.json','embedding-reference.v1.json']]
  for i in range(3):
   changed=copy.deepcopy(docs);changed[i]['forged']=True;self.assertRaises(ValueError,audit.validate,c,*changed)
 def test_closed_bounded_loader_duplicate_symlink_and_wire_rejection(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'x';p.write_text('{"x":1,"x":2}');self.assertRaises(ValueError,audit.load,p)
   p.write_bytes(b' '*65537);self.assertRaises(ValueError,audit.load,p)
   p.write_text('{}');link=p.with_name('link');link.symlink_to(p);self.assertRaises(ValueError,audit.load,link)
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);import shutil
   shutil.copytree(ROOT/'catalog',root/'catalog');shutil.copytree(ROOT/'contracts',root/'contracts');f=root/'catalog/qwen3-embedding-0.6b.v1.eyl';f.write_bytes(f.read_bytes()+b'\x00');self.assertRaises(ValueError,audit.check_catalog,root)
if __name__=='__main__':unittest.main()
