import MWPC.Bounds

/-! Model-independent consequences of the finite-step objective. These results
    concern supplied rewards and feasible batches, never future model logits. -/
namespace MWPC

def IsOptimum {α : Type} (feasible : α → Prop) (reward : α → Nat) (witness : α) : Prop :=
  feasible witness ∧ ∀ batch, feasible batch → reward batch ≤ reward witness

theorem same_input_dominance {α : Type} {feasible : α → Prop} {reward : α → Nat}
    {witness : α}
    (optimum : IsOptimum feasible reward witness) (batch : α) (valid : feasible batch) :
    reward batch ≤ reward witness := optimum.2 batch valid

theorem fixed_reward_preserves_optimum {α : Type}
    {feasible : α → Prop} {reward : α → Nat} {witness : α} (fixedReward : Nat)
    (optimum : IsOptimum feasible reward witness) :
    IsOptimum feasible (fun batch => fixedReward + reward batch) witness := by
  exact ⟨optimum.1, fun batch valid => Nat.add_le_add_left (optimum.2 batch valid) fixedReward⟩

theorem support_expansion_certificate {α : Type}
    {original expanded : α → Prop} {reward : α → Nat} {upper : Nat}
    {witness : α}
    (retained : ∀ batch, original batch → expanded batch)
    (bound : ∀ batch, expanded batch → reward batch ≤ upper)
    (valid : original witness) (tight : reward witness = upper) :
    IsOptimum expanded reward witness := by
  refine ⟨retained witness valid, ?_⟩
  intro batch feasible
  rw [tight]
  exact bound batch feasible

theorem budget_feasibility_monotone {α : Type} {feasible : α → Prop} {cost : α → Nat}
    {batch : α} {small large : Nat}
    (valid : feasible batch ∧ cost batch ≤ small) (larger : small ≤ large) :
    feasible batch ∧ cost batch ≤ large := ⟨valid.1, Nat.le_trans valid.2 larger⟩

theorem optimum_monotone {α : Type} {feasible : α → Prop} {cost reward : α → Nat}
    {left right : α} {small large : Nat}
    (smallOpt : IsOptimum (fun batch => feasible batch ∧ cost batch ≤ small) reward left)
    (largeOpt : IsOptimum (fun batch => feasible batch ∧ cost batch ≤ large) reward right)
    (larger : small ≤ large) : reward left ≤ reward right := by
  exact largeOpt.2 left (budget_feasibility_monotone smallOpt.1 larger)

theorem minimum_capacity {α : Type} {feasible : α → Prop} {cost reward : α → Nat}
    {witness : α} {target budget : Nat}
    (optimum : IsOptimum (fun batch => feasible batch ∧ cost batch ≤ budget) reward witness) :
    (∃ batch, feasible batch ∧ cost batch ≤ budget ∧ target ≤ reward batch) ↔
      target ≤ reward witness := by
  constructor
  · rintro ⟨batch, valid, cap, reached⟩
    exact Nat.le_trans reached (optimum.2 batch ⟨valid, cap⟩)
  · intro reached
    exact ⟨witness, optimum.1.1, optimum.1.2, reached⟩

theorem witness_update_preserves_feasibility {α β : Type}
    {compatible : α → β → Prop} {state : α} (witness : β) (update : α → β → α)
    (valid : compatible state witness)
    (preserved : compatible state witness → compatible (update state witness) witness) :
    compatible (update state witness) witness := preserved valid

end MWPC
