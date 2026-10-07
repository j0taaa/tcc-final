import Std

/-! A finite fooling-set state lower bound, independent of experiment frequency.
    Prefix/suffix reachability is an explicit hypothesis, not an assumed-correct
    Python parser. Instantiating it with two-type balanced delimiters is explained
    in M34's written proof. No neural trajectory distribution is specified here. -/

namespace MWPC

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

end MWPC
