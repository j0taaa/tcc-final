# Controle final e razão exata de tentativas

O controle de rejeição constante, mesmo fortalecido, não esgota alternativas
clássicas. Antes de chamar um lote concluído de vantagem própria, comparar uma
inclinação exponencial única com majorante global. Esta é uma checagem adicional
de adversário competente, não outra contribuição ou seleção de novos casos.

Para `L<H`, aproximar `log(f(L)/f(H))/(H-L)` com 80 dígitos Decimal e converter
o resultado a uma fração racional. Essa secante minimiza o normalizador do
majorante exponencial global: sua derivada é `L-E_t[S]<0` antes do cruzamento
dos extremos e `H-E_t[S]>0` depois. É o controle competente dessa família.
Clampar a taxa por `k/(L+c_min)` e por
`bit_length(floor(f(L)/f(H)))/(H-L)` protege o argumento positivo das séries.
Ambas são cotas superiores da secante exata. Não anunciar a aproximação como
um ótimo real exato. Escolher a taxa aproximadamente não aproxima a lei alvo.

Pela convexidade, `log f(s)+t*s` atinge seu máximo
nos extremos. Logo `C=max(f(L) exp(tL), f(H) exp(tH))` dá o majorante
`C exp(-tS)`. Enclosures superiores racionais/dyádicos preservam a dominação;
aceitar com `f(S)/Rbar(y)` mantém o alvo exato. O caso constante usa a base.
Se `H/L<=2`, `tH<=2k`; caso contrário a segunda cota limita o argumento a
`O(k log(kappa))`. Não esconder uma exponencial ideal ou custo de precisão.

Para todos os samplers de rejeição, `E[N]=N_proposta/Z_alvo`. Portanto a razão
de duas esperanças é a razão de seus normalizadores de proposta, **sem calcular
o normalizador do alvo**. Guardar esses valores como frações com inteiros em
hexadecimal e conferir a identidade por enumeração pequena. A diferença em
tentativas não implica igual diferença em segundos ou custo neural.

Os oito critérios do README continuam: objetivo, aplicação e contratos iguais;
inclinação/covariância são conhecidos; avanço próprio continua candidato;
benefício estatístico não é treinamento realizado; medir preparação, perdas
e recusas; publicação/novidade não serão inferidas do controle que perder.

Campanha adicional declarada: os mesmos nove inputs, eventos/sementes e
budgets; mistura dyádica com limites estruturais, rejeição constante ótima,
enumeração e a inclinação única; três repetições e lotes 1/4/16. Registrar as
quatro ordens efetivamente usadas. A rotação de três repetições não constitui
balanceamento estatístico perfeito de quatro métodos. Usar também o melhor
custo dos controles anteriores; não cobrar min/max onde foi desnecessário.
Este conjunto já foi usado no desenvolvimento, não é avaliação externa nova.
