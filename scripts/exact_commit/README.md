# Ferramentas de reprodução

Use os alvos da raiz em vez de memorizar comandos de módulos:

- `make evidence`: integridade dos dados, certificados e derivados do artigo.
- `make formal`: especificações Lean e exemplo canônico de certificado.
- `make demo`: exemplo público de inferência sobre um head já capturado.

Os módulos `build_*_results.py` verificam/regeneram os produtos correspondentes;
`--check` compara sem sobrescrever. `full_head_packet.py` audita a captura pública.
Os módulos `capture_*`, `mdlm_cpu.py` e `run_*` são ferramentas especializadas,
opt-in, para os protocolos originais; não integram os testes cotidianos.

A [reprodução](../../docs/reproducing.md) explica ambientes e limites. Para
comandos antigos, consulte o [histórico](../../docs/history/README.md).
