//! Indexed max-plus dynamic program over an epsilon-free terminal DAG.

use std::collections::BTreeMap;
use std::time::{Duration, Instant};

use crate::types::{
    BinaryProduction, Certificate, CnfGrammar, Diagnostics, EdgeId, NodeId, NonterminalId,
    ProductionId, SolveResult, SolveStatus, TerminalId, TerminalLabel, TerminalProduction,
    ValidationError, WeightedTerminalDag,
};

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum Backpointer {
    Terminal {
        production_id: ProductionId,
        terminal_id: TerminalId,
        edge_id: EdgeId,
    },
    Binary {
        production_id: ProductionId,
        intermediate_state: NodeId,
        left_nonterminal_id: NonterminalId,
        right_nonterminal_id: NonterminalId,
    },
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct ChartEntry {
    pub score: f64,
    pub backpointer: Backpointer,
}

type SpanKey = (NodeId, NodeId);

/// Resource controls for one parser invocation.
#[derive(Clone, Debug)]
pub struct SolveOptions {
    timeout: Option<Duration>,
    deadline_check_interval: u64,
    deterministic_work_limit: Option<u64>,
}

impl SolveOptions {
    /// Build validated controls. The work limit is a deterministic test and
    /// reproducibility hook: a limit of zero times out before the first unit.
    pub fn new(
        timeout: Option<Duration>,
        deadline_check_interval: u64,
        deterministic_work_limit: Option<u64>,
    ) -> Result<Self, ValidationError> {
        if deadline_check_interval == 0 {
            return Err(ValidationError::new(
                "deadline check interval must be positive",
            ));
        }
        Ok(Self {
            timeout,
            deadline_check_interval,
            deterministic_work_limit,
        })
    }
}

impl Default for SolveOptions {
    fn default() -> Self {
        Self {
            timeout: None,
            deadline_check_interval: 1_024,
            deterministic_work_limit: None,
        }
    }
}

#[derive(Debug)]
struct DeadlineController {
    started: Instant,
    deadline: Option<Instant>,
    check_interval: u64,
    deterministic_work_limit: Option<u64>,
    work_units: u64,
    deadline_checks: u64,
}

impl DeadlineController {
    fn new(options: &SolveOptions) -> Result<Self, ValidationError> {
        let started = Instant::now();
        let deadline = options
            .timeout
            .map(|timeout| {
                started.checked_add(timeout).ok_or_else(|| {
                    ValidationError::new("timeout exceeds the platform Instant range")
                })
            })
            .transpose()?;
        Ok(Self {
            started,
            deadline,
            check_interval: options.deadline_check_interval,
            deterministic_work_limit: options.deterministic_work_limit,
            work_units: 0,
            deadline_checks: 0,
        })
    }

    fn expired_before_work(&mut self) -> bool {
        self.deadline_checks += 1;
        self.deterministic_work_limit == Some(0)
            || self
                .deadline
                .is_some_and(|deadline| Instant::now() >= deadline)
    }

    fn step(&mut self) -> bool {
        self.work_units = self.work_units.saturating_add(1);
        if self
            .deterministic_work_limit
            .is_some_and(|limit| self.work_units > limit)
        {
            self.deadline_checks += 1;
            return true;
        }
        if !self.work_units.is_multiple_of(self.check_interval) {
            return false;
        }
        self.deadline_checks += 1;
        self.deadline
            .is_some_and(|deadline| Instant::now() >= deadline)
    }
}

#[derive(Clone, Debug)]
pub(crate) struct ParseComputation {
    pub status: SolveStatus,
    pub entries: BTreeMap<SpanKey, BTreeMap<NonterminalId, ChartEntry>>,
    pub final_node_id: Option<NodeId>,
    pub diagnostics: Diagnostics,
}

impl ParseComputation {
    pub fn entry(
        &self,
        nonterminal_id: NonterminalId,
        source: NodeId,
        target: NodeId,
    ) -> Option<&ChartEntry> {
        self.entries
            .get(&(source, target))
            .and_then(|span| span.get(&nonterminal_id))
    }

    pub fn root_score(&self, grammar: &CnfGrammar, graph: &WeightedTerminalDag) -> Option<f64> {
        let final_node = self.final_node_id?;
        if final_node == graph.start_node_id() && grammar.accepts_empty() {
            return Some(0.0);
        }
        self.entry(
            grammar.start_nonterminal_id(),
            graph.start_node_id(),
            final_node,
        )
        .map(|entry| entry.score)
    }
}

#[cfg(test)]
pub(crate) fn run_max_plus(
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
) -> Result<ParseComputation, ValidationError> {
    run_max_plus_with_options(grammar, graph, &SolveOptions::default())
}

fn run_max_plus_with_options(
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
    options: &SolveOptions,
) -> Result<ParseComputation, ValidationError> {
    let mut controller = DeadlineController::new(options)?;
    let mut entries: BTreeMap<SpanKey, BTreeMap<NonterminalId, ChartEntry>> = BTreeMap::new();
    let mut relaxations = 0_u64;

    if controller.expired_before_work() {
        return Ok(finish_computation(
            SolveStatus::Timeout,
            entries,
            None,
            relaxations,
            grammar,
            graph,
            &controller,
        ));
    }

    let mut terminal_productions_by_label: BTreeMap<
        crate::types::TerminalLabel,
        Vec<&TerminalProduction>,
    > = BTreeMap::new();
    for production in grammar.terminal_productions() {
        if controller.step() {
            return Ok(finish_computation(
                SolveStatus::Timeout,
                entries,
                None,
                relaxations,
                grammar,
                graph,
                &controller,
            ));
        }
        let label = grammar
            .terminal_label(production.terminal_id)
            .expect("validated terminal production must reference a terminal")
            .clone();
        terminal_productions_by_label
            .entry(label)
            .or_default()
            .push(production);
    }
    for edge in graph.edges() {
        if controller.step() {
            return Ok(finish_computation(
                SolveStatus::Timeout,
                entries,
                None,
                relaxations,
                grammar,
                graph,
                &controller,
            ));
        }
        if let Some(productions) = terminal_productions_by_label.get(edge.terminal_label()) {
            for production in productions {
                if controller.step() {
                    return Ok(finish_computation(
                        SolveStatus::Timeout,
                        entries,
                        None,
                        relaxations,
                        grammar,
                        graph,
                        &controller,
                    ));
                }
                relaxations += 1;
                stable_update(
                    &mut entries,
                    (edge.source_state(), edge.target_state()),
                    production.head_id,
                    edge.weight(),
                    Backpointer::Terminal {
                        production_id: production.production_id,
                        terminal_id: production.terminal_id,
                        edge_id: edge.edge_id(),
                    },
                );
            }
        }
    }

    let mut binary_by_children: BTreeMap<(NonterminalId, NonterminalId), Vec<&BinaryProduction>> =
        BTreeMap::new();
    for production in grammar.binary_productions() {
        if controller.step() {
            return Ok(finish_computation(
                SolveStatus::Timeout,
                entries,
                None,
                relaxations,
                grammar,
                graph,
                &controller,
            ));
        }
        binary_by_children
            .entry((production.left_id, production.right_id))
            .or_default()
            .push(production);
    }

    let order = graph.topological_order();
    for width in 1..order.len() {
        for source_index in 0..(order.len() - width) {
            let target_index = source_index + width;
            let source = order[source_index];
            let target = order[target_index];
            let mut candidates = Vec::new();
            for middle in &order[(source_index + 1)..target_index] {
                if controller.step() {
                    return Ok(finish_computation(
                        SolveStatus::Timeout,
                        entries,
                        None,
                        relaxations,
                        grammar,
                        graph,
                        &controller,
                    ));
                }
                let Some(left_entries) = entries.get(&(source, *middle)) else {
                    continue;
                };
                let Some(right_entries) = entries.get(&(*middle, target)) else {
                    continue;
                };
                for (left_id, left) in left_entries {
                    for (right_id, right) in right_entries {
                        if controller.step() {
                            return Ok(finish_computation(
                                SolveStatus::Timeout,
                                entries,
                                None,
                                relaxations,
                                grammar,
                                graph,
                                &controller,
                            ));
                        }
                        let Some(productions) = binary_by_children.get(&(*left_id, *right_id))
                        else {
                            continue;
                        };
                        for production in productions {
                            let score = left.score + right.score;
                            if !score.is_finite() {
                                return Err(ValidationError::new(
                                    "max-plus objective overflowed finite f64 range",
                                ));
                            }
                            relaxations += 1;
                            candidates.push((
                                production.head_id,
                                score,
                                Backpointer::Binary {
                                    production_id: production.production_id,
                                    intermediate_state: *middle,
                                    left_nonterminal_id: *left_id,
                                    right_nonterminal_id: *right_id,
                                },
                            ));
                        }
                    }
                }
            }
            for (head_id, score, backpointer) in candidates {
                stable_update(&mut entries, (source, target), head_id, score, backpointer);
            }
        }
    }

    let mut finals = graph.final_node_ids().to_vec();
    finals.sort_by_key(|node| {
        (
            graph
                .topological_index(*node)
                .expect("validated final must have a topological index"),
            *node,
        )
    });
    let mut best_final = None;
    let mut best_score = None;
    for final_node in finals {
        if controller.step() {
            return Ok(finish_computation(
                SolveStatus::Timeout,
                entries,
                None,
                relaxations,
                grammar,
                graph,
                &controller,
            ));
        }
        let candidate = if final_node == graph.start_node_id() && grammar.accepts_empty() {
            Some(0.0)
        } else {
            entries
                .get(&(graph.start_node_id(), final_node))
                .and_then(|span| span.get(&grammar.start_nonterminal_id()))
                .map(|entry| entry.score)
        };
        if let Some(score) = candidate {
            if best_score.is_none_or(|current| score > current) {
                best_score = Some(score);
                best_final = Some(final_node);
            }
        }
    }

    Ok(finish_computation(
        if best_final.is_some() {
            SolveStatus::Optimal
        } else {
            SolveStatus::InfeasibleOnSupport
        },
        entries,
        best_final,
        relaxations,
        grammar,
        graph,
        &controller,
    ))
}

fn finish_computation(
    status: SolveStatus,
    entries: BTreeMap<SpanKey, BTreeMap<NonterminalId, ChartEntry>>,
    final_node_id: Option<NodeId>,
    relaxations: u64,
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
    controller: &DeadlineController,
) -> ParseComputation {
    let diagnostics = Diagnostics {
        chart_entries: entries.values().map(BTreeMap::len).sum::<usize>() as u64,
        relaxations,
        graph_nodes: graph.node_ids().len() as u64,
        graph_edges: graph.edges().len() as u64,
        grammar_nonterminals: grammar.nonterminal_ids().len() as u64,
        grammar_productions: grammar.production_count() as u64,
        elapsed_parser_seconds: controller.started.elapsed().as_secs_f64(),
        deadline_checks: controller.deadline_checks,
    };
    ParseComputation {
        status,
        entries,
        final_node_id,
        diagnostics,
    }
}

/// Solve one validated epsilon-free graph and return a certified result.
pub fn solve(
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
) -> Result<SolveResult, ValidationError> {
    solve_with_options(grammar, graph, &SolveOptions::default())
}

/// Solve with explicit deadline and deterministic work-budget controls.
pub fn solve_with_options(
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
    options: &SolveOptions,
) -> Result<SolveResult, ValidationError> {
    let solve_started = Instant::now();
    let computation = run_max_plus_with_options(grammar, graph, options)?;
    if computation.status != SolveStatus::Optimal {
        return SolveResult::without_certificate(computation.status, computation.diagnostics);
    }
    let certificate = reconstruct_certificate(&computation, grammar, graph)?;
    let mut diagnostics = computation.diagnostics;
    diagnostics.elapsed_parser_seconds = solve_started.elapsed().as_secs_f64();
    if options
        .timeout
        .is_some_and(|timeout| solve_started.elapsed() >= timeout)
    {
        diagnostics.deadline_checks += 1;
        return SolveResult::without_certificate(SolveStatus::Timeout, diagnostics);
    }
    SolveResult::optimal(certificate, diagnostics)
}

fn reconstruct_certificate(
    computation: &ParseComputation,
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
) -> Result<Certificate, ValidationError> {
    if computation.status != SolveStatus::Optimal {
        return Err(ValidationError::new(
            "cannot reconstruct a non-optimal chart",
        ));
    }
    let final_node = computation
        .final_node_id
        .ok_or_else(|| ValidationError::new("optimal chart omitted its final node"))?;
    if final_node == graph.start_node_id() {
        if !grammar.accepts_empty() {
            return Err(ValidationError::new(
                "empty path requires empty grammar acceptance",
            ));
        }
        return Certificate::new(0.0, vec![], vec![], vec![], vec![]);
    }

    let mut edge_ids = Vec::new();
    let reconstructed_tree_score = visit_backpointer(
        computation,
        grammar,
        graph,
        grammar.start_nonterminal_id(),
        graph.start_node_id(),
        final_node,
        &mut edge_ids,
    )?;
    let certificate = validate_and_build_certificate(graph, &edge_ids)?;
    let recorded_root_score = computation
        .root_score(grammar, graph)
        .ok_or_else(|| ValidationError::new("optimal chart omitted its root score"))?;
    if !scores_close(certificate.objective_value, reconstructed_tree_score)
        || !scores_close(certificate.objective_value, recorded_root_score)
    {
        return Err(ValidationError::new(
            "recomputed path objective does not match the root chart objective",
        ));
    }
    Ok(certificate)
}

#[allow(clippy::too_many_arguments)]
fn visit_backpointer(
    computation: &ParseComputation,
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
    nonterminal_id: NonterminalId,
    source: NodeId,
    target: NodeId,
    edge_ids: &mut Vec<EdgeId>,
) -> Result<f64, ValidationError> {
    let entry = computation
        .entry(nonterminal_id, source, target)
        .ok_or_else(|| {
            ValidationError::new(format!(
                "missing chart entry ({nonterminal_id}, {source}, {target})"
            ))
        })?;
    match &entry.backpointer {
        Backpointer::Terminal {
            production_id,
            terminal_id,
            edge_id,
        } => {
            let production = grammar
                .terminal_productions()
                .iter()
                .find(|production| production.production_id == *production_id)
                .ok_or_else(|| {
                    ValidationError::new(format!("unknown terminal production ID {production_id}"))
                })?;
            let edge = graph.edge(*edge_id).ok_or_else(|| {
                ValidationError::new(format!("unknown terminal edge ID {edge_id}"))
            })?;
            if production.head_id != nonterminal_id
                || production.terminal_id != *terminal_id
                || edge.source_state() != source
                || edge.target_state() != target
                || grammar.terminal_label(*terminal_id) != Some(edge.terminal_label())
            {
                return Err(ValidationError::new(
                    "terminal backpointer does not match its production, edge, and chart key",
                ));
            }
            if !scores_close(entry.score, edge.weight()) {
                return Err(ValidationError::new(
                    "terminal chart score does not equal its edge weight",
                ));
            }
            edge_ids.push(*edge_id);
            Ok(edge.weight())
        }
        Backpointer::Binary {
            production_id,
            intermediate_state,
            left_nonterminal_id,
            right_nonterminal_id,
        } => {
            let production = grammar
                .binary_productions()
                .iter()
                .find(|production| production.production_id == *production_id)
                .ok_or_else(|| {
                    ValidationError::new(format!("unknown binary production ID {production_id}"))
                })?;
            let source_index = graph
                .topological_index(source)
                .expect("chart source must be a graph node");
            let middle_index = graph
                .topological_index(*intermediate_state)
                .ok_or_else(|| ValidationError::new("unknown binary intermediate state"))?;
            let target_index = graph
                .topological_index(target)
                .expect("chart target must be a graph node");
            if !(source_index < middle_index && middle_index < target_index) {
                return Err(ValidationError::new(
                    "binary intermediate state lies outside its chart span",
                ));
            }
            if production.head_id != nonterminal_id
                || production.left_id != *left_nonterminal_id
                || production.right_id != *right_nonterminal_id
            {
                return Err(ValidationError::new(
                    "binary backpointer does not match its production",
                ));
            }
            let left_score = visit_backpointer(
                computation,
                grammar,
                graph,
                *left_nonterminal_id,
                source,
                *intermediate_state,
                edge_ids,
            )?;
            let right_score = visit_backpointer(
                computation,
                grammar,
                graph,
                *right_nonterminal_id,
                *intermediate_state,
                target,
                edge_ids,
            )?;
            let score = left_score + right_score;
            if !score.is_finite() || !scores_close(entry.score, score) {
                return Err(ValidationError::new(
                    "binary chart score does not equal its child-score sum",
                ));
            }
            Ok(score)
        }
    }
}

fn validate_and_build_certificate(
    graph: &WeightedTerminalDag,
    edge_ids: &[EdgeId],
) -> Result<Certificate, ValidationError> {
    let mut current = graph.start_node_id();
    let mut weights = Vec::with_capacity(edge_ids.len());
    let mut labels: Vec<TerminalLabel> = Vec::with_capacity(edge_ids.len());
    let mut proposal_ids = Vec::new();
    let mut token_edge_ids = Vec::with_capacity(edge_ids.len());
    for edge_id in edge_ids {
        let edge = graph
            .edge(*edge_id)
            .ok_or_else(|| ValidationError::new(format!("unknown witness edge ID {edge_id}")))?;
        if edge.source_state() != current {
            return Err(ValidationError::new(
                "reconstructed graph edges do not form a continuous path",
            ));
        }
        current = edge.target_state();
        weights.push(edge.weight());
        labels.push(edge.terminal_label().clone());
        proposal_ids.extend_from_slice(edge.matched_proposal_ids());
        token_edge_ids.push(edge.provenance_token_edge_id());
    }
    if !graph.final_node_ids().contains(&current) {
        return Err(ValidationError::new(
            "reconstructed graph path does not end at a final node",
        ));
    }
    let objective = compensated_sum(&weights);
    Certificate::new(
        objective,
        proposal_ids,
        labels,
        edge_ids.to_vec(),
        token_edge_ids,
    )
}

fn compensated_sum(values: &[f64]) -> f64 {
    let mut sum = 0.0;
    let mut compensation = 0.0;
    for value in values {
        let tentative = sum + value;
        if sum.abs() >= value.abs() {
            compensation += (sum - tentative) + value;
        } else {
            compensation += (value - tentative) + sum;
        }
        sum = tentative;
    }
    sum + compensation
}

fn scores_close(left: f64, right: f64) -> bool {
    let scale = left.abs().max(right.abs()).max(1.0);
    (left - right).abs() <= 1e-12 * scale
}

fn stable_update(
    entries: &mut BTreeMap<SpanKey, BTreeMap<NonterminalId, ChartEntry>>,
    span: SpanKey,
    nonterminal_id: NonterminalId,
    score: f64,
    backpointer: Backpointer,
) {
    let span_entries = entries.entry(span).or_default();
    match span_entries.get(&nonterminal_id) {
        Some(existing) if existing.score >= score => {}
        _ => {
            span_entries.insert(nonterminal_id, ChartEntry { score, backpointer });
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{TerminalEdge, TerminalLabel, TerminalProduction};

    fn pair_grammar() -> CnfGrammar {
        CnfGrammar::new(
            vec![0, 1, 2],
            vec![
                (10, TerminalLabel::Text("x".to_owned())),
                (20, TerminalLabel::Text("y".to_owned())),
            ],
            0,
            vec![
                TerminalProduction {
                    production_id: 2,
                    head_id: 1,
                    terminal_id: 10,
                },
                TerminalProduction {
                    production_id: 3,
                    head_id: 2,
                    terminal_id: 20,
                },
            ],
            vec![BinaryProduction {
                production_id: 1,
                head_id: 0,
                left_id: 1,
                right_id: 2,
            }],
            false,
        )
        .unwrap()
    }

    fn edge(
        edge_id: EdgeId,
        source: NodeId,
        target: NodeId,
        label: &str,
        weight: f64,
    ) -> TerminalEdge {
        TerminalEdge::new(
            edge_id,
            source,
            target,
            TerminalLabel::Text(label.to_owned()),
            weight,
            Some(edge_id),
            vec![edge_id],
        )
        .unwrap()
    }

    #[test]
    fn canonical_chain_matches_python_reference_score() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(7, 0, 1, "x", 2.0), edge(8, 1, 2, "y", 7.0)],
        )
        .unwrap();

        let result = run_max_plus(&pair_grammar(), &graph).unwrap();

        assert_eq!(result.status, SolveStatus::Optimal);
        assert_eq!(result.root_score(&pair_grammar(), &graph), Some(9.0));
        assert_eq!(result.diagnostics.relaxations, 3);
    }

    #[test]
    fn parallel_edges_select_the_heavier_path_deterministically() {
        let grammar = CnfGrammar::new(
            vec![0],
            vec![(10, TerminalLabel::Byte(b'x'))],
            0,
            vec![TerminalProduction {
                production_id: 0,
                head_id: 0,
                terminal_id: 10,
            }],
            vec![],
            false,
        )
        .unwrap();
        let graph = WeightedTerminalDag::new(
            vec![0, 1],
            0,
            vec![1],
            vec![
                TerminalEdge::new(8, 0, 1, TerminalLabel::Byte(b'x'), 2.0, None, vec![]).unwrap(),
                TerminalEdge::new(3, 0, 1, TerminalLabel::Byte(b'x'), 5.0, None, vec![]).unwrap(),
            ],
        )
        .unwrap();

        let result = run_max_plus(&grammar, &graph).unwrap();
        let root = result.entry(0, 0, 1).unwrap();

        assert_eq!(root.score, 5.0);
        assert!(matches!(
            root.backpointer,
            Backpointer::Terminal { edge_id: 3, .. }
        ));
    }

    #[test]
    fn valid_infeasible_input_returns_explicit_status_without_panic() {
        let graph =
            WeightedTerminalDag::new(vec![0, 1], 0, vec![1], vec![edge(0, 0, 1, "x", 100.0)])
                .unwrap();

        let result = run_max_plus(&pair_grammar(), &graph).unwrap();

        assert_eq!(result.status, SolveStatus::InfeasibleOnSupport);
        assert_eq!(result.final_node_id, None);
        assert_eq!(result.root_score(&pair_grammar(), &graph), None);
    }

    #[test]
    fn binary_index_skips_grammar_bodies_absent_from_child_charts() {
        let grammar = CnfGrammar::new(
            vec![0, 1, 2, 3, 4],
            vec![
                (10, TerminalLabel::Text("x".to_owned())),
                (20, TerminalLabel::Text("y".to_owned())),
            ],
            0,
            vec![
                TerminalProduction {
                    production_id: 0,
                    head_id: 1,
                    terminal_id: 10,
                },
                TerminalProduction {
                    production_id: 1,
                    head_id: 2,
                    terminal_id: 20,
                },
            ],
            vec![
                BinaryProduction {
                    production_id: 2,
                    head_id: 0,
                    left_id: 1,
                    right_id: 2,
                },
                BinaryProduction {
                    production_id: 3,
                    head_id: 0,
                    left_id: 3,
                    right_id: 4,
                },
            ],
            false,
        )
        .unwrap();
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(0, 0, 1, "x", 1.0), edge(1, 1, 2, "y", 1.0)],
        )
        .unwrap();

        let result = run_max_plus(&grammar, &graph).unwrap();

        assert_eq!(result.root_score(&grammar, &graph), Some(2.0));
        assert_eq!(result.diagnostics.relaxations, 3);
    }

    #[test]
    fn public_solve_reconstructs_path_labels_and_all_provenance() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![
                TerminalEdge::new(
                    7,
                    0,
                    1,
                    TerminalLabel::Text("x".to_owned()),
                    2.0,
                    Some(70),
                    vec![100, 101],
                )
                .unwrap(),
                TerminalEdge::new(
                    8,
                    1,
                    2,
                    TerminalLabel::Text("y".to_owned()),
                    7.0,
                    Some(80),
                    vec![102],
                )
                .unwrap(),
            ],
        )
        .unwrap();

        let result = solve(&pair_grammar(), &graph).unwrap();
        let certificate = result.certificate.unwrap();

        assert_eq!(result.status, SolveStatus::Optimal);
        assert_eq!(certificate.objective_value, 9.0);
        assert_eq!(certificate.witness_graph_edge_ids, vec![7, 8]);
        assert_eq!(
            certificate.witness_terminal_labels,
            vec![
                TerminalLabel::Text("x".to_owned()),
                TerminalLabel::Text("y".to_owned())
            ]
        );
        assert_eq!(certificate.selected_proposal_ids, vec![100, 101, 102]);
        assert_eq!(certificate.witness_token_edge_ids, vec![Some(70), Some(80)]);
    }

    #[test]
    fn public_infeasible_result_has_no_partial_certificate() {
        let graph =
            WeightedTerminalDag::new(vec![0, 1], 0, vec![1], vec![edge(0, 0, 1, "x", 100.0)])
                .unwrap();

        let result = solve(&pair_grammar(), &graph).unwrap();

        assert_eq!(result.status, SolveStatus::InfeasibleOnSupport);
        assert!(result.objective_value.is_none());
        assert!(result.certificate.is_none());
    }

    #[test]
    fn certificate_preserves_repeated_proposal_id_occurrences() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![
                TerminalEdge::new(
                    7,
                    0,
                    1,
                    TerminalLabel::Text("x".to_owned()),
                    2.0,
                    None,
                    vec![100],
                )
                .unwrap(),
                TerminalEdge::new(
                    8,
                    1,
                    2,
                    TerminalLabel::Text("y".to_owned()),
                    7.0,
                    None,
                    vec![100],
                )
                .unwrap(),
            ],
        )
        .unwrap();

        let result = solve(&pair_grammar(), &graph).unwrap();

        assert_eq!(
            result.certificate.unwrap().selected_proposal_ids,
            vec![100, 100]
        );
    }

    #[test]
    fn corrupted_backpointer_is_rejected_during_reconstruction() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(7, 0, 1, "x", 2.0), edge(8, 1, 2, "y", 7.0)],
        )
        .unwrap();
        let grammar = pair_grammar();
        let mut computation = run_max_plus(&grammar, &graph).unwrap();
        computation
            .entries
            .get_mut(&(0, 1))
            .unwrap()
            .get_mut(&1)
            .unwrap()
            .backpointer = Backpointer::Terminal {
            production_id: 999,
            terminal_id: 10,
            edge_id: 7,
        };

        let error = reconstruct_certificate(&computation, &grammar, &graph).unwrap_err();

        assert!(error.to_string().contains("unknown terminal production"));
    }

    #[test]
    fn deterministic_work_limit_returns_timeout_without_partial_certificate() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(7, 0, 1, "x", 2.0), edge(8, 1, 2, "y", 7.0)],
        )
        .unwrap();
        let options = SolveOptions::new(None, 1_024, Some(0)).unwrap();

        let result = solve_with_options(&pair_grammar(), &graph, &options).unwrap();

        assert_eq!(result.status, SolveStatus::Timeout);
        assert!(result.objective_value.is_none());
        assert!(result.certificate.is_none());
        assert_eq!(result.diagnostics.graph_nodes, 3);
        assert_eq!(result.diagnostics.graph_edges, 2);
        assert_eq!(result.diagnostics.grammar_nonterminals, 3);
        assert_eq!(result.diagnostics.grammar_productions, 3);
        assert_eq!(result.diagnostics.deadline_checks, 1);
    }

    #[test]
    fn adequate_deterministic_work_limit_preserves_optimal_result() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(7, 0, 1, "x", 2.0), edge(8, 1, 2, "y", 7.0)],
        )
        .unwrap();
        let options = SolveOptions::new(None, 2, Some(1_000)).unwrap();

        let result = solve_with_options(&pair_grammar(), &graph, &options).unwrap();

        assert_eq!(result.status, SolveStatus::Optimal);
        assert_eq!(result.objective_value, Some(9.0));
        assert!(result.diagnostics.deadline_checks > 1);
    }

    #[test]
    fn deadline_check_interval_must_be_positive() {
        let error = SolveOptions::new(Some(Duration::ZERO), 0, None).unwrap_err();

        assert!(error
            .to_string()
            .contains("deadline check interval must be positive"));
    }
}
