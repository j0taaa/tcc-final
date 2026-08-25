//! Thin Python conversion boundary for `mwpc_parser`.

use std::time::Duration;

use mwpc_parser::{
    solve_with_options, BinaryProduction, CnfGrammar, SolveOptions, TerminalEdge, TerminalLabel,
    TerminalProduction, ValidationError, WeightedTerminalDag,
};
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBool, PyDict, PyList, PyModule};

fn value_error(context: &str, error: impl std::fmt::Display) -> PyErr {
    PyValueError::new_err(format!("{context}: {error}"))
}

fn extract_id(value: &Bound<'_, PyAny>, field_name: &str) -> PyResult<u64> {
    if value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(format!(
            "{field_name} must be a non-negative integer, not bool"
        )));
    }
    value.extract::<u64>().map_err(|error| {
        PyTypeError::new_err(format!(
            "{field_name} must be a non-negative integer: {error}"
        ))
    })
}

fn extract_id_attr(item: &Bound<'_, PyAny>, field_name: &str) -> PyResult<u64> {
    let value = item.getattr(field_name).map_err(|error| {
        PyTypeError::new_err(format!("missing integer field {field_name}: {error}"))
    })?;
    extract_id(&value, field_name)
}

fn extract_id_sequence(value: &Bound<'_, PyAny>, field_name: &str) -> PyResult<Vec<u64>> {
    if value.is_instance_of::<pyo3::types::PyString>()
        || value.is_instance_of::<pyo3::types::PyBytes>()
    {
        return Err(PyTypeError::new_err(format!(
            "{field_name} must be a sequence of non-negative integers"
        )));
    }
    let iterator = value.try_iter().map_err(|error| {
        PyTypeError::new_err(format!(
            "{field_name} must be a sequence of non-negative integers: {error}"
        ))
    })?;
    iterator
        .enumerate()
        .map(|(index, item)| {
            let item = item?;
            extract_id(&item, &format!("{field_name}[{index}]"))
        })
        .collect()
}

fn extract_id_sequence_attr(item: &Bound<'_, PyAny>, field_name: &str) -> PyResult<Vec<u64>> {
    let value = item.getattr(field_name).map_err(|error| {
        PyTypeError::new_err(format!("missing sequence field {field_name}: {error}"))
    })?;
    extract_id_sequence(&value, field_name)
}

fn extract_optional_id_attr(item: &Bound<'_, PyAny>, field_name: &str) -> PyResult<Option<u64>> {
    let value = item.getattr(field_name).map_err(|error| {
        PyTypeError::new_err(format!(
            "missing optional integer field {field_name}: {error}"
        ))
    })?;
    if value.is_none() {
        Ok(None)
    } else {
        extract_id(&value, field_name).map(Some)
    }
}

fn extract_label(value: &Bound<'_, PyAny>, field_name: &str) -> PyResult<TerminalLabel> {
    if value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(format!(
            "{field_name} must be a byte integer or non-empty string, not bool"
        )));
    }
    if let Ok(byte) = value.extract::<u8>() {
        return Ok(TerminalLabel::Byte(byte));
    }
    if let Ok(text) = value.extract::<String>() {
        return TerminalLabel::text(text).map_err(|error| value_error(field_name, error));
    }
    Err(PyTypeError::new_err(format!(
        "{field_name} must be a byte integer or non-empty string"
    )))
}

fn extract_grammar(grammar: &Bound<'_, PyAny>) -> PyResult<CnfGrammar> {
    let nonterminal_objects = grammar.getattr("nonterminals").map_err(|error| {
        PyTypeError::new_err(format!("grammar must expose nonterminals: {error}"))
    })?;
    let mut nonterminal_ids = Vec::new();
    for item in nonterminal_objects.try_iter().map_err(|error| {
        PyTypeError::new_err(format!("grammar.nonterminals must be iterable: {error}"))
    })? {
        nonterminal_ids.push(extract_id_attr(&item?, "symbol_id")?);
    }

    let terminal_objects = grammar
        .getattr("terminals")
        .map_err(|error| PyTypeError::new_err(format!("grammar must expose terminals: {error}")))?;
    let mut terminals = Vec::new();
    for item in terminal_objects.try_iter().map_err(|error| {
        PyTypeError::new_err(format!("grammar.terminals must be iterable: {error}"))
    })? {
        let item = item?;
        let terminal_id = extract_id_attr(&item, "symbol_id")?;
        let label = item.getattr("label").map_err(|error| {
            PyTypeError::new_err(format!("terminal must expose label: {error}"))
        })?;
        terminals.push((terminal_id, extract_label(&label, "terminal label")?));
    }

    let terminal_production_objects = grammar.getattr("terminal_productions").map_err(|error| {
        PyTypeError::new_err(format!("grammar must expose terminal_productions: {error}"))
    })?;
    let mut terminal_productions = Vec::new();
    for item in terminal_production_objects.try_iter().map_err(|error| {
        PyTypeError::new_err(format!(
            "grammar.terminal_productions must be iterable: {error}"
        ))
    })? {
        let item = item?;
        terminal_productions.push(TerminalProduction {
            production_id: extract_id_attr(&item, "production_id")?,
            head_id: extract_id_attr(&item, "head_id")?,
            terminal_id: extract_id_attr(&item, "terminal_id")?,
        });
    }

    let binary_production_objects = grammar.getattr("binary_productions").map_err(|error| {
        PyTypeError::new_err(format!("grammar must expose binary_productions: {error}"))
    })?;
    let mut binary_productions = Vec::new();
    for item in binary_production_objects.try_iter().map_err(|error| {
        PyTypeError::new_err(format!(
            "grammar.binary_productions must be iterable: {error}"
        ))
    })? {
        let item = item?;
        binary_productions.push(BinaryProduction {
            production_id: extract_id_attr(&item, "production_id")?,
            head_id: extract_id_attr(&item, "head_id")?,
            left_id: extract_id_attr(&item, "left_id")?,
            right_id: extract_id_attr(&item, "right_id")?,
        });
    }

    let start_nonterminal_id = extract_id_attr(grammar, "start_nonterminal_id")?;
    let accepts_empty = grammar
        .getattr("accepts_empty")
        .map_err(|error| {
            PyTypeError::new_err(format!("grammar must expose accepts_empty: {error}"))
        })?
        .extract::<bool>()
        .map_err(|error| PyTypeError::new_err(format!("accepts_empty must be bool: {error}")))?;
    CnfGrammar::new(
        nonterminal_ids,
        terminals,
        start_nonterminal_id,
        terminal_productions,
        binary_productions,
        accepts_empty,
    )
    .map_err(|error| value_error("invalid grammar", error))
}

fn extract_graph(graph: &Bound<'_, PyAny>) -> PyResult<WeightedTerminalDag> {
    let node_ids = extract_id_sequence_attr(graph, "node_ids")?;
    let start_node_id = extract_id_attr(graph, "start_node_id")?;
    let final_node_ids = extract_id_sequence_attr(graph, "final_node_ids")?;
    let edge_objects = graph
        .getattr("edges")
        .map_err(|error| PyTypeError::new_err(format!("graph must expose edges: {error}")))?;
    let mut edges = Vec::new();
    for (index, item) in edge_objects
        .try_iter()
        .map_err(|error| PyTypeError::new_err(format!("graph.edges must be iterable: {error}")))?
        .enumerate()
    {
        let item = item?;
        let label = item.getattr("terminal_label").map_err(|_| {
            PyValueError::new_err(format!(
                "graph.edges[{index}] is not a terminal edge; normalize epsilon edges first"
            ))
        })?;
        let weight = item
            .getattr("weight")
            .map_err(|error| PyTypeError::new_err(format!("edge must expose weight: {error}")))?
            .extract::<f64>()
            .map_err(|error| PyTypeError::new_err(format!("edge weight must be real: {error}")))?;
        edges.push(
            TerminalEdge::new(
                extract_id_attr(&item, "edge_id")?,
                extract_id_attr(&item, "source_state")?,
                extract_id_attr(&item, "target_state")?,
                extract_label(&label, "terminal label")?,
                weight,
                extract_optional_id_attr(&item, "provenance_token_edge_id")?,
                extract_id_sequence_attr(&item, "matched_proposal_ids")?,
            )
            .map_err(|error| value_error(&format!("invalid graph edge at index {index}"), error))?,
        );
    }
    WeightedTerminalDag::new(node_ids, start_node_id, final_node_ids, edges)
        .map_err(|error| value_error("invalid graph", error))
}

fn timeout_duration(timeout_seconds: Option<f64>) -> PyResult<Option<Duration>> {
    let Some(seconds) = timeout_seconds else {
        return Ok(None);
    };
    if !seconds.is_finite() || seconds < 0.0 {
        return Err(PyValueError::new_err(
            "timeout_seconds must be finite and non-negative",
        ));
    }
    Duration::try_from_secs_f64(seconds)
        .map(Some)
        .map_err(|error| value_error("invalid timeout_seconds", error))
}

fn append_labels(list: &Bound<'_, PyList>, labels: &[TerminalLabel]) -> PyResult<()> {
    for label in labels {
        match label {
            TerminalLabel::Byte(byte) => list.append(*byte)?,
            TerminalLabel::Text(text) => list.append(text)?,
        }
    }
    Ok(())
}

#[pyfunction(
    name = "solve",
    signature = (
        grammar,
        graph,
        *,
        timeout_seconds = None,
        deadline_check_interval = 1024,
        deterministic_work_limit = None
    )
)]
fn solve_py(
    py: Python<'_>,
    grammar: &Bound<'_, PyAny>,
    graph: &Bound<'_, PyAny>,
    timeout_seconds: Option<f64>,
    deadline_check_interval: u64,
    deterministic_work_limit: Option<u64>,
) -> PyResult<Py<PyAny>> {
    let grammar = extract_grammar(grammar)?;
    let graph = extract_graph(graph)?;
    let options = SolveOptions::new(
        timeout_duration(timeout_seconds)?,
        deadline_check_interval,
        deterministic_work_limit,
    )
    .map_err(|error| value_error("invalid solve options", error))?;
    let result = py
        .allow_threads(|| solve_with_options(&grammar, &graph, &options))
        .map_err(|error: ValidationError| value_error("Rust solver failure", error))?;

    let output = PyDict::new(py);
    let status_type = py.import("mwpc_exact")?.getattr("SolveStatus")?;
    output.set_item("status", status_type.call1((result.status.as_str(),))?)?;
    output.set_item("objective_value", result.objective_value)?;
    let labels = PyList::empty(py);
    let selected_proposal_ids = PyList::empty(py);
    let witness_graph_edge_ids = PyList::empty(py);
    let witness_token_edge_ids = PyList::empty(py);
    if let Some(certificate) = result.certificate {
        append_labels(&labels, &certificate.witness_terminal_labels)?;
        for proposal_id in certificate.selected_proposal_ids {
            selected_proposal_ids.append(proposal_id)?;
        }
        for edge_id in certificate.witness_graph_edge_ids {
            witness_graph_edge_ids.append(edge_id)?;
        }
        for token_edge_id in certificate.witness_token_edge_ids {
            witness_token_edge_ids.append(token_edge_id)?;
        }
    }
    output.set_item("selected_proposal_ids", selected_proposal_ids)?;
    output.set_item("witness_terminal_labels", labels)?;
    output.set_item("witness_graph_edge_ids", witness_graph_edge_ids)?;
    output.set_item("witness_token_edge_ids", witness_token_edge_ids)?;

    let diagnostics = PyDict::new(py);
    diagnostics.set_item("chart_entries", result.diagnostics.chart_entries)?;
    diagnostics.set_item("relaxations", result.diagnostics.relaxations)?;
    diagnostics.set_item("graph_nodes", result.diagnostics.graph_nodes)?;
    diagnostics.set_item("graph_edges", result.diagnostics.graph_edges)?;
    diagnostics.set_item(
        "grammar_nonterminals",
        result.diagnostics.grammar_nonterminals,
    )?;
    diagnostics.set_item(
        "grammar_productions",
        result.diagnostics.grammar_productions,
    )?;
    diagnostics.set_item(
        "elapsed_chart_seconds",
        result.diagnostics.elapsed_chart_seconds,
    )?;
    diagnostics.set_item(
        "elapsed_backtracking_seconds",
        result.diagnostics.elapsed_backtracking_seconds,
    )?;
    diagnostics.set_item(
        "elapsed_parser_seconds",
        result.diagnostics.elapsed_parser_seconds,
    )?;
    diagnostics.set_item("deadline_checks", result.diagnostics.deadline_checks)?;
    output.set_item("diagnostics", diagnostics)?;
    Ok(output.into_any().unbind())
}

#[pymodule]
fn mwpc_parser_py(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(solve_py, module)?)?;
    Ok(())
}
