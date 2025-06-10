# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import logging

import httpx

from . import IntelConfig

logger = logging.getLogger(__name__)


def _is_intel_hosted(config: IntelConfig) -> bool:
    return "api.inference.denvrdata.com" in config.url


