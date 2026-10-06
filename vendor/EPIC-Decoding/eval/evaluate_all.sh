#!/bin/bash

for seed in 42 43 44; do
    for model in Dream DreamCoder LLaDA DiffuCoder; do
        for step in 16 32 64 128 256; do
            echo ${model}_*_seed${seed}_steps${step}
            DATASETS_VERBOSITY=error HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 python -u eval/evaluate_all.py results/json/${model}_*_seed${seed}_steps${step}.jsonl --output-dir eval_results/json
            DATASETS_VERBOSITY=error HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 python -u eval/evaluate_all.py results/smiles/${model}_*_seed${seed}_steps${step}.jsonl --output-dir eval_results/smiles
        done
    done
done

for seed in 42 43 44; do
    for model in Dream DreamCoder LLaDA DiffuCoder; do
        for step in 16 64 128 256; do
            for method in unconstrained baseline epic; do
                date
                echo ${model}_${method}_seed${seed}_steps${step}
                DATASETS_VERBOSITY=error HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 python -u eval/evaluate_all.py results/cpp/${model}_${method}_seed${seed}_steps${step}.jsonl --output-dir cpp_eval_results/cpp --task-timeout 400
            done
        done
        for step in 32; do
            for method in unconstrained baseline cache earley cache_earley regular cache_regular earley_regular epic; do
                date
                echo ${model}_${method}_seed${seed}_steps${step}
                DATASETS_VERBOSITY=error HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 python -u eval/evaluate_all.py results/cpp/${model}_${method}_seed${seed}_steps${step}.jsonl --output-dir cpp_eval_results/cpp --task-timeout 400
            done
        done
    done
done