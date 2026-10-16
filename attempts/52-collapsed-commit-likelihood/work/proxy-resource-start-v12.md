# V12 resource-start refusal, before ANY old-head query

2026-10-16 20:40UTC. Frozen producer dc906e1 started the first replay attempt
in a52_proxy_functionality_v12_initial. Its initial NVML guard detected a
foreign GPU process and refused BEFORE runtime/source checks, lexical setup,
old-head loading or any new proxy calculation. All70 inputs are explicitly
NOT_RUN; complete observer/summary/log/manifest are retained. Zero new model
forwards/samples/updates and zero attempted numeric replay queries.

The resource prerequisite has not been met; this is not an error of the proxy
or evidence of its benefit. Do not modify the isolation rule, cap, source,
thresholds or question set to bypass it. After the unrelated process naturally
finishes, the SAME frozen replay may start in a NEW output directory, preserving
this initial refusal. The one70-query replay budget remains unused. No killing
or contacting the other job is authorized. Any later resource attempt must
also retain its whole-capture monitor and be reported alongside this one.
