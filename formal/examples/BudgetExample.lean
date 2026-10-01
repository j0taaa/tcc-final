import MWPC
-- Generated; edit the original JSON proof, never this certificate.
-- Original-input SHA-256: 2b79ca0715898174e002a415c70a7003a02c98860f6925b5378cf61493826d7e
-- Integer reward unit: 1/8
-- Scope: finite resource CFG graph; Python independently checks input correspondence.
set_option maxRecDepth 100000
set_option maxHeartbeats 100000000
namespace MWPC.Generated
def arc0 : Arc 8 := ⟨(⟨0, by decide⟩ : Fin 8), (⟨2, by decide⟩ : Fin 8), some 97, 0, 0⟩
def arc1 : Arc 8 := ⟨(⟨0, by decide⟩ : Fin 8), (⟨2, by decide⟩ : Fin 8), some 97, 7, 1⟩
def arc2 : Arc 8 := ⟨(⟨0, by decide⟩ : Fin 8), (⟨2, by decide⟩ : Fin 8), some 120, 0, 0⟩
def arc3 : Arc 8 := ⟨(⟨2, by decide⟩ : Fin 8), (⟨4, by decide⟩ : Fin 8), some 98, 0, 0⟩
def arc4 : Arc 8 := ⟨(⟨2, by decide⟩ : Fin 8), (⟨4, by decide⟩ : Fin 8), some 121, 0, 0⟩
def arc5 : Arc 8 := ⟨(⟨2, by decide⟩ : Fin 8), (⟨4, by decide⟩ : Fin 8), some 121, 4, 1⟩
def arc6 : Arc 8 := ⟨(⟨4, by decide⟩ : Fin 8), (⟨6, by decide⟩ : Fin 8), some 99, 0, 0⟩
def arc7 : Arc 8 := ⟨(⟨4, by decide⟩ : Fin 8), (⟨6, by decide⟩ : Fin 8), some 122, 0, 0⟩
def arc8 : Arc 8 := ⟨(⟨4, by decide⟩ : Fin 8), (⟨6, by decide⟩ : Fin 8), some 122, 4, 1⟩
def grammar : Grammar := ⟨0, [(1, 97), (2, 98), (3, 99), (4, 120), (5, 121), (6, 122)], [(0, 1, 7), (7, 2, 3), (0, 4, 8), (8, 5, 6)], false⟩
def graph : Graph 8 := ⟨(⟨0, by decide⟩ : Fin 8), [(⟨6, by decide⟩ : Fin 8)], [arc0, arc1, arc2, arc3, arc4, arc5, arc6, arc7, arc8]⟩
def epsilonTable (u v : Fin 8) (k : Nat) : Option Nat :=
  match u.val, v.val, k with
  | 0, 0, 0 => some 0
  | 1, 1, 0 => some 0
  | 2, 2, 0 => some 0
  | 3, 3, 0 => some 0
  | 4, 4, 0 => some 0
  | 5, 5, 0 => some 0
  | 6, 6, 0 => some 0
  | 7, 7, 0 => some 0
  | _, _, _ => none
def grammarTable (head : Nat) (u v : Fin 8) (k : Nat) : Option Nat :=
  match head, u.val, v.val, k with
  | 0, 0, 6, 0 => some 0
  | 0, 0, 6, 1 => some 7
  | 0, 0, 6, 2 => some 8
  | 1, 0, 2, 0 => some 0
  | 1, 0, 2, 1 => some 7
  | 2, 2, 4, 0 => some 0
  | 3, 4, 6, 0 => some 0
  | 4, 0, 2, 0 => some 0
  | 5, 2, 4, 0 => some 0
  | 5, 2, 4, 1 => some 4
  | 6, 4, 6, 0 => some 0
  | 6, 4, 6, 1 => some 4
  | 7, 2, 6, 0 => some 0
  | 8, 2, 6, 0 => some 0
  | 8, 2, 6, 1 => some 4
  | 8, 2, 6, 2 => some 8
  | _, _, _, _ => none
def potentials : Potentials 8 := ⟨3, epsilonTable, grammarTable⟩
theorem valid : ValidPotentials grammar graph potentials := by
  constructor <;> decide
theorem roots_0 : RootUpper grammar graph potentials 0 0 := by
  unfold RootUpper; decide
theorem witness_0 : Accepted grammar graph 0 0 := by
  exact ⟨(⟨6, by decide⟩ : Fin 8), by decide, 0, by decide, Or.inl (Derivation.binary (head := 0) (left := 1) (right := 7) (by decide) (Derivation.terminal arc0 (head := 1) (label := 97) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨0, by decide⟩ : Fin 8)) (Epsilon.identity (⟨2, by decide⟩ : Fin 8))) (Derivation.binary (head := 7) (left := 2) (right := 3) (by decide) (Derivation.terminal arc3 (head := 2) (label := 98) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨2, by decide⟩ : Fin 8)) (Epsilon.identity (⟨4, by decide⟩ : Fin 8))) (Derivation.terminal arc6 (head := 3) (label := 99) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨4, by decide⟩ : Fin 8)) (Epsilon.identity (⟨6, by decide⟩ : Fin 8)))))⟩
theorem optimal_0 : Accepted grammar graph 0 0 ∧
    ∀ reward, Accepted grammar graph 0 reward → reward ≤ 0 :=
  certified_optimal valid (by decide) roots_0 witness_0
#print axioms optimal_0
theorem roots_1 : RootUpper grammar graph potentials 1 7 := by
  unfold RootUpper; decide
theorem witness_1 : Accepted grammar graph 1 7 := by
  exact ⟨(⟨6, by decide⟩ : Fin 8), by decide, 1, by decide, Or.inl (Derivation.binary (head := 0) (left := 1) (right := 7) (by decide) (Derivation.terminal arc1 (head := 1) (label := 97) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨0, by decide⟩ : Fin 8)) (Epsilon.identity (⟨2, by decide⟩ : Fin 8))) (Derivation.binary (head := 7) (left := 2) (right := 3) (by decide) (Derivation.terminal arc3 (head := 2) (label := 98) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨2, by decide⟩ : Fin 8)) (Epsilon.identity (⟨4, by decide⟩ : Fin 8))) (Derivation.terminal arc6 (head := 3) (label := 99) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨4, by decide⟩ : Fin 8)) (Epsilon.identity (⟨6, by decide⟩ : Fin 8)))))⟩
theorem optimal_1 : Accepted grammar graph 1 7 ∧
    ∀ reward, Accepted grammar graph 1 reward → reward ≤ 7 :=
  certified_optimal valid (by decide) roots_1 witness_1
#print axioms optimal_1
theorem roots_2 : RootUpper grammar graph potentials 2 8 := by
  unfold RootUpper; decide
theorem witness_2 : Accepted grammar graph 2 8 := by
  exact ⟨(⟨6, by decide⟩ : Fin 8), by decide, 2, by decide, Or.inl (Derivation.binary (head := 0) (left := 4) (right := 8) (by decide) (Derivation.terminal arc2 (head := 4) (label := 120) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨0, by decide⟩ : Fin 8)) (Epsilon.identity (⟨2, by decide⟩ : Fin 8))) (Derivation.binary (head := 8) (left := 5) (right := 6) (by decide) (Derivation.terminal arc5 (head := 5) (label := 121) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨2, by decide⟩ : Fin 8)) (Epsilon.identity (⟨4, by decide⟩ : Fin 8))) (Derivation.terminal arc8 (head := 6) (label := 122) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨4, by decide⟩ : Fin 8)) (Epsilon.identity (⟨6, by decide⟩ : Fin 8)))))⟩
theorem optimal_2 : Accepted grammar graph 2 8 ∧
    ∀ reward, Accepted grammar graph 2 reward → reward ≤ 8 :=
  certified_optimal valid (by decide) roots_2 witness_2
#print axioms optimal_2
theorem roots_3 : RootUpper grammar graph potentials 3 8 := by
  unfold RootUpper; decide
theorem witness_3 : Accepted grammar graph 3 8 := by
  exact ⟨(⟨6, by decide⟩ : Fin 8), by decide, 2, by decide, Or.inl (Derivation.binary (head := 0) (left := 4) (right := 8) (by decide) (Derivation.terminal arc2 (head := 4) (label := 120) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨0, by decide⟩ : Fin 8)) (Epsilon.identity (⟨2, by decide⟩ : Fin 8))) (Derivation.binary (head := 8) (left := 5) (right := 6) (by decide) (Derivation.terminal arc5 (head := 5) (label := 121) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨2, by decide⟩ : Fin 8)) (Epsilon.identity (⟨4, by decide⟩ : Fin 8))) (Derivation.terminal arc8 (head := 6) (label := 122) (by decide) (by rfl) (by decide) (Epsilon.identity (⟨4, by decide⟩ : Fin 8)) (Epsilon.identity (⟨6, by decide⟩ : Fin 8)))))⟩
theorem optimal_3 : Accepted grammar graph 3 8 ∧
    ∀ reward, Accepted grammar graph 3 reward → reward ≤ 8 :=
  certified_optimal valid (by decide) roots_3 witness_3
#print axioms optimal_3
end MWPC.Generated
