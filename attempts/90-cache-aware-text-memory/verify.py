"""CPU-only integrity and independent cache-accounting invariants."""
import hashlib,json,re
from pathlib import Path
import pilot
P=Path(__file__).resolve().parent

def main():
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(pilot.AR,local_files_only=True)
 freeze=json.loads((P/'evidence/freeze-v1.json').read_text())
 for name,sha in freeze['files'].items():
  if name=='pilot.py':
   a=json.loads((P/'evidence/pre-dllm-stop-amendment.json').read_text());assert sha==a['before_sha256'];sha=a['after_sha256'];b=json.loads((P/'evidence/pre-qa-fp32-amendment.json').read_text());assert sha==b['before_sha256'];sha=b['after_sha256']
  assert hashlib.sha256((P/name).read_bytes()).hexdigest()==sha,name
 streams=json.loads((P/'data/streams.json').read_text());evaluation=json.loads((P/'data/evaluation.json').read_text())
 assert len({s['id'] for s in streams})==11
 assert {s['id'] for s in streams}=={s['id'] for s in evaluation}
 assert sum(len(s['events']) for s in streams)==35
 raw=json.loads((P/'data/longmemeval_oracle_cleaned.json').read_text())
 selected=json.loads((P/'data/selection.json').read_text())['external']
 for chosen in selected:
  group=[x for x in raw if x['question_id'].endswith('_abs')] if chosen['abstention'] else [x for x in raw if x['question_type']==chosen['type'] and not x['question_id'].endswith('_abs')]
  assert min(group,key=lambda x:hashlib.sha256(('a90-v1:'+x['question_id']).encode()).hexdigest())['question_id']==chosen['id']
 # A changed beginning cannot authorize an equal suffix for causal KV reuse.
 before=['A','B','C','D'];after=['Z','B','C','D'];assert pilot.lcp(before,after)==0
 assert pilot.lcp(before,before+['E'])==4
 # Audit independently of lcp implementation: every reused index is in equal prefix.
 for old,new in [('foo','foobar'),('city Recife; job Orion','city Natal; job Orion'),('A\nB\nC','A\nB\nD')]:
  a=tok.encode(old,add_special_tokens=False);b=tok.encode(new,add_special_tokens=False);r=pilot.lcp(a,b)
  assert a[:r]==b[:r]
  assert r==min(len(a),len(b)) or a[r]!=b[r]
 for s in streams:
  for event in s['events']:
   assert not any(x in event for x in ['has_answer','answer_session_ids'])
 cp=[json.loads(l) for l in (P/'evidence/cpu-v1.jsonl').read_text().splitlines()]
 assert len([x for x in cp if x['type']=='memory'])==105
 for x in cp:
  if x['type']=='memory' and x['method']!='full_history':assert x['memory_tokens']<=320
 report={'passed':True,'streams':11,'updates':35,'cpu_memory_states':105,'selection_reproduced':7,'frozen_inputs_unchanged_with_documented_runtime_amendments':True,'cache_invariants':'prefix only; causal suffix never reused after divergence'}
 if (P/'evidence/reader-v1a.jsonl').exists():
  for phase in ['ar','dllm']:
   rows=[json.loads(l) for l in (P/f'evidence/{phase}-v1.jsonl').read_text().splitlines()]
   assert not any(x['type']=='failure' for x in rows)
   ms=[x for x in rows if x['type']=='memory'];assert len(ms)==70
   assert all(x['memory_tokens']<=320 for x in ms)
  rows=[json.loads(l) for l in (P/'evidence/reader-v1a.jsonl').read_text().splitlines()]
  if rows[-1]['type']=='phase_wall' and not any(x['type']=='failure' for x in rows):
   ans=[x for x in rows if x['type']=='answer'];assert len(ans)==245
   audits=[x for x in rows if x['type']=='cache_audit'];assert len(audits)==5 and all(x['passed'] for x in audits)
   assert all(x['prompt_tokens']==x['prefill_tokens']+x['reused_tokens'] for x in ans)
   assert all(x['forwards']==x['decode_tokens'] for x in ans)
   report.update(neural_memory_states=140,reader_calls=245,gpu_cache_audits=5)
 for review,manifest in [('blind-review.json','blind-review-score-freeze.json'),('synthetic-review.json','synthetic-review-freeze.json')]:
  if (P/'evidence'/manifest).exists():
   item=json.loads((P/'evidence'/manifest).read_text());assert hashlib.sha256((P/'evidence'/review).read_bytes()).hexdigest()==item['sha256']
 report['locked_review_files_valid']=True
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
