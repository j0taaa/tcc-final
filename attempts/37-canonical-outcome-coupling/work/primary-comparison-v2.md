# A37: additional primary comparison

2026-10-11. Supplements the unchanged v1 reading record; no paper-wide
novelty exclusion or independent human review is claimed.

## Additional primary reading after the first small oracle

- **Rowland et al.2018**, original Sections1--2.3 and the sampling-cost passage
  before Section3 ACTUALLY READ:
  [NeurIPS authored PDF](https://mlg.eng.cam.ac.uk/adrian/NeurIPS18-gcmc.pdf).
  SHA256 `4b45a2f21e96cedb33b793e262089a0012734ce7a8d418de7e3adeef0ab7aba4`.
  Coupling for costly downstream computation, marginal preservation and
  transport/kernel objectives are already explicit. Theorem2.9 uses an
  isotropic distribution, radial CDF and a particular decreasing convex
  kernel; this is not an unknown-canonical-law oracle guarantee. Its general
  transport framing encompasses our diversity objective, so that framing
  is NOT a novelty claim. The whole appendix has not been read here.
- **Ermon et al.2013 PAWS**, original Sections2/3/3.1 ACTUALLY READ:
  [NeurIPS PDF](https://proceedings.neurips.cc/paper_files/paper/2013/file/6d70cb65d15211726dcce4c0e971e21c-Paper.pdf).
  SHA256 `4cccf3bc24653c8fc03e36906503ab93374a5485e2137354ed8fe21099dbe2a5`.
  Universal hashing for discrete sampling is already central. This input is
  a known weight function with search/feasibility oracles and approximate
  sampling guarantees; it is not simply an iid complete-generation oracle.
  Hashing in constrained generation cannot be called new in isolation.
- **Craiu/Meng2005**, original Sections1/2.1/2.2, Theorem1 and its proof,
  and Theorems5--7 ACTUALLY READ:
  [Annals original reprint](https://arxiv.org/pdf/math/0505631).
  SHA256 `b4728fdc75f59e109a30f7cc34d01fca1d8acb52288398c1c7776ab1b6fd6b3f`.
  Native path antithetics and CFTP are precedents. Theorem1's monotone update
  assumption must be retained; Theorem6 ALSO covers arbitrary L2 functions
  asymptotically in the number of trajectories. Do not weaken it by claiming
  that every result there is only for monotone observables. The inspected
  statements do not supply our finite-pair canonical constant/unknown-law
  contract, but this is not a paper-wide exclusion or a novelty certificate.

