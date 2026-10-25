"""Download only the pinned dataset and AR snapshot; no GPU, no training."""
import hashlib,json,os
from pathlib import Path
P=Path(__file__).resolve().parent

def main():
 import requests
 from huggingface_hub import snapshot_download
 source=json.loads((P/'data/source.json').read_text());dest=P/'data/longmemeval_oracle_cleaned.json'
 if not dest.exists():
  r=requests.get(source['url'],timeout=120);r.raise_for_status();dest.write_bytes(r.content)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==source['sha256']
 snapshot_download('unsloth/Qwen2.5-3B-Instruct-bnb-4bit',revision='2672b588848527e456d320c11926c794539f47d5',allow_patterns=['*.json','*.safetensors','*.txt'],max_workers=2)
 snapshot_download('Qwen/Qwen2.5-1.5B-Instruct',revision='989aa7980e4cf806f80c7fef2b1adb7bc71aa306',allow_patterns=['*.json','*.safetensors','*.txt','LICENSE'],max_workers=2)
 print('Pinned inputs ready. Existing LLaDA snapshot is required; see models.json.')
if __name__=='__main__':main()
