import MWPC.Selection

/-! Independent cover and conflict transport theorems. Rewards use common
    natural-number units; Python checks their original rational correspondence.
    This specification does not assume the CFG oracle or master source correct. -/
namespace MWPC

def Avoids (excluded batch : List Nat) : Prop :=
  ∀ choice ∈ excluded, choice ∉ batch

def ValidConflict (feasible : List Nat → Prop) (core : List Nat) : Prop :=
  ∀ batch, feasible batch → ¬ (∀ choice ∈ core, choice ∈ batch)

theorem conflict_missing_member {feasible : List Nat → Prop} {core batch : List Nat}
    (sound : ValidConflict feasible core) (valid : feasible batch) :
    ∃ choice ∈ core, choice ∉ batch := by
  classical
  exact Classical.byContradiction fun absent =>
    sound batch valid fun choice member =>
      Classical.byContradiction fun missing => absent ⟨choice, member, missing⟩

theorem empty_conflict_infeasible {feasible : List Nat → Prop}
    (sound : ValidConflict feasible []) : ∀ batch, ¬ feasible batch := by
  intro batch valid
  exact sound batch valid (by simp)

inductive ConflictCover (feasible : List Nat → Prop) (reward : List Nat → Nat) :
    List Nat → Nat → Prop
  | leaf (excluded : List Nat) (upper : Nat)
      (bound : ∀ batch, Avoids excluded batch → reward batch ≤ upper) :
      ConflictCover feasible reward excluded upper
  | split (excluded core : List Nat) (upper : Nat)
      (sound : ValidConflict feasible core)
      (children : ∀ choice ∈ core, ConflictCover feasible reward (choice :: excluded) upper) :
      ConflictCover feasible reward excluded upper

theorem conflict_cover_bound
    (cover : ConflictCover feasible reward excluded upper)
    (valid : feasible batch) (allowed : Avoids excluded batch) : reward batch ≤ upper := by
  induction cover with
  | leaf excluded upper bound => exact bound batch allowed
  | split excluded core upper sound children ih =>
      obtain ⟨choice, member, missing⟩ := conflict_missing_member sound valid
      apply ih choice member
      intro other membership
      simp only [List.mem_cons] at membership
      rcases membership with same | old
      · simpa only [same] using missing
      · exact allowed other old

theorem conflict_certified_optimal
    (cover : ConflictCover feasible reward [] (reward witness))
    (valid : feasible witness) : IsOptimum feasible reward witness := by
  refine ⟨valid, ?_⟩
  intro batch accepted
  exact conflict_cover_bound cover accepted (by simp [Avoids])

theorem conflict_transport {original retained : List Nat → Prop}
    (contained : ∀ batch, retained batch → original batch)
    (sound : ValidConflict original core) : ValidConflict retained core := by
  intro batch valid
  exact sound batch (contained batch valid)

theorem feasible_witness_transport {original expanded : List Nat → Prop}
    (contained : ∀ batch, original batch → expanded batch)
    (valid : original witness) : expanded witness := contained witness valid

theorem fixed_conflict_discharge {feasible : List Nat → Prop}
    {original discharged : List Nat}
    (sound : ValidConflict feasible original)
    (fixed : ∀ batch, feasible batch →
      (∀ choice ∈ discharged, choice ∈ batch) →
      (∀ choice ∈ original, choice ∈ batch)) : ValidConflict feasible discharged := by
  intro batch valid contains
  exact sound batch valid (fixed batch valid contains)

/- Each finish is one solve's final oracle query; each learned core pays its
   failed main query and at most B deletion queries. Reused infeasibility can
   finish without a new oracle query. -/
inductive ConflictQueries (budget : Nat) : Nat → Nat → Nat → Prop
  | finish : ConflictQueries budget 1 0 1
  | reusedInfeasible : ConflictQueries budget 1 0 0
  | learn {calls learned queries : Nat} (size : Nat) (small : size ≤ budget)
      (tail : ConflictQueries budget calls learned queries) :
      ConflictQueries budget calls (learned + 1) (queries + size + 1)
  | append {c₁ c₂ h₁ h₂ q₁ q₂ : Nat}
      (left : ConflictQueries budget c₁ h₁ q₁)
      (right : ConflictQueries budget c₂ h₂ q₂) :
      ConflictQueries budget (c₁ + c₂) (h₁ + h₂) (q₁ + q₂)

theorem amortized_conflict_queries
    (trace : ConflictQueries budget calls learned queries) :
    queries ≤ calls + (budget + 1) * learned := by
  induction trace with
  | finish => simp
  | reusedInfeasible => simp
  | learn size small tail ih =>
      simp only [Nat.mul_add, Nat.mul_one]
      omega
  | append left right ih₁ ih₂ =>
      simp only [Nat.mul_add]
      omega

end MWPC
