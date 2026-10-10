# Exact envelope — development

Records 702/702; {'complete': 648, 'resource_refusal': 53, 'worker_error': 1}.
First statuses: {'complete': 655, 'resource_refusal': 46, 'worker_error': 1}; certificate checks: 162.
First wins {'handoff': 0, 'closed': 0}; batch wins {'handoff': 1, 'closed': 1}.
Selected handoff; first gate False.

All losses/refusals preserved. Partial campaigns cannot confirm benefits.

| Case | Masks | Method | First status | First wall | Batch wall |
|---|---:|---|---|---:|---:|
| 017a7a6d | 4 | handoff | {'complete': 3} | 0.137712 | 0.139325 |
| 017a7a6d | 4 | closed | {'complete': 3} | 0.133628 | 0.135322 |
| 017a7a6d | 4 | grammar_hit | {'complete': 3} | 0.133828 | 0.135480 |
| 017a7a6d | 4 | counter_only | {'complete': 3} | 0.129631 | 0.137814 |
| 017a7a6d | 4 | cars | {'complete': 3} | 0.130891 | 0.143469 |
| 017a7a6d | 4 | cars_perfect | {'complete': 3} | 0.131231 | 0.142477 |
| 017a7a6d | 4 | counter_cars | {'complete': 3} | 0.132859 | 0.173329 |
| 017a7a6d | 4 | counter_cars_perfect | {'complete': 3} | 0.133119 | 0.170619 |
| 017a7a6d | 4 | exact_stack | {'complete': 3} | 0.128173 | 0.129494 |
| 017a7a6d | 4 | exact_bidir_local | {'complete': 3} | 0.131090 | 0.133650 |
| 017a7a6d | 4 | exact_local | {'complete': 3} | 0.142056 | 0.144716 |
| 017a7a6d | 4 | exact_eps_local | {'complete': 3} | 0.130632 | 0.133754 |
| 017a7a6d | 4 | rejection | {'complete': 3} | 0.120311 | 0.134888 |
| 017a7a6d | 8 | closed | {'complete': 3} | 0.243949 | 0.246052 |
| 017a7a6d | 8 | grammar_hit | {'complete': 3} | 0.265981 | 0.268033 |
| 017a7a6d | 8 | counter_only | {'complete': 3} | 0.220897 | 0.231622 |
| 017a7a6d | 8 | cars | {'complete': 3} | 0.220835 | 0.237040 |
| 017a7a6d | 8 | cars_perfect | {'complete': 3} | 0.232732 | 0.249100 |
| 017a7a6d | 8 | counter_cars | {'complete': 3} | 0.220528 | 0.266844 |
| 017a7a6d | 8 | counter_cars_perfect | {'complete': 3} | 0.235329 | 0.280967 |
| 017a7a6d | 8 | exact_stack | {'complete': 3} | 0.243677 | 0.245384 |
| 017a7a6d | 8 | exact_bidir_local | {'complete': 3} | 0.483228 | 0.486451 |
| 017a7a6d | 8 | exact_local | {'complete': 3} | 0.769764 | 0.772895 |
| 017a7a6d | 8 | exact_eps_local | {'complete': 3} | 0.581668 | 0.585557 |
| 017a7a6d | 8 | rejection | {'complete': 3} | 0.198928 | 0.202218 |
| 017a7a6d | 8 | handoff | {'complete': 3} | 0.254682 | 0.256694 |
| 017a7a6d | 16 | grammar_hit | {'complete': 3} | 2.175262 | 2.185914 |
| 017a7a6d | 16 | counter_only | {'complete': 2, 'worker_error': 1} | 31.033638 |  |
| 017a7a6d | 16 | cars | {'complete': 3} | 1.292316 | 4.266448 |
| 017a7a6d | 16 | cars_perfect | {'complete': 3} | 0.931756 | 3.291824 |
| 017a7a6d | 16 | counter_cars | {'complete': 3} | 0.540567 | 0.819829 |
| 017a7a6d | 16 | counter_cars_perfect | {'complete': 3} | 0.466647 | 0.722507 |
| 017a7a6d | 16 | exact_stack | {'complete': 3} | 12.225834 | 12.229662 |
| 017a7a6d | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |
| 017a7a6d | 16 | exact_local | {'resource_refusal': 3} |  |  |
| 017a7a6d | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |
| 017a7a6d | 16 | rejection | {'complete': 1, 'resource_refusal': 2} | 9.914957 |  |
| 017a7a6d | 16 | handoff | {'complete': 3} | 0.738155 | 0.752964 |
| 017a7a6d | 16 | closed | {'complete': 3} | 0.673687 | 0.684566 |
| 05dacb44 | 4 | counter_only | {'complete': 3} | 0.122701 | 0.373523 |
| 05dacb44 | 4 | cars | {'complete': 3} | 0.121828 | 0.136039 |
| 05dacb44 | 4 | cars_perfect | {'complete': 3} | 0.122471 | 0.136034 |
| 05dacb44 | 4 | counter_cars | {'complete': 3} | 0.127871 | 0.177901 |
| 05dacb44 | 4 | counter_cars_perfect | {'complete': 3} | 0.128658 | 0.178479 |
| 05dacb44 | 4 | exact_stack | {'complete': 3} | 0.122592 | 0.123894 |
| 05dacb44 | 4 | exact_bidir_local | {'complete': 3} | 0.152296 | 0.155462 |
| 05dacb44 | 4 | exact_local | {'complete': 3} | 0.175776 | 0.178997 |
| 05dacb44 | 4 | exact_eps_local | {'complete': 3} | 0.155738 | 0.159691 |
| 05dacb44 | 4 | rejection | {'complete': 3} | 0.135439 | 1.134569 |
| 05dacb44 | 4 | handoff | {'complete': 3} | 0.136685 | 0.138332 |
| 05dacb44 | 4 | closed | {'complete': 3} | 0.134420 | 0.136109 |
| 05dacb44 | 4 | grammar_hit | {'complete': 3} | 0.132936 | 0.134633 |
| 05dacb44 | 8 | cars | {'complete': 3} | 0.223124 | 0.262661 |
| 05dacb44 | 8 | cars_perfect | {'complete': 3} | 0.235128 | 0.266841 |
| 05dacb44 | 8 | counter_cars | {'complete': 3} | 0.229814 | 0.285324 |
| 05dacb44 | 8 | counter_cars_perfect | {'complete': 3} | 0.233567 | 0.282777 |
| 05dacb44 | 8 | exact_stack | {'complete': 3} | 0.299361 | 0.301262 |
| 05dacb44 | 8 | exact_bidir_local | {'complete': 3} | 1.558382 | 1.564951 |
| 05dacb44 | 8 | exact_local | {'complete': 3} | 2.102399 | 2.108807 |
| 05dacb44 | 8 | exact_eps_local | {'complete': 3} | 2.288542 | 2.296014 |
| 05dacb44 | 8 | rejection | {'complete': 3} | 0.204636 | 0.245236 |
| 05dacb44 | 8 | handoff | {'complete': 3} | 0.348768 | 0.350982 |
| 05dacb44 | 8 | closed | {'complete': 3} | 0.332870 | 0.335206 |
| 05dacb44 | 8 | grammar_hit | {'complete': 3} | 0.332625 | 0.334896 |
| 05dacb44 | 8 | counter_only | {'complete': 3} | 0.223663 | 0.231919 |
| 05dacb44 | 16 | cars_perfect | {'complete': 3} | 0.668933 | 1.133463 |
| 05dacb44 | 16 | counter_cars | {'complete': 3} | 0.578379 | 1.237789 |
| 05dacb44 | 16 | counter_cars_perfect | {'complete': 3} | 0.484895 | 0.645518 |
| 05dacb44 | 16 | exact_stack | {'complete': 3} | 35.805609 | 35.816467 |
| 05dacb44 | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |
| 05dacb44 | 16 | exact_local | {'resource_refusal': 3} |  |  |
| 05dacb44 | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |
| 05dacb44 | 16 | rejection | {'resource_refusal': 2, 'complete': 1} | 13.233473 |  |
| 05dacb44 | 16 | handoff | {'complete': 3} | 0.697670 | 0.707845 |
| 05dacb44 | 16 | closed | {'complete': 3} | 0.885877 | 0.896673 |
| 05dacb44 | 16 | grammar_hit | {'complete': 3} | 1.401834 | 1.446777 |
| 05dacb44 | 16 | counter_only | {'complete': 3} | 1.550849 | 51.786465 |
| 05dacb44 | 16 | cars | {'complete': 3} | 1.204364 | 2.550973 |
| 079f141a | 4 | counter_cars | {'complete': 3} | 0.133544 | 0.228002 |
| 079f141a | 4 | counter_cars_perfect | {'complete': 3} | 0.135072 | 0.229407 |
| 079f141a | 4 | exact_stack | {'complete': 3} | 0.121672 | 0.124012 |
| 079f141a | 4 | exact_bidir_local | {'complete': 3} | 0.125082 | 0.130405 |
| 079f141a | 4 | exact_local | {'complete': 3} | 0.133743 | 0.139046 |
| 079f141a | 4 | exact_eps_local | {'complete': 3} | 0.124368 | 0.130996 |
| 079f141a | 4 | rejection | {'complete': 3} | 0.114103 | 0.116151 |
| 079f141a | 4 | handoff | {'complete': 3} | 0.128792 | 0.131602 |
| 079f141a | 4 | closed | {'complete': 3} | 0.131027 | 0.133795 |
| 079f141a | 4 | grammar_hit | {'complete': 3} | 0.128431 | 0.131276 |
| 079f141a | 4 | counter_only | {'complete': 3} | 0.124820 | 0.130691 |
| 079f141a | 4 | cars | {'complete': 3} | 0.127752 | 0.149605 |
| 079f141a | 4 | cars_perfect | {'complete': 3} | 0.128160 | 0.150212 |
| 079f141a | 8 | counter_cars_perfect | {'complete': 3} | 0.233368 | 0.332404 |
| 079f141a | 8 | exact_stack | {'complete': 3} | 0.227655 | 0.230322 |
| 079f141a | 8 | exact_bidir_local | {'complete': 3} | 0.317424 | 0.323512 |
| 079f141a | 8 | exact_local | {'complete': 3} | 0.411901 | 0.417881 |
| 079f141a | 8 | exact_eps_local | {'complete': 3} | 0.304482 | 0.311835 |
| 079f141a | 8 | rejection | {'complete': 3} | 0.201380 | 0.203921 |
| 079f141a | 8 | handoff | {'complete': 3} | 0.229039 | 0.232105 |
| 079f141a | 8 | closed | {'complete': 3} | 0.238463 | 0.241632 |
| 079f141a | 8 | grammar_hit | {'complete': 3} | 0.228121 | 0.231207 |
| 079f141a | 8 | counter_only | {'complete': 3} | 0.221761 | 0.233652 |
| 079f141a | 8 | cars | {'complete': 3} | 0.221844 | 0.253189 |
| 079f141a | 8 | cars_perfect | {'complete': 3} | 0.225070 | 0.255434 |
| 079f141a | 8 | counter_cars | {'complete': 3} | 0.239672 | 0.339146 |
| 079f141a | 16 | exact_stack | {'complete': 3} | 11.527299 | 11.531522 |
| 079f141a | 16 | exact_bidir_local | {'complete': 3} | 11.441238 | 11.465269 |
| 079f141a | 16 | exact_local | {'complete': 3} | 13.958669 | 13.972370 |
| 079f141a | 16 | exact_eps_local | {'complete': 3} | 16.418640 | 16.433238 |
| 079f141a | 16 | rejection | {'complete': 3} | 0.379764 | 0.382372 |
| 079f141a | 16 | handoff | {'complete': 3} | 0.487660 | 0.491992 |
| 079f141a | 16 | closed | {'complete': 3} | 0.534183 | 0.538758 |
| 079f141a | 16 | grammar_hit | {'complete': 3} | 0.689547 | 0.694118 |
| 079f141a | 16 | counter_only | {'complete': 3} | 0.425035 | 0.442119 |
| 079f141a | 16 | cars | {'complete': 3} | 0.415453 | 0.464837 |
| 079f141a | 16 | cars_perfect | {'complete': 3} | 0.433393 | 0.475781 |
| 079f141a | 16 | counter_cars | {'complete': 3} | 0.443405 | 0.540045 |
| 079f141a | 16 | counter_cars_perfect | {'complete': 3} | 0.453126 | 0.551770 |
| 0a4b768a | 4 | exact_bidir_local | {'complete': 3} | 0.139619 | 0.142743 |
| 0a4b768a | 4 | exact_local | {'complete': 3} | 0.144665 | 0.147827 |
| 0a4b768a | 4 | exact_eps_local | {'complete': 3} | 0.133549 | 0.137403 |
| 0a4b768a | 4 | rejection | {'complete': 3} | 0.111236 | 0.117220 |
| 0a4b768a | 4 | handoff | {'complete': 3} | 0.141762 | 0.143586 |
| 0a4b768a | 4 | closed | {'complete': 3} | 0.135929 | 0.137748 |
| 0a4b768a | 4 | grammar_hit | {'complete': 3} | 0.136995 | 0.138795 |
| 0a4b768a | 4 | counter_only | {'complete': 3} | 0.121198 | 0.128348 |
| 0a4b768a | 4 | cars | {'complete': 3} | 0.122762 | 0.139773 |
| 0a4b768a | 4 | cars_perfect | {'complete': 3} | 0.123534 | 0.135531 |
| 0a4b768a | 4 | counter_cars | {'complete': 3} | 0.127026 | 0.172607 |
| 0a4b768a | 4 | counter_cars_perfect | {'complete': 3} | 0.128528 | 0.177284 |
| 0a4b768a | 4 | exact_stack | {'complete': 3} | 0.128528 | 0.129985 |
| 0a4b768a | 8 | exact_local | {'complete': 3} | 0.681915 | 0.686269 |
| 0a4b768a | 8 | exact_eps_local | {'complete': 3} | 0.519803 | 0.525054 |
| 0a4b768a | 8 | rejection | {'complete': 3} | 0.201828 | 0.203087 |
| 0a4b768a | 8 | handoff | {'complete': 3} | 0.275011 | 0.277996 |
| 0a4b768a | 8 | closed | {'complete': 3} | 0.273807 | 0.276885 |
| 0a4b768a | 8 | grammar_hit | {'complete': 3} | 0.266336 | 0.269129 |
| 0a4b768a | 8 | counter_only | {'complete': 3} | 0.225738 | 0.253592 |
| 0a4b768a | 8 | cars | {'complete': 3} | 0.228065 | 0.265816 |
| 0a4b768a | 8 | cars_perfect | {'complete': 3} | 0.232299 | 0.269733 |
| 0a4b768a | 8 | counter_cars | {'complete': 3} | 0.233953 | 0.297910 |
| 0a4b768a | 8 | counter_cars_perfect | {'complete': 3} | 0.240970 | 0.301253 |
| 0a4b768a | 8 | exact_stack | {'complete': 3} | 0.259611 | 0.261695 |
| 0a4b768a | 8 | exact_bidir_local | {'complete': 3} | 0.473939 | 0.477949 |
| 0a4b768a | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |
| 0a4b768a | 16 | rejection | {'resource_refusal': 3} |  |  |
| 0a4b768a | 16 | handoff | {'complete': 3} | 3.911406 | 3.932651 |
| 0a4b768a | 16 | closed | {'complete': 3} | 3.199468 | 3.220975 |
| 0a4b768a | 16 | grammar_hit | {'complete': 3} | 3.714104 | 3.735378 |
| 0a4b768a | 16 | counter_only | {'complete': 3} | 0.621332 | 7.066087 |
| 0a4b768a | 16 | cars | {'complete': 3} | 1.803149 | 6.418761 |
| 0a4b768a | 16 | cars_perfect | {'complete': 3} | 1.527843 | 4.694726 |
| 0a4b768a | 16 | counter_cars | {'complete': 3} | 0.604358 | 1.198843 |
| 0a4b768a | 16 | counter_cars_perfect | {'complete': 3} | 0.640812 | 1.238237 |
| 0a4b768a | 16 | exact_stack | {'complete': 3} | 42.412116 | 42.432835 |
| 0a4b768a | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |
| 0a4b768a | 16 | exact_local | {'resource_refusal': 3} |  |  |
| 0bb39717 | 4 | rejection | {'complete': 3} | 0.115285 | 0.143627 |
| 0bb39717 | 4 | handoff | {'complete': 3} | 0.139503 | 0.143717 |
| 0bb39717 | 4 | closed | {'complete': 3} | 0.137657 | 0.141808 |
| 0bb39717 | 4 | grammar_hit | {'complete': 3} | 0.139529 | 0.143638 |
| 0bb39717 | 4 | counter_only | {'complete': 3} | 0.132482 | 0.139630 |
| 0bb39717 | 4 | cars | {'complete': 3} | 0.136673 | 0.165906 |
| 0bb39717 | 4 | cars_perfect | {'complete': 3} | 0.136036 | 0.165742 |
| 0bb39717 | 4 | counter_cars | {'complete': 3} | 0.145608 | 0.292896 |
| 0bb39717 | 4 | counter_cars_perfect | {'complete': 3} | 0.145809 | 0.292711 |
| 0bb39717 | 4 | exact_stack | {'complete': 3} | 0.128133 | 0.131527 |
| 0bb39717 | 4 | exact_bidir_local | {'complete': 3} | 0.130693 | 0.137812 |
| 0bb39717 | 4 | exact_local | {'complete': 3} | 0.140006 | 0.146978 |
| 0bb39717 | 4 | exact_eps_local | {'complete': 3} | 0.130575 | 0.139247 |
| 0bb39717 | 8 | handoff | {'complete': 3} | 0.244908 | 0.249576 |
| 0bb39717 | 8 | closed | {'complete': 3} | 0.242262 | 0.246838 |
| 0bb39717 | 8 | grammar_hit | {'complete': 3} | 0.245166 | 0.249779 |
| 0bb39717 | 8 | counter_only | {'complete': 3} | 0.241044 | 0.250906 |
| 0bb39717 | 8 | cars | {'complete': 3} | 0.247124 | 0.279119 |
| 0bb39717 | 8 | cars_perfect | {'complete': 3} | 0.246638 | 0.278817 |
| 0bb39717 | 8 | counter_cars | {'complete': 3} | 0.252102 | 0.402037 |
| 0bb39717 | 8 | counter_cars_perfect | {'complete': 3} | 0.257244 | 0.401586 |
| 0bb39717 | 8 | exact_stack | {'complete': 3} | 0.235952 | 0.239780 |
| 0bb39717 | 8 | exact_bidir_local | {'complete': 3} | 0.251187 | 0.258805 |
| 0bb39717 | 8 | exact_local | {'complete': 3} | 0.261098 | 0.268787 |
| 0bb39717 | 8 | exact_eps_local | {'complete': 3} | 0.251557 | 0.260764 |
| 0bb39717 | 8 | rejection | {'complete': 3} | 0.204281 | 0.207199 |
| 0bb39717 | 16 | closed | {'complete': 3} | 0.543660 | 0.549016 |
| 0bb39717 | 16 | grammar_hit | {'complete': 3} | 0.536271 | 0.541484 |
| 0bb39717 | 16 | counter_only | {'complete': 3} | 0.439171 | 0.500514 |
| 0bb39717 | 16 | cars | {'complete': 3} | 0.445458 | 0.509745 |
| 0bb39717 | 16 | cars_perfect | {'complete': 3} | 0.489922 | 0.551047 |
| 0bb39717 | 16 | counter_cars | {'complete': 3} | 0.464634 | 0.641506 |
| 0bb39717 | 16 | counter_cars_perfect | {'complete': 3} | 0.516282 | 0.669127 |
| 0bb39717 | 16 | exact_stack | {'complete': 3} | 0.741512 | 0.746113 |
| 0bb39717 | 16 | exact_bidir_local | {'complete': 3} | 0.626401 | 0.635472 |
| 0bb39717 | 16 | exact_local | {'complete': 3} | 0.829769 | 0.839009 |
| 0bb39717 | 16 | exact_eps_local | {'complete': 3} | 0.666987 | 0.678100 |
| 0bb39717 | 16 | rejection | {'complete': 3} | 0.385701 | 0.398082 |
| 0bb39717 | 16 | handoff | {'complete': 3} | 0.491651 | 0.496902 |
| 0ce7169f | 4 | grammar_hit | {'complete': 3} | 0.123316 | 0.124993 |
| 0ce7169f | 4 | counter_only | {'complete': 3} | 0.119769 | 0.123356 |
| 0ce7169f | 4 | cars | {'complete': 3} | 0.118191 | 0.129828 |
| 0ce7169f | 4 | cars_perfect | {'complete': 3} | 0.118889 | 0.130487 |
| 0ce7169f | 4 | counter_cars | {'complete': 3} | 0.121376 | 0.163152 |
| 0ce7169f | 4 | counter_cars_perfect | {'complete': 3} | 0.122513 | 0.164202 |
| 0ce7169f | 4 | exact_stack | {'complete': 3} | 0.121223 | 0.122547 |
| 0ce7169f | 4 | exact_bidir_local | {'complete': 3} | 0.125976 | 0.128699 |
| 0ce7169f | 4 | exact_local | {'complete': 3} | 0.137751 | 0.140475 |
| 0ce7169f | 4 | exact_eps_local | {'complete': 3} | 0.125570 | 0.128758 |
| 0ce7169f | 4 | rejection | {'complete': 3} | 0.108943 | 0.109725 |
| 0ce7169f | 4 | handoff | {'complete': 3} | 0.123925 | 0.125596 |
| 0ce7169f | 4 | closed | {'complete': 3} | 0.123984 | 0.125651 |
| 0ce7169f | 8 | counter_only | {'complete': 3} | 0.215819 | 0.232626 |
| 0ce7169f | 8 | cars | {'complete': 3} | 0.215314 | 0.249180 |
| 0ce7169f | 8 | cars_perfect | {'complete': 3} | 0.218183 | 0.256080 |
| 0ce7169f | 8 | counter_cars | {'complete': 3} | 0.220859 | 0.272473 |
| 0ce7169f | 8 | counter_cars_perfect | {'complete': 3} | 0.223287 | 0.274348 |
| 0ce7169f | 8 | exact_stack | {'complete': 3} | 0.236226 | 0.238093 |
| 0ce7169f | 8 | exact_bidir_local | {'complete': 3} | 0.412482 | 0.416156 |
| 0ce7169f | 8 | exact_local | {'complete': 3} | 0.570531 | 0.574382 |
| 0ce7169f | 8 | exact_eps_local | {'complete': 3} | 0.454190 | 0.458446 |
| 0ce7169f | 8 | rejection | {'complete': 3} | 0.198380 | 0.199698 |
| 0ce7169f | 8 | handoff | {'complete': 3} | 0.244686 | 0.247123 |
| 0ce7169f | 8 | closed | {'complete': 3} | 0.248013 | 0.250158 |
| 0ce7169f | 8 | grammar_hit | {'complete': 3} | 0.238377 | 0.240780 |
| 0ce7169f | 16 | cars | {'complete': 3} | 17.875222 | 103.039488 |
| 0ce7169f | 16 | cars_perfect | {'complete': 3} | 9.018053 | 71.362364 |
| 0ce7169f | 16 | counter_cars | {'complete': 3} | 0.673192 | 2.408472 |
| 0ce7169f | 16 | counter_cars_perfect | {'complete': 3} | 0.698978 | 1.866501 |
| 0ce7169f | 16 | exact_stack | {'complete': 3} | 25.893596 | 25.918733 |
| 0ce7169f | 16 | exact_bidir_local | {'resource_refusal': 3} |  |  |
| 0ce7169f | 16 | exact_local | {'resource_refusal': 3} |  |  |
| 0ce7169f | 16 | exact_eps_local | {'resource_refusal': 3} |  |  |
| 0ce7169f | 16 | rejection | {'resource_refusal': 3} |  |  |
| 0ce7169f | 16 | handoff | {'complete': 3} | 1.322712 | 1.328682 |
| 0ce7169f | 16 | closed | {'complete': 3} | 1.107874 | 1.113443 |
| 0ce7169f | 16 | grammar_hit | {'complete': 3} | 8.470884 | 8.500922 |
| 0ce7169f | 16 | counter_only | {'complete': 3} | 43.687571 |  |
