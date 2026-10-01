import MWPC.Bounds

/-! A shared prefix is a byte sequence, not a token identity. Identity, reward,
    and resource cost belong to the closing transition. -/
namespace MWPC

inductive PrefixWalk : List Nat → List Nat → Prop
  | root : PrefixWalk [] []
  | extend (walk : PrefixWalk bytes emitted) (byte : Nat) :
      PrefixWalk (bytes ++ [byte]) (emitted ++ [byte])

theorem prefix_walk_emits_prefix (walk : PrefixWalk bytes emitted) : emitted = bytes := by
  induction walk with
  | root => rfl
  | extend walk byte ih => simp only [ih]

structure TokenClosing where
  tokenId : Nat
  word : List Nat
  leading : List Nat
  suffix : List Nat
  reward : Nat
  cost : Nat
  complete : leading ++ suffix = word

theorem closing_emits_token (closing : TokenClosing)
    (walk : PrefixWalk closing.leading emitted) :
    emitted ++ closing.suffix = closing.word := by
  rw [prefix_walk_emits_prefix walk]
  exact closing.complete

def uniquePrefixes : List (List Nat) → List (List Nat)
  | [] => []
  | p :: rest =>
      if p ∈ uniquePrefixes rest then uniquePrefixes rest else p :: uniquePrefixes rest

theorem unique_prefixes_size (prefixes : List (List Nat)) :
    (uniquePrefixes prefixes).length ≤ prefixes.length := by
  induction prefixes with
  | nil => simp [uniquePrefixes]
  | cons p rest ih =>
      simp only [uniquePrefixes]
      split <;> simp only [List.length_cons] <;> omega

theorem unique_prefixes_membership (p : List Nat) (prefixes : List (List Nat)) :
    p ∈ uniquePrefixes prefixes ↔ p ∈ prefixes := by
  induction prefixes generalizing p with
  | nil => simp [uniquePrefixes]
  | cons q rest ih =>
      simp only [uniquePrefixes]
      split
      · rename_i member
        have original : q ∈ rest := (ih q).mp member
        simp only [ih p, List.mem_cons]
        constructor
        · exact Or.inr
        · rintro (rfl | present)
          · exact original
          · exact present
      · simp only [List.mem_cons, ih p]

theorem compact_node_count (boundaries : Nat) (prefixes : List (List Nat)) :
    boundaries + (uniquePrefixes prefixes).length ≤ boundaries + prefixes.length := by
  exact Nat.add_le_add_left (unique_prefixes_size prefixes) boundaries

end MWPC
