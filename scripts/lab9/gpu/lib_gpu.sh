# Settings of the GPU extension (minikube with --gpus all). Source after scripts/lab9/lib.sh.
GPU_PROFILE="${LAB9_GPU_PROFILE:-lab9-gpu}"
GPU_KCTX="$GPU_PROFILE"
LLM_IMAGE="${LAB9_LLM_IMAGE:-fraud-llm:lab9}"
LLM_CACHE_DIR="${LAB9_LLM_CACHE_DIR:-$LAB9_DIR/llm-cache}"   # qwen3/ + dataset JSON; reuse week-2's wb_monitoring dir if you have it
MINIKUBE_VERSION="${LAB9_MINIKUBE_VERSION:-v1.37.0}"
GPU_CPUS="${LAB9_GPU_CPUS:-4}"
GPU_MEMORY="${LAB9_GPU_MEMORY:-16g}"
kg() { kubectl --context "$GPU_KCTX" "$@"; }
