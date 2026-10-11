import Std

/- Finite local premise of the written lookup lower bound only.
   No statement about Python, gradient covariance, real dLLMs or publication. -/
namespace NoisingObstructions

abbrev Color := Fin 3
abbrev Quad := Color × Color × Color × Color

def valueAt (c : Quad) (i : Fin 4) : Color :=
  if i.val = 0 then c.1
  else if i.val = 1 then c.2.1
  else if i.val = 2 then c.2.2.1
  else c.2.2.2

def count (c : Quad) (k : Color) : Nat :=
  (if c.1 = k then 1 else 0) + (if c.2.1 = k then 1 else 0) +
  (if c.2.2.1 = k then 1 else 0) + (if c.2.2.2 = k then 1 else 0)

def observed (c : Quad) (n : Fin 4) : Prop :=
  (n.val ≥ 1 → c.1 = 0) ∧ (n.val ≥ 2 → c.2.1 = 1) ∧
  (n.val ≥ 3 → c.2.2.1 = 2)

def violates (c : Quad) (anchor companion : Fin 4) : Prop :=
  ∃ k : Color, count c k = 2 ∧
    (if valueAt c anchor = k then 1 else 0) +
    (if valueAt c companion = k then 1 else 0) ≠ (1 : Nat)

set_option maxRecDepth 4096 in
set_option maxHeartbeats 2000000 in
theorem no_safe_early_return : ∀ (n anchor companion : Fin 4),
    ∃ (c0 c1 c2 c3 : Color),
      observed (c0, c1, c2, c3) n ∧
      violates (c0, c1, c2, c3) anchor companion := by
  unfold observed violates count valueAt
  decide

-- Includes unqueried output addresses and cloning the retained anchor.
#print axioms no_safe_early_return

end NoisingObstructions
