"""Standalone scientific plots; no model or CUDA use."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/"evidence/analysis-v1.json").read_text())
MODES=["fixed_cpu","fixed_gpu","adaptive_cpu","adaptive_gpu","simple_cpu","reserve_cpu","epic"]
LABELS=["Fixo CPU","Fixo GPU","Adaptativo CPU","Adaptativo GPU","Expansão simples","Reserva 96 CPU","EPIC"]
fig,axes=plt.subplots(2,2,figsize=(12,7.3),layout="constrained")
colors=plt.get_cmap("tab10").colors
for col,family in enumerate(("flat","grouped")):
    rows={ (r["mode"],r["steps"]):r for r in DATA["summary"] if r["family"]==family }
    ax=axes[0,col]
    x=np.arange(len(MODES))
    for j,steps in enumerate((8,16)):
        values=[rows[m,steps]["median_seconds"] for m in MODES]
        ax.bar(x+(j-.5)*.36,values,.36,label=f"{steps} passos",color=colors[j])
    ax.set_xticks(x,LABELS,rotation=28,ha="right",fontsize=8)
    ax.set_ylabel("Decode sincronizado completo (s)")
    ax.set_title("JSON plano" if family=="flat" else "JSON agrupado")
    ax.legend(frameon=False)
    ax.spines[["top","right"]].set_visible(False)
    ax=axes[1,col]
    for j,(mode,label) in enumerate(zip(MODES,LABELS,strict=True)):
        xx=[rows[mode,s]["median_seconds"] for s in (8,16)]
        yy=[rows[mode,s]["correct_unique"] for s in (8,16)]
        ax.plot(xx,yy,"o-",label=label,color=colors[j],alpha=.7,markersize=5)
    ax.set_ylim(-.2,4.2)
    ax.set_yticks(range(5))
    ax.set_xlabel("Latência completa (s), 8 e 16 passos")
    ax.set_ylabel("Acertos únicos / 4")
    ax.text(.5,.6,"Todos os métodos: 0/4",transform=ax.transAxes,ha="center",fontsize=12)
    ax.spines[["top","right"]].set_visible(False)
handles,labels=axes[1,0].get_legend_handles_labels()
fig.legend(handles,labels,loc="outside lower center",ncol=4,frameon=False,fontsize=9)
fig.suptitle("A89 — avaliação prospectiva; três repetições por item, RTX 3080 Ti NF4",fontsize=13)
fig.savefig(HERE/"evidence/quality-latency.svg")
fig.savefig(HERE/"evidence/quality-latency.png",dpi=140)
print("Wrote SVG/PNG; matplotlib",matplotlib.__version__)
