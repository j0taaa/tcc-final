"""Build a self-contained review view from frozen aggregates. CPU only."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
data=json.loads((HERE/"evidence/analysis-v1.json").read_text())
template='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:var(--font-sans,system-ui);color:var(--foreground,#20252c);margin:0;line-height:1.5}
p{margin:8px 0 14px}.lead{font-size:21px;font-weight:650;margin:0 0 8px}.muted,small{color:var(--muted-foreground,#626971)}
.facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin:16px 0}.facts strong{font-size:25px;display:block}.facts span{font-size:12px}
.controls{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0 10px}label{font-size:13px}select{display:block;padding:7px 28px 7px 9px;background:var(--background,white);color:inherit;border:1px solid var(--border,#ccd1d7);border-radius:6px;font:inherit}
svg{width:100%;height:250px;display:block;overflow:visible}svg text{fill:var(--foreground,#20252c);font-family:inherit;font-size:12px}
.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:12px}th,td{padding:9px 6px;border-bottom:1px solid var(--border,#e1e4e8);text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{color:var(--muted-foreground,#626971);font-weight:550}
.note{font-size:13px;margin-top:14px}details{margin:16px 0;font-size:13px}summary{cursor:pointer;font-weight:600}a{color:var(--primary,#2876b7)}
@media(max-width:450px){.facts{gap:15px;grid-template-columns:1fr}.facts strong{font-size:22px}th,td{padding:8px 4px}.lead{font-size:19px}svg{display:none}}
</style>
<p class="lead">A89: sem benefício neural demonstrado</p>
<p>384 decodes reais na RTX 3080 Ti. Nenhum método acertou uma tarefa inteira. A hipótese não passou o critério de continuidade; não foi escrito kernel próprio.</p>
<div class="facts"><div><strong>0/8</strong><span>itens TEST acertados por qualquer método</span></div><div><strong>1,44%</strong><span>mediana de custo do verificador CPU em VAL</span></div><div><strong>96/96</strong><span>pares CPU/GPU com decisões e IDs iguais</span></div></div>
<div class="controls"><label>Tarefa<select id="family"><option value="flat">JSON plano</option><option value="grouped">JSON agrupado</option></select></label><label>Orçamento<select id="steps"><option value="8">8 passos</option><option value="16">16 passos</option></select></label></div>
<svg id="bars" viewBox="0 0 680 250" role="img" aria-label="Latência completa por método"></svg>
<div class="scroll"><table><thead><tr><th>Método</th><th>Tempo, s</th><th>Acerto</th><th>Válidos</th><th>Forwards</th><th>Posições</th></tr></thead><tbody id="rows"></tbody></table></div>
<p class="note">Latência sincronizada do decode inteiro; mediana por item após três repetições. Acerto e validade em quatro itens por família. As oito tarefas derivam de quatro listas BBH, sem 336 amostras independentes. Todos os pontos das curvas de acerto × latência ficam em zero.</p>
<details><summary>Custos e limites da conclusão</summary><p>3.996 forwards TEST e 332,215 s somados de decode. Cada braço adaptativo inseriu 744 posições. A GPU Torch foi mais lenta; um kernel otimizado não foi avaliado porque o perfil CPU ficou abaixo do gate de 10%.</p><p>Carga do modelo: 249,13 s em VAL e 81,33 s em TEST; compilação C++ sem cache: 0,859 s. O uso frio completo é parcialmente medido: inicialização/imports anteriores ao primeiro marcador não têm cronômetro global. Picos alocados: ~5,45 GiB nos métodos próprios e ~6,13 GiB no EPIC.</p><p>O domínio é um subconjunto recursivo de JSON; não qualquer CFG. O controle simples é inspirado em DAEDAL. EPIC recebeu otimizações comuns. O programa determinístico de ordenação resolve os oito itens; o zero neural geral impede concluir que toda expansão gramatical é inútil.</p></details>
<details><summary>Antecedentes e originalidade</summary><p>DAEDAL, DreamOn e Mündler já tratam expansão; Gram2Token já usa GPU; FactorDLM cobre inferência finita CPU/CUDA. <a href="https://arxiv.org/html/2608.28229">SWYB</a> e <a href="https://arxiv.org/html/2605.13076">TruncProof</a> já consideram orçamento em tokens. Não foi estabelecida contribuição própria para alocação conjunta em CFGs gerais.</p></details>
<script>
const data=DATA;
const modes=['fixed_cpu','fixed_gpu','adaptive_cpu','adaptive_gpu','simple_cpu','reserve_cpu','epic'];
const names=['Fixo CPU · 32','Fixo GPU · 32','Adaptativo CPU','Adaptativo GPU','Expansão simples','Reserva CPU · 96','EPIC · 96'];
const colors=['#53779b','#8fa9bd','#cf853c','#e3ad75','#838e6a','#839da0','#ad8eac'];
function update(){
 const f=document.getElementById('family').value,s=+document.getElementById('steps').value;
 const rows=modes.map(m=>data.find(r=>r.family===f&&r.steps===s&&r.mode===m));
 const max=Math.max(...rows.map(r=>r.median_seconds))*1.12;
 document.getElementById('rows').innerHTML=rows.map((r,i)=>`<tr><td>${names[i]}</td><td>${r.median_seconds.toFixed(3).replace('.',',')}</td><td>${r.correct_unique}/4</td><td>${r.valid_unique}/4</td><td>${r.median_forwards}</td><td>${r.median_capacity.toString().replace('.',',')}</td></tr>`).join('');
 document.getElementById('bars').innerHTML='<text x="0" y="15">Decode completo, em segundos · menor é mais rápido</text>'+rows.map((r,i)=>{const y=31+i*29,w=430*r.median_seconds/max;return `<text x="0" y="${y+16}">${names[i]}</text><rect x="165" y="${y}" width="${w}" height="21" rx="2" fill="${colors[i]}"><title>${names[i]}: ${r.median_seconds.toFixed(4)} s</title></rect><text x="${172+w}" y="${y+16}">${r.median_seconds.toFixed(3).replace('.',',')}</text>`}).join('');
 console.assert(rows.length===7&&rows.every(r=>r.correct_unique===0),'Unexpected result table');
}
document.querySelectorAll('select').forEach(e=>e.addEventListener('change',update));update();
console.log('A89: 28 aggregate cells, seven methods; all functional scores zero.');
</script></html>'''
(HERE/"evidence/review.html").write_text(template.replace("DATA",json.dumps(data["summary"])))
print("Wrote self-contained review.html")
