import Std

/-! Exact finite budget relaxation. Each physical position is either skipped or
    paid once, with actual reward bounded by that position's maximum. -/

namespace MWPC

def budgetUpper (budget : Nat) : List Nat → Nat
  | [] => 0
  | maximum :: rest =>
    match budget with
    | 0 => 0
    | b + 1 => max (budgetUpper (b + 1) rest) (maximum + budgetUpper b rest)

theorem budgetUpper_zero (maxima : List Nat) : budgetUpper 0 maxima = 0 := by
  cases maxima <;> rfl

inductive BoundedBatch : List Nat → Nat → Nat → Prop
  | nil : BoundedBatch [] 0 0
  | skip (maximum : Nat) {rest : List Nat} {cost reward : Nat}
      (tail : BoundedBatch rest cost reward) :
      BoundedBatch (maximum :: rest) cost reward
  | take (maximum actual : Nat) {rest : List Nat} {cost reward : Nat}
      (bounded : actual ≤ maximum) (tail : BoundedBatch rest cost reward) :
      BoundedBatch (maximum :: rest) (cost + 1) (actual + reward)

theorem batch_upper (batch : BoundedBatch maxima cost reward) (cap : cost ≤ budget) :
    reward ≤ budgetUpper budget maxima := by
  induction batch generalizing budget with
  | nil => simp [budgetUpper]
  | skip maximum tail ih =>
      cases budget with
      | zero => simpa [budgetUpper_zero] using ih cap
      | succ b => exact Nat.le_trans (ih cap) (Nat.le_max_left _ _)
  | take maximum actual bounded tail ih =>
      cases budget with
      | zero => omega
      | succ b =>
          exact Nat.le_trans (Nat.add_le_add bounded (ih (by omega))) (Nat.le_max_right _ _)

theorem upper_attained (maxima : List Nat) (budget : Nat) :
    ∃ cost, cost ≤ budget ∧ BoundedBatch maxima cost (budgetUpper budget maxima) := by
  induction maxima generalizing budget with
  | nil => exact ⟨0, Nat.zero_le _, .nil⟩
  | cons maximum rest ih =>
      cases budget with
      | zero =>
          obtain ⟨cost, cap, witness⟩ := ih 0
          have zero : BoundedBatch (maximum :: rest) cost 0 := by
            simpa only [budgetUpper_zero] using BoundedBatch.skip maximum witness
          exact ⟨cost, cap, zero⟩
      | succ b =>
          by_cases choose : budgetUpper (b + 1) rest ≤ maximum + budgetUpper b rest
          · obtain ⟨cost, cap, witness⟩ := ih b
            refine ⟨cost + 1, by omega, ?_⟩
            simpa [budgetUpper, Nat.max_eq_right choose] using
              BoundedBatch.take maximum maximum (Nat.le_refl _) witness
          · obtain ⟨cost, cap, witness⟩ := ih (b + 1)
            refine ⟨cost, cap, ?_⟩
            have other : maximum + budgetUpper b rest ≤ budgetUpper (b + 1) rest := by omega
            simpa [budgetUpper, Nat.max_eq_left other] using BoundedBatch.skip maximum witness

theorem certified_gap {lower upper optimum : Nat}
    (feasible : lower ≤ optimum) (bound : optimum ≤ upper) :
    optimum - lower ≤ upper - lower := by omega

theorem bound_attainment {lower upper optimum : Nat}
    (feasible : lower ≤ optimum) (bound : optimum ≤ upper) (tight : lower = upper) :
    optimum = lower := by omega

theorem multiplicative_bound {lower upper optimum numerator denominator : Nat}
    (bound : optimum ≤ upper) (certificate : numerator * upper ≤ denominator * lower) :
    numerator * optimum ≤ denominator * lower := by
  exact Nat.le_trans (Nat.mul_le_mul_left numerator bound) certificate

theorem representation_preserves_optima {α β : Type}
    (leftReward : α → Nat) (rightReward : β → Nat)
    (encode : α → β) (decode : β → α)
    (encoding : ∀ a, rightReward (encode a) = leftReward a)
    (decoding : ∀ b, leftReward (decode b) = rightReward b)
    (a : α) (optimal : ∀ x, leftReward x ≤ leftReward a) :
    ∀ b, rightReward b ≤ rightReward (encode a) := by
  intro b
  rw [encoding, ← decoding]
  exact optimal (decode b)

end MWPC
