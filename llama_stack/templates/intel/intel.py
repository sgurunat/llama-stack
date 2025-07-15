# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from pathlib import Path

from llama_stack.distribution.datatypes import ModelInput, Provider, ShieldInput, ToolGroupInput
from llama_stack.providers.remote.inference.intel_openai_compat.config import IntelCompatConfig
from llama_stack.providers.remote.inference.intel_openai_compat.models import MODEL_ENTRIES
from llama_stack.templates.template import DistributionTemplate, RunConfigSettings, get_model_registry


def get_inference_providers() -> tuple[list[Provider], list[ModelInput]]:
    # in this template, we allow each API key to be optional
    providers = [
        (
            "intel-openai-compat",
            MODEL_ENTRIES,
            IntelCompatConfig.sample_run_config(openai_compat_api_base="${env.INTEL_BASE_URL}", api_key="${env.INTEL_API_KEY:}"),
        ),
    ]
    inference_providers = []
    available_models = {}
    for provider_id, model_entries, config in providers:
        inference_providers.append(
            Provider(
                provider_id=provider_id,
                provider_type=f"remote::{provider_id}",
                config=config,
            )
        )
        available_models[provider_id] = model_entries
    return inference_providers, available_models


def get_distribution_template() -> DistributionTemplate:
    inference_providers, available_models = get_inference_providers()
    providers = {
        "inference": ["remote::intel-openai-compat"],
        "vector_io": ["inline::faiss"],
        "safety": ["inline::llama-guard"],
        "agents": ["inline::meta-reference"],
        "telemetry": ["inline::meta-reference"],
        "eval": ["inline::meta-reference"],
        "datasetio": ["inline::localfs"],
        "scoring": ["inline::basic"],
        "tool_runtime": ["inline::rag-runtime"],
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
        template_path=None,
        providers=providers,
        available_models_by_provider=available_models,
        run_configs={
            "run.yaml": RunConfigSettings(
                provider_overrides={
                    "inference": inference_providers
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
                "",
                "Base URL for Intel Inference Endpoint",
            )
        },
    )
