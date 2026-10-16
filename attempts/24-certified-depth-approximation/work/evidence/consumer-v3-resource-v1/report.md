# A24 V3 — complete known-data resource screen

45/45 records; statuses:{'complete': 42, 'zero_true_mass': 3}.
Native statuses:{'complete': 190, 'allocation_guard': 20}; 190 complete/correct.
Warnings:0.
30 tail/conditional checks against exact full masses pass. Resource gate:14/15 states.

These are OLD weights with an appended fixed EOT/PAD, not new neural outputs.
The target is JSON EOT PAD* over all original IDs. Torch2.8/CUDA12.8 is the declared kernel port.
An allocation guard is not a measured OOM or a general CFG lower bound.
Single-run diagnostic clocks, partly overlapping dependency downloads, establish no latency advantage.
The independent confirmation/cost/originality goals remain open.

| Old case | d1 nodes | d1 bound | d3 nodes | d3 bound | Full nodes | Native full completed |
|---|---:|---:|---:|---:|---:|---:|
|149c0c8c-16|95|1.09791e-05|581|2.14617e-14|22421|0/5|
|149c0c8c-4|14|0|14|0|14|5/5|
|149c0c8c-8|15|4.8804e-12|16|6.20733e-30|16|5/5|
|8d5fc991-16|50|0.175981|293|1.55929e-07|12720|0/5|
|8d5fc991-4|13|0|13|0|13|5/5|
|8d5fc991-8|23|8.12003e-06|69|4.07548e-17|71|5/5|
|c87bca6a-16|104|7.28546e-06|591|4.44618e-13|42038|0/5|
|c87bca6a-4|8|0|8|0|8|5/5|
|c87bca6a-8|25|3.23043e-05|47|1.88114e-18|47|5/5|
|d62b9d62-16|28|2.3802e-15|90|2.94023e-33|147|5/5|
|d62b9d62-4|11|0|11|0|11|5/5|
|d62b9d62-8|11|0|11|0|11|5/5|
|d829cdbc-16|1|zero L|295|0.99983|12317|0/5|
|d829cdbc-4|1|zero L|14|8.75973e-05|14|5/5|
|d829cdbc-8|1|zero L|45|9.25096e-05|73|5/5|

Observed maximum sampled-confidence absolute difference:0.000334101814; fp64:1.04360964e-14.
These are observed errors, not certificates for the entire rounded sampling law.
