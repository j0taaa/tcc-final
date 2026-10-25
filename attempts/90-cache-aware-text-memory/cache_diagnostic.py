"""Bounded cache diagnostic after V1 threshold failure, before QA outcomes."""
import os,subprocess,time,json,gc
from pathlib import Path
from pilot import AR,CachedAR,reader_messages
P=Path(__file__).resolve().parent
assert os.environ.get('A90_GPU_LOCKED')=='1'
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer
from bitsandbytes.nn import Linear4bit
torch.set_num_threads(4);torch.manual_seed(90001)
tok=AutoTokenizer.from_pretrained(AR,local_files_only=True)
model=AutoModelForCausalLM.from_pretrained(AR,local_files_only=True,device_map={'':0},torch_dtype=torch.bfloat16,attn_implementation='sdpa').eval()
before='B0: Mira lives in Recife.\nB1: Orion employs Mira.\nB2: Pixel is a dog.'
variants={'append':before+'\nB3: Code Cedar.','early':before.replace('Mira lives in Recife','Mira lives in Natal'),'middle':before.replace('Orion','Atlas'),'late':before.replace('dog','cat'),'boundary':'foobar'}
f=open(P/'evidence/cache-diagnostic.jsonl','x',buffering=1)
for mode in ['nf4','dequantized_bf16']:
 if mode=='dequantized_bf16':
  start=time.perf_counter();model.dequantize();torch.cuda.synchronize()
  f.write(json.dumps({'type':'dequantize','seconds':time.perf_counter()-start,'remaining_4bit_modules':sum(isinstance(m,Linear4bit) for m in model.modules()),'dtype':str(model.dtype),'allocated_bytes':torch.cuda.memory_allocated()})+'\n')
 engine=CachedAR(model,tok,torch)
 for name,after in variants.items():
  engine.clear();engine.run(reader_messages(before if name!='boundary' else 'foo','Say OK.'),4)
  cached,cost,cl=engine.run(reader_messages(after,'Say OK.'),8)
  engine.clear();fresh,fc,fl=engine.run(reader_messages(after,'Say OK.'),8)
  engine.clear();fresh2,_,fl2=engine.run(reader_messages(after,'Say OK.'),8)
  f.write(json.dumps({'type':'comparison','mode':mode,'case':name,'max_abs_logits':float((cl-fl).abs().max()),'mean_abs_logits':float((cl-fl).abs().mean()),'fresh_repeat_max_abs':float((fl-fl2).abs().max()),'cached':cached,'fresh':fresh,'fresh2':fresh2,'first_argmax_equal':int(cl.argmax())==int(fl.argmax()),'reused_tokens':cost['reused_tokens']})+'\n')
  print(mode,name,float((cl-fl).abs().max()),flush=True)
 engine.clear();del engine;gc.collect()
f.close()
