# Full vocabulary posterior — development

Rows: 264/702. Statuses: {'complete': 212, 'resource_refusal': 52}.
Default/frozen candidate: eps_global. Strong benefits: 0/18; sampling: 0.
Candidate benefit counts: {'eps_global': 0, 'eps_position': 0, 'eps_local': 0}

Prepared service costs include frame compilation, full marginals and shared actual forward.
| Case / masks | bidir_global wall / CPU | bidir_position wall / CPU | stack wall / CPU | eps_global wall / CPU | rejection wall / CPU | Strong |
|---|---:|---:|---:|---:|---:|---|
| 017a7a6d / 4 | 0.168 / 0.218 | 0.166 / 0.216 | 0.161 / 0.212 | 0.162 / 0.212 | 0.122 / 0.172 | False |
| 017a7a6d / 8 | 0.869 / 0.904 | 0.631 / 0.667 | 0.325 / 0.361 | 1.090 / 1.126 | 0.203 / 0.239 | False |
| 017a7a6d / 16 | {'resource_refusal': 1} | {'resource_refusal': 1} | 12.766 / 12.814 | {'resource_refusal': 1} | 37.408 / 37.453 | False |
| 05dacb44 / 4 | 0.217 / 0.258 | 0.216 / 0.258 | 0.155 / 0.196 | 0.240 / 0.281 | 0.142 / 0.183 | False |
| 05dacb44 / 8 | 4.637 / 4.685 | 3.263 / 3.312 | 0.390 / 0.439 | 7.606 / 7.654 | 0.209 / 0.258 | False |
| 05dacb44 / 16 | {'resource_refusal': 1} | {'resource_refusal': 1} | 36.269 / 36.333 | {'resource_refusal': 1} | 0.518 / 0.591 | False |
| 079f141a / 4 | 0.155 / 0.201 | 0.158 / 0.205 | 0.149 / 0.196 | 0.153 / 0.200 | 0.116 / 0.162 | False |
| 079f141a / 8 | 0.495 / 0.541 | 0.445 / 0.491 | 0.301 / 0.347 | 0.532 / 0.578 | 0.207 / 0.253 | False |
| 079f141a / 16 | 25.793 / 25.838 | 23.433 / 23.475 | 11.800 / 11.848 | {'resource_refusal': 1} | 0.397 / 0.448 | False |
| 0a4b768a / 4 | 0.171 / 0.211 | 0.180 / 0.220 | 0.162 / 0.202 | 0.170 / 0.210 | 0.114 / 0.154 | False |
| 0a4b768a / 8 | 1.054 / 1.098 | 0.849 / 0.894 | 0.358 / 0.403 | 1.513 / 1.557 | 0.206 / 0.251 | False |
| 0a4b768a / 16 | {'resource_refusal': 1} | {'resource_refusal': 1} | 43.119 / 43.157 | {'resource_refusal': 1} | 23.737 / 23.785 | False |
| 0bb39717 / 4 | 0.169 / 0.222 | 0.168 / 0.221 | 0.162 / 0.215 | 0.165 / 0.218 | 0.117 / 0.170 | False |
| 0bb39717 / 8 | 0.343 / 0.391 | 0.346 / 0.394 | 0.318 / 0.366 | 0.343 / 0.391 | 0.209 / 0.257 | False |
| 0bb39717 / 16 | 1.131 / 1.177 | 0.934 / 0.982 | 1.009 / 1.057 | 1.294 / 1.341 | 0.395 / 0.443 | False |
| 0ce7169f / 4 | 0.165 / 0.201 | 0.168 / 0.204 | 0.153 / 0.189 | 0.158 / 0.193 | 0.110 / 0.146 | False |
| 0ce7169f / 8 | 0.902 / 0.932 | 0.683 / 0.713 | 0.334 / 0.364 | 1.151 / 1.180 | 0.210 / 0.240 | False |
| 0ce7169f / 16 | {'resource_refusal': 1} | {'resource_refusal': 1} | 26.536 / 26.594 | {'resource_refusal': 1} | {'resource_refusal': 1} | False |

Full frozen vocabulary posterior, not whole-generation speed or semantic accuracy
Known lexer/semiring/quotient principles; world novelty unconfirmed

All startup/cold costs, refusals and exact mass retained in decision.json.
