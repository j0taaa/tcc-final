# Unmodified NNCPv2 source excerpts

From Fabrice Bellard's original NNCPv2 archive2021-02-06-1, retrieved from
https://bellard.org/nncp/nncp_v2-2021-02-06-1.tar.gz . provenance.json gives
the archive/member SHA256 values. These are THIRD-PARTY sources, not original
A70 implementation. Original bytes and attribution headers are preserved.

mem_transformer.py credits Transformer-XL and Fabrice Bellard's2020
modifications under Apache-2.0; the complete license is Apache-2.0.txt.
arithmetic_coder.py credits Project Nayuki and the package readme declares
the arithmetic coder MIT and the credited tensorflow-compress simplifications
public domain; MIT text is retained in MIT-Nayuki.txt. The original readme
describes its remaining licensing/provenance.

Only mem_transformer.py/arithmetic_coder.py are imported by the separately
frozen resource driver. nncp.py and shell scripts are READ-ONLY operation/
configuration references, not executed. No LibNC binary, model checkpoint,
corpus or original published GPU/Apex runtime is bundled or run.
