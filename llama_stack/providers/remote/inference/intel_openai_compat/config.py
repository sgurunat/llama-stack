# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from typing import Any

from pydantic import BaseModel, Field

from llama_stack.schema_utils import json_schema_type


class IntelProviderDataValidator(BaseModel):
    intel_api_key: str | None = Field(
        default=None,
        description="API key for Intel models",
    )


@json_schema_type
class IntelCompatConfig(BaseModel):
    api_key: str | None = Field(
        default=None,
        description="The Intel API key",
    )

    openai_compat_api_base: str = Field(
        default=None,
        description="The URL for the Intel API server",
    )

    @classmethod
    def sample_run_config(cls, api_key: str = "${env.INTEL_API_KEY}", **kwargs) -> dict[str, Any]:
        return {
            "openai_compat_api_base": "${env.INTEL_BASE_URL:}",
            "api_key": api_key,
        }
