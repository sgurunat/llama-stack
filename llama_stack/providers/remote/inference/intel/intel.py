# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import logging
import warnings
from collections.abc import AsyncGenerator, AsyncIterator
from functools import lru_cache
from typing import Any

from openai import APIConnectionError, AsyncOpenAI, BadRequestError

from llama_stack.apis.common.content_types import (
    InterleavedContent,
    InterleavedContentItem,
    TextContentItem,
)
from llama_stack.apis.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseStreamChunk,
    CompletionRequest,
    CompletionResponse,
    CompletionResponseStreamChunk,
    EmbeddingsResponse,
    EmbeddingTaskType,
    Inference,
    LogProbConfig,
    Message,
    OpenAIEmbeddingsResponse,
    ResponseFormat,
    SamplingParams,
    TextTruncation,
    ToolChoice,
    ToolConfig,
)
from llama_stack.apis.inference.inference import (
    OpenAIChatCompletion,
    OpenAIChatCompletionChunk,
    OpenAICompletion,
    OpenAIMessageParam,
    OpenAIResponseFormatParam,
)
from llama_stack.apis.models import Model, ModelType
from llama_stack.models.llama.datatypes import ToolDefinition, ToolPromptFormat
from llama_stack.providers.utils.inference import (
    ALL_HUGGINGFACE_REPOS_TO_MODEL_DESCRIPTOR,
)
from llama_stack.providers.utils.inference.model_registry import (
    ModelRegistryHelper,
)
from llama_stack.providers.utils.inference.openai_compat import (
    convert_openai_chat_completion_choice,
    convert_openai_chat_completion_stream,
    prepare_openai_completion_params,
)
from llama_stack.providers.utils.inference.prompt_adapter import content_has_media

from . import IntelConfig
from .models import MODEL_ENTRIES
from .openai_utils import (
    convert_chat_completion_request,
    convert_completion_request,
    convert_openai_completion_choice,
    convert_openai_completion_stream,
)
from .utils import _is_intel_hosted

logger = logging.getLogger(__name__)


class IntelInferenceAdapter(Inference, ModelRegistryHelper):
    def __init__(self, config: IntelConfig) -> None:
        # TODO(mf): filter by available models
        ModelRegistryHelper.__init__(self, model_entries=MODEL_ENTRIES)

        logger.info(f"Initializing IntelInferenceAdapter({config.url})...")

        if _is_intel_hosted(config):
            if not config.api_key:
                raise RuntimeError(
                    "API key is required for hosted Intel Inferencce Endpoint."
                )

        self._config = config

    @lru_cache  
    def _get_client(self, provider_model_id: str) -> AsyncOpenAI:
        

        @lru_cache  
        def _get_client_for_base_url(base_url: str) -> AsyncOpenAI:
            """
            Maintain a single OpenAI client per base_url.
            """
            return AsyncOpenAI(
                base_url=base_url,
                api_key=(self._config.api_key.get_secret_value() if self._config.api_key else "NO KEY"),
                timeout=self._config.timeout,
            )

        base_url = self._config.url

        return _get_client_for_base_url(base_url)

    async def _get_provider_model_id(self, model_id: str) -> str:
        if not self.model_store:
            raise RuntimeError("Model store is not set")
        model = await self.model_store.get_model(model_id)
        if model is None:
            raise ValueError(f"Model {model_id} is unknown")
        return model.provider_model_id

    async def completion(
        self,
        model_id: str,
        content: InterleavedContent,
        sampling_params: SamplingParams | None = None,
        response_format: ResponseFormat | None = None,
        stream: bool | None = False,
        logprobs: LogProbConfig | None = None,
    ) -> CompletionResponse | AsyncIterator[CompletionResponseStreamChunk]:
        if sampling_params is None:
            sampling_params = SamplingParams()

        # if hasattr(sampling_params, "type") and sampling_params.type == "greedy":
        #     sampling_params.type = "default"
        if content_has_media(content):
            raise NotImplementedError("Media is not supported")


        provider_model_id = await self._get_provider_model_id(model_id)
        request = convert_completion_request(
            request=CompletionRequest(
                model=provider_model_id,
                content=content,
                sampling_params=sampling_params,
                response_format=response_format,
                stream=stream,
                logprobs=logprobs,
            ),
            n=1,
        )

        try:
            response = await self._get_client(provider_model_id).completions.create(**request)
        except APIConnectionError as e:
            raise ConnectionError(f"Failed to connect to Intel Inference at {self._config.url}: {e}") from e

        if stream:
            return convert_openai_completion_stream(response)
        else:
            # we pass n=1 to get only one completion
            return convert_openai_completion_choice(response.choices[0])

        # if stream:
        #     return self._stream_completion(request)
        # else:
        #     return await self._nonstream_completion(request)

    async def embeddings(
        self,
        model_id: str,
        contents: list[str] | list[InterleavedContentItem],
        text_truncation: TextTruncation | None = TextTruncation.none,
        output_dimension: int | None = None,
        task_type: EmbeddingTaskType | None = None,
    ) -> EmbeddingsResponse:
        if any(content_has_media(content) for content in contents):
            raise NotImplementedError("Media is not supported")

        flat_contents = [content.text if isinstance(content, TextContentItem) else content for content in contents]
        input = [content.text if isinstance(content, TextContentItem) else content for content in flat_contents]
        provider_model_id = await self._get_provider_model_id(model_id)

        if text_truncation is not None:
            text_truncation_options = {
                TextTruncation.none: "NONE",
                TextTruncation.end: "END",
                TextTruncation.start: "START",
            }

        if task_type is not None:
            task_type_options = {
                EmbeddingTaskType.document: "passage",
                EmbeddingTaskType.query: "query",
            }

        try:
            response = await self._get_client(provider_model_id).embeddings.create(
                model=provider_model_id,
                input=input,
            )
        except BadRequestError as e:
            raise ValueError(f"Failed to get embeddings: {e}") from e

       
        return EmbeddingsResponse(embeddings=[embedding.embedding for embedding in response.data])

    async def openai_embeddings(
        self,
        model: str,
        input: str | list[str],
        encoding_format: str | None = "float",
        dimensions: int | None = None,
        user: str | None = None,
    ) -> OpenAIEmbeddingsResponse:
        raise NotImplementedError()

    async def chat_completion(
        self,
        model_id: str,
        messages: list[Message],
        sampling_params: SamplingParams | None = None,
        response_format: ResponseFormat | None = None,
        tools: list[ToolDefinition] | None = None,
        tool_choice: ToolChoice | None = ToolChoice.auto,
        tool_prompt_format: ToolPromptFormat | None = None,
        stream: bool | None = False,
        logprobs: LogProbConfig | None = None,
        tool_config: ToolConfig | None = None,
    ) -> ChatCompletionResponse | AsyncIterator[ChatCompletionResponseStreamChunk]:
        if sampling_params is None:
            sampling_params = SamplingParams()
        # if hasattr(sampling_params, "type") and sampling_params.type == "greedy":
        #     sampling_params.type = "default"
        if tool_prompt_format:
            warnings.warn("tool_prompt_format is not supported by Intel Inference, ignoring", stacklevel=2)

        provider_model_id = await self._get_provider_model_id(model_id)
        request = await convert_chat_completion_request(
            request=ChatCompletionRequest(
                model=provider_model_id,
                messages=messages,
                sampling_params=sampling_params,
                response_format=response_format,
                tools=tools,
                stream=stream,
                logprobs=logprobs,
                tool_config=tool_config,
            ),
            n=1,
        )

        #openai_client = self._get_client(provider_model_id)
        try:
            response = await self._get_client(provider_model_id).chat.completions.create(**request)
        except APIConnectionError as e:
            raise ConnectionError(f"Failed to connect to Intel Inference at {self._config.url}: {e}") from e

        if stream:
            return convert_openai_chat_completion_stream(response, enable_incremental_tool_calls=False)
        else:
            # we pass n=1 to get only one completion
            return convert_openai_chat_completion_choice(response.choices[0])
        # if stream:
        #     return self._stream_chat_completion(request, openai_client)
        # else:
        #     return await self._nonstream_chat_completion(request, openai_client)

    async def openai_completion(
        self,
        model: str,
        prompt: str | list[str] | list[int] | list[list[int]],
        best_of: int | None = None,
        echo: bool | None = None,
        frequency_penalty: float | None = None,
        logit_bias: dict[str, float] | None = None,
        logprobs: bool | None = None,
        max_tokens: int | None = None,
        n: int | None = None,
        presence_penalty: float | None = None,
        seed: int | None = None,
        stop: str | list[str] | None = None,
        stream: bool | None = None,
        stream_options: dict[str, Any] | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        user: str | None = None,
        guided_choice: list[str] | None = None,
        prompt_logprobs: int | None = None,
    ) -> OpenAICompletion:
        provider_model_id = await self._get_provider_model_id(model)

        params = await prepare_openai_completion_params(
            model=provider_model_id,
            prompt=prompt,
            best_of=best_of,
            echo=echo,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            max_tokens=max_tokens,
            n=n,
            presence_penalty=presence_penalty,
            seed=seed,
            stop=stop,
            stream=stream,
            stream_options=stream_options,
            temperature=temperature,
            top_p=top_p,
            user=user,
        )

        try:
            return await self._get_client(provider_model_id).completions.create(**params)
        except APIConnectionError as e:
            raise ConnectionError(f"Failed to connect to Intel Inference at {self._config.url}: {e}") from e

    async def openai_chat_completion(
        self,
        model: str,
        messages: list[OpenAIMessageParam],
        frequency_penalty: float | None = None,
        function_call: str | dict[str, Any] | None = None,
        functions: list[dict[str, Any]] | None = None,
        logit_bias: dict[str, float] | None = None,
        logprobs: bool | None = None,
        max_completion_tokens: int | None = None,
        max_tokens: int | None = None,
        n: int | None = None,
        parallel_tool_calls: bool | None = None,
        presence_penalty: float | None = None,
        response_format: OpenAIResponseFormatParam | None = None,
        seed: int | None = None,
        stop: str | list[str] | None = None,
        stream: bool | None = None,
        stream_options: dict[str, Any] | None = None,
        temperature: float | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        top_logprobs: int | None = None,
        top_p: float | None = None,
        user: str | None = None,
    ) -> OpenAIChatCompletion | AsyncIterator[OpenAIChatCompletionChunk]:
        provider_model_id = await self._get_provider_model_id(model)

        params = await prepare_openai_completion_params(
            model=provider_model_id,
            messages=messages,
            frequency_penalty=frequency_penalty,
            function_call=function_call,
            functions=functions,
            logit_bias=logit_bias,
            logprobs=logprobs,
            max_completion_tokens=max_completion_tokens,
            max_tokens=max_tokens,
            n=n,
            parallel_tool_calls=parallel_tool_calls,
            presence_penalty=presence_penalty,
            response_format=response_format,
            seed=seed,
            stop=stop,
            stream=stream,
            stream_options=stream_options,
            temperature=temperature,
            tool_choice=tool_choice,
            tools=tools,
            top_logprobs=top_logprobs,
            top_p=top_p,
            user=user,
        )

        try:
            return await self._get_client(provider_model_id).chat.completions.create(**params)
        except APIConnectionError as e:
            raise ConnectionError(f"Failed to connect to Intel Inference at {self._config.url}: {e}") from e

    # async def _nonstream_chat_completion(
    #     self, request: ChatCompletionRequest, client: AsyncOpenAI
    # ) -> ChatCompletionResponse:
    #     params = await self._get_params(request)
    #     r = await client.chat.completions.create(**params)
    #     choice = r.choices[0]
    #     result = ChatCompletionResponse(
    #         completion_message=CompletionMessage(
    #             content=choice.message.content or "",
    #             stop_reason=_convert_to_vllm_finish_reason(choice.finish_reason),
    #             tool_calls=_convert_to_vllm_tool_calls_in_response(choice.message.tool_calls),
    #         ),
    #         logprobs=None,
    #     )
    #     return result

    # async def _stream_chat_completion(
    #     self, request: ChatCompletionRequest, client: AsyncOpenAI
    # ) -> AsyncGenerator[ChatCompletionResponseStreamChunk, None]:
    #     params = await self._get_params(request)

    #     stream = await client.chat.completions.create(**params)
    #     if request.tools:
    #         res = _process_vllm_chat_completion_stream_response(stream)
    #     else:
    #         res = process_chat_completion_stream_response(stream, request)
    #     async for chunk in res:
    #         yield chunk

    # async def _nonstream_completion(self, request: CompletionRequest) -> CompletionResponse:
    #     assert self.client is not None
    #     params = await self._get_params(request)
    #     r = await self.client.completions.create(**params)
    #     return process_completion_response(r)

    # async def _stream_completion(
    #     self, request: CompletionRequest
    # ) -> AsyncGenerator[CompletionResponseStreamChunk, None]:
    #     assert self.client is not None
    #     params = await self._get_params(request)

    #     stream = await self.client.completions.create(**params)
    #     async for chunk in process_completion_stream_response(stream):
    #         yield chunk

    async def register_model(self, model: Model) -> Model:
        """
        Allow non-llama model registration.

        Non-llama model registration: API Catalogue models, post-training models, etc.
            client = LlamaStackAsLibraryClient("intel")
            client.models.register(
                    model_id="mistralai/mixtral-8x7b-instruct-v0.1",
                    model_type=ModelType.llm,
                    provider_id="intel",
                    provider_model_id="mistralai/mixtral-8x7b-instruct-v0.1"
            )

            NOTE: Only supports models endpoints compatible with AsyncOpenAI base_url format.
        """
        if model.model_type == ModelType.embedding:
            # embedding models are always registered by their provider model id and does not need to be mapped to a llama model
            provider_resource_id = model.provider_resource_id
        else:
            provider_resource_id = self.get_provider_model_id(model.provider_resource_id)

        if provider_resource_id:
            model.provider_resource_id = provider_resource_id
        else:
            llama_model = model.metadata.get("llama_model")
            existing_llama_model = self.get_llama_model(model.provider_resource_id)
            if existing_llama_model:
                if existing_llama_model != llama_model:
                    raise ValueError(
                        f"Provider model id '{model.provider_resource_id}' is already registered to a different llama model: '{existing_llama_model}'"
                    )
            else:
                # not llama model
                if llama_model in ALL_HUGGINGFACE_REPOS_TO_MODEL_DESCRIPTOR:
                    self.provider_id_to_llama_model_map[model.provider_resource_id] = (
                        ALL_HUGGINGFACE_REPOS_TO_MODEL_DESCRIPTOR[llama_model]
                    )
                else:
                    self.alias_to_provider_id_map[model.provider_model_id] = model.provider_model_id
        return model
