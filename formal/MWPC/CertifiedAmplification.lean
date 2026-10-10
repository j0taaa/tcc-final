import MWPC.ExactEnvelope

/-! Integer certificate for increasing valid product mass by amplifying one
    original coordinate. Z is the full valid mass in common units, P its joint
    valid/selected-coordinate mass. N is a known-valid joint lower mass, M an
    upper bound on Z, and W/D the original coordinate probability.
    This checks the comparative algebra, not Python or the grammar compiler. -/
namespace MWPC.CertifiedAmplification

theorem certified_margin (N P Z M W D : Nat)
    (joint_lower : N ≤ P) (mass_upper : Z ≤ M)
    (strict_margin : W * M < N * D) : W * Z < P * D := by
  calc
    W * Z ≤ W * M := Nat.mul_le_mul_left W mass_upper
    _ < N * D := strict_margin
    _ ≤ P * D := Nat.mul_le_mul_right D joint_lower

-- Amplifier is 1+k. Positive normalization denominators are additionally
-- required when interpreting this cross multiplication as a mass ratio.
theorem strictly_increases_valid_mass (N P Z M W D k : Nat)
    (joint_lower : N ≤ P) (mass_upper : Z ≤ M)
    (strict_margin : W * M < N * D) (positive_boost : 0 < k) :
    Z * (D + k * W) < D * (Z + k * P) := by
  have weighted := Nat.mul_lt_mul_of_pos_left
    (certified_margin N P Z M W D joint_lower mass_upper strict_margin) positive_boost
  calc
    Z * (D + k * W) = Z * D + k * (W * Z) := by
      rw [Nat.mul_add]
      ac_rfl
    _ < Z * D + k * (P * D) := Nat.add_lt_add_left weighted (Z * D)
    _ = D * (Z + k * P) := by
      rw [Nat.mul_add]
      ac_rfl
end MWPC.CertifiedAmplification
