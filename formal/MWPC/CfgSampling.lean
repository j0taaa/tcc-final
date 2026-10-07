import Std

/-! A finite fooling-set state lower bound, independent of experiment frequency.
    Prefix/suffix reachability is an explicit hypothesis, not an assumed-correct
    Python parser. Instantiating it with two-type balanced delimiters is explained
    in M34's written proof. No neural trajectory distribution is specified here. -/

namespace MWPC

/- A complete path consumes the same row set: integer row scaling therefore
   factors into one constant product. Input rationalization and forest/path
   bijection remain explicit written obligations, not Lean source refinement. -/
theorem row_product_scaling (rows : List (Nat × Nat)) :
    (rows.map (fun row => row.1 * row.2)).prod =
      (rows.map Prod.fst).prod * (rows.map Prod.snd).prod := by
  induction rows with
  | nil => simp
  | cons row rows ih =>
      simp [ih, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

def openingStacks : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (openingStacks n).map (false :: ·) ++
      (openingStacks n).map (true :: ·)

theorem opening_stacks_count (depth : Nat) :
    (openingStacks depth).length = 2 ^ depth := by
  induction depth with
  | zero => simp [openingStacks]
  | succ n ih => simp [openingStacks, ih, Nat.pow_succ, Nat.mul_two]

theorem opening_stacks_distinct (depth : Nat) : (openingStacks depth).Nodup := by
  induction depth with
  | zero => simp [openingStacks]
  | succ n ih =>
      apply List.nodup_append.mpr
      refine ⟨?_, ?_, ?_⟩
      · exact ih.map _ (by intro a b ne same; exact ne (List.cons.inj same).2)
      · exact ih.map _ (by intro a b ne same; exact ne (List.cons.inj same).2)
      · intro a ha b hb same
        obtain ⟨u, _, rfl⟩ := List.mem_map.mp ha
        obtain ⟨v, _, rfl⟩ := List.mem_map.mp hb
        cases same

theorem fooling_routes_injective {U S : Type}
    (prefixReach : U → S → Prop) (suffix : S → U → Prop) (route : U → S)
    (left : ∀ u, prefixReach u (route u))
    (right : ∀ u, suffix (route u) u)
    (cross : ∀ u v s, prefixReach u s → suffix s v → u = v) :
    ∀ u v, route u = route v → u = v := by
  intro u v same
  apply cross u v (route u) (left u)
  rw [same]
  exact right v

theorem fooling_state_count {U S : Type}
    (prefixReach : U → S → Prop) (suffix : S → U → Prop) (route : U → S)
    (left : ∀ u, prefixReach u (route u))
    (right : ∀ u, suffix (route u) u)
    (cross : ∀ u v s, prefixReach u s → suffix s v → u = v)
    (words : List U) (states : List S) (unique : words.Nodup)
    (complete : ∀ u, route u ∈ states) : words.length ≤ states.length := by
  have inj := fooling_routes_injective prefixReach suffix route left right cross
  have distinct : (words.map route).Nodup :=
    unique.map route (by intro a b ne same; exact ne (inj a b same))
  have contained : words.map route ⊆ states := by
    intro s member
    obtain ⟨u, _, rfl⟩ := List.mem_map.mp member
    exact complete u
  simpa using distinct.length_le_of_subset contained

theorem exponential_fooling_state_bound {S : Type} (depth : Nat)
    (prefixReach : Fin (2 ^ depth) → S → Prop)
    (suffix : S → Fin (2 ^ depth) → Prop) (route : Fin (2 ^ depth) → S)
    (left : ∀ u, prefixReach u (route u))
    (right : ∀ u, suffix (route u) u)
    (cross : ∀ u v s, prefixReach u s → suffix s v → u = v)
    (states : List S) (complete : ∀ u, route u ∈ states) :
    2 ^ depth ≤ states.length := by
  simpa using fooling_state_count prefixReach suffix route left right cross
    (List.finRange (2 ^ depth)) states (List.nodup_finRange _) complete

end MWPC
