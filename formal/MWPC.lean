import MWPC.Probability
import MWPC.Certificates
import MWPC.Bounds
import MWPC.Prefixes
import MWPC.Selection
import MWPC.Conflicts

/-! Mathematical verification of finite, per-step commitment.
    No model, floating-point arithmetic or foreign code is part of this module. -/

namespace MWPC

def score (rewards : List Nat) : Nat := rewards.sum

theorem score_append (a b : List Nat) : score (a ++ b) = score a + score b := by
  simp [score]

end MWPC

