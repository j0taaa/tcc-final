import MWPC.SemanticProfiles

/-! Finite refinement progress and the p-exclusion obstruction.
    Probabilistic conditioning and the Python implementation are separate
    written/tested obligations. No sampling distribution is axiomatized here. -/

namespace MWPC

theorem semantic_refinement_new {Y : Type} {m : Nat}
    (checks : Fin m → Y → Bool) (active : List (Fin m)) (y : Y)
    (consistent : ∀ i ∈ active, checks i y = true)
    (i : Fin m) (violated : checks i y = false) : i ∉ active := by
  intro member
  have yes := consistent i member
  simp_all

theorem semantic_refinement_progress {m : Nat} (active : List (Fin m))
    (distinct : active.Nodup) (i : Fin m) (fresh : i ∉ active) :
    (i :: active).Nodup ∧ (i :: active).length = active.length + 1 := by
  simp [distinct, fresh]

theorem semantic_refinement_bound {m : Nat} (rejections : List (Fin m))
    (distinct : rejections.Nodup) : rejections.length ≤ m := by
  have bound := distinct.length_le_of_subset
    (l₂ := List.finRange m) (by intro i _; simp)
  simpa using bound

def semanticViolationCount {Y : Type} (domain : List Y) (core check : Y → Bool) : Nat :=
  (domain.filter (fun y => core y && !check y)).length

theorem semantic_zero_violations_imply {Y : Type} (domain : List Y)
    (core check : Y → Bool) (zero : semanticViolationCount domain core check = 0)
    (y : Y) (member : y ∈ domain) (satisfies : core y = true) : check y = true := by
  have empty : domain.filter (fun y => core y && !check y) = [] :=
    List.length_eq_zero_iff.mp zero
  cases value : check y with
  | true => rfl
  | false =>
    have included : y ∈ domain.filter (fun y => core y && !check y) := by
      simp [member, satisfies, value]
    simp [empty] at included

theorem semantic_core_complete {Y : Type} {m : Nat} (domain : List Y)
    (checks : Fin m → Y → Bool) (active : List (Fin m))
    (zero : ∀ i, semanticViolationCount domain
      (fun y => active.all (fun j => checks j y)) (checks i) = 0)
    (y : Y) (member : y ∈ domain) :
    (List.finRange m).all (fun i => checks i y) = active.all (fun i => checks i y) := by
  cases value : active.all (fun i => checks i y) with
  | true =>
    apply List.all_eq_true.mpr
    intro i _
    exact semantic_zero_violations_imply domain _ (checks i) (zero i) y member value
  | false =>
    cases full : (List.finRange m).all (fun i => checks i y) with
    | false => rfl
    | true =>
      have yes : active.all (fun i => checks i y) = true := by
        apply List.all_eq_true.mpr
        intro i _
        exact List.all_eq_true.mp full i (by simp)
      simp [value] at yes

def semanticAcceptedMass {Y : Type} (domain : List Y) (weights : Y → Nat)
    (accept : Y → Bool) : Nat := (domain.map (fun y => if accept y then weights y else 0)).sum

theorem semantic_core_arbitrary_reweighting {Y : Type} (base restricted : List Y)
    (full core : Y → Bool) (agree : ∀ y ∈ base, full y = core y)
    (weights : Y → Nat) (subset : restricted ⊆ base) :
    semanticAcceptedMass restricted weights full = semanticAcceptedMass restricted weights core := by
  revert subset
  induction restricted with
  | nil => intro _; rfl
  | cons y ys ih =>
    intro subset
    have head := agree y (subset (by simp))
    have rest : ys ⊆ base := by intro x hx; exact subset (by simp [hx])
    simp only [semanticAcceptedMass, List.map_cons, List.sum_cons, head]
    exact congrArg (fun n => (if core y then weights y else 0) + n) (ih rest)

def parity : List Bool → Bool
  | [] => false
  | b :: bs => Bool.xor b (parity bs)

theorem parity_append (a b : List Bool) :
    parity (a ++ b) = Bool.xor (parity a) (parity b) := by
  induction a with
  | nil => simp [parity]
  | cons x xs ih =>
    simp only [List.cons_append, parity, ih]
    cases x <;> cases parity xs <;> cases parity b <;> decide

theorem parity_zeros (n : Nat) : parity (List.replicate n false) = false := by
  induction n with
  | zero => rfl
  | succ n ih => simp [List.replicate_succ, parity, ih]

theorem parity_prefix_extend (n : Nat) (p : List Bool)
    (short : p.length ≤ n) :
    ∃ suffix, (p ++ suffix).length = n + 1 ∧ parity (p ++ suffix) = false := by
  refine ⟨List.replicate (n - p.length) false ++ [parity p], ?_, ?_⟩
  · simp only [List.length_append, List.length_replicate, List.length_singleton]
    omega
  · simp only [parity_append, parity_zeros, parity, Bool.xor_false]
    cases parity p <;> decide

def binaryWords : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (binaryWords n).map (false :: ·) ++ (binaryWords n).map (true :: ·)

theorem binary_words_count (n : Nat) : (binaryWords n).length = 2 ^ n := by
  induction n with
  | zero => simp [binaryWords]
  | succ n ih => simp [binaryWords, ih, Nat.pow_succ]; omega

theorem binary_words_length (n : Nat) (w : List Bool) (member : w ∈ binaryWords n) :
    w.length = n := by
  induction n generalizing w with
  | zero => simp [binaryWords] at member; simp [member]
  | succ n ih =>
    simp only [binaryWords, List.mem_append, List.mem_map] at member
    rcases member with ⟨v, hv, rfl⟩ | ⟨v, hv, rfl⟩ <;> simp [ih v hv]

theorem binary_words_distinct (n : Nat) : (binaryWords n).Nodup := by
  induction n with
  | zero => simp [binaryWords]
  | succ n ih =>
    have mapped (b : Bool) : ((binaryWords n).map (b :: ·)).Nodup :=
      ih.map _ (by intro a c ne same; exact ne (List.cons.inj same).2)
    simp only [binaryWords, List.nodup_append]
    refine ⟨mapped false, mapped true, ?_⟩
    intro a ha b hb same
    obtain ⟨u, _, rfl⟩ := List.mem_map.mp ha
    obtain ⟨v, _, rfl⟩ := List.mem_map.mp hb
    have head := (List.cons.inj same).1
    contradiction

def parityBad (w : List Bool) : List Bool := w ++ [!(parity w)]

theorem parity_bad_value (w : List Bool) : parity (parityBad w) = true := by
  simp only [parityBad, parity_append, parity, Bool.xor_false]
  cases parity w <;> decide

theorem parity_bad_injective (u v : List Bool) (same : parityBad u = parityBad v) : u = v := by
  have eq := congrArg List.dropLast same
  simpa [parityBad] using eq

theorem parity_exclusion_prefix_unique (n : Nat) (w p : List Bool)
    (length : w.length = n + 1)
    (covered : ∃ suffix, p ++ suffix = w)
    (invalid : ∀ suffix, (p ++ suffix).length = n + 1 →
      parity (p ++ suffix) ≠ false) : p = w := by
  obtain ⟨suffix, eq⟩ := covered
  have sizes : p.length + suffix.length = n + 1 := by
    simpa only [List.length_append, length] using congrArg List.length eq
  have full : p.length = n + 1 := by
    apply Classical.byContradiction
    intro ne
    have short : p.length ≤ n := by omega
    obtain ⟨tail, ht, good⟩ := parity_prefix_extend n p short
    exact invalid tail ht good
  have zero : suffix.length = 0 := by omega
  have empty : suffix = [] := List.length_eq_zero_iff.mp zero
  simpa [empty] using eq

theorem parity_prefix_exclusion_bound (n : Nat) (prefixes : List (List Bool))
    (invalid : ∀ p ∈ prefixes, ∀ suffix,
      (p ++ suffix).length = n + 1 → parity (p ++ suffix) ≠ false)
    (route : {w : List Bool // w ∈ binaryWords n} → List Bool)
    (inList : ∀ w, route w ∈ prefixes)
    (covered : ∀ w, ∃ suffix, route w ++ suffix = parityBad w.val) :
    2 ^ n ≤ prefixes.length := by
  have full (w : {w : List Bool // w ∈ binaryWords n}) : route w = parityBad w.val := by
    apply parity_exclusion_prefix_unique n (parityBad w.val) (route w)
    · simp [parityBad, binary_words_length n w.val w.property]
    · exact covered w
    · exact invalid (route w) (inList w)
  have inj : ∀ u v, route u = route v → u = v := by
    intro u v same
    apply Subtype.ext
    apply parity_bad_injective
    simpa only [full] using same
  have distinct : (binaryWords n).attach.Nodup := by
    apply List.Pairwise.of_map (S := fun a b : List Bool => a ≠ b) Subtype.val
      (fun a b ne eq => ne (congrArg Subtype.val eq))
    simpa [List.Nodup] using binary_words_distinct n
  have mapped : ((binaryWords n).attach.map route).Nodup :=
    distinct.map route (by intro a b ne same; exact ne (inj a b same))
  have subset : (binaryWords n).attach.map route ⊆ prefixes := by
    intro p member
    obtain ⟨w, _, rfl⟩ := List.mem_map.mp member
    exact inList w
  simpa [binary_words_count] using mapped.length_le_of_subset subset

end MWPC
