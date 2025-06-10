# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from pathlib import Path

from llama_stack.distribution.datatypes import ModelInput, Provider, ShieldInput, ToolGroupInput
from llama_stack.providers.remote.inference.intel import IntelConfig
from llama_stack.providers.remote.inference.intel.models import MODEL_ENTRIES
from llama_stack.templates.template import DistributionTemplate, RunConfigSettings, get_model_registry


def get_distribution_template() -> DistributionTemplate:
    providers = {
        "inference": ["remote::intel"],
        "vector_io": ["inline::faiss"],
        "safety": ["inline::llama-guard"],
        "agents": ["inline::meta-reference"],
        "telemetry": ["inline::meta-reference"],
        "eval": ["inline::meta-reference"],
        "datasetio": ["inline::localfs"],
        "scoring": ["inline::basic"],
        "tool_runtime": ["inline::rag-runtime"],
    }

    inference_provider = Provider(
        provider_id="intel",
        provider_type="remote::intel",
        config=IntelConfig.sample_run_config(),
    )
   
    inference_model = ModelInput(
        model_id="${env.INFERENCE_MODEL}",
        provider_id="intel",
    )
    safety_model = ModelInput(
        model_id="${env.SAFETY_MODEL}",
        provider_id="intel",
    )

    available_models = {
        "intel": MODEL_ENTRIES,
    }
    default_tool_groups = [
        ToolGroupInput(
            toolgroup_id="builtin::rag",
            provider_id="rag-runtime",
        ),
    ]

    default_models = get_model_registry(available_models)
    return DistributionTemplate(
        name="intel",
        distro_type="self_hosted",
        description="Use Intel for running LLM inference",
        container_image=None,
        template_path=Path(__file__).parent / "doc_template.md",
        providers=providers,
        available_models_by_provider=available_models,
        run_configs={
            "run.yaml": RunConfigSettings(
                provider_overrides={
                    "inference": [inference_provider]
                },
                default_models=default_models,
                default_tool_groups=default_tool_groups,
            )
        },
        run_config_env_vars={
            "INTEL_API_KEY": (
                "",
                "INTEL API Key",
            ),
            "INTEL_BASE_URL": (
                "https://inference.api.intel.com",
                "Base URL for Intel Inference Endpoint",
            ),
            "INFERENCE_MODEL": (
                "Llama3.3-70B-Instruct",
                "Inference model",
            ),
            "SAFETY_MODEL": (
                "meta/llama-3.1-8b-instruct",
                "Name of the model to use for safety",
            ),
        },
    )
