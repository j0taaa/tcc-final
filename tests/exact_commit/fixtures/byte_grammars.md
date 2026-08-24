# Byte grammar fixtures, version 1

These grammars consume raw byte integers directly. All examples in
`byte_grammar_corpus.json` are ASCII strings encoded byte-for-byte without
Unicode normalization, whitespace insertion, or tokenization. The source
grammars are normalized by `mwpc_exact.reference.normalization`; their corpus
labels are checked with the independent Boolean CNF recognizer.

## `arithmetic_expression_bytes_v1`

```text
expression       ::= expression ("+" | "-") term | term
term             ::= term ("*" | "/") factor | factor
factor           ::= unsigned_integer | "(" expression ")"
unsigned_integer ::= digit+
digit            ::= "0" ... "9"
```

The grammar encodes conventional multiplication/division precedence over
addition/subtraction and left associativity. It deliberately allows leading
zeros. It has no whitespace, signs/unary operators, decimal points,
exponents, identifiers, calls, or implicit multiplication. Parentheses cannot
be empty.

## `tiny_assignment_dsl_bytes_v1`

```text
program          ::= statement (LF statement)*
statement        ::= "set " name "=" unsigned_integer ";"
                   | "print " name ";"
name             ::= lowercase (lowercase | digit | "_")*
unsigned_integer ::= digit+
lowercase        ::= "a" ... "z"
digit            ::= "0" ... "9"
LF               ::= byte 0x0a
```

Exactly one ASCII space follows each keyword; no other whitespace is accepted.
Programs are non-empty. Statements are separated by exactly one LF. There is
no leading/trailing LF or blank lines. Integers are unsigned and may have
leading zeros. The DSL has no declarations beyond `set`, expressions,
comments, quoted names, Unicode identifiers, or execution semantics; this
fixture defines syntax only.

## `lower_ascii_json_value_subset_v1`

```text
value      ::= "null" | "true" | "false" | integer | string | array | object
integer    ::= "0" | nonzero digit*
string     ::= '"' (lowercase | digit | " ")* '"'
array      ::= "[" "]" | "[" value ("," value)* "]"
object     ::= "{" "}" | "{" member ("," member)* "}"
member     ::= string ":" value
nonzero    ::= "1" ... "9"
digit      ::= "0" ... "9"
lowercase  ::= "a" ... "z"
```

This is a deliberately named subset of JSON values, not a JSON grammar. It
accepts recursive arrays/objects, lowercase literals, JSON-compatible
non-negative integers without leading zeros, and strings containing only
lowercase ASCII letters, digits, and byte `0x20`. It omits negative,
fractional, and exponent numbers; escapes; uppercase/non-ASCII string
characters; and all structural whitespace. Trailing commas are rejected and
object keys use the same restricted string syntax.
