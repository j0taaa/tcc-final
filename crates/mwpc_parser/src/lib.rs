//! Production weighted CFG-on-DAG parser for exact MWPC.
//!
//! This crate is implemented independently from the readable Python reference
//! solver. The public data contracts reject malformed inputs before solving.

pub mod types;

pub use types::{
    BinaryProduction, Certificate, CnfGrammar, Diagnostics, ExactnessScope, NonterminalId,
    ProductionId, SolveResult, SolveStatus, SupportKind, TerminalEdge, TerminalId, TerminalLabel,
    TerminalProduction, ValidationError, WeightedTerminalDag,
};
