# Primary source audit before the numeral prototype

2026-10-16 local date. Source inspection, not benchmark execution or an
exhaustive novelty review. No external project file was modified/executed.

* llguidance commit6cef6ed9c973c2a155a85f2bb1996320af28b289:
  [numeric.rs](https://github.com/guidance-ai/llguidance/blob/6cef6ed9c973c2a155a85f2bb1996320af28b289/parser/src/json/numeric.rs),
  SHA256c42cca7e3b03bfd92801f914427acf2912025373a5d979ea08cee2e6ddfddd39.
  Directly read Decimal/TryFrom, integer-range construction and the COMPLETE
  rx_float_range function, lines347--506. Its unrestricted (None,None) branch
  allows an exponent; the bounded positive [1,2) branch constructs decimal
  integer/fraction alternatives without exponent forms. The broad feature
  list in docs/json_schema.md does not establish full lexical completeness.
* XGrammar commit7e269d56c74c89de52bc8c31e42191155416371f:
  [json_schema_converter.cc](https://github.com/mlc-ai/xgrammar/blob/7e269d56c74c89de52bc8c31e42191155416371f/cpp/json_schema_converter.cc),
  SHA256db1cb65e61b4a2ef91e3a658a098483dd249349a3f9a31a6fcbe3ef6b0d430c2.
  Directly read GenerateNumber's bounded/unbounded dispatch, lines2701--2740;
  the NumberGenerator interface/comments, lines4240--4318; and the COMPLETE
  FloatRangeRegex/wrapper, lines4937--5040. The bounded JSON-schema dispatch
  passes fraction precision6; the range function constructs signed decimal
  grid forms, without exponent branches. Its bound-grid rounding is explicitly
  directed toward soundness. This is a source-level support distinction, not
  an assertion of a bug or of behaviour in every other entry point/version.

Raw source files were downloaded ONLY for inspection into the external cache
/home/jota/.cache/tcc-final/numeric-reading; hashes and immutable links above
allow retrieval. No native package install, model read/forward, timing or
numeric test of either library occurred in this reading audit.

Other searches surfaced canonical/precision-limited range frontends and
scientific-notation lexers. Their snippets do not establish semantic interval
completeness or absence of antecedents. No negative search result is priority
evidence. Follow-up must inspect complete numeric register/digit-DP and bounded
regular-expression constructions before claiming a scientific separation.

ODD/Mosaic and FactorDLM already supply weighted finite-automata/factor
conditioning. A59 does not claim the projection law, token quotient or generic
sum-product as new. The candidate concerns the number-language compiler.

Later same-turn standards check, after the small prototype (not attributed to
the pre-code reading): [RFC8259 Section6](https://www.rfc-editor.org/rfc/rfc8259#section-6)
gives fraction/exponent syntax and permits implementations to set numeric
range/precision limits. [JSON Schema2020-12 validation Sections4.2/6.2](https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-01)
uses numeric comparisons without adding a precision bound. A59 chooses exact
decimal semantics as its explicit contract. This does not establish that a
restricted production frontend is violating RFC8259, nor does it preserve a
consumer's binary64-rounding semantics automatically.
