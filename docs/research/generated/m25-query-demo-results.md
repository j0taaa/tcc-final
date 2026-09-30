# Consulta real e diagnóstico de suporte

One fixed geographic request; v2 is post-hoc application diagnosis. All eight attempts are retained. This is not a benchmark accuracy estimate, paired performance comparison, or evidence of decoder superiority.

| Fase | Política | Estado API | Forwards | Certificados conferidos | Chamada |
|---|---|---|---:|---:|---|
| 1 | confidence_0.8 | query_empty | 12 | 12 | `get_location(name='of "Belo Horizonte')` |
| 1 | catalog_map8 | query_empty | 8 | 0 | `get_location(name='of "Belo Horizonte')` |
| 1 | epic_lexical_32 | query_empty | 32 | 0 | `get_location(name='geographic coordinates of "Belo Horizonte')` |
| 1 | exact_b64 | query_empty | 3 | 3 | `get_location(name='geographic coordinates of "Belo Horizonte')` |
| 2 | confidence_0.8 | query_complete | 12 | 12 | `get_location(name='Belo Horizonte')` |
| 2 | catalog_map8 | query_complete | 8 | 0 | `get_location(name='Belo Horizonte')` |
| 2 | epic_lexical_32 | query_complete | 32 | 0 | `get_location (name= 'Belo Horizonte')` |
| 2 | exact_b64 | query_empty | 3 | 3 | `get_location(name='Find the geographic coordinates of')` |

Fontes, hashes, datas e suporte declarado ficam no JSON associado.
