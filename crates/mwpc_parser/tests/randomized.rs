//! Independent small-instance checks for the production parser.

use std::collections::BTreeSet;

use mwpc_parser::{
    solve, BinaryProduction, CnfGrammar, SolveStatus, TerminalEdge, TerminalLabel,
    TerminalProduction, WeightedTerminalDag,
};

#[derive(Clone, Debug)]
struct Lcg(u64);

impl Lcg {
    fn new(seed: u64) -> Self {
        Self(seed)
    }

    fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        self.0
    }

    fn below(&mut self, upper: u64) -> u64 {
        self.next() % upper
    }

    fn coin(&mut self, numerator: u64, denominator: u64) -> bool {
        self.below(denominator) < numerator
    }
}

fn labels() -> Vec<(u64, TerminalLabel)> {
    vec![
        (10, TerminalLabel::Text("x".to_owned())),
        (11, TerminalLabel::Text("y".to_owned())),
    ]
}

fn grammar_for_case(case: u64) -> CnfGrammar {
    match case % 4 {
        0 => CnfGrammar::new(
            vec![0],
            labels(),
            0,
            vec![
                TerminalProduction {
                    production_id: 0,
                    head_id: 0,
                    terminal_id: 10,
                },
                TerminalProduction {
                    production_id: 1,
                    head_id: 0,
                    terminal_id: 11,
                },
            ],
            vec![],
            false,
        ),
        1 => CnfGrammar::new(
            vec![0, 1, 2],
            labels(),
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
                    terminal_id: 11,
                },
            ],
            vec![BinaryProduction {
                production_id: 2,
                head_id: 0,
                left_id: 1,
                right_id: 2,
            }],
            false,
        ),
        2 => CnfGrammar::new(
            vec![0],
            labels(),
            0,
            vec![
                TerminalProduction {
                    production_id: 0,
                    head_id: 0,
                    terminal_id: 10,
                },
                TerminalProduction {
                    production_id: 1,
                    head_id: 0,
                    terminal_id: 11,
                },
            ],
            vec![BinaryProduction {
                production_id: 2,
                head_id: 0,
                left_id: 0,
                right_id: 0,
            }],
            false,
        ),
        _ => CnfGrammar::new(
            vec![0, 1],
            labels(),
            0,
            vec![
                TerminalProduction {
                    production_id: 0,
                    head_id: 0,
                    terminal_id: 10,
                },
                TerminalProduction {
                    production_id: 1,
                    head_id: 1,
                    terminal_id: 10,
                },
                TerminalProduction {
                    production_id: 2,
                    head_id: 1,
                    terminal_id: 11,
                },
            ],
            vec![
                BinaryProduction {
                    production_id: 3,
                    head_id: 0,
                    left_id: 0,
                    right_id: 1,
                },
                BinaryProduction {
                    production_id: 4,
                    head_id: 0,
                    left_id: 1,
                    right_id: 0,
                },
            ],
            true,
        ),
    }
    .unwrap()
}

fn random_graph(seed: u64) -> WeightedTerminalDag {
    let mut random = Lcg::new(seed ^ 0x05ee_d5ee_da11_ce55);
    let node_count = 2 + random.below(5);
    let node_ids: Vec<_> = (0..node_count).collect();
    let mut edges = Vec::new();
    let mut edge_id = 0;
    for source in 0..node_count {
        for target in (source + 1)..node_count {
            if !random.coin(2, 5) {
                continue;
            }
            let parallel_count = if random.coin(1, 5) { 2 } else { 1 };
            for parallel_index in 0..parallel_count {
                let label = if random.coin(1, 2) { "x" } else { "y" };
                let weight = if parallel_index == 1 && random.coin(1, 2) {
                    edges
                        .last()
                        .map_or_else(|| random.below(10) as f64, TerminalEdge::weight)
                } else {
                    random.below(10) as f64
                };
                let proposal_ids = (weight > 0.0)
                    .then_some(vec![10_000 + edge_id])
                    .unwrap_or_default();
                edges.push(
                    TerminalEdge::new(
                        edge_id,
                        source,
                        target,
                        TerminalLabel::Text(label.to_owned()),
                        weight,
                        Some(20_000 + edge_id),
                        proposal_ids,
                    )
                    .unwrap(),
                );
                edge_id += 1;
            }
        }
    }
    let mut final_node_ids: Vec<_> = (0..node_count).filter(|_| random.coin(1, 3)).collect();
    if final_node_ids.is_empty() {
        final_node_ids.push(node_count - 1);
    }
    WeightedTerminalDag::new(node_ids, 0, final_node_ids, edges).unwrap()
}

fn recognizes(grammar: &CnfGrammar, word: &[TerminalLabel]) -> bool {
    if word.is_empty() {
        return grammar.accepts_empty();
    }
    let size = word.len();
    let mut chart = vec![vec![BTreeSet::new(); size + 1]; size];
    for (index, label) in word.iter().enumerate() {
        for production in grammar.terminal_productions() {
            if grammar.terminal_label(production.terminal_id) == Some(label) {
                chart[index][index + 1].insert(production.head_id);
            }
        }
    }
    for width in 2..=size {
        for source in 0..=(size - width) {
            let target = source + width;
            for middle in (source + 1)..target {
                let left = chart[source][middle].clone();
                let right = chart[middle][target].clone();
                for production in grammar.binary_productions() {
                    if left.contains(&production.left_id) && right.contains(&production.right_id) {
                        chart[source][target].insert(production.head_id);
                    }
                }
            }
        }
    }
    chart[0][size].contains(&grammar.start_nonterminal_id())
}

fn brute_force_objective(grammar: &CnfGrammar, graph: &WeightedTerminalDag) -> Option<f64> {
    struct Search<'a> {
        grammar: &'a CnfGrammar,
        graph: &'a WeightedTerminalDag,
        best: Option<f64>,
    }

    impl Search<'_> {
        fn visit(&mut self, node: u64, word: &mut Vec<TerminalLabel>, score: f64) {
            if self.graph.final_node_ids().contains(&node)
                && recognizes(self.grammar, word)
                && self.best.is_none_or(|best| score > best)
            {
                self.best = Some(score);
            }
            for edge in self.graph.outgoing_edges(node) {
                word.push(edge.terminal_label().clone());
                self.visit(edge.target_state(), word, score + edge.weight());
                word.pop();
            }
        }
    }

    let mut search = Search {
        grammar,
        graph,
        best: None,
    };
    search.visit(graph.start_node_id(), &mut Vec::new(), 0.0);
    search.best
}

fn validate_certificate(grammar: &CnfGrammar, graph: &WeightedTerminalDag) {
    let result = solve(grammar, graph).unwrap();
    let oracle = brute_force_objective(grammar, graph);
    match oracle {
        None => {
            assert_eq!(result.status, SolveStatus::InfeasibleOnSupport);
            assert!(result.objective_value.is_none());
            assert!(result.certificate.is_none());
        }
        Some(expected) => {
            assert_eq!(result.status, SolveStatus::Optimal);
            assert_eq!(result.objective_value, Some(expected));
            let certificate = result.certificate.unwrap();
            assert_eq!(certificate.objective_value, expected);
            assert!(recognizes(grammar, &certificate.witness_terminal_labels));

            let mut node = graph.start_node_id();
            let mut reward = 0.0;
            let mut expected_proposals = Vec::new();
            for (index, edge_id) in certificate.witness_graph_edge_ids.iter().enumerate() {
                let edge = graph.edge(*edge_id).unwrap();
                assert_eq!(edge.source_state(), node);
                assert_eq!(
                    edge.terminal_label(),
                    &certificate.witness_terminal_labels[index]
                );
                assert_eq!(
                    edge.provenance_token_edge_id(),
                    certificate.witness_token_edge_ids[index]
                );
                node = edge.target_state();
                reward += edge.weight();
                expected_proposals.extend_from_slice(edge.matched_proposal_ids());
            }
            assert!(graph.final_node_ids().contains(&node));
            assert_eq!(reward, expected);
            assert_eq!(certificate.selected_proposal_ids, expected_proposals);
        }
    }
}

#[test]
fn canonical_ambiguity_parallel_tie_and_multiple_final_fixture() {
    let grammar = grammar_for_case(2);
    let graph = WeightedTerminalDag::new(
        vec![0, 1, 2, 3],
        0,
        vec![2, 3],
        vec![
            TerminalEdge::new(
                0,
                0,
                1,
                TerminalLabel::Text("x".to_owned()),
                2.0,
                Some(10),
                vec![20],
            )
            .unwrap(),
            TerminalEdge::new(
                1,
                0,
                1,
                TerminalLabel::Text("x".to_owned()),
                2.0,
                Some(11),
                vec![21],
            )
            .unwrap(),
            TerminalEdge::new(
                2,
                1,
                2,
                TerminalLabel::Text("y".to_owned()),
                3.0,
                Some(12),
                vec![22],
            )
            .unwrap(),
            TerminalEdge::new(
                3,
                2,
                3,
                TerminalLabel::Text("x".to_owned()),
                5.0,
                Some(13),
                vec![23],
            )
            .unwrap(),
        ],
    )
    .unwrap();

    validate_certificate(&grammar, &graph);
    assert_eq!(solve(&grammar, &graph).unwrap().objective_value, Some(10.0));
}

#[test]
fn accepts_epsilon_normalization_output_as_an_epsilon_free_terminal_dag() {
    let grammar = grammar_for_case(0);
    // This direct 10 -> 30 edge is the shape emitted after an epsilon closure
    // saturates an original 10 -> 20 (epsilon), 20 -> 30 (x) path.
    let graph = WeightedTerminalDag::new(
        vec![10, 30],
        10,
        vec![30],
        vec![TerminalEdge::new(
            700,
            10,
            30,
            TerminalLabel::Text("x".to_owned()),
            4.0,
            Some(900),
            vec![1_100],
        )
        .unwrap()],
    )
    .unwrap();

    validate_certificate(&grammar, &graph);
}

#[test]
fn randomized_small_dags_match_independent_path_and_boolean_cyk_oracle() {
    for seed in 0..500 {
        let grammar = grammar_for_case(seed);
        let graph = random_graph(seed);
        let result = std::panic::catch_unwind(|| validate_certificate(&grammar, &graph));
        assert!(
            result.is_ok(),
            "randomized Rust oracle failure at seed {seed}"
        );
    }
}
