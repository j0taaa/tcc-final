# Full vocabulary posterior — development

Rows: 411/540. Statuses: {'complete': 331, 'resource_refusal': 80}.
Default/frozen candidate: local. Strong benefits: 0/18; sampling: 0.
Candidate benefit counts: {'local': 0, 'bidir_local': 0}

Prepared service costs include frame compilation, full marginals and shared actual forward.
| Case / masks | bidir_global wall / CPU | bidir_position wall / CPU | stack wall / CPU | local wall / CPU | rejection wall / CPU | Strong |
|---|---:|---:|---:|---:|---:|---|
| 017a7a6d / 4 | 0.170 / 0.220 | 0.164 / 0.214 | 0.156 / 0.207 | 0.172 / 0.222 | 0.123 / 0.174 | False |
| 017a7a6d / 8 | 0.860 / 0.896 | 0.630 / 0.666 | 0.325 / 0.361 | 0.840 / 0.876 | 0.204 / 0.240 | False |
| 017a7a6d / 16 | {'resource_refusal': 3} | {'resource_refusal': 3} | 12.856 / 12.904 | {'resource_refusal': 3} | 29.894 / 29.938 | False |
| 05dacb44 / 4 | 0.217 / 0.259 | 0.211 / 0.252 | 0.155 / 0.197 | 0.209 / 0.251 | 0.138 / 0.179 | False |
| 05dacb44 / 8 | 4.610 / 4.659 | 3.243 / 3.292 | 0.394 / 0.443 | 2.199 / 2.248 | 0.209 / 0.259 | False |
| 05dacb44 / 16 | {'resource_refusal': 2} | {'resource_refusal': 2} | 36.366 / 36.431 | {'resource_refusal': 2} | 3.014 / 3.087 | False |
| 079f141a / 4 | 0.154 / 0.200 | 0.162 / 0.208 | 0.150 / 0.196 | 0.163 / 0.210 | 0.117 / 0.163 | False |
| 079f141a / 8 | 0.492 / 0.538 | 0.453 / 0.499 | 0.300 / 0.346 | 0.481 / 0.527 | 0.208 / 0.254 | False |
| 079f141a / 16 | 25.606 / 25.651 | 23.080 / 23.125 | 11.850 / 11.898 | 14.388 / 14.435 | 0.394 / 0.445 | False |
| 0a4b768a / 4 | 0.169 / 0.210 | 0.181 / 0.221 | 0.164 / 0.205 | 0.181 / 0.222 | 0.114 / 0.155 | False |
| 0a4b768a / 8 | 1.045 / 1.090 | 0.842 / 0.886 | 0.351 / 0.396 | 0.785 / 0.830 | 0.208 / 0.253 | False |
| 0a4b768a / 16 | {'resource_refusal': 2} | {'resource_refusal': 2} | 43.105 / 43.143 | {'resource_refusal': 2} | 24.163 / 24.207 | False |
| 0bb39717 / 4 | 0.171 / 0.224 | 0.168 / 0.221 | 0.161 / 0.214 | 0.173 / 0.226 | 0.118 / 0.171 | False |
| 0bb39717 / 8 | 0.340 / 0.388 | 0.341 / 0.389 | 0.330 / 0.378 | 0.349 / 0.397 | 0.208 / 0.256 | False |
| 0bb39717 / 16 | 1.141 / 1.188 | 0.925 / 0.972 | 1.007 / 1.055 | 1.069 / 1.117 | 0.402 / 0.450 | False |
| 0ce7169f / 4 | 0.162 / 0.198 | 0.168 / 0.204 | 0.154 / 0.190 | 0.172 / 0.207 | 0.112 / 0.148 | False |
| 0ce7169f / 8 | 0.909 / 0.939 | 0.672 / 0.702 | 0.335 / 0.365 | 0.650 / 0.679 | 0.202 / 0.232 | False |
| 0ce7169f / 16 | {'resource_refusal': 2} | {'resource_refusal': 2} | 26.570 / 26.627 | {'resource_refusal': 2} | {'resource_refusal': 2} | False |

Full frozen vocabulary posterior, not whole-generation speed or semantic accuracy
Known lexer/semiring/quotient principles; world novelty unconfirmed

All startup/cold costs, refusals and exact mass retained in decision.json.
