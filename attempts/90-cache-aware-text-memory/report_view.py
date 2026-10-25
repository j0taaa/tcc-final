"""Self-contained result table; no remote assets and no hidden aggregation."""
import json,html
from pathlib import Path
P=Path(__file__).resolve().parent
s=json.loads((P/'evidence/summary-v1a.json').read_text());rows=s['methods']
labels={'dllm_local':'dLLM · edição local','ar_local':'AR · mesma edição local','dllm_global':'dLLM · reescrita global','ar_global':'AR · resumo incremental','extractive':'Seleção extrativa','raw_tail':'Cauda textual','full_history':'Histórico completo + cache'}
tr=[]
for key in ['dllm_local','ar_local','dllm_global','ar_global','extractive','raw_tail','full_history']:
 r=rows[key]['all'];a=rows[key]['synthetic'];e=rows[key]['external']
 tr.append(f'<tr><td>{html.escape(labels[key])}</td><td>{r["edit_seconds"]:.1f}</td><td>{r["reader_seconds"]:.1f}</td><td><b>{r["total_seconds"]:.1f}</b></td><td>{a["synthetic_all_correct"]}/12</td><td>{e["external_full_correct"]}/7</td><td>{r["reader_reused"]:,}</td></tr>')
doc='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{font-family:var(--font-sans,system-ui);color:var(--foreground);margin:0;line-height:1.45}h2{font-size:19px;margin:0 0 8px}p{margin:8px 0 16px;font-size:13px}.small{color:var(--muted-foreground);font-size:12px}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}th,td{padding:9px 5px;border-bottom:1px solid var(--border,#ddd);text-align:right;white-space:nowrap}th{font-weight:600;color:var(--muted-foreground)}th:first-child,td:first-child{text-align:left;white-space:normal;min-width:150px}tbody tr:first-child{background:var(--accent-surface,transparent)}a{color:var(--accent-foreground)}.note{border-left:3px solid var(--border,#aaa);padding-left:12px;margin:16px 0}h3{font-size:14px;margin:18px 0 6px}</style>
<h2>A90 · Piloto de memória textual e custo de cache</h2>
<p>4 histórias sintéticas × 3 estados e 7 histórias LongMemEval oracle, escolhidas por hash de ID. Modelos congelados; sem treinamento. Consumidor comum Qwen 1,5B FP32 (emenda V1a); GPU isolada por lock.</p>
<div class="wrap"><table><thead><tr><th>Método</th><th>Edição<br>segundos</th><th>Leitor<br>segundos</th><th>Total<br>segundos</th><th>Sintético<br>completo</th><th>Externo<br>completo*</th><th>Tokens KV<br>reutilizados</th></tr></thead><tbody>'''+''.join(tr)+'''</tbody></table></div>
<p class="small">Total = seleção + montagem + edição + respostas, somados de fases medidas separadamente. Tempos residentes, uma execução por célula; não representam latência intercalada nem incluem carga de modelos. Histórico completo ultrapassa o orçamento de compactação de 320 tokens.</p>
<div class="note"><p>* Utilidade externa: revisão semântica pelo agente com rótulos de método ocultos, rubricada antes de abrir a chave. Não é avaliação humana independente nem acurácia oficial LongMemEval. Acerto sintético completo exige menções de todos os fatos; erros de fatos superados são auditados no relatório.</p></div>
<h3>Limite da contribuição</h3><p><a href="https://aclanthology.org/2026.acl-long.2036/">DiffuAgent</a> já usa memória incremental dLLM → AR. <a href="https://arxiv.org/abs/2609.37012">CADOC</a> já agenda compactação pelo custo do cache. <a href="https://arxiv.org/abs/2510.00615">ACON</a> já otimiza compressão com sinal downstream. A heurística deste piloto não estabelece contribuição original substancial.</p></html>'''
(P/'evidence/results.html').write_text(doc)
print(P/'evidence/results.html')
