import MWPC.Certificates

/-! Rational probabilities use common natural-number units. These proofs
    specify partition bounds and conditional-error algebra, not model/source
    verification or a machine-checked probability coupling construction. -/
namespace MWPC
variable {α : Type} (valid : α → Prop) [DecidablePred valid] (weight : α → Nat)

def totalMass (xs : List α) : Nat := (xs.map weight).sum

def validMass : List α → Nat
  | [] => 0
  | a :: tail => (if valid a then weight a else 0) + validMass tail

theorem valid_mass_append (left right : List α) :
    validMass valid weight (left ++ right) =
      validMass valid weight left + validMass valid weight right := by
  induction left with
  | nil => simp [validMass]
  | cons a tail ih => simp [validMass, ih, Nat.add_assoc]

theorem valid_mass_le_total (xs : List α) :
    validMass valid weight xs ≤ totalMass weight xs := by
  induction xs with
  | nil => simp [validMass, totalMass]
  | cons a tail ih =>
      simp only [validMass, totalMass, List.map_cons, List.sum_cons]
      by_cases h : valid a
      · simp only [h, ite_true]; exact Nat.add_le_add_left ih _
      · simp only [h, ite_false, Nat.zero_add]
        exact Nat.le_trans ih (Nat.le_add_left _ _)

theorem excluded_mass_zero (xs : List α)
    (excluded : ∀ a ∈ xs, ¬ valid a) : validMass valid weight xs = 0 := by
  induction xs with
  | nil => rfl
  | cons a tail ih =>
      have absent := excluded a (by simp)
      have rest : ∀ b ∈ tail, ¬ valid b := fun b h => excluded b (by simp [h])
      simp [validMass, absent, ih rest]

inductive PartitionMass : List α → Nat → Nat → Prop
  | accepted (a : α) (ok : valid a) : PartitionMass [a] (weight a) 0
  | excluded (xs : List α) (absent : ∀ a ∈ xs, ¬ valid a) : PartitionMass xs 0 0
  | unknown (xs : List α) : PartitionMass xs 0 (totalMass weight xs)
  | split {left right : List α} {l₁ l₂ u₁ u₂ : Nat}
      (first : PartitionMass left l₁ u₁) (second : PartitionMass right l₂ u₂) :
      PartitionMass (left ++ right) (l₁ + l₂) (u₁ + u₂)

theorem partition_mass_envelope
    (certificate : PartitionMass valid weight xs lower unknown) :
    lower ≤ validMass valid weight xs ∧ validMass valid weight xs ≤ lower + unknown := by
  induction certificate with
  | accepted a ok => simp [validMass, ok]
  | excluded xs absent => simp [excluded_mass_zero valid weight xs absent]
  | unknown xs => exact ⟨Nat.zero_le _, by simpa using valid_mass_le_total valid weight xs⟩
  | split first second ih₁ ih₂ =>
      rw [valid_mass_append]
      constructor
      · exact Nat.add_le_add ih₁.1 ih₂.1
      · have h := Nat.add_le_add ih₁.2 ih₂.2
        omega

-- Cross-multiplied ratios; the API separately requires positive known mass.
theorem conditional_missing_bound (known missing upper : Nat) (bounded : missing ≤ upper) :
    missing * (known + upper) ≤ upper * (known + missing) := by
  have h := Nat.mul_le_mul_right known bounded
  simp only [Nat.mul_add]
  rw [Nat.mul_comm upper missing]
  exact Nat.add_le_add_right h _

def scaledMass : List Nat → Nat → Nat
  | [], _ => 0
  | a :: tail, unit => a * unit + scaledMass tail unit

theorem scaled_mass_sum (xs : List Nat) (unit : Nat) :
    scaledMass xs unit = xs.sum * unit := by
  induction xs with
  | nil => simp [scaledMass]
  | cons a tail ih => simp [scaledMass, ih, Nat.add_mul]

theorem conditional_l1_numerator (known outside : List Nat) :
    scaledMass known outside.sum + scaledMass outside known.sum =
      2 * (known.sum * outside.sum) := by
  rw [scaled_mass_sum, scaled_mass_sum, Nat.mul_comm outside.sum known.sum]
  omega

theorem conditional_event_lower (known event missing eventMissing upper : Nat)
    (bounded : missing ≤ upper) :
    event * (known + missing) ≤ (event + eventMissing) * (known + upper) := by
  exact Nat.mul_le_mul (Nat.le_add_right event eventMissing) (Nat.add_le_add_left bounded known)

theorem conditional_event_upper (known event missing eventMissing upper : Nat)
    (eventBound : event ≤ known) (missingBound : missing ≤ upper)
    (eventMissingBound : eventMissing ≤ missing) :
    (event + eventMissing) * (known + upper) ≤ (event + upper) * (known + missing) := by
  apply Nat.le_trans (Nat.mul_le_mul_right (known + upper)
    (Nat.add_le_add_left eventMissingBound event))
  obtain ⟨c, hc⟩ := Nat.exists_eq_add_of_le eventBound
  obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le missingBound
  rw [hc, hd]
  simp only [Nat.mul_add, Nat.mul_comm]
  omega

inductive ErrorBudget : List Nat → List Nat → Prop
  | nil : ErrorBudget [] []
  | cons {failures bounds : List Nat} {failure bound : Nat}
      (small : failure ≤ bound) (tail : ErrorBudget failures bounds) :
      ErrorBudget (failure :: failures) (bound :: bounds)

theorem finite_error_budget (certificate : ErrorBudget failures bounds) :
    failures.sum ≤ bounds.sum := by
  induction certificate with
  | nil => simp
  | cons small tail ih => simpa using Nat.add_le_add small ih

inductive WordYield (g : Grammar) : Nat → List Nat → Prop
  | terminal {head label : Nat} (production : (head, label) ∈ g.terminals) :
      WordYield g head [label]
  | binary {head left right : Nat} {a b : List Nat}
      (production : (head, left, right) ∈ g.binaries)
      (lhs : WordYield g left a) (rhs : WordYield g right b) : WordYield g head (a ++ b)

def ClosedYields (g : Grammar) (bounds : Nat → List (List Nat)) : Prop :=
  (∀ head label, (head, label) ∈ g.terminals → [label] ∈ bounds head) ∧
  (∀ head left right, (head, left, right) ∈ g.binaries →
    ∀ a ∈ bounds left, ∀ b ∈ bounds right, a ++ b ∈ bounds head)

theorem closed_yield_envelope (closed : ClosedYields g bounds)
    (derivation : WordYield g head word) : word ∈ bounds head := by
  induction derivation with
  | terminal production => exact closed.1 _ _ production
  | binary production lhs rhs ih₁ ih₂ => exact closed.2 _ _ _ production _ ih₁ _ ih₂

-- Empty acceptance is an additional explicit premise, checked by Python.
theorem support_coverage_transport {tokens : Type} {emitted : tokens → List Nat}
    {represented : tokens → Prop} {path : tokens} (closed : ClosedYields g bounds)
    (coverage : ∀ word ∈ bounds g.start, ∀ t, emitted t = word → represented t)
    (accepted : WordYield g g.start (emitted path)) : represented path := by
  exact coverage _ (closed_yield_envelope closed accepted) path rfl

-- A necessary byte condition needs no finite-language or unambiguity assumption.
theorem grammar_yield_alphabet (derivation : WordYield g head word) :
    ∀ byte ∈ word, byte ∈ g.terminals.map Prod.snd := by
  induction derivation with
  | terminal production =>
      intro byte member
      simp only [List.mem_singleton] at member
      subst byte
      exact List.mem_map_of_mem production
  | binary production lhs rhs ih₁ ih₂ =>
      intro byte member
      rcases List.mem_append.mp member with left | right
      · exact ih₁ byte left
      · exact ih₂ byte right

theorem alphabet_support_transport {tokens : Type} {emitted : tokens → List Nat}
    {represented : tokens → Prop} {path : tokens}
    (coverage : ∀ t, (∀ byte ∈ emitted t, byte ∈ g.terminals.map Prod.snd) → represented t)
    (accepted : WordYield g g.start (emitted path)) : represented path := by
  exact coverage path (grammar_yield_alphabet accepted)
end MWPC
