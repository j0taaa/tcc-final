import MWPC.Probability

/-! Selected finite-ticket specifications. Classical arithmetic identities;
    not a refinement proof of the Python batch, CFG compiler, neural decoder,
    or the written all-K trajectory dominance/variance theorem. -/
namespace MWPC.StratifiedBatches

-- Every original ticket has exactly K lifts, one for each residue s<K.
theorem ticket_lift_div (K i s : Nat) (positive : 0 < K) (residue : s < K) :
    (i * K + s) / K = i := by
  rw [Nat.add_comm, Nat.add_mul_div_right _ _ positive, Nat.div_eq_of_lt residue]
  simp

theorem ticket_lift_mod (K i s : Nat) (positive : 0 < K) (residue : s < K) :
    (i * K + s) % K = s := by
  have h := Nat.div_add_mod (i * K + s) K
  rw [ticket_lift_div K i s positive residue, Nat.mul_comm K i] at h
  omega

theorem ticket_reconstruction (K z : Nat) :
    (z / K) * K + z % K = z := by
  simpa only [Nat.mul_comm] using Nat.div_add_mod z K

theorem ticket_lift_injective (K i j s t : Nat) (positive : 0 < K)
    (hs : s < K) (ht : t < K) (equal : i * K + s = j * K + t) :
    i = j ∧ s = t := by
  have hi := ticket_lift_div K i s positive hs
  have hj := ticket_lift_div K j t positive ht
  rw [equal] at hi
  have ij : i = j := by omega
  constructor
  · exact ij
  · rw [ij] at equal; omega

-- With two strata of W tickets, a,b failures: stratified failure ab/W²
-- is at most iid failure ((a+b)/(2W))². No floating-point or RNG assumption
-- is hidden in this integer comparison; positivity of W is needed for ratios.
theorem two_strata_failure_dominance (a b : Nat) :
    4 * (a * b) ≤ (a + b) * (a + b) := by
  have ordered (x y : Nat) (h : x ≤ y) :
      4 * (x * y) ≤ (x + y) * (x + y) := by
    obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le h
    rw [hd]
    simp only [Nat.add_mul, Nat.mul_add, Nat.mul_comm]
    omega
  rcases Nat.le_total a b with h | h
  · exact ordered a b h
  · simpa only [Nat.add_comm, Nat.mul_comm] using ordered b a h

end MWPC.StratifiedBatches
