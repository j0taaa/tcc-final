import MWPC.CfgSampling

/-! The combinatorial obstruction behind non-negative covering products.
    Natural-coefficient plans reduce to finite rectangles in this file. The
    real-coefficient reduction, Python and neural models are outside its scope.
    Ternary words encode disjoint left/right witness masks. -/

namespace MWPC

def semanticLeft (x : Fin 3) : Bool := x == 2
def semanticRight (x : Fin 3) : Bool := x == 1
def semanticOutput (x : Fin 3) : Bool := x != 0

theorem semantic_bit_fooling (x y : Fin 3)
    (same : semanticOutput x = semanticOutput y)
    (lr : (semanticLeft x || semanticRight y) = semanticOutput x)
    (rl : (semanticLeft y || semanticRight x) = semanticOutput x) : x = y := by
  obtain ⟨x, hx⟩ := x
  obtain ⟨y, hy⟩ := y
  have cx : x = 0 ∨ x = 1 ∨ x = 2 := by omega
  have cy : y = 0 ∨ y = 1 ∨ y = 2 := by omega
  rcases cx with rfl | rfl | rfl <;> rcases cy with rfl | rfl | rfl <;>
    simp_all [semanticLeft, semanticRight, semanticOutput]

theorem semantic_word_fooling (u v : List (Fin 3))
    (same : u.map semanticOutput = v.map semanticOutput)
    (lr : List.zipWith Bool.or (u.map semanticLeft) (v.map semanticRight) =
      u.map semanticOutput)
    (rl : List.zipWith Bool.or (v.map semanticLeft) (u.map semanticRight) =
      u.map semanticOutput) : u = v := by
  induction u generalizing v with
  | nil => cases v <;> simp_all
  | cons x xs ih =>
    cases v with
    | nil => simp at same
    | cons y ys =>
      simp only [List.map_cons, List.zipWith_cons_cons, List.cons.injEq] at same lr rl
      have xy := semantic_bit_fooling x y same.1 lr.1 rl.1
      have rest := ih ys same.2 lr.2 rl.2
      rw [xy, rest]

def semanticWitnesses : Nat → List (List (Fin 3))
  | 0 => [[]]
  | n + 1 => (semanticWitnesses n).map (0 :: ·) ++
    (semanticWitnesses n).map (1 :: ·) ++ (semanticWitnesses n).map (2 :: ·)

theorem semantic_witnesses_count (m : Nat) :
    (semanticWitnesses m).length = 3 ^ m := by
  induction m with
  | zero => simp [semanticWitnesses]
  | succ m ih => simp [semanticWitnesses, ih, Nat.pow_succ]; omega

theorem semantic_witnesses_distinct (m : Nat) : (semanticWitnesses m).Nodup := by
  induction m with
  | zero => simp [semanticWitnesses]
  | succ m ih =>
    have mapped (c : Fin 3) : ((semanticWitnesses m).map (c :: ·)).Nodup :=
      ih.map _ (by intro a b ne same; exact ne (List.cons.inj same).2)
    have disjoint (c d : Fin 3) (ne : c ≠ d) :
        ∀ a ∈ (semanticWitnesses m).map (c :: ·),
          ∀ b ∈ (semanticWitnesses m).map (d :: ·), a ≠ b := by
      intro a ha b hb same
      obtain ⟨u, _, rfl⟩ := List.mem_map.mp ha
      obtain ⟨v, _, rfl⟩ := List.mem_map.mp hb
      exact ne (List.cons.inj same).1
    simp only [semanticWitnesses, List.nodup_append]
    refine ⟨⟨mapped 0, mapped 1, disjoint 0 1 (by decide)⟩, mapped 2, ?_⟩
    intro a ha b hb same
    rcases List.mem_append.mp ha with ha | ha
    · exact disjoint 0 2 (by decide) a ha b hb same
    · exact disjoint 1 2 (by decide) a ha b hb same

theorem semantic_rectangle_cover_bound {R : Type} (m : Nat)
    (left right output : R → List Bool → Prop)
    (correct : ∀ r a b c, left r a → right r b → output r c →
      List.zipWith Bool.or a b = c)
    (route : {w : List (Fin 3) // w ∈ semanticWitnesses m} → R)
    (covered : ∀ w, left (route w) (w.val.map semanticLeft) ∧
      right (route w) (w.val.map semanticRight) ∧ output (route w) (w.val.map semanticOutput))
    (rectangles : List R) (complete : ∀ w, route w ∈ rectangles) :
    3 ^ m ≤ rectangles.length := by
  have inj : ∀ u v, route u = route v → u = v := by
    intro u v eq
    obtain ⟨lu, ru, ou⟩ := covered u
    obtain ⟨lv, rv, ov⟩ := covered v
    rw [← eq] at lv rv ov
    have own := correct (route u) _ _ _ lu ru ou
    have same := correct (route u) _ _ _ lu ru ov
    apply Subtype.ext
    apply semantic_word_fooling u.val v.val (own.symm.trans same)
    · exact correct (route u) _ _ _ lu rv ou
    · exact correct (route u) _ _ _ lv ru ou
  have unique : (semanticWitnesses m).attach.Nodup := by
    apply List.Pairwise.of_map (S := fun a b : List (Fin 3) => a ≠ b) Subtype.val
      (fun a b ne eq => ne (congrArg Subtype.val eq))
    simpa [List.Nodup] using semantic_witnesses_distinct m
  have distinct : ((semanticWitnesses m).attach.map route).Nodup :=
    unique.map route (by intro a b ne eq; exact ne (inj a b eq))
  have subset : (semanticWitnesses m).attach.map route ⊆ rectangles := by
    intro r member
    obtain ⟨w, _, rfl⟩ := List.mem_map.mp member
    exact complete w
  have count := distinct.length_le_of_subset subset
  simpa [semantic_witnesses_count] using count

theorem semantic_witness_length (m : Nat) (w : List (Fin 3))
    (member : w ∈ semanticWitnesses m) : w.length = m := by
  induction m generalizing w with
  | zero => simp [semanticWitnesses] at member; simp [member]
  | succ m ih =>
    simp only [semanticWitnesses, List.mem_append, List.mem_map] at member
    rcases member with (⟨v, hv, rfl⟩ | ⟨v, hv, rfl⟩) | ⟨v, hv, rfl⟩ <;>
      simp [ih v hv]

theorem semantic_coordinate_union (x : Fin 3) :
    (semanticLeft x || semanticRight x) = semanticOutput x := by
  obtain ⟨x, hx⟩ := x
  have cx : x = 0 ∨ x = 1 ∨ x = 2 := by omega
  rcases cx with rfl | rfl | rfl <;>
    simp [semanticLeft, semanticRight, semanticOutput]

theorem semantic_witness_union (w : List (Fin 3)) :
    List.zipWith Bool.or (w.map semanticLeft) (w.map semanticRight) =
      w.map semanticOutput := by
  induction w with
  | nil => simp
  | cons x xs ih => simp [semantic_coordinate_union, ih]

/- Natural coefficients also permit a non-unit uniform tensor scale k. Thus
   non-negative rational coefficients may be covered after clearing their
   denominators. The real-coefficient support reduction remains written. -/
theorem semantic_nonnegative_bilinear_lower_bound (m r k : Nat) (positive : 0 < k)
    (u v w : Fin r → List Bool → Nat)
    (coefficients : ∀ a b c, a.length = m → b.length = m → c.length = m →
      ((List.finRange r).map (fun j => u j a * v j b * w j c)).sum =
        if List.zipWith Bool.or a b = c then k else 0) : 3 ^ m ≤ r := by
  classical
  let U := {word : List (Fin 3) // word ∈ semanticWitnesses m}
  have covered : ∀ word : U, ∃ j : Fin r,
      0 < u j (word.val.map semanticLeft) * v j (word.val.map semanticRight) *
        w j (word.val.map semanticOutput) := by
    intro word
    have length := semantic_witness_length m word.val word.property
    have total := coefficients (word.val.map semanticLeft) (word.val.map semanticRight)
      (word.val.map semanticOutput) (by simpa) (by simpa) (by simpa)
    rw [ite_eq_left (semantic_witness_union word.val)] at total
    have nonzero : 0 < ((List.finRange r).map (fun j =>
        u j (word.val.map semanticLeft) * v j (word.val.map semanticRight) *
          w j (word.val.map semanticOutput))).sum := by omega
    obtain ⟨x, member, hx⟩ := List.sum_pos_iff_exists_pos_nat.mp nonzero
    obtain ⟨j, _, rfl⟩ := List.mem_map.mp member
    exact ⟨j, hx⟩
  let route : U → Fin r := fun word => Classical.choose (covered word)
  let left : Fin r → List Bool → Prop := fun j a => a.length = m ∧ 0 < u j a
  let right : Fin r → List Bool → Prop := fun j b => b.length = m ∧ 0 < v j b
  let output : Fin r → List Bool → Prop := fun j c => c.length = m ∧ 0 < w j c
  have correct : ∀ j a b c, left j a → right j b → output j c →
      List.zipWith Bool.or a b = c := by
    intro j a b c ha hb hc
    apply Classical.byContradiction
    intro ne
    have total := coefficients a b c ha.1 hb.1 hc.1
    rw [ite_eq_right ne] at total
    have zero := List.sum_eq_zero_iff_forall_eq_nat.mp total
    have member : u j a * v j b * w j c ∈
        (List.finRange r).map (fun j => u j a * v j b * w j c) := by simp
    have isZero := zero _ member
    have isPositive := Nat.mul_pos (Nat.mul_pos ha.2 hb.2) hc.2
    omega
  have routes : ∀ word : U, left (route word) (word.val.map semanticLeft) ∧
      right (route word) (word.val.map semanticRight) ∧
      output (route word) (word.val.map semanticOutput) := by
    intro word
    have length := semantic_witness_length m word.val word.property
    have term := Classical.choose_spec (covered word)
    have pair := Nat.pos_of_mul_pos_right term
    exact ⟨⟨by simpa, Nat.pos_of_mul_pos_right pair⟩,
      ⟨by simpa, Nat.pos_of_mul_pos_left pair⟩,
      ⟨by simpa, Nat.pos_of_mul_pos_left term⟩⟩
  simpa using semantic_rectangle_cover_bound m left right output correct route routes
    (List.finRange r) (by intro word; simp)

end MWPC
