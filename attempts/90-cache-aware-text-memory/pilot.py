"""A90 frozen training-free memory pilot; all model phases require external flock."""
from __future__ import annotations
import argparse,gc,hashlib,json,os,random,re,resource,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent
AR=Path.home()/'.cache/huggingface/hub/models--unsloth--Qwen2.5-3B-Instruct-bnb-4bit/snapshots/2672b588848527e456d320c11926c794539f47d5'
DL=Path.home()/'.cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/08b83a6feb34df1a6011b80c3c00c7563e963b07'
READER=Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots/989aa7980e4cf806f80c7fef2b1adb7bc71aa306'
STOP=set('the a an is are was were be been and or of to in on at for from with by as now current new old user assistant have has had this that it i my me you your we our do does not no all also must keep changed change update correction effective replace than before after only memory block blocks information event events previous unchanged'.split())
METHODS=['dllm_local','ar_local','dllm_global','ar_global','extractive','raw_tail','full_history']

def vocab(s):return set(re.findall(r'[a-z][a-z0-9]+',s.lower()))-STOP

def select(blocks,event,ntokens):
 if not any(blocks) or ntokens>768:return list(range(4)),'global'
 ev=vocab(event);selected={i for i,b in enumerate(blocks) if len(vocab(b)&ev)>=2}
 if not selected:
  selected={next((i for i,b in enumerate(blocks) if not b),3)}
 else:
  while True:
   extra={i for i,b in enumerate(blocks) if any(len(vocab(b)&vocab(blocks[j]))>=3 for j in selected)}
   if extra<=selected:break
   selected|=extra
 if len(selected)>=3:return list(range(4)),'global'
 return sorted(selected),'local'

def serialize(blocks):return '\n'.join(f'B{i}: {b}' for i,b in enumerate(blocks))

def split_text(text,tok):
 ids=tok.encode(text,add_special_tokens=False)[:256]
 return [tok.decode(ids[i*64:(i+1)*64],skip_special_tokens=True).strip() for i in range(4)]

def patch(blocks,text,chosen,tok):
 ids=tok.encode(text,add_special_tokens=False)[:64*len(chosen)]
 out=blocks.copy()
 for j,i in enumerate(chosen):out[i]=tok.decode(ids[j*64:(j+1)*64],skip_special_tokens=True).strip()
 assert len(tok.encode(serialize(out),add_special_tokens=False))<=320
 assert all(out[i]==blocks[i] for i in range(4) if i not in chosen)
 return out

def extract(blocks,event,tok):
 old=' '.join(blocks)
 sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+',old+'\n'+event) if s.strip()]
 # Greedy density/diversity selection, with chronological rendering; no query input.
 keep=[];seen=set();remaining=256
 while sentences:
  rank=[]
  for i,s in enumerate(sentences):
   if not s:continue
   words=vocab(s);n=len(tok.encode(s,add_special_tokens=False))
   score=(len(words-seen)+2*len(re.findall(r'\b[A-Z][a-z]+\b|\d+',s)))/(max(8,n)**.5)+.15*i/max(1,len(sentences))
   if n<=remaining:rank.append((score,i,n,words))
  if not rank:break
  _,i,n,words=max(rank);keep.append((i,sentences[i]));remaining-=n;seen|=words
  # Preserve absolute chronology using a parallel identity below.
  sentences[i]=''
  if remaining<8:break
 selected={s for _,s in keep}
 text=' '.join(s for s in re.split(r'(?<=[.!?])\s+|\n+',old+'\n'+event) if s.strip() in selected)
 return split_text(text,tok)

def editor_prompt(blocks,event,chosen):
 return ('Maintain accurate compact factual memory for an assistant. Do not answer any question. '
 'Use only the supplied previous memory and new event. Preserve names, numbers, dates, preferences and useful facts. '
 'Newer explicit corrections supersede old facts; update related dependent facts consistently. '
 'Write only concise replacement memory text, no commentary, no headings. '
 f'The selected blocks are {chosen}; other blocks will be copied exactly. '
 f'Write at most {64*len(chosen)} tokens total, retaining useful facts from selected blocks and integrating the new event.\n'
 'PREVIOUS MEMORY:\n'+serialize(blocks)+'\nNEW EVENT:\n'+event+'\nREPLACEMENT TEXT:')

def lcp(a,b):
 n=0
 for x,y in zip(a,b):
  if x!=y:break
  n+=1
 return n

class Logger:
 def __init__(self,path):self.f=open(path,'x',buffering=1)
 def __call__(self,kind,**kw):self.f.write(json.dumps({'type':kind,**kw},ensure_ascii=False)+'\n')

class CachedAR:
 def __init__(self,model,tok,torch):self.model=model;self.tok=tok;self.torch=torch;self.cache=None;self.ids=[]
 def clear(self):self.cache=None;self.ids=[]
 def run(self,messages,max_tokens):
  th=self.torch;th.cuda.synchronize();start=time.perf_counter()
  ids=self.tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True)
  reused=min(lcp(self.ids,ids),max(0,len(ids)-1)) if self.cache is not None else 0
  if self.cache is not None:self.cache.crop(reused)
  else:
   from transformers import DynamicCache
   self.cache=DynamicCache()
  x=th.tensor([ids[reused:]],device='cuda');fwd=1
  with th.inference_mode():
   out=self.model(input_ids=x,past_key_values=self.cache,use_cache=True,logits_to_keep=1)
   logits=out.logits[0,-1];self.cache=out.past_key_values
   initial=logits.detach().float().cpu()
   generated=[]
   eos=self.model.generation_config.eos_token_id
   if isinstance(eos,int):eos=[eos]
   while len(generated)<max_tokens:
    token=int(logits.argmax());generated.append(token)
    if token in eos or len(generated)==max_tokens:break
    out=self.model(input_ids=th.tensor([[token]],device='cuda'),past_key_values=self.cache,use_cache=True,logits_to_keep=1)
    logits=out.logits[0,-1];self.cache=out.past_key_values;fwd+=1
  # Final sampled token has not been forwarded into KV.
  self.ids=ids+generated[:-1]
  assert self.cache.get_seq_length()==len(self.ids)
  text=self.tok.decode(generated,skip_special_tokens=True).strip()
  th.cuda.synchronize();elapsed=time.perf_counter()-start
  kv=0
  for key,val in self.cache:
   kv+=key.numel()*key.element_size()+val.numel()*val.element_size()
  return text,{'seconds':elapsed,'prompt_tokens':len(ids),'reused_tokens':reused,'prefill_tokens':len(ids)-reused,'decode_tokens':len(generated),'forwards':fwd,'kv_bytes':kv},initial

class Diffusion:
 def __init__(self,model,tok,torch):self.model=model;self.tok=tok;self.torch=torch
 def run(self,prompt,length):
  th=self.torch;th.cuda.synchronize();start=time.perf_counter()
  ids=self.tok.apply_chat_template([{'role':'user','content':prompt}],tokenize=True,add_generation_prompt=True)
  if len(ids)+length>4096:raise ValueError(f'LLaDA context overflow {len(ids)}+{length}; no truncation permitted')
  mask=126336
  x=th.full((1,len(ids)+length),mask,device='cuda',dtype=th.long);x[0,:len(ids)]=th.tensor(ids,device='cuda')
  steps=16
  with th.inference_mode():
   for s in range(steps):
    logits=self.model(x).logits[:,len(ids):,:]
    logits[:,:,mask]=-float('inf')
    # Official greedy low-confidence reveal; fixed equal quotas, no sampling.
    pred=logits.argmax(-1);conf=th.softmax(logits.float(),dim=-1).gather(-1,pred.unsqueeze(-1)).squeeze(-1)
    open_=x[:,len(ids):]==mask;conf=conf.masked_fill(~open_,-float('inf'))
    take=length//steps+(s<length%steps)
    pos=conf.topk(take,dim=-1).indices
    x[:,len(ids):].scatter_(1,pos,pred.gather(1,pos))
    del logits,conf,pred
  gen=x[0,len(ids):].tolist()
  stops={self.tok.eos_token_id,self.tok.convert_tokens_to_ids('<|eot_id|>')}
  gen=gen[:next((i for i,v in enumerate(gen) if v in stops),len(gen))]
  text=self.tok.decode(gen,skip_special_tokens=True).strip()
  th.cuda.synchronize()
  return text,{'seconds':time.perf_counter()-start,'prompt_tokens':len(ids),'canvas_tokens':length,'decode_tokens':len(gen),'forwards':steps,'processed_tokens':steps*(len(ids)+length),'reused_tokens':0}

def model_phase(phase,log):
 # external flock is mandatory; no CUDA initialization before process inventory.
 if os.environ.get('A90_GPU_LOCKED')!='1':raise RuntimeError('Use reproduce.sh: lock must cover process lifetime')
 active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'],text=True).strip()
 if active:raise RuntimeError('GPU occupied despite lock; refusing: '+active)
 start=time.perf_counter()
 import torch,transformers
 from transformers import AutoModel,AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
 torch.set_num_threads(4);torch.manual_seed(90001);random.seed(90001)
 log('environment',phase=phase,torch=torch.__version__,transformers=transformers.__version__,gpu=torch.cuda.get_device_name(),initial_processes=active,import_seconds=time.perf_counter()-start,revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
 start=time.perf_counter();ct=AutoTokenizer.from_pretrained(AR,local_files_only=True)
 if phase=='dllm':
  tok=AutoTokenizer.from_pretrained(DL,trust_remote_code=True,local_files_only=True)
  model=AutoModel.from_pretrained(DL,trust_remote_code=True,local_files_only=True,device_map={'':0},torch_dtype=torch.bfloat16,low_cpu_mem_usage=True,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)).eval()
  engine=Diffusion(model,tok,torch)
 else:
  tok=AutoTokenizer.from_pretrained(READER if phase=='reader' else AR,local_files_only=True)
  model=AutoModelForCausalLM.from_pretrained(READER if phase=='reader' else AR,local_files_only=True,device_map={'':0},torch_dtype=torch.float32 if phase=='reader' else torch.bfloat16,attn_implementation='sdpa',low_cpu_mem_usage=True).eval();engine=CachedAR(model,tok,torch)
 assert all(str(d) in ('0','cuda:0') or d==0 for d in model.hf_device_map.values()),model.hf_device_map
 torch.cuda.synchronize();log('load',phase=phase,seconds=time.perf_counter()-start,allocated_bytes=torch.cuda.memory_allocated(),reserved_bytes=torch.cuda.memory_reserved(),device_map=model.hf_device_map,model=str(DL if phase=='dllm' else (READER if phase=='reader' else AR)),cpu_maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 if phase=='dllm':_,warm=engine.run('Write a concise memory: Mira likes tea.',64)
 else:_,warm,_=engine.run([{'role':'user','content':'Say OK.'}],4);engine.clear()
 log('warmup',phase=phase,**warm);torch.cuda.reset_peak_memory_stats()
 if phase in ('ar','dllm'):editors(phase,engine,ct,log)
 else:readers(engine,ct,torch,log)
 log('peak',phase=phase,allocated_bytes=torch.cuda.max_memory_allocated(),reserved_bytes=torch.cuda.max_memory_reserved(),cpu_maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 engine.clear() if phase!='dllm' else None
 del engine,model;gc.collect();torch.cuda.empty_cache();torch.cuda.synchronize();log('release',allocated_bytes=torch.cuda.memory_allocated(),reserved_bytes=torch.cuda.memory_reserved())

def editors(phase,engine,tok,log):
 streams=json.loads((P/'data/streams.json').read_text());jobs=[(s,m) for s in streams for m in [phase+'_local',phase+'_global']];random.Random(901).shuffle(jobs)
 for stream,method in jobs:
  blocks=['']*4
  if phase=='ar':engine.clear()
  for step,event in enumerate(stream['events']):
   start=time.perf_counter();chosen,action=select(blocks,event,len(tok.encode(event,add_special_tokens=False))) if method.endswith('local') else (list(range(4)),'global')
   prompt=editor_prompt(blocks,event,chosen);prep=time.perf_counter()-start
   if phase=='dllm':text,cost=engine.run(prompt,64*len(chosen))
   else:text,cost,_=engine.run([{'role':'user','content':prompt}],64*len(chosen))
   start=time.perf_counter();blocks=patch(blocks,text,chosen,tok);assembly=time.perf_counter()-start
   log('memory',id=stream['id'],family=stream['family'],step=step,method=method,action=action,chosen=chosen,memory=serialize(blocks),blocks=blocks,raw_output=text,selection_seconds=prep,assembly_seconds=assembly,memory_tokens=len(tok.encode(serialize(blocks),add_special_tokens=False)),**cost)
   print(method,stream['id'],step,round(cost['seconds'],3),flush=True)

def cpu_phase(log):
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(AR,local_files_only=True)
 for stream in json.loads((P/'data/streams.json').read_text()):
  for method in ['extractive','raw_tail','full_history']:
   blocks=['']*4;history='';memory=''
   for step,event in enumerate(stream['events']):
    start=time.perf_counter()
    if method=='extractive':blocks=extract(blocks,event,tok);memory=serialize(blocks)
    elif method=='raw_tail':blocks=split_text(tok.decode(tok.encode(' '.join(blocks)+'\n'+event,add_special_tokens=False)[-256:],skip_special_tokens=True),tok);memory=serialize(blocks)
    else:history+=('\n' if history else '')+event;memory=history
    elapsed=time.perf_counter()-start
    log('memory',id=stream['id'],family=stream['family'],step=step,method=method,memory=memory,seconds=elapsed,selection_seconds=0,assembly_seconds=0,memory_tokens=len(tok.encode(memory,add_special_tokens=False)),forwards=0,reused_tokens=0,prefill_tokens=0,decode_tokens=0)

SYSTEM='Answer using the dated memory below. Respect explicit corrections and the latest facts. If information is absent say I do not know. Be concise and answer every part of the question.'
def reader_messages(memory,q):return [{'role':'system','content':SYSTEM},{'role':'user','content':'MEMORY:\n'+memory+'\nQUESTION:\n'+q}]

def readers(engine,tok,torch,log):
 cache_audit(engine,tok,torch,log)
 rows=[]
 for name in ['cpu','ar','dllm']:
  rows += [x for x in map(json.loads,(P/f'evidence/{name}-v1.jsonl').read_text().splitlines()) if x['type']=='memory']
 evals={x['id']:x for x in json.loads((P/'data/evaluation.json').read_text())}
 streams=json.loads((P/'data/streams.json').read_text());jobs=[(s,m) for s in streams for m in METHODS];random.Random(902).shuffle(jobs)
 for stream,method in jobs:
  engine.clear()
  for step in range(len(stream['events'])):
   memory=next(x['memory'] for x in rows if x['id']==stream['id'] and x['method']==method and x['step']==step)
   e=evals[stream['id']]
   if stream['family']=='synthetic':
    q='Give the current delivery city, appointment day, reminder day, employer, dog name, project code, and emergency contact. Label each field.'
    limit=96
   elif step==len(stream['events'])-1:q='Today is '+e['questions'][0]['date']+'. '+e['questions'][0]['question'];limit=96
   else:q='Acknowledge receipt.';limit=4
   out,cost,_=engine.run(reader_messages(memory,q),limit)
   record={'id':stream['id'],'family':stream['family'],'method':method,'step':step,'question':q,'answer':out,'final':step==len(stream['events'])-1,**cost}
   if stream['family']=='synthetic':
    expected=e['states'][step]['questions'];facts=sum([v.get('required',[v['answer']]) for v in expected],[])
    obsolete=sum([v.get('obsolete',[]) for v in expected],[])
    # Token boundaries, case insensitive. Negated obsolete mentions are still flagged as conservative diagnostics.
    match=lambda w,s:bool(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',s,re.I))
    record.update(required=facts,fact_hits=sum(match(w,out) for w in facts),fact_total=len(facts),all_correct=all(match(w,out) for w in facts),obsolete=obsolete,obsolete_mentions=sum(match(w,out) for w in obsolete),retained_hits=sum(match(w,memory) for w in facts))
   log('answer',**record);print('reader',method,stream['id'],step,round(cost['seconds'],3),flush=True)

def cache_audit(engine,tok,torch,log):
 before='B0: Mira lives in Recife.\nB1: Orion employs Mira.\nB2: Pixel is a dog.'
 variants={'append':before+'\nB3: Code Cedar.','early':before.replace('Mira lives in Recife','Mira lives in Natal'),'middle':before.replace('Orion','Atlas'),'late':before.replace('dog','cat'),'boundary':'foobar'}
 for name,after in variants.items():
  engine.clear();engine.run(reader_messages(before if name!='boundary' else 'foo','Say OK.'),4)
  cached,cost,c_logits=engine.run(reader_messages(after,'Say OK.'),8)
  engine.clear();fresh,fcost,f_logits=engine.run(reader_messages(after,'Say OK.'),8)
  error=float((c_logits-f_logits).abs().max());same=cached==fresh;argmax=int(c_logits.argmax())==int(f_logits.argmax())
  log('cache_audit',case=name,reused_tokens=cost['reused_tokens'],prefill_tokens=cost['prefill_tokens'],cached=cached,fresh=fresh,max_abs_logits=error,first_argmax_equal=argmax,output_equal=same,tolerance=.25,passed=error<=.25 and same)
  if error>.25 or not same:raise RuntimeError('cache audit failed; preserve results and stop')
 engine.clear()

def audit_cpu(log):
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(AR,local_files_only=True)
 blocks=['Mira lives in Recife','delivery address Recife Mira','Project Cedar','']
 chosen,action=select(blocks,'Mira moved from Recife to Natal. Delivery address Natal.',30)
 assert {0,1}<=set(chosen)
 out=patch(blocks,'Mira lives in Natal. Delivery address Natal.',chosen,tok)
 assert all(out[i]==blocks[i] for i in range(4) if i not in chosen)
 a=tok.encode('foo',add_special_tokens=False);b=tok.encode('foobar',add_special_tokens=False)
 assert lcp(a,b)<len(a)
 inputs=json.loads((P/'data/streams.json').read_text())
 assert all(set(x)=={'id','family','events'} for x in inputs)
 log('cpu_audit',passed=True,dependent_blocks=chosen,boundary_old=a,boundary_new=b,streams=len(inputs),events=sum(len(x['events']) for x in inputs))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['cpu','audit','ar','dllm','reader'],required=True);ap.add_argument('--output',required=True);a=ap.parse_args();log=Logger(a.output);start=time.perf_counter()
 try:
  if a.phase=='cpu':cpu_phase(log)
  elif a.phase=='audit':audit_cpu(log)
  else:model_phase(a.phase,log)
 except BaseException as e:log('failure',error=repr(e));raise
 finally:log('phase_wall',phase=a.phase,seconds=time.perf_counter()-start)
if __name__=='__main__':main()
