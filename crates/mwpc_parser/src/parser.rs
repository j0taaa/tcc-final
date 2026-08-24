//! Indexed max-plus dynamic program over an epsilon-free terminal DAG.

use std::collections::BTreeMap;
use std::time::Instant;

use crate::types::{
    BinaryProduction, CnfGrammar, Diagnostics, EdgeId, NodeId, NonterminalId, ProductionId,
    SolveStatus, TerminalId, TerminalProduction, ValidationError, WeightedTerminalDag,
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

pub(crate) fn run_max_plus(
    grammar: &CnfGrammar,
    graph: &WeightedTerminalDag,
) -> Result<ParseComputation, ValidationError> {
    let started = Instant::now();
    let mut entries: BTreeMap<SpanKey, BTreeMap<NonterminalId, ChartEntry>> = BTreeMap::new();
    let mut relaxations = 0_u64;

    let mut terminal_productions_by_label: BTreeMap<
        crate::types::TerminalLabel,
        Vec<&TerminalProduction>,
    > = BTreeMap::new();
    for production in grammar.terminal_productions() {
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
        if let Some(productions) = terminal_productions_by_label.get(edge.terminal_label()) {
            for production in productions {
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
                let Some(left_entries) = entries.get(&(source, *middle)) else {
                    continue;
                };
                let Some(right_entries) = entries.get(&(*middle, target)) else {
                    continue;
                };
                for (left_id, left) in left_entries {
                    for (right_id, right) in right_entries {
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

    let chart_entries = entries.values().map(BTreeMap::len).sum::<usize>() as u64;
    let diagnostics = Diagnostics {
        chart_entries,
        relaxations,
        graph_nodes: graph.node_ids().len() as u64,
        graph_edges: graph.edges().len() as u64,
        grammar_nonterminals: grammar.nonterminal_ids().len() as u64,
        grammar_productions: grammar.production_count() as u64,
        elapsed_parser_seconds: started.elapsed().as_secs_f64(),
        deadline_checks: 0,
    };
    Ok(ParseComputation {
        status: if best_final.is_some() {
            SolveStatus::Optimal
        } else {
            SolveStatus::InfeasibleOnSupport
        },
        entries,
        final_node_id: best_final,
        diagnostics,
    })
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
}
