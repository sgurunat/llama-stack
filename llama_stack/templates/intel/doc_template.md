# INTEL Distribution

The `llamastack/distribution-{{ name }}` distribution consists of the following provider configurations.

{{ providers_table }}

{% if run_config_env_vars %}
### Environment Variables

The following environment variables can be configured:

{% for var, (default_value, description) in run_config_env_vars.items() %}
- `{{ var }}`: {{ description }} (default: `{{ default_value }}`)
{% endfor %}
{% endif %}

{% if default_models %}
### Models

The following models are available by default:

{% for model in default_models %}
- `{{ model.model_id }} {{ model.doc_string }}`
{% endfor %}
{% endif %}


## Prerequisites
### INTEL API Keys

Make sure you have access to a INTEL API Key. Use this key for the `INTEL_API_KEY` environment variable.


## Running Llama Stack with INTEL

You can do this via Conda or venv (build code), or Docker which has a pre-built image.

### Via Docker

This method allows you to get started quickly without having to build the distribution code.

```bash
LLAMA_STACK_PORT=8321
docker run \
  -it \
  --pull always \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ./run.yaml:/root/my-run.yaml \
  llamastack/distribution-{{ name }} \
  --config /root/my-run.yaml \
  --port $LLAMA_STACK_PORT \
  --env INTEL_API_KEY=$INTEL_API_KEY
```

### Via Conda

```bash
INFERENCE_MODEL=meta-llama/Llama-3.1-8b-Instruct
llama stack build --template intel --image-type conda
llama stack run ./run.yaml \
  --port 8321 \
  --env INTEL_API_KEY=$INTEL_API_KEY \
  --env INFERENCE_MODEL=$INFERENCE_MODEL
```

### Via venv

If you've set up your local development environment, you can also build the image using your local virtual environment.

```bash
INFERENCE_MODEL=meta-llama/Llama-3.1-8b-Instruct
llama stack build --template intel --image-type venv
llama stack run ./run.yaml \
  --port 8321 \
  --env INTEL_API_KEY=$INTEL_API_KEY \
  --env INFERENCE_MODEL=$INFERENCE_MODEL
```
