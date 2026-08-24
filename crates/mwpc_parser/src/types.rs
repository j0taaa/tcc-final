//! Validated stable-ID contracts shared by the Rust solver and PyO3 binding.

use std::cmp::Reverse;
use std::collections::{BTreeMap, BTreeSet, BinaryHeap};
use std::error::Error;
use std::fmt::{Display, Formatter};

pub type NodeId = u64;
pub type EdgeId = u64;
pub type NonterminalId = u64;
pub type TerminalId = u64;
pub type ProductionId = u64;
pub type ProposalId = u64;
pub type TokenEdgeId = u64;

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum TerminalLabel {
    Byte(u8),
    Text(String),
}

impl TerminalLabel {
    pub fn text(value: impl Into<String>) -> Result<Self, ValidationError> {
        let value = value.into();
        if value.is_empty() {
            return Err(ValidationError::new(
                "string terminal labels must be non-empty",
            ));
        }
        Ok(Self::Text(value))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ValidationError {
    message: String,
}

impl ValidationError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl Display for ValidationError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.message)
    }
}

impl Error for ValidationError {}

#[derive(Clone, Debug, PartialEq)]
pub struct TerminalEdge {
    edge_id: EdgeId,
    source_state: NodeId,
    target_state: NodeId,
    terminal_label: TerminalLabel,
    weight: f64,
    provenance_token_edge_id: Option<TokenEdgeId>,
    matched_proposal_ids: Vec<ProposalId>,
}

impl TerminalEdge {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        edge_id: EdgeId,
        source_state: NodeId,
        target_state: NodeId,
        terminal_label: TerminalLabel,
        weight: f64,
        provenance_token_edge_id: Option<TokenEdgeId>,
        matched_proposal_ids: Vec<ProposalId>,
    ) -> Result<Self, ValidationError> {
        if source_state == target_state {
            return Err(ValidationError::new("terminal edges cannot be self-loops"));
        }
        require_weight(weight, "edge weight")?;
        require_unique(&matched_proposal_ids, "matched proposal IDs")?;
        Ok(Self {
            edge_id,
            source_state,
            target_state,
            terminal_label,
            weight,
            provenance_token_edge_id,
            matched_proposal_ids,
        })
    }

    pub fn edge_id(&self) -> EdgeId {
        self.edge_id
    }

    pub fn source_state(&self) -> NodeId {
        self.source_state
    }

    pub fn target_state(&self) -> NodeId {
        self.target_state
    }

    pub fn terminal_label(&self) -> &TerminalLabel {
        &self.terminal_label
    }

    pub fn weight(&self) -> f64 {
        self.weight
    }

    pub fn provenance_token_edge_id(&self) -> Option<TokenEdgeId> {
        self.provenance_token_edge_id
    }

    pub fn matched_proposal_ids(&self) -> &[ProposalId] {
        &self.matched_proposal_ids
    }
}

#[derive(Clone, Debug)]
pub struct WeightedTerminalDag {
    node_ids: Vec<NodeId>,
    start_node_id: NodeId,
    final_node_ids: Vec<NodeId>,
    edges: Vec<TerminalEdge>,
    topological_order: Vec<NodeId>,
    topological_index: BTreeMap<NodeId, usize>,
    edge_index_by_id: BTreeMap<EdgeId, usize>,
    outgoing_edge_indices: BTreeMap<NodeId, Vec<usize>>,
    edges_by_label: BTreeMap<TerminalLabel, Vec<usize>>,
}

impl WeightedTerminalDag {
    pub fn new(
        node_ids: Vec<NodeId>,
        start_node_id: NodeId,
        final_node_ids: Vec<NodeId>,
        mut edges: Vec<TerminalEdge>,
    ) -> Result<Self, ValidationError> {
        if node_ids.is_empty() {
            return Err(ValidationError::new("node IDs must be non-empty"));
        }
        require_unique(&node_ids, "node IDs")?;
        let node_set: BTreeSet<_> = node_ids.iter().copied().collect();
        if !node_set.contains(&start_node_id) {
            return Err(ValidationError::new(
                "start node must reference an existing node",
            ));
        }
        if final_node_ids.is_empty() {
            return Err(ValidationError::new("final node IDs must be non-empty"));
        }
        require_unique(&final_node_ids, "final node IDs")?;
        if final_node_ids.iter().any(|node| !node_set.contains(node)) {
            return Err(ValidationError::new(
                "final nodes must reference existing nodes",
            ));
        }

        edges.sort_by_key(TerminalEdge::edge_id);
        let edge_ids: Vec<_> = edges.iter().map(TerminalEdge::edge_id).collect();
        require_unique(&edge_ids, "edge IDs")?;
        if edges.iter().any(|edge| {
            !node_set.contains(&edge.source_state()) || !node_set.contains(&edge.target_state())
        }) {
            return Err(ValidationError::new(
                "every edge endpoint must reference an existing node",
            ));
        }

        let mut indegree: BTreeMap<NodeId, usize> =
            node_ids.iter().map(|node| (*node, 0)).collect();
        let mut outgoing_edge_indices: BTreeMap<NodeId, Vec<usize>> =
            node_ids.iter().map(|node| (*node, Vec::new())).collect();
        let mut edge_index_by_id = BTreeMap::new();
        let mut edges_by_label: BTreeMap<TerminalLabel, Vec<usize>> = BTreeMap::new();
        for (edge_index, edge) in edges.iter().enumerate() {
            edge_index_by_id.insert(edge.edge_id(), edge_index);
            outgoing_edge_indices
                .get_mut(&edge.source_state())
                .expect("validated source node must be indexed")
                .push(edge_index);
            *indegree
                .get_mut(&edge.target_state())
                .expect("validated target node must be indexed") += 1;
            edges_by_label
                .entry(edge.terminal_label().clone())
                .or_default()
                .push(edge_index);
        }

        let mut ready: BinaryHeap<Reverse<NodeId>> = indegree
            .iter()
            .filter_map(|(node, degree)| (*degree == 0).then_some(Reverse(*node)))
            .collect();
        let mut topological_order = Vec::with_capacity(node_ids.len());
        while let Some(Reverse(node)) = ready.pop() {
            topological_order.push(node);
            for edge_index in outgoing_edge_indices
                .get(&node)
                .expect("every validated node has an outgoing index")
            {
                let target = edges[*edge_index].target_state();
                let degree = indegree
                    .get_mut(&target)
                    .expect("validated target node must have indegree");
                *degree -= 1;
                if *degree == 0 {
                    ready.push(Reverse(target));
                }
            }
        }
        if topological_order.len() != node_ids.len() {
            let cyclic_nodes: Vec<_> = indegree
                .iter()
                .filter_map(|(node, degree)| (*degree > 0).then_some(*node))
                .collect();
            return Err(ValidationError::new(format!(
                "weighted terminal graph must be acyclic; cycle involves nodes {cyclic_nodes:?}"
            )));
        }
        let topological_index: BTreeMap<_, _> = topological_order
            .iter()
            .enumerate()
            .map(|(index, node)| (*node, index))
            .collect();

        Ok(Self {
            node_ids,
            start_node_id,
            final_node_ids,
            edges,
            topological_order,
            topological_index,
            edge_index_by_id,
            outgoing_edge_indices,
            edges_by_label,
        })
    }

    pub fn validate_topological_order(&self, order: &[NodeId]) -> Result<(), ValidationError> {
        if order.len() != self.node_ids.len() {
            return Err(ValidationError::new(
                "topological order must contain every node exactly once",
            ));
        }
        require_unique(order, "topological order node IDs")?;
        let indices: BTreeMap<_, _> = order
            .iter()
            .enumerate()
            .map(|(index, node)| (*node, index))
            .collect();
        if indices.keys().copied().collect::<BTreeSet<_>>()
            != self.node_ids.iter().copied().collect::<BTreeSet<_>>()
        {
            return Err(ValidationError::new(
                "topological order must contain exactly the graph nodes",
            ));
        }
        if self
            .edges
            .iter()
            .any(|edge| indices[&edge.source_state()] >= indices[&edge.target_state()])
        {
            return Err(ValidationError::new(
                "topological order places an edge target before its source",
            ));
        }
        Ok(())
    }

    pub fn node_ids(&self) -> &[NodeId] {
        &self.node_ids
    }

    pub fn start_node_id(&self) -> NodeId {
        self.start_node_id
    }

    pub fn final_node_ids(&self) -> &[NodeId] {
        &self.final_node_ids
    }

    pub fn edges(&self) -> &[TerminalEdge] {
        &self.edges
    }

    pub fn topological_order(&self) -> &[NodeId] {
        &self.topological_order
    }

    pub fn topological_index(&self, node: NodeId) -> Option<usize> {
        self.topological_index.get(&node).copied()
    }

    pub fn edge(&self, edge_id: EdgeId) -> Option<&TerminalEdge> {
        self.edge_index_by_id
            .get(&edge_id)
            .map(|index| &self.edges[*index])
    }

    pub fn outgoing_edges(&self, node: NodeId) -> impl Iterator<Item = &TerminalEdge> {
        self.outgoing_edge_indices
            .get(&node)
            .into_iter()
            .flatten()
            .map(|index| &self.edges[*index])
    }

    pub fn edges_with_label(&self, label: &TerminalLabel) -> impl Iterator<Item = &TerminalEdge> {
        self.edges_by_label
            .get(label)
            .into_iter()
            .flatten()
            .map(|index| &self.edges[*index])
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SupportKind {
    Full,
    TopK,
    Explicit,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ExactnessScope {
    pub kind: SupportKind,
    pub vocabulary_size: u64,
    pub included_special_tokens: Vec<u64>,
    pub top_k: Option<u64>,
    pub adaptive_expansions: Vec<u64>,
    pub pruning_description: Option<String>,
}

impl ExactnessScope {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        kind: SupportKind,
        vocabulary_size: u64,
        included_special_tokens: Vec<u64>,
        top_k: Option<u64>,
        adaptive_expansions: Vec<u64>,
        pruning_description: Option<String>,
    ) -> Result<Self, ValidationError> {
        if vocabulary_size == 0 {
            return Err(ValidationError::new("vocabulary size must be positive"));
        }
        require_unique(&included_special_tokens, "included special token IDs")?;
        if included_special_tokens
            .iter()
            .any(|token| *token >= vocabulary_size)
        {
            return Err(ValidationError::new(
                "included special token IDs must be within the vocabulary",
            ));
        }
        match kind {
            SupportKind::TopK => {
                let width = top_k
                    .ok_or_else(|| ValidationError::new("top-k scope requires an initial width"))?;
                if width == 0 || width > vocabulary_size {
                    return Err(ValidationError::new(
                        "top-k width must be positive and within the vocabulary",
                    ));
                }
                let mut previous = width;
                for expansion in &adaptive_expansions {
                    if *expansion <= previous || *expansion > vocabulary_size {
                        return Err(ValidationError::new(
                            "adaptive expansions must strictly increase within the vocabulary",
                        ));
                    }
                    previous = *expansion;
                }
            }
            SupportKind::Full | SupportKind::Explicit => {
                if top_k.is_some() || !adaptive_expansions.is_empty() {
                    return Err(ValidationError::new(
                        "only top-k scope may define widths or expansions",
                    ));
                }
            }
        }
        if pruning_description
            .as_ref()
            .is_some_and(|description| description.trim().is_empty())
        {
            return Err(ValidationError::new(
                "pruning description must be non-empty when provided",
            ));
        }
        Ok(Self {
            kind,
            vocabulary_size,
            included_special_tokens,
            top_k,
            adaptive_expansions,
            pruning_description,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TerminalProduction {
    pub production_id: ProductionId,
    pub head_id: NonterminalId,
    pub terminal_id: TerminalId,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BinaryProduction {
    pub production_id: ProductionId,
    pub head_id: NonterminalId,
    pub left_id: NonterminalId,
    pub right_id: NonterminalId,
}

#[derive(Clone, Debug)]
pub struct CnfGrammar {
    nonterminal_ids: Vec<NonterminalId>,
    terminals: BTreeMap<TerminalId, TerminalLabel>,
    start_nonterminal_id: NonterminalId,
    terminal_productions: Vec<TerminalProduction>,
    binary_productions: Vec<BinaryProduction>,
    accepts_empty: bool,
}

impl CnfGrammar {
    pub fn new(
        nonterminal_ids: Vec<NonterminalId>,
        terminals: Vec<(TerminalId, TerminalLabel)>,
        start_nonterminal_id: NonterminalId,
        mut terminal_productions: Vec<TerminalProduction>,
        mut binary_productions: Vec<BinaryProduction>,
        accepts_empty: bool,
    ) -> Result<Self, ValidationError> {
        if nonterminal_ids.is_empty() {
            return Err(ValidationError::new(
                "CNF grammar requires at least one nonterminal",
            ));
        }
        require_unique(&nonterminal_ids, "nonterminal IDs")?;
        let nonterminal_set: BTreeSet<_> = nonterminal_ids.iter().copied().collect();
        if !nonterminal_set.contains(&start_nonterminal_id) {
            return Err(ValidationError::new(
                "start nonterminal must reference an existing nonterminal",
            ));
        }
        let terminal_ids: Vec<_> = terminals.iter().map(|(id, _)| *id).collect();
        require_unique(&terminal_ids, "terminal IDs")?;
        let terminal_labels: Vec<_> = terminals.iter().map(|(_, label)| label.clone()).collect();
        require_unique(&terminal_labels, "terminal labels")?;
        let terminal_map: BTreeMap<_, _> = terminals.into_iter().collect();

        terminal_productions.sort_by_key(|production| production.production_id);
        binary_productions.sort_by_key(|production| production.production_id);
        let production_ids: Vec<_> = terminal_productions
            .iter()
            .map(|production| production.production_id)
            .chain(
                binary_productions
                    .iter()
                    .map(|production| production.production_id),
            )
            .collect();
        require_unique(&production_ids, "production IDs")?;
        if terminal_productions.iter().any(|production| {
            !nonterminal_set.contains(&production.head_id)
                || !terminal_map.contains_key(&production.terminal_id)
        }) {
            return Err(ValidationError::new(
                "terminal production references an unknown symbol",
            ));
        }
        if binary_productions.iter().any(|production| {
            !nonterminal_set.contains(&production.head_id)
                || !nonterminal_set.contains(&production.left_id)
                || !nonterminal_set.contains(&production.right_id)
        }) {
            return Err(ValidationError::new(
                "binary production references an unknown nonterminal",
            ));
        }
        Ok(Self {
            nonterminal_ids,
            terminals: terminal_map,
            start_nonterminal_id,
            terminal_productions,
            binary_productions,
            accepts_empty,
        })
    }

    pub fn nonterminal_ids(&self) -> &[NonterminalId] {
        &self.nonterminal_ids
    }

    pub fn terminal_label(&self, terminal_id: TerminalId) -> Option<&TerminalLabel> {
        self.terminals.get(&terminal_id)
    }

    pub fn terminals(&self) -> &BTreeMap<TerminalId, TerminalLabel> {
        &self.terminals
    }

    pub fn start_nonterminal_id(&self) -> NonterminalId {
        self.start_nonterminal_id
    }

    pub fn terminal_productions(&self) -> &[TerminalProduction] {
        &self.terminal_productions
    }

    pub fn binary_productions(&self) -> &[BinaryProduction] {
        &self.binary_productions
    }

    pub fn accepts_empty(&self) -> bool {
        self.accepts_empty
    }

    pub fn production_count(&self) -> usize {
        self.terminal_productions.len() + self.binary_productions.len()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SolveStatus {
    Optimal,
    InfeasibleOnSupport,
    Timeout,
    Unsupported,
    Error,
}

impl SolveStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Optimal => "optimal",
            Self::InfeasibleOnSupport => "infeasible_on_support",
            Self::Timeout => "timeout",
            Self::Unsupported => "unsupported",
            Self::Error => "error",
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Certificate {
    pub objective_value: f64,
    pub selected_proposal_ids: Vec<ProposalId>,
    pub witness_terminal_labels: Vec<TerminalLabel>,
    pub witness_graph_edge_ids: Vec<EdgeId>,
    pub witness_token_edge_ids: Vec<Option<TokenEdgeId>>,
}

impl Certificate {
    pub fn new(
        objective_value: f64,
        selected_proposal_ids: Vec<ProposalId>,
        witness_terminal_labels: Vec<TerminalLabel>,
        witness_graph_edge_ids: Vec<EdgeId>,
        witness_token_edge_ids: Vec<Option<TokenEdgeId>>,
    ) -> Result<Self, ValidationError> {
        require_weight(objective_value, "certificate objective")?;
        require_unique(&selected_proposal_ids, "selected proposal IDs")?;
        if witness_terminal_labels.len() != witness_graph_edge_ids.len()
            || witness_graph_edge_ids.len() != witness_token_edge_ids.len()
        {
            return Err(ValidationError::new(
                "certificate labels, graph edges, and token provenance must align",
            ));
        }
        require_unique(&witness_graph_edge_ids, "witness graph edge IDs")?;
        Ok(Self {
            objective_value,
            selected_proposal_ids,
            witness_terminal_labels,
            witness_graph_edge_ids,
            witness_token_edge_ids,
        })
    }
}

#[derive(Clone, Debug, Default, PartialEq)]
pub struct Diagnostics {
    pub chart_entries: u64,
    pub relaxations: u64,
    pub graph_nodes: u64,
    pub graph_edges: u64,
    pub grammar_nonterminals: u64,
    pub grammar_productions: u64,
    pub elapsed_parser_seconds: f64,
    pub deadline_checks: u64,
}

impl Diagnostics {
    pub fn validate(&self) -> Result<(), ValidationError> {
        if !self.elapsed_parser_seconds.is_finite() || self.elapsed_parser_seconds < 0.0 {
            return Err(ValidationError::new(
                "elapsed parser time must be finite and non-negative",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct SolveResult {
    pub status: SolveStatus,
    pub objective_value: Option<f64>,
    pub certificate: Option<Certificate>,
    pub diagnostics: Diagnostics,
}

impl SolveResult {
    pub fn optimal(
        certificate: Certificate,
        diagnostics: Diagnostics,
    ) -> Result<Self, ValidationError> {
        diagnostics.validate()?;
        Ok(Self {
            status: SolveStatus::Optimal,
            objective_value: Some(certificate.objective_value),
            certificate: Some(certificate),
            diagnostics,
        })
    }

    pub fn without_certificate(
        status: SolveStatus,
        diagnostics: Diagnostics,
    ) -> Result<Self, ValidationError> {
        if status == SolveStatus::Optimal {
            return Err(ValidationError::new(
                "optimal result requires a certificate",
            ));
        }
        diagnostics.validate()?;
        Ok(Self {
            status,
            objective_value: None,
            certificate: None,
            diagnostics,
        })
    }
}

fn require_weight(value: f64, field_name: &str) -> Result<(), ValidationError> {
    if !value.is_finite() {
        return Err(ValidationError::new(format!("{field_name} must be finite")));
    }
    if value < 0.0 {
        return Err(ValidationError::new(format!(
            "{field_name} must be non-negative"
        )));
    }
    Ok(())
}

fn require_unique<T: Ord + Clone>(values: &[T], field_name: &str) -> Result<(), ValidationError> {
    let unique: BTreeSet<_> = values.iter().cloned().collect();
    if unique.len() != values.len() {
        return Err(ValidationError::new(format!(
            "{field_name} must not contain duplicates"
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn edge(edge_id: EdgeId, source: NodeId, target: NodeId) -> TerminalEdge {
        TerminalEdge::new(
            edge_id,
            source,
            target,
            TerminalLabel::Text("x".to_owned()),
            edge_id as f64,
            Some(100 + edge_id),
            vec![200 + edge_id],
        )
        .unwrap()
    }

    #[test]
    fn graph_computes_stable_order_and_keeps_parallel_edges() {
        let graph = WeightedTerminalDag::new(
            vec![30, 10, 20, 40],
            10,
            vec![20, 40],
            vec![edge(9, 10, 20), edge(3, 10, 20), edge(4, 30, 40)],
        )
        .unwrap();

        assert_eq!(graph.topological_order(), &[10, 20, 30, 40]);
        assert_eq!(
            graph
                .outgoing_edges(10)
                .map(TerminalEdge::edge_id)
                .collect::<Vec<_>>(),
            vec![3, 9]
        );
        assert_eq!(graph.final_node_ids(), &[20, 40]);
    }

    #[test]
    fn graph_rejects_unknown_endpoints_duplicate_ids_and_cycles() {
        assert!(
            WeightedTerminalDag::new(vec![0, 1], 0, vec![1], vec![edge(0, 0, 2)])
                .unwrap_err()
                .to_string()
                .contains("endpoint")
        );
        assert!(WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(0, 0, 1), edge(0, 1, 2)]
        )
        .unwrap_err()
        .to_string()
        .contains("edge IDs"));
        assert!(WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(0, 0, 1), edge(1, 1, 0)]
        )
        .unwrap_err()
        .to_string()
        .contains("acyclic"));
    }

    #[test]
    fn edge_rejects_non_finite_negative_and_self_loop_weights() {
        for weight in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, -1.0] {
            assert!(
                TerminalEdge::new(0, 0, 1, TerminalLabel::Byte(b'x'), weight, None, vec![])
                    .is_err()
            );
        }
        assert!(TerminalEdge::new(0, 1, 1, TerminalLabel::Byte(b'x'), 0.0, None, vec![]).is_err());
    }

    #[test]
    fn caller_topological_order_is_validated() {
        let graph = WeightedTerminalDag::new(
            vec![0, 1, 2],
            0,
            vec![2],
            vec![edge(0, 0, 1), edge(1, 1, 2)],
        )
        .unwrap();

        graph.validate_topological_order(&[0, 1, 2]).unwrap();
        assert!(graph.validate_topological_order(&[0, 2, 1]).is_err());
        assert!(graph.validate_topological_order(&[0, 1]).is_err());
    }

    #[test]
    fn grammar_and_scope_reject_invalid_references() {
        assert!(CnfGrammar::new(
            vec![0],
            vec![(10, TerminalLabel::Byte(b'x'))],
            0,
            vec![TerminalProduction {
                production_id: 1,
                head_id: 9,
                terminal_id: 10,
            }],
            vec![],
            false,
        )
        .is_err());
        assert!(
            ExactnessScope::new(SupportKind::TopK, 100, vec![], Some(10), vec![9], None,).is_err()
        );
    }

    #[test]
    fn non_optimal_result_never_exposes_partial_certificate() {
        let result =
            SolveResult::without_certificate(SolveStatus::Timeout, Diagnostics::default()).unwrap();

        assert_eq!(result.status, SolveStatus::Timeout);
        assert!(result.objective_value.is_none());
        assert!(result.certificate.is_none());
    }
}
