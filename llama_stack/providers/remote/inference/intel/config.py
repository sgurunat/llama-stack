# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import os
from typing import Any

from pydantic import BaseModel, Field, SecretStr

from llama_stack.schema_utils import json_schema_type


@json_schema_type
class IntelConfig(BaseModel):
    """
    Configuration for the Intel inference endpoint.

    Attributes:
        url (str): A base url for accessing the Intel Inference Endpoint, e.g. http://localhost:8000
        api_key (str): The access key for the hosted Intel Inference endpoints
    """

    url: str = Field(
        default_factory=lambda: os.getenv("INTEL_BASE_URL", "https://api.inference.denvrdata.com/v1"),
        description="A base url for accessing the Intel Inference Endpoint",
    )
    api_key: SecretStr | None = Field(
        default_factory=lambda: os.getenv("INTEL_API_KEY"),
        description="The Intel API key, only needed of using the hosted service",
    )
    timeout: int = Field(
        default=60,
        description="Timeout for the HTTP requests",
    )
    

    @classmethod
    def sample_run_config(cls, **kwargs) -> dict[str, Any]:
        return {
            "url": "${env.INTEL_BASE_URL:https://api.inference.denvrdata.com/v1}",
            "api_key": "${env.INTEL_API_KEY:}"
        }
