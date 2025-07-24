---
orphan: true
---
# Remote vLLM Distribution
```{toctree}
:maxdepth: 2
:hidden:

self
```

The `llamastack/distribution-{{ name }}` distribution consists of the following provider configurations:

{{ providers_table }}

You can use this distribution if you want to run an independent vLLM server for inference.

{% if run_config_env_vars %}
### Environment Variables

The following environment variables can be configured:

{% for var, (default_value, description) in run_config_env_vars.items() %}
- `{{ var }}`: {{ description }} (default: `{{ default_value }}`)
{% endfor %}
{% endif %}


## Setting up vLLM server

In the following sections, we'll use AMD, NVIDIA or Intel GPUs to serve as hardware accelerators for the vLLM
server, which acts as both the LLM inference provider and the safety provider. Note that vLLM also
[supports many other hardware accelerators](https://docs.vllm.ai/en/latest/getting_started/installation.html) and
that we only use GPUs here for demonstration purposes. Note that if you run into issues, you can include the environment variable `--env VLLM_DEBUG_LOG_API_SERVER_RESPONSE=true` (available in vLLM v0.8.3 and above) in the `docker run` command to enable log response from API server for debugging.

### Setting up vLLM server on AMD GPU

AMD provides two main vLLM container options:
- rocm/vllm: Production-ready container
- rocm/vllm-dev: Development container with the latest vLLM features

Please check the [Blog about ROCm vLLM Usage](https://rocm.blogs.amd.com/software-tools-optimization/vllm-container/README.html) to get more details.

Here is a sample script to start a ROCm vLLM server locally via Docker:

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-3B-Instruct
export CUDA_VISIBLE_DEVICES=0
export VLLM_DIMG="rocm/vllm-dev:main"

docker run \
    --pull always \
    --ipc=host \
    --privileged \
    --shm-size 16g \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    --cap-add=SYS_PTRACE \
    --cap-add=CAP_SYS_ADMIN \
    --security-opt seccomp=unconfined \
    --security-opt apparmor=unconfined \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env "HIP_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES" \
    -p $INFERENCE_PORT:$INFERENCE_PORT \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    $VLLM_DIMG \
    python -m vllm.entrypoints.openai.api_server \
    --model $INFERENCE_MODEL \
    --port $INFERENCE_PORT
```

Note that you'll also need to set `--enable-auto-tool-choice` and `--tool-call-parser` to [enable tool calling in vLLM](https://docs.vllm.ai/en/latest/features/tool_calling.html).

If you are using Llama Stack Safety / Shield APIs, then you will need to also run another instance of a vLLM with a corresponding safety model like `meta-llama/Llama-Guard-3-1B` using a script like:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B
export CUDA_VISIBLE_DEVICES=1
export VLLM_DIMG="rocm/vllm-dev:main"

docker run \
    --pull always \
    --ipc=host \
    --privileged \
    --shm-size 16g \
    --device=/dev/kfd \
    --device=/dev/dri \
    --group-add video \
    --cap-add=SYS_PTRACE \
    --cap-add=CAP_SYS_ADMIN \
    --security-opt seccomp=unconfined \
    --security-opt apparmor=unconfined \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env "HIP_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES" \
    -p $SAFETY_PORT:$SAFETY_PORT \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    $VLLM_DIMG \
    python -m vllm.entrypoints.openai.api_server \
    --model $SAFETY_MODEL \
    --port $SAFETY_PORT
```

### Setting up vLLM server on NVIDIA GPU

Please check the [vLLM Documentation](https://docs.vllm.ai/en/v0.5.5/serving/deploying_with_docker.html) to get a vLLM endpoint. Here is a sample script to start a vLLM server locally via Docker:

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-3B-Instruct
export CUDA_VISIBLE_DEVICES=0

docker run \
    --pull always \
    --runtime nvidia \
    --gpus $CUDA_VISIBLE_DEVICES \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    -p $INFERENCE_PORT:$INFERENCE_PORT \
    --ipc=host \
    vllm/vllm-openai:latest \
    --gpu-memory-utilization 0.7 \
    --model $INFERENCE_MODEL \
    --port $INFERENCE_PORT
```

Note that you'll also need to set `--enable-auto-tool-choice` and `--tool-call-parser` to [enable tool calling in vLLM](https://docs.vllm.ai/en/latest/features/tool_calling.html).

If you are using Llama Stack Safety / Shield APIs, then you will need to also run another instance of a vLLM with a corresponding safety model like `meta-llama/Llama-Guard-3-1B` using a script like:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B
export CUDA_VISIBLE_DEVICES=1

docker run \
    --pull always \
    --runtime nvidia \
    --gpus $CUDA_VISIBLE_DEVICES \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    -p $SAFETY_PORT:$SAFETY_PORT \
    --ipc=host \
    vllm/vllm-openai:latest \
    --gpu-memory-utilization 0.7 \
    --model $SAFETY_MODEL \
    --port $SAFETY_PORT
```

### Setting up vLLM server on Intel GPU

Refer to [vLLM Documentation for XPU](https://docs.vllm.ai/en/v0.8.2/getting_started/installation/gpu.html?device=xpu) to get a vLLM endpoint. In addition to vLLM side setup which guides towards installing vLLM from sources orself-building vLLM Docker container, Intel provides prebuilt vLLM container to use on systems with Intel GPUs supported by PyTorch XPU backend:
- [intel/vllm](https://hub.docker.com/r/intel/vllm)

Here is a sample script to start a vLLM server locally via Docker using Intel provided container:

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-1B-Instruct
export ZE_AFFINITY_MASK=0

docker run \
    --pull always \
    --device /dev/dri \
    -v /dev/dri/by-path:/dev/dri/by-path \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env ZE_AFFINITY_MASK=$ZE_AFFINITY_MASK \
    -p $INFERENCE_PORT:$INFERENCE_PORT \
    --ipc=host \
    intel/vllm:xpu \
    --gpu-memory-utilization 0.7 \
    --model $INFERENCE_MODEL \
    --port $INFERENCE_PORT
```

If you are using Llama Stack Safety / Shield APIs, then you will need to also run another instance of a vLLM with a corresponding safety model like `meta-llama/Llama-Guard-3-1B` using a script like:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B
export ZE_AFFINITY_MASK=1

docker run \
    --pull always \
    --device /dev/dri \
    -v /dev/dri/by-path:/dev/dri/by-path \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env ZE_AFFINITY_MASK=$ZE_AFFINITY_MASK \
    -p $SAFETY_PORT:$SAFETY_PORT \
    --ipc=host \
    intel/vllm:xpu \
    --gpu-memory-utilization 0.7 \
    --model $SAFETY_MODEL \
    --port $SAFETY_PORT
```

## Setting up vLLM Server on Intel CPU (Xeon)

Intel provides a prebuilt Docker container for running vLLM on systems with Intel CPUs, such as Xeon processors. This is ideal for environments without discrete GPUs or for CPU-based inference workloads.

### Running vLLM Server on Intel CPU

Here is a sample script to start a vLLM server locally via Docker using the Intel CPU container:

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-1B-Instruct

docker run \
    --pull always \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    -p $INFERENCE_PORT:$INFERENCE_PORT \
    --ipc=host \
    public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.9.2 \
    --model $INFERENCE_MODEL \
    --max-model-len 32768 \
    --port $INFERENCE_PORT
```

If you are using Llama Stack Safety / Shield APIs, then you will need to also run another instance of a vLLM with a corresponding safety model like `meta-llama/Llama-Guard-3-1B` using a script like:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B

docker run \
    --pull always \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    -p $SAFETY_PORT:$SAFETY_PORT \
    --ipc=host \
    public.ecr.aws/q9t5s3a7/vllm-cpu-release-repo:v0.9.2 \
    --model $SAFETY_MODEL \
    --port $SAFETY_PORT
```


## Setting up vLLM Server on Intel HPU (Gaudi)

Intel HPU (Gaudi) accelerators are designed for high-performance AI inference workloads. To run vLLM on Gaudi, you can use the prebuilt Docker container provided by the OPEA community.

### Running vLLM Server on Intel Gaudi

Here is a sample script to start a vLLM server locally via Docker using the Gaudi container:

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-1B-Instruct
export HABANA_VISIBLE_DEVICES=all

docker run \
    --runtime=habana \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env "HABANA_VISIBLE_DEVICES=$HABANA_VISIBLE_DEVICES" \
    -p $INFERENCE_PORT:$INFERENCE_PORT \
    --cap-add=sys_nice \
    --net=host \
    --ipc=host \
    opea/vllm-gaudi:latest \
    --model $INFERENCE_MODEL \
    --port $INFERENCE_PORT \
    --block-size 128 \
    --max-num-seqs 256 \
    --max-seq-len-to-capture 2048

```

If you are using Llama Stack Safety / Shield APIs, then you will need to also run another instance of a vLLM with a corresponding safety model like `meta-llama/Llama-Guard-3-1B` using a script like:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B
export HABANA_VISIBLE_DEVICES=all

docker run \
    --runtime=habana \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env "HABANA_VISIBLE_DEVICES=$HABANA_VISIBLE_DEVICES" \
    -p $SAFETY_PORT:$SAFETY_PORT \
    --cap-add=sys_nice \
    --net=host \
    --ipc=host \
    opea/vllm-gaudi:latest \
    --model $SAFETY_MODEL \
    --port $SAFETY_PORT \
    --block-size 128 \
    --max-num-seqs 256 \
    --max-seq-len-to-capture 2048

```


## Running Llama Stack

Now you are ready to run Llama Stack with vLLM as the inference provider. You can do this via Conda (build code) or Docker which has a pre-built image.

### Via Docker

This method allows you to get started quickly without having to build the distribution code.

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-3B-Instruct
export LLAMA_STACK_PORT=8321

# You need a local checkout of llama-stack to run this, get it using
# git clone https://github.com/meta-llama/llama-stack.git
cd /path/to/llama-stack

docker run \
  --pull always \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ./llama_stack/templates/remote-vllm/run.yaml:/root/my-run.yaml \
  llamastack/distribution-{{ name }} \
  --config /root/my-run.yaml \
  --port $LLAMA_STACK_PORT \
  --env INFERENCE_MODEL=$INFERENCE_MODEL \
  --env VLLM_URL=http://host.docker.internal:$INFERENCE_PORT/v1
```

If you are using Llama Stack Safety / Shield APIs, use:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B

# You need a local checkout of llama-stack to run this, get it using
# git clone https://github.com/meta-llama/llama-stack.git
cd /path/to/llama-stack

docker run \
  --pull always \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ~/.llama:/root/.llama \
  -v ./llama_stack/templates/remote-vllm/run-with-safety.yaml:/root/my-run.yaml \
  llamastack/distribution-{{ name }} \
  --config /root/my-run.yaml \
  --port $LLAMA_STACK_PORT \
  --env INFERENCE_MODEL=$INFERENCE_MODEL \
  --env VLLM_URL=http://host.docker.internal:$INFERENCE_PORT/v1 \
  --env SAFETY_MODEL=$SAFETY_MODEL \
  --env SAFETY_VLLM_URL=http://host.docker.internal:$SAFETY_PORT/v1
```


### Via Conda

Make sure you have done `uv pip install llama-stack` and have the Llama Stack CLI available.

```bash
export INFERENCE_PORT=8000
export INFERENCE_MODEL=meta-llama/Llama-3.2-3B-Instruct
export LLAMA_STACK_PORT=8321

cd distributions/remote-vllm
llama stack build --template remote-vllm --image-type conda

llama stack run ./run.yaml \
  --port $LLAMA_STACK_PORT \
  --env INFERENCE_MODEL=$INFERENCE_MODEL \
  --env VLLM_URL=http://localhost:$INFERENCE_PORT/v1
```

If you are using Llama Stack Safety / Shield APIs, use:

```bash
export SAFETY_PORT=8081
export SAFETY_MODEL=meta-llama/Llama-Guard-3-1B

llama stack run ./run-with-safety.yaml \
  --port $LLAMA_STACK_PORT \
  --env INFERENCE_MODEL=$INFERENCE_MODEL \
  --env VLLM_URL=http://localhost:$INFERENCE_PORT/v1 \
  --env SAFETY_MODEL=$SAFETY_MODEL \
  --env SAFETY_VLLM_URL=http://localhost:$SAFETY_PORT/v1
```
