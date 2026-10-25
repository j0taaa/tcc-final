"""Freeze question-blind chronological streams and disjoint evaluator inputs."""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent
MODEL='unsloth/Qwen2.5-3B-Instruct-bnb-4bit'
REV='2672b588848527e456d320c11926c794539f47d5'
def main():
 from transformers import AutoTokenizer
 t=AutoTokenizer.from_pretrained(MODEL,revision=REV,local_files_only=True)
 raw=json.loads((P/'data/longmemeval_oracle_cleaned.json').read_text())
 chosen=[]
 for kind in sorted({x['question_type'] for x in raw}):
  pool=[x for x in raw if x['question_type']==kind and not x['question_id'].endswith('_abs')]
  chosen.append(min(pool,key=lambda x:hashlib.sha256(('a90-v1:'+x['question_id']).encode()).hexdigest()))
 # One abstention control, independently selected by id. No length/answer filtering.
 chosen.append(min([x for x in raw if x['question_id'].endswith('_abs')],key=lambda x:hashlib.sha256(('a90-v1:'+x['question_id']).encode()).hexdigest()))
 streams=[];evaluation=[];meta=[]
 for x in chosen:
  sessions=sorted(zip(x['haystack_dates'],x['haystack_session_ids'],x['haystack_sessions']),key=lambda z:(z[0],z[1]))
  text='\n'.join(date+'\n'+'\n'.join(y['role']+': '+y['content'] for y in sess) for date,_,sess in sessions)
  ids=t.encode(text,add_special_tokens=False)
  # No truncation and no has_answer metadata. Bound each model call, not each history.
  events=[t.decode(ids[i:i+1536],skip_special_tokens=True) for i in range(0,len(ids),1536)] or ['No past sessions.']
  streams.append({'id':x['question_id'],'family':'external','events':events})
  evaluation.append({'id':x['question_id'],'type':x['question_type'],'questions':[{'question':x['question'],'answer':x['answer'],'date':x['question_date']}],'abstention':x['question_id'].endswith('_abs')})
  meta.append({'id':x['question_id'],'type':x['question_type'],'tokens':len(ids),'updates':len(events),'abstention':x['question_id'].endswith('_abs')})
 # Fixed independent updates, contradiction, dependent revisions, early/late facts.
 for j,(name,city,newcity,day,newday) in enumerate([('Mira','Recife','Natal','Tuesday','Friday'),('Noah','Lima','Cusco','Monday','Thursday'),('Iris','Oslo','Bergen','Wednesday','Saturday'),('Enzo','Rome','Turin','Friday','Sunday')]):
  events=[f'{name} lives in {city}. {name} works for Orion. The current delivery address is {city}. The current appointment day is {day}. The reminder is on the day before the appointment. {name} likes tea and has a dog named Pixel. The project code is Cedar. The emergency contact is Livia.',f'Correction effective now: {name} moved to {newcity}. Replace the current delivery address with {newcity} too. The employer, pet, likes, project code and contact did not change.',f'Update effective now: the appointment moved from {day} to {newday}. The reminder must also move to the day before the new appointment. Keep the current city and delivery address. The emergency contact changed to Bruno.']
  before={'Tuesday':'Monday','Monday':'Sunday','Wednesday':'Tuesday','Friday':'Thursday'}[day]
  after={'Friday':'Thursday','Thursday':'Wednesday','Saturday':'Friday','Sunday':'Saturday'}[newday]
  states=[(city,day,before,'Livia'),(newcity,day,before,'Livia'),(newcity,newday,after,'Bruno')]
  qs=[]
  for step,(c,d,r,contact) in enumerate(states):
   qs.append({'step':step,'questions':[{'question':f'What is {name}\'s current delivery city?','answer':c,'obsolete':[city] if c!=city else []},{'question':'What is the current appointment day and reminder day?','answer':d+' '+r,'required':[d,r],'obsolete':[day] if d!=day else []},{'question':f'What is {name}\'s employer, dog name, project code and emergency contact?','answer':'Orion Pixel Cedar '+contact,'required':['Orion','Pixel','Cedar',contact],'obsolete':['Livia'] if contact!='Livia' else []}]})
  streams.append({'id':f'synthetic-{j}','family':'synthetic','events':events})
  evaluation.append({'id':f'synthetic-{j}','type':'dependent-update','states':qs})
 (P/'data/streams.json').write_text(json.dumps(streams,ensure_ascii=False,indent=2)+'\n')
 (P/'data/evaluation.json').write_text(json.dumps(evaluation,ensure_ascii=False,indent=2)+'\n')
 (P/'data/selection.json').write_text(json.dumps({'rule':'minimum SHA256(a90-v1:question_id) in each of six types excluding _abs, plus minimum among _abs; no length filtering','external':meta,'consumer_tokenizer':MODEL,'revision':REV},indent=2)+'\n')
 print(json.dumps(meta,indent=2));print('total updates',sum(len(x['events']) for x in streams))
if __name__=='__main__':main()
