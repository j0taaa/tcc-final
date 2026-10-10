"""Independent exact original-ID oracles for certified depth approximation."""

from importlib import import_module

DepthCertificateCorrectness = import_module(
    "attempts.24-certified-depth-approximation.work.test_correctness"
).DepthCertificateCorrectness

CorpusIdentityTests = import_module(
    "attempts.24-certified-depth-approximation.work.test_corpus"
).CorpusIdentityTests
CertifiedAmplification = import_module(
    "attempts.24-certified-depth-approximation.work.test_amplification"
).CertifiedAmplification
CertifiedGeneration = import_module(
    "attempts.24-certified-depth-approximation.work.test_generation"
).CertifiedGeneration
