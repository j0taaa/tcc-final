#!/bin/bash

for seed in 42 43 44; do
    for step in 16 32 64 128 256; do
        for model in Dream-org/Dream-v0-Instruct-7B GSAI-ML/LLaDA-8B-Instruct apple/DiffuCoder-7B-Instruct Dream-org/Dream-Coder-v0-Instruct-7B; do
            CUDA_VISIBLE_DEVICES=0 python scripts/run_main.py --out ./result_logging/cpp --result ./results/cpp --print-command -- python -m constrained_diffusion.eval.dllm.generic_inference --max-tokens 256 --model_name $model --seed $seed --temp 0.0 --dataset-name zai-org/humaneval-x/cpp --steps $step --constrained True --trace False

            CUDA_VISIBLE_DEVICES=0 python scripts/run_main.py --out ./result_logging/json --result ./results/json --print-command -- python -m constrained_diffusion.eval.dllm.generic_inference --max-tokens 256 --model_name $model --seed $seed --temp 0.0 --dataset-name jsonschema --steps $step --constrained True --trace False

            CUDA_VISIBLE_DEVICES=0 python scripts/run_main.py --out ./result_logging/smiles --result ./results/smiles --print-command -- python -m constrained_diffusion.eval.dllm.generic_inference --max-tokens 256 --model_name $model --seed $seed --temp 0.0 --dataset-name smiles --steps $step --constrained True --trace False
        done
    done
done

for seed in 42 43 44; do
    for step in 32; do
        for model in Dream-org/Dream-v0-Instruct-7B GSAI-ML/LLaDA-8B-Instruct apple/DiffuCoder-7B-Instruct Dream-org/Dream-Coder-v0-Instruct-7B; do
            CUDA_VISIBLE_DEVICES=0 python scripts/run_ablation.py --out ./result_logging/cpp --result ./results/cpp --print-command -- python -m constrained_diffusion.eval.dllm.generic_inference --max-tokens 256 --model_name $model --seed $seed --temp 0.0 --dataset-name zai-org/humaneval-x/cpp --steps $step --constrained True --trace False

            CUDA_VISIBLE_DEVICES=0 python scripts/run_ablation.py --out ./result_logging/json --result ./results/json --print-command -- python -m constrained_diffusion.eval.dllm.generic_inference --max-tokens 256 --model_name $model --seed $seed --temp 0.0 --dataset-name jsonschema --steps $step --constrained True --trace False

            CUDA_VISIBLE_DEVICES=0 python scripts/run_ablation.py --out ./result_logging/smiles --result ./results/smiles --print-command -- python -m constrained_diffusion.eval.dllm.generic_inference --max-tokens 256 --model_name $model --seed $seed --temp 0.0 --dataset-name smiles --steps $step --constrained True --trace False
        done
    done
done
