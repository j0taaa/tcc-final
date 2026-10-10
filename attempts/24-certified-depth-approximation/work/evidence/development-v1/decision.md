# Certified posterior — development

Records 486/486; {'complete': 445, 'resource_refusal': 41}.
Exact-ground-truth certificate checks: 216.
Candidate strong benefits: {'handoff': 3, 'closed': 3}.
Selected: handoff; practical gate: True.

All refusals, zeros and errors remain. Partial campaigns cannot confirm benefits.

| Case | Masks | Method | Statuses | Total wall | Total CPU | Depth |
|---|---:|---|---|---:|---:|---|
| 017a7a6d | 4 | handoff | {'complete': 3} | 0.165861 | 0.216047 | [3, 3, 3] |
| 017a7a6d | 4 | closed | {'complete': 3} | 0.162515 | 0.212684 | [3, 3, 3] |
| 017a7a6d | 4 | grammar_hit | {'complete': 3} | 0.163193 | 0.213365 | [3, 3, 3] |
| 017a7a6d | 4 | suffix_hit | {'complete': 3} | 0.164961 | 0.215141 | [4, 4, 4] |
| 017a7a6d | 4 | exact_stack | {'complete': 3} | 0.155857 | 0.206029 |  |
| 017a7a6d | 4 | exact_bidir_local | {'complete': 3} | 0.161345 | 0.211536 |  |
| 017a7a6d | 4 | exact_local | {'complete': 3} | 0.170862 | 0.221042 |  |
| 017a7a6d | 4 | exact_eps_local | {'complete': 3} | 0.159913 | 0.210089 |  |
| 017a7a6d | 4 | rejection | {'complete': 3} | 0.121629 | 0.171816 |  |
| 017a7a6d | 8 | closed | {'complete': 3} | 0.323673 | 0.359634 | [3, 3, 3] |
| 017a7a6d | 8 | grammar_hit | {'complete': 3} | 0.341402 | 0.377401 | [4, 4, 4] |
| 017a7a6d | 8 | suffix_hit | {'complete': 3} | 0.340316 | 0.376311 | [4, 4, 4] |
| 017a7a6d | 8 | exact_stack | {'complete': 3} | 0.323586 | 0.359576 |  |
| 017a7a6d | 8 | exact_bidir_local | {'complete': 3} | 0.555777 | 0.591722 |  |
| 017a7a6d | 8 | exact_local | {'complete': 3} | 0.847419 | 0.883398 |  |
| 017a7a6d | 8 | exact_eps_local | {'complete': 3} | 0.659552 | 0.695509 |  |
| 017a7a6d | 8 | rejection | {'complete': 3} | 0.202951 | 0.238956 |  |
| 017a7a6d | 8 | handoff | {'complete': 3} | 0.331013 | 0.366990 | [3, 3, 3] |
| 017a7a6d | 16 | grammar_hit | {'complete': 3} | 2.460893 | 2.511275 | [6, 6, 6] |
| 017a7a6d | 16 | suffix_hit | {'complete': 3} | 5.105207 | 5.155383 | [8, 8, 8] |
| 017a7a6d | 16 | exact_stack | {'complete': 3} | 12.848414 | 12.896720 |  |
| 017a7a6d | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |  |
| 017a7a6d | 16 | exact_local | {'resource_refusal': 3} |  |  |  |
| 017a7a6d | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |  |
| 017a7a6d | 16 | rejection | {'complete': 3} | 29.479493 | 29.522948 |  |
| 017a7a6d | 16 | handoff | {'complete': 3} | 0.953759 | 1.004437 | [3, 3, 3] |
| 017a7a6d | 16 | closed | {'complete': 3} | 0.907594 | 0.958341 | [3, 3, 3] |
| 05dacb44 | 4 | suffix_hit | {'complete': 3} | 0.166580 | 0.207773 | [6, 6, 6] |
| 05dacb44 | 4 | exact_stack | {'complete': 3} | 0.153825 | 0.195034 |  |
| 05dacb44 | 4 | exact_bidir_local | {'complete': 3} | 0.186239 | 0.227448 |  |
| 05dacb44 | 4 | exact_local | {'complete': 3} | 0.208697 | 0.249865 |  |
| 05dacb44 | 4 | exact_eps_local | {'complete': 3} | 0.189331 | 0.230532 |  |
| 05dacb44 | 4 | rejection | {'complete': 3} | 0.137331 | 0.178549 |  |
| 05dacb44 | 4 | handoff | {'complete': 3} | 0.165219 | 0.206440 | [4, 4, 4] |
| 05dacb44 | 4 | closed | {'complete': 3} | 0.166055 | 0.207245 | [6, 6, 6] |
| 05dacb44 | 4 | grammar_hit | {'complete': 3} | 0.168101 | 0.209282 | [6, 6, 6] |
| 05dacb44 | 8 | exact_stack | {'complete': 3} | 0.389374 | 0.438573 |  |
| 05dacb44 | 8 | exact_bidir_local | {'complete': 3} | 1.656176 | 1.705103 |  |
| 05dacb44 | 8 | exact_local | {'complete': 3} | 2.216702 | 2.265621 |  |
| 05dacb44 | 8 | exact_eps_local | {'complete': 3} | 2.402273 | 2.450956 |  |
| 05dacb44 | 8 | rejection | {'complete': 3} | 0.213946 | 0.263134 |  |
| 05dacb44 | 8 | handoff | {'complete': 3} | 0.439751 | 0.488925 | [6, 6, 6] |
| 05dacb44 | 8 | closed | {'complete': 3} | 0.417690 | 0.466864 | [6, 6, 6] |
| 05dacb44 | 8 | grammar_hit | {'complete': 3} | 0.425568 | 0.474758 | [6, 6, 6] |
| 05dacb44 | 8 | suffix_hit | {'complete': 3} | 0.495681 | 0.544843 | [8, 8, 8] |
| 05dacb44 | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |  |
| 05dacb44 | 16 | exact_local | {'resource_refusal': 3} |  |  |  |
| 05dacb44 | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |  |
| 05dacb44 | 16 | rejection | {'complete': 3} | 5.430505 | 5.502601 |  |
| 05dacb44 | 16 | handoff | {'complete': 3} | 0.949936 | 1.022636 | [2, 2, 2] |
| 05dacb44 | 16 | closed | {'complete': 3} | 1.155756 | 1.228404 | [3, 3, 3] |
| 05dacb44 | 16 | grammar_hit | {'complete': 3} | 1.701396 | 1.773899 | [4, 4, 4] |
| 05dacb44 | 16 | suffix_hit | {'complete': 3} | 3.142588 | 3.214831 | [6, 6, 6] |
| 05dacb44 | 16 | exact_stack | {'complete': 3} | 36.255552 | 36.320113 |  |
| 079f141a | 4 | exact_local | {'complete': 3} | 0.163922 | 0.210154 |  |
| 079f141a | 4 | exact_eps_local | {'complete': 3} | 0.154478 | 0.200765 |  |
| 079f141a | 4 | rejection | {'complete': 3} | 0.116251 | 0.162532 |  |
| 079f141a | 4 | handoff | {'complete': 3} | 0.160798 | 0.207044 | [3, 3, 3] |
| 079f141a | 4 | closed | {'complete': 3} | 0.158713 | 0.204963 | [4, 4, 4] |
| 079f141a | 4 | grammar_hit | {'complete': 3} | 0.155859 | 0.202141 | [3, 3, 3] |
| 079f141a | 4 | suffix_hit | {'complete': 3} | 0.161715 | 0.207993 | [6, 6, 6] |
| 079f141a | 4 | exact_stack | {'complete': 3} | 0.150103 | 0.196391 |  |
| 079f141a | 4 | exact_bidir_local | {'complete': 3} | 0.155187 | 0.201456 |  |
| 079f141a | 8 | exact_eps_local | {'complete': 3} | 0.377339 | 0.423621 |  |
| 079f141a | 8 | rejection | {'complete': 3} | 0.206978 | 0.253288 |  |
| 079f141a | 8 | handoff | {'complete': 3} | 0.303405 | 0.349677 | [3, 3, 3] |
| 079f141a | 8 | closed | {'complete': 3} | 0.308395 | 0.354600 | [4, 4, 4] |
| 079f141a | 8 | grammar_hit | {'complete': 3} | 0.303878 | 0.350189 | [3, 3, 3] |
| 079f141a | 8 | suffix_hit | {'complete': 3} | 0.317336 | 0.363650 | [6, 6, 6] |
| 079f141a | 8 | exact_stack | {'complete': 3} | 0.298281 | 0.344584 |  |
| 079f141a | 8 | exact_bidir_local | {'complete': 3} | 0.384999 | 0.431258 |  |
| 079f141a | 8 | exact_local | {'complete': 3} | 0.479795 | 0.526071 |  |
| 079f141a | 16 | rejection | {'complete': 3} | 0.393560 | 0.444349 |  |
| 079f141a | 16 | handoff | {'complete': 3} | 0.722492 | 0.773405 | [3, 3, 3] |
| 079f141a | 16 | closed | {'complete': 3} | 0.774384 | 0.825242 | [4, 4, 4] |
| 079f141a | 16 | grammar_hit | {'complete': 3} | 0.943008 | 0.993873 | [6, 6, 6] |
| 079f141a | 16 | suffix_hit | {'complete': 3} | 0.908164 | 0.959032 | [6, 6, 6] |
| 079f141a | 16 | exact_stack | {'complete': 3} | 11.777957 | 11.824693 |  |
| 079f141a | 16 | exact_bidir_local | {'complete': 3} | 12.066954 | 12.113537 |  |
| 079f141a | 16 | exact_local | {'complete': 3} | 14.506811 | 14.554977 |  |
| 079f141a | 16 | exact_eps_local | {'complete': 3} | 17.098396 | 17.145566 |  |
| 0a4b768a | 4 | handoff | {'complete': 3} | 0.173470 | 0.213860 | [6, 6, 6] |
| 0a4b768a | 4 | closed | {'complete': 3} | 0.171041 | 0.211298 | [6, 6, 6] |
| 0a4b768a | 4 | grammar_hit | {'complete': 3} | 0.172736 | 0.213111 | [6, 6, 6] |
| 0a4b768a | 4 | suffix_hit | {'complete': 3} | 0.169240 | 0.209579 | [6, 6, 6] |
| 0a4b768a | 4 | exact_stack | {'complete': 3} | 0.162252 | 0.202629 |  |
| 0a4b768a | 4 | exact_bidir_local | {'complete': 3} | 0.174938 | 0.215280 |  |
| 0a4b768a | 4 | exact_local | {'complete': 3} | 0.180473 | 0.220818 |  |
| 0a4b768a | 4 | exact_eps_local | {'complete': 3} | 0.168488 | 0.208855 |  |
| 0a4b768a | 4 | rejection | {'complete': 3} | 0.112443 | 0.152822 |  |
| 0a4b768a | 8 | closed | {'complete': 3} | 0.363180 | 0.408125 | [6, 6, 6] |
| 0a4b768a | 8 | grammar_hit | {'complete': 3} | 0.358612 | 0.403516 | [6, 6, 6] |
| 0a4b768a | 8 | suffix_hit | {'complete': 3} | 0.361186 | 0.406129 | [6, 6, 6] |
| 0a4b768a | 8 | exact_stack | {'complete': 3} | 0.350720 | 0.395621 |  |
| 0a4b768a | 8 | exact_bidir_local | {'complete': 3} | 0.561010 | 0.605783 |  |
| 0a4b768a | 8 | exact_local | {'complete': 3} | 0.790161 | 0.834925 |  |
| 0a4b768a | 8 | exact_eps_local | {'complete': 3} | 0.607842 | 0.652769 |  |
| 0a4b768a | 8 | rejection | {'complete': 3} | 0.206643 | 0.251567 |  |
| 0a4b768a | 8 | handoff | {'complete': 3} | 0.367334 | 0.412280 | [6, 6, 6] |
| 0a4b768a | 16 | grammar_hit | {'complete': 3} | 4.075244 | 4.124974 | [8, 8, 8] |
| 0a4b768a | 16 | suffix_hit | {'complete': 3} | 23.659339 | 23.705311 | [12, 12, 12] |
| 0a4b768a | 16 | exact_stack | {'complete': 3} | 43.084260 | 43.124328 |  |
| 0a4b768a | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |  |
| 0a4b768a | 16 | exact_local | {'resource_refusal': 3} |  |  |  |
| 0a4b768a | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |  |
| 0a4b768a | 16 | rejection | {'complete': 1, 'resource_refusal': 2} | 23.858973 | 23.903702 |  |
| 0a4b768a | 16 | handoff | {'complete': 3} | 4.202127 | 4.250125 | [8, 8, 8] |
| 0a4b768a | 16 | closed | {'complete': 3} | 3.444111 | 3.494026 | [8, 8, 8] |
| 0bb39717 | 4 | suffix_hit | {'complete': 3} | 0.171980 | 0.225077 | [8, 8, 8] |
| 0bb39717 | 4 | exact_stack | {'complete': 3} | 0.161125 | 0.214189 |  |
| 0bb39717 | 4 | exact_bidir_local | {'complete': 3} | 0.171933 | 0.225036 |  |
| 0bb39717 | 4 | exact_local | {'complete': 3} | 0.174838 | 0.227956 |  |
| 0bb39717 | 4 | exact_eps_local | {'complete': 3} | 0.164563 | 0.217662 |  |
| 0bb39717 | 4 | rejection | {'complete': 3} | 0.117518 | 0.170636 |  |
| 0bb39717 | 4 | handoff | {'complete': 3} | 0.170328 | 0.223434 | [6, 6, 6] |
| 0bb39717 | 4 | closed | {'complete': 3} | 0.167348 | 0.220455 | [6, 6, 6] |
| 0bb39717 | 4 | grammar_hit | {'complete': 3} | 0.169953 | 0.223056 | [6, 6, 6] |
| 0bb39717 | 8 | exact_stack | {'complete': 3} | 0.320663 | 0.368631 |  |
| 0bb39717 | 8 | exact_bidir_local | {'complete': 3} | 0.335830 | 0.383817 |  |
| 0bb39717 | 8 | exact_local | {'complete': 3} | 0.345732 | 0.393604 |  |
| 0bb39717 | 8 | exact_eps_local | {'complete': 3} | 0.335966 | 0.383945 |  |
| 0bb39717 | 8 | rejection | {'complete': 3} | 0.208006 | 0.255991 |  |
| 0bb39717 | 8 | handoff | {'complete': 3} | 0.321772 | 0.369762 | [6, 6, 6] |
| 0bb39717 | 8 | closed | {'complete': 3} | 0.318905 | 0.366889 | [6, 6, 6] |
| 0bb39717 | 8 | grammar_hit | {'complete': 3} | 0.322870 | 0.370846 | [6, 6, 6] |
| 0bb39717 | 8 | suffix_hit | {'complete': 3} | 0.317521 | 0.365478 | [6, 6, 6] |
| 0bb39717 | 16 | exact_bidir_local | {'complete': 3} | 0.900614 | 0.948408 |  |
| 0bb39717 | 16 | exact_local | {'complete': 3} | 1.069852 | 1.117756 |  |
| 0bb39717 | 16 | exact_eps_local | {'complete': 3} | 0.928214 | 0.976155 |  |
| 0bb39717 | 16 | rejection | {'complete': 3} | 0.394100 | 0.442030 |  |
| 0bb39717 | 16 | handoff | {'complete': 3} | 0.744851 | 0.792679 | [6, 6, 6] |
| 0bb39717 | 16 | closed | {'complete': 3} | 0.791965 | 0.839732 | [8, 8, 8] |
| 0bb39717 | 16 | grammar_hit | {'complete': 3} | 0.796006 | 0.843920 | [8, 8, 8] |
| 0bb39717 | 16 | suffix_hit | {'complete': 3} | 1.017240 | 1.064824 | [12, 12, 12] |
| 0bb39717 | 16 | exact_stack | {'complete': 3} | 1.006175 | 1.054066 |  |
| 0ce7169f | 4 | exact_local | {'complete': 3} | 0.170626 | 0.206607 |  |
| 0ce7169f | 4 | exact_eps_local | {'complete': 3} | 0.158990 | 0.194961 |  |
| 0ce7169f | 4 | rejection | {'complete': 3} | 0.110482 | 0.146484 |  |
| 0ce7169f | 4 | handoff | {'complete': 3} | 0.157218 | 0.193210 | [2, 2, 2] |
| 0ce7169f | 4 | closed | {'complete': 3} | 0.156065 | 0.192039 | [2, 2, 2] |
| 0ce7169f | 4 | grammar_hit | {'complete': 3} | 0.155827 | 0.191825 | [2, 2, 2] |
| 0ce7169f | 4 | suffix_hit | {'complete': 3} | 0.159879 | 0.195841 | [3, 3, 3] |
| 0ce7169f | 4 | exact_stack | {'complete': 3} | 0.153065 | 0.189030 |  |
| 0ce7169f | 4 | exact_bidir_local | {'complete': 3} | 0.164719 | 0.200696 |  |
| 0ce7169f | 8 | exact_eps_local | {'complete': 3} | 0.547732 | 0.577663 |  |
| 0ce7169f | 8 | rejection | {'complete': 3} | 0.203035 | 0.232926 |  |
| 0ce7169f | 8 | handoff | {'complete': 3} | 0.340964 | 0.370949 | [3, 3, 3] |
| 0ce7169f | 8 | closed | {'complete': 3} | 0.335898 | 0.365719 | [3, 3, 3] |
| 0ce7169f | 8 | grammar_hit | {'complete': 3} | 0.335873 | 0.365834 | [3, 3, 3] |
| 0ce7169f | 8 | suffix_hit | {'complete': 3} | 0.344047 | 0.374043 | [4, 4, 4] |
| 0ce7169f | 8 | exact_stack | {'complete': 3} | 0.331491 | 0.361485 |  |
| 0ce7169f | 8 | exact_bidir_local | {'complete': 3} | 0.507429 | 0.537333 |  |
| 0ce7169f | 8 | exact_local | {'complete': 3} | 0.656861 | 0.686814 |  |
| 0ce7169f | 16 | rejection | {'resource_refusal': 3} |  |  |  |
| 0ce7169f | 16 | handoff | {'complete': 3} | 1.471551 | 1.534303 | [4, 4, 4] |
| 0ce7169f | 16 | closed | {'complete': 3} | 1.349312 | 1.412162 | [4, 4, 4] |
| 0ce7169f | 16 | grammar_hit | {'complete': 3} | 9.084015 | 9.145666 | [8, 8, 8] |
| 0ce7169f | 16 | suffix_hit | {'complete': 3} | 29.932358 | 29.987110 | [12, 12, 12] |
| 0ce7169f | 16 | exact_stack | {'complete': 3} | 26.497029 | 26.553753 |  |
| 0ce7169f | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |  |
| 0ce7169f | 16 | exact_local | {'resource_refusal': 3} |  |  |  |
| 0ce7169f | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |  |
