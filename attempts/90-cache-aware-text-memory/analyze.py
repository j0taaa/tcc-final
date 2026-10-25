"""Outcome accounting; keeps raw outcomes, blind rubric and mapping separate."""
import json,hashlib,random,collections,re
from pathlib import Path
P=Path(__file__).resolve().parent

def load(name):return [json.loads(s) for s in (P/'evidence'/name).read_text().splitlines()]

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--blind',action='store_true');a=ap.parse_args()
 answers=[x for x in load('reader-v1a.jsonl') if x['type']=='answer']
 if a.blind:
  ev={x['id']:x for x in json.loads((P/'data/evaluation.json').read_text())}
  rows=[x for x in answers if x['family']=='external' and x['final']];random.Random(903).shuffle(rows)
  blind=[];mapping={}
  for i,x in enumerate(rows):
   k=f'R{i:03d}';mapping[k]={'method':x['method'],'id':x['id']}
   blind.append({'label':k,'question':x['question'],'reference':ev[x['id']]['questions'][0]['answer'],'response':x['answer'],'score':None,'reason':''})
  (P/'evidence/blind-review.json').write_text(json.dumps(blind,ensure_ascii=False,indent=2)+'\n')
  (P/'evidence/blind-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
  return
 memories=sum(([x for x in load(n+('-v1a.jsonl' if n=='reader' else '-v1.jsonl')) if x['type']=='memory'] for n in ['cpu','ar','dllm']),[])
 mapping=json.loads((P/'evidence/blind-mapping.json').read_text())
 review=json.loads((P/'evidence/blind-review.json').read_text())
 assert all(x['score'] in [0,1,2] and x['reason'] for x in review)
 results={}
 norm=lambda z:' '.join(re.sub(r'[^\w\s]',' ',str(z).lower()).split())
 ev={x['id']:x for x in json.loads((P/'data/evaluation.json').read_text())}
 for method in sorted({x['method'] for x in answers}):
  result={}
  for family in ['synthetic','external','all']:
   ans=[x for x in answers if x['method']==method and (family=='all' or x['family']==family)]
   mem=[x for x in memories if x['method']==method and (family=='all' or x['family']==family)]
   sub={'answers':len(ans),'updates':len(mem),'edit_seconds':sum(x['seconds']+x.get('selection_seconds',0)+x.get('assembly_seconds',0) for x in mem),'reader_seconds':sum(x['seconds'] for x in ans),'reader_prefill':sum(x['prefill_tokens'] for x in ans),'reader_reused':sum(x['reused_tokens'] for x in ans),'reader_forwards':sum(x['forwards'] for x in ans),'editor_forwards':sum(x['forwards'] for x in mem),'editor_processed_tokens':sum(x.get('processed_tokens',x.get('prefill_tokens',0)+max(0,x['decode_tokens']-1)) for x in mem),'mean_memory_tokens':sum(x['memory_tokens'] for x in mem)/len(mem),'max_memory_tokens':max(x['memory_tokens'] for x in mem),'local_actions':sum(x.get('action')=='local' for x in mem),'max_kv_bytes':max(x['kv_bytes'] for x in ans)}
   sub['total_seconds']=sub['edit_seconds']+sub['reader_seconds']
   discarded=0
   for story in {x['id'] for x in ans}:
    seq=sorted([x for x in ans if x['id']==story],key=lambda x:x['step'])
    for prev,cur in zip(seq,seq[1:]):
     discarded+=prev['prompt_tokens']+prev['decode_tokens']-1-cur['reused_tokens']
   sub['discarded_cached_tokens']=discarded
   sub['reader_prompt_tokens']=sub['reader_prefill']+sub['reader_reused']
   sy=[x for x in ans if x['family']=='synthetic']
   sub.update(synthetic_all_correct=sum(x['all_correct'] for x in sy),synthetic_states=len(sy),fact_hits=sum(x['fact_hits'] for x in sy),fact_total=sum(x['fact_total'] for x in sy),obsolete_mentions=sum(x['obsolete_mentions'] for x in sy),explicit_memory_fact_mentions=sum(x['retained_hits'] for x in sy))
   scores=[x['score'] for x in review if mapping[x['label']]['method']==method] if family!='synthetic' else []
   external_ans=[x for x in ans if x['family']=='external' and x['final']]
   sub['external_reference_substring']=sum(norm(ev[x['id']]['questions'][0]['answer']) in norm(x['answer']) for x in external_ans)
   sub.update(external_full_correct=scores.count(2),external_partial=scores.count(1),external_wrong=scores.count(0),external_score=sum(scores),external_n=len(scores))
   result[family]=sub
  results[method]=result
 meta={n:[x for x in load(n+('-v1a.jsonl' if n=='reader' else '-v1.jsonl')) if x['type'] in ['load','warmup','peak','phase_wall','release','environment']] for n in ['ar','dllm','reader','cpu']}
 out={'methods':results,'phase_costs':meta,'cache_audits':[x for x in load('reader-v1a.jsonl') if x['type']=='cache_audit'],'note':'Resident end-to-end is a sum of measured stage costs, not observed interleaved latency. External semantic rubric is agent review, not official/human-independent accuracy.'}
 (P/'evidence/summary-v1.json').write_text(json.dumps(out,indent=2)+'\n')
 if (P/'evidence/synthetic-semantic-summary.json').exists():
  out['synthetic_semantic_audit']=json.loads((P/'evidence/synthetic-semantic-summary.json').read_text())
 out['version']='V1a common FP32 consumer; V1 NF4 audit failed, preserved separately'
 ca=results['dllm_local']['all'];ar=results['ar_local']['all'];fh=results['full_history']['all']
 out['gate']={'passed':False,'candidate':'dllm_local','runtime_ratio_to_ar_local':ca['total_seconds']/ar['total_seconds'],'runtime_ratio_to_full_history':ca['total_seconds']/fh['total_seconds'],'quality_vs_ar_local':ca['synthetic_all_correct']>=ar['synthetic_all_correct'] and ca['obsolete_mentions']<=ar['obsolete_mentions'],'novelty_substantial_established':False,'posttraining':'not justified by this pilot','all_controllers_use_real_prefix_cache':True}
 (P/'evidence/summary-v1a.json').write_text(json.dumps(out,indent=2)+'\n')
 for m,r in results.items():
  v=r['all'];print(m,'seconds',round(v['total_seconds'],3),'states',v['synthetic_all_correct'],'/12','ext',v['external_full_correct'],'/7','stale',v['obsolete_mentions'],'new',v['reader_prefill'],'reused',v['reader_reused'])
if __name__=='__main__':main()
