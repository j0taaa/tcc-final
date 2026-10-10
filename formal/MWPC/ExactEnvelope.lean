import MWPC.Probability

/-! Exact integer counts for a fixed-budget rejection experiment. A proposal
    has M equally weighted units; R are invalid, and each valid event owns w.
    Returning after the first success leaves later draws unobserved. The counts
    include those latent draws to put every history over denominator M^k.
    This is a sampling specification, not a Python/compiler refinement. -/
namespace MWPC.ExactEnvelope

def geometricFactor (M R : Nat) : Nat → Nat
  | 0 => 0
  | k + 1 => M ^ k + R * geometricFactor M R k

def returnedCount (w M R : Nat) : Nat → Nat
  | 0 => 0
  | k + 1 => w * M ^ k + R * returnedCount w M R k

theorem returned_factor (w M R k : Nat) :
    returnedCount w M R k = w * geometricFactor M R k := by
  induction k with
  | zero => simp [returnedCount, geometricFactor]
  | succ k ih =>
      simp only [returnedCount, geometricFactor, ih, Nat.mul_add]
      rw [Nat.mul_left_comm R w]

theorem returned_sum (weights : List Nat) (M R k : Nat) :
    (weights.map (fun w => returnedCount w M R k)).sum =
      weights.sum * geometricFactor M R k := by
  induction weights with
  | nil => simp
  | cons w tail ih =>
      simp only [List.map_cons, List.sum_cons, Nat.add_mul]
      rw [returned_factor, ih]

theorem complete_partition (Z R M k : Nat) (partition : M = R + Z) :
    R ^ k + Z * geometricFactor M R k = M ^ k := by
  induction k with
  | zero => simp [geometricFactor]
  | succ k ih =>
      calc
        R ^ (k + 1) + Z * geometricFactor M R (k + 1) =
            (R ^ k + Z * geometricFactor M R k) * R + Z * M ^ k := by
              simp only [geometricFactor, Nat.pow_succ, Nat.mul_add, Nat.add_mul]
              ac_rfl
        _ = M ^ k * R + Z * M ^ k := by rw [ih]
        _ = M ^ k * (R + Z) := by rw [Nat.mul_add]; ac_rfl
        _ = M ^ (k + 1) := by rw [← partition, Nat.pow_succ]

-- Cross multiplication proves exact law conditional on success; positive
-- success mass is required before interpreting this equation as a ratio.
theorem finite_budget_preserves_law (w : Nat) (weights : List Nat) (M R k : Nat) :
    returnedCount w M R k * weights.sum =
      w * (weights.map (fun v => returnedCount v M R k)).sum := by
  rw [returned_factor, returned_sum]
  ac_rfl

theorem rejected_units_le_tail (L U Z R : Nat)
    (envelope : L + U = Z + R) (known_valid : L ≤ Z) : R ≤ U := by
  omega

theorem finite_refusal_bound (R U k : Nat) (bounded : R ≤ U) : R ^ k ≤ U ^ k := by
  induction k with
  | zero => simp
  | succ k ih => simpa only [Nat.pow_succ] using Nat.mul_le_mul ih bounded

-- The combined envelope has mass L+U, unlike an arbitrary mixture proposal.
-- Therefore these counts specify P(refusal) ≤ (U/(L+U))^k, including k=0.
theorem certified_refusal_bound (L U Z R k : Nat)
    (envelope : L + U = Z + R) (known_valid : L ≤ Z) : R ^ k ≤ U ^ k := by
  exact finite_refusal_bound R U k (rejected_units_le_tail L U Z R envelope known_valid)
end MWPC.ExactEnvelope
