# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from llama_stack.apis.inference import Inference

from .config import IntelConfig


async def get_adapter_impl(config: IntelConfig, _deps) -> Inference:
    # import dynamically so `llama stack build` does not fail due to missing dependencies
    from .intel import IntelInferenceAdapter

    if not isinstance(config, IntelConfig):
        raise RuntimeError(f"Unexpected config type: {type(config)}")
    adapter = IntelInferenceAdapter(config)
    return adapter


__all__ = ["get_adapter_impl", "IntelConfig"]
