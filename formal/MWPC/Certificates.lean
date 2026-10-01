import Std

/-! Soundness of resource-aware CFG upper-potential certificates.
    Nonnegative rational weights are represented in common integer units.
    Missing cells are impossible, never zero. No DAG algorithm is trusted here. -/

namespace MWPC

structure Arc (n : Nat) where
  source : Fin n
  target : Fin n
  label : Option Nat
  reward : Nat
  cost : Nat
  deriving DecidableEq, Repr

structure Graph (n : Nat) where
  start : Fin n
  finals : List (Fin n)
  arcs : List (Arc n)

structure Grammar where
  start : Nat
  terminals : List (Nat × Nat)
  binaries : List (Nat × Nat × Nat)
  acceptsEmpty : Bool

inductive Epsilon (g : Graph n) : Fin n → Fin n → Nat → Nat → Prop
  | identity (u : Fin n) : Epsilon g u u 0 0
  | step (a : Arc n) {u : Fin n} {k r : Nat}
      (member : a ∈ g.arcs) (silent : a.label = none)
      (leading : Epsilon g u a.source k r) :
      Epsilon g u a.target (k + a.cost) (r + a.reward)

inductive Derivation (G : Grammar) (g : Graph n) : Nat → Fin n → Fin n → Nat → Nat → Prop
  | terminal (a : Arc n) {head label : Nat} {u v : Fin n}
      {k₁ k₂ r₁ r₂ : Nat}
      (member : a ∈ g.arcs) (visible : a.label = some label)
      (production : (head, label) ∈ G.terminals)
      (leading : Epsilon g u a.source k₁ r₁)
      (suffix : Epsilon g a.target v k₂ r₂) :
      Derivation G g head u v (k₁ + a.cost + k₂) (r₁ + a.reward + r₂)
  | binary {head left right : Nat} {u m v : Fin n} {k₁ k₂ r₁ r₂ : Nat}
      (production : (head, left, right) ∈ G.binaries)
      (lhs : Derivation G g left u m k₁ r₁)
      (rhs : Derivation G g right m v k₂ r₂) :
      Derivation G g head u v (k₁ + k₂) (r₁ + r₂)

def Covers (cell : Option Nat) (reward : Nat) : Prop :=
  match cell with
  | none => False
  | some upper => reward ≤ upper

instance (cell : Option Nat) (reward : Nat) : Decidable (Covers cell reward) := by
  unfold Covers
  cases cell <;> infer_instance

theorem covers_value {cell : Option Nat} {r : Nat} (h : Covers cell r) :
    ∃ upper, cell = some upper ∧ r ≤ upper := by
  cases cell with
  | none => simp [Covers] at h
  | some upper => exact ⟨upper, rfl, h⟩

theorem covers_mono {cell : Option Nat} {a b : Nat}
    (h : Covers cell b) (le : a ≤ b) : Covers cell a := by
  cases cell with
  | none => simp [Covers] at h
  | some upper => exact Nat.le_trans le h

structure Potentials (n : Nat) where
  cap : Nat
  epsilon : Fin n → Fin n → Nat → Option Nat
  grammar : Nat → Fin n → Fin n → Nat → Option Nat

def ExtendCovers (previous target : Option Nat) (extra : Nat) : Prop :=
  match previous with
  | none => True
  | some x => Covers target (x + extra)

instance (previous target : Option Nat) (extra : Nat) :
    Decidable (ExtendCovers previous target extra) := by
  unfold ExtendCovers
  cases previous <;> infer_instance

def SumCovers (left right target : Option Nat) (extra : Nat) : Prop :=
  match left, right with
  | some x, some y => Covers target (x + extra + y)
  | _, _ => True

instance (left right target : Option Nat) (extra : Nat) :
    Decidable (SumCovers left right target extra) := by
  unfold SumCovers
  cases left <;> cases right <;> infer_instance

structure ValidPotentials (G : Grammar) (g : Graph n) (p : Potentials n) : Prop where
  identity : ∀ u, Covers (p.epsilon u u 0) 0
  step : ∀ a ∈ g.arcs, a.label = none → ∀ u (k : Fin (p.cap + 1)),
    k.val + a.cost ≤ p.cap →
    ExtendCovers (p.epsilon u a.source k.val)
      (p.epsilon u a.target (k.val + a.cost)) a.reward
  terminal : ∀ rule ∈ G.terminals, ∀ a ∈ g.arcs, a.label = some rule.2 →
    ∀ u v (k₁ k₂ : Fin (p.cap + 1)), k₁.val + a.cost + k₂.val ≤ p.cap →
    SumCovers (p.epsilon u a.source k₁.val) (p.epsilon a.target v k₂.val)
      (p.grammar rule.1 u v (k₁.val + a.cost + k₂.val)) a.reward
  binary : ∀ rule ∈ G.binaries, ∀ u m v (k₁ k₂ : Fin (p.cap + 1)),
    k₁.val + k₂.val ≤ p.cap →
    SumCovers (p.grammar rule.2.1 u m k₁.val) (p.grammar rule.2.2 m v k₂.val)
      (p.grammar rule.1 u v (k₁.val + k₂.val)) 0

theorem epsilon_bound (valid : ValidPotentials G g p)
    (path : Epsilon g u v k r) (cap : k ≤ p.cap) : Covers (p.epsilon u v k) r := by
  induction path with
  | identity u => exact valid.identity u
  | @step a u k r member silent leading ih =>
      have previous : k ≤ p.cap := by omega
      obtain ⟨x, lookup, le⟩ := covers_value (ih previous)
      have next := valid.step a member silent u ⟨k, by omega⟩ cap
      simp only [lookup, ExtendCovers] at next
      exact covers_mono next (Nat.add_le_add_right le a.reward)

theorem derivation_bound (valid : ValidPotentials G g p)
    (derivation : Derivation G g head u v k r) (cap : k ≤ p.cap) :
    Covers (p.grammar head u v k) r := by
  induction derivation with
  | @terminal a head label u v k₁ k₂ r₁ r₂ member visible production leading suffix =>
      have c₁ : k₁ ≤ p.cap := by omega
      have c₂ : k₂ ≤ p.cap := by omega
      obtain ⟨x, lookup₁, le₁⟩ := covers_value (epsilon_bound valid leading c₁)
      obtain ⟨y, lookup₂, le₂⟩ := covers_value (epsilon_bound valid suffix c₂)
      have next := valid.terminal (head, label) production a member visible u v
        ⟨k₁, by omega⟩ ⟨k₂, by omega⟩ cap
      simp only [lookup₁, lookup₂, SumCovers] at next
      exact covers_mono next (by omega)
  | @binary head left right u m v k₁ k₂ r₁ r₂ production lhs rhs ih₁ ih₂ =>
      obtain ⟨x, lookup₁, le₁⟩ := covers_value (ih₁ (by omega))
      obtain ⟨y, lookup₂, le₂⟩ := covers_value (ih₂ (by omega))
      have next := valid.binary (head, left, right) production u m v
        ⟨k₁, by omega⟩ ⟨k₂, by omega⟩ cap
      simp only [lookup₁, lookup₂, SumCovers, Nat.add_zero] at next
      exact covers_mono next (Nat.add_le_add le₁ le₂)

def Accepted (G : Grammar) (g : Graph n) (budget reward : Nat) : Prop :=
  ∃ final ∈ g.finals, ∃ cost, cost ≤ budget ∧
    (Derivation G g G.start g.start final cost reward ∨
      G.acceptsEmpty = true ∧ Epsilon g g.start final cost reward)

def CellBelow (cell : Option Nat) (upper : Nat) : Prop :=
  match cell with
  | none => True
  | some value => value ≤ upper

instance (cell : Option Nat) (upper : Nat) : Decidable (CellBelow cell upper) := by
  unfold CellBelow
  cases cell <;> infer_instance

def RootUpper (G : Grammar) (g : Graph n) (p : Potentials n) (budget upper : Nat) : Prop :=
  ∀ final ∈ g.finals, ∀ cost : Fin (budget + 1),
    CellBelow (p.grammar G.start g.start final cost.val) upper ∧
    (G.acceptsEmpty = true → CellBelow (p.epsilon g.start final cost.val) upper)

theorem accepted_bound (valid : ValidPotentials G g p) (cap : budget ≤ p.cap)
    (roots : RootUpper G g p budget upper) (accepted : Accepted G g budget reward) :
    reward ≤ upper := by
  obtain ⟨final, member, cost, budgetCost, path⟩ := accepted
  have bounds := roots final member ⟨cost, by omega⟩
  rcases path with nonempty | empty
  · obtain ⟨x, lookup, le⟩ := covers_value (derivation_bound valid nonempty (by omega))
    have root := bounds.1
    simp only [lookup, CellBelow] at root
    exact Nat.le_trans le root
  · obtain ⟨x, lookup, le⟩ := covers_value (epsilon_bound valid empty.2 (by omega))
    have root := bounds.2 empty.1
    simp only [lookup, CellBelow] at root
    exact Nat.le_trans le root

theorem certified_optimal (valid : ValidPotentials G g p) (cap : budget ≤ p.cap)
    (roots : RootUpper G g p budget optimum) (witness : Accepted G g budget optimum) :
    Accepted G g budget optimum ∧ ∀ reward, Accepted G g budget reward → reward ≤ optimum := by
  exact ⟨witness, fun _ accepted => accepted_bound valid cap roots accepted⟩

def AbsentRoots (G : Grammar) (g : Graph n) (p : Potentials n) (budget : Nat) : Prop :=
  ∀ final ∈ g.finals, ∀ cost : Fin (budget + 1),
    p.grammar G.start g.start final cost.val = none ∧
    (G.acceptsEmpty = true → p.epsilon g.start final cost.val = none)

theorem certified_infeasible (valid : ValidPotentials G g p) (cap : budget ≤ p.cap)
    (roots : AbsentRoots G g p budget) : ¬ ∃ reward, Accepted G g budget reward := by
  rintro ⟨reward, final, member, cost, budgetCost, path⟩
  have absent := roots final member ⟨cost, by omega⟩
  rcases path with nonempty | empty
  · have bound := derivation_bound valid nonempty (by omega)
    simp only [absent.1, Covers] at bound
  · have bound := epsilon_bound valid empty.2 (by omega)
    simp only [absent.2 empty.1, Covers] at bound

end MWPC
