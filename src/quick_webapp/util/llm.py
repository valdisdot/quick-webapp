from abc import ABC, abstractmethod
from typing import Iterator, Any
from collections.abc import Iterable, Mapping
import requests
import json
from genson import SchemaBuilder
from io import StringIO

class LLMClientException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class Content:
    """
    Chat content data class.
    """

    def __init__(self, type: str, content: str):
        if type and type in ("text", "image"): self.__type: str = type
        else: raise LLMClientException(f"Message type {'is null' if not type else ('is unknown: ' + type)}")

        if content and len(content.strip()) > 0: self.__content: str = content
        else: raise LLMClientException(f"Message content is {'null' if not content else 'blank'}")

    @property
    def type(self) -> str:
        """
        Returns content type: "text" or "image".
        """

        return self.__type

    @property
    def content(self) -> str:
        """
        Returns char content.
        """

        return self.__content

class Message:
    """
    Chat message data class.
    """

    def __init__(self, role: str, content: Content | list[Content], reasoning_content: str | None = None):
        if role and role in ("user", "assistant"): self.__role: str = role
        else: raise LLMClientException(f"Message role {'is null' if not role else ('is unknown: ' + role)}")

        self.__content: list[Content] = []

        if isinstance(content, list):
            for _content in content:
                if isinstance(_content, Content): self.__content.append(_content)
                else: raise LLMClientException("One of the content elements is not a Content")
        elif isinstance(content, Content): self.__content.append(content)
        else: raise LLMClientException("Content is neither a Content or a list of Content")

        self.__reasoning_content: str | None = reasoning_content

    @property
    def role(self) -> str:
        """
        Returns content type: "user" or "assistant".
        """

        return self.__role
    
    @property
    def content(self) -> Iterator[Content]:
        """
        Returns content iterator of the message.
        """

        return iter(self.__content)
    
    @property
    def reasoning_content(self) -> str | None:
        """
        Returns reasoning content if present.
        """

        return self.__reasoning_content
    
    def has_reasoning_content(self) -> bool:
        """
        Checks if reasoning content is present.
        """

        return self.__reasoning_content is not None

class JsonSchema:
    """
    Helper class to build json_schema for the chat that is build on the base example user provides in the constructor.
    """

    def __init__(self, name: str, base_example: dict[str, Any], top_level_required_fields: list[str] | str | None = None):
        self.__name = name
        builder = SchemaBuilder()
        builder.add_object(base_example)
        self.__schema = builder.to_schema()
        self.__schema["type"] = "object"
        self.__schema["additionalProperties"] = False

        if top_level_required_fields:
            if isinstance(top_level_required_fields, str):
                self.__schema["required"] = [top_level_required_fields]
            elif isinstance(top_level_required_fields, Iterable):
                self.__schema["required"] = list(top_level_required_fields)

    @property
    def name(self) -> str:
        """
        Returns json_schema name.
        """

        return self.__name

    @property
    def schema(self) -> dict[str, Any]:
        """
        Returns the json schema dict.
        """

        return self.__schema

class Chat:
    """
    Chat data class.
    """

    def __init__(self, system_prompt: str | None = None, show_reasoning: bool = True, json_schema: JsonSchema | None = None):
        self.__system_prompt = system_prompt
        self.__show_reasoning = show_reasoning if show_reasoning is not None else False
        self.__json_schema = json_schema
        self.__messages = []
        self.__interrupted = False
    
    @property
    def system_prompt(self) -> str | None:
        """
        Returns system prompt.
        """

        return self.__system_prompt
    
    @property
    def show_reasoning(self) -> bool:
        """
        Returns seting if the reasoning must be shown.
        """

        return self.__show_reasoning

    @property
    def json_schema(self) -> JsonSchema | None:
        """
        Returns json schema object.
        """

        return self.__json_schema
    
    @property
    def messages(self) -> Iterator[Message]:
        """
        Returns the iterator of the chat messages.
        """

        return iter(self.__messages)
    
    def has_messages(self) -> bool:
        """
        Checks if the chat contains any messages.
        """

        return len(self.__messages) > 0
    
    def add_message(self, message: Message):
        """
        Add a message to the chat.
        """

        if message: self.__messages.append(message)
        else: raise LLMClientException("Message is null")

    @property
    def interrupted(self) -> bool:
        """
        Checks if last message was interrupted.
        """

        return self.__interrupted
    
    @interrupted.setter
    def interrupted(self, interrupted: bool):
        """
        Sets the flag that last message was interrupted.
        """

        self.__interrupted = bool(interrupted)

class LLMClient(ABC):
    """
    Abstract OpenAI compatible LLM client.
    """

    __chat_id_c = 0

    def __init__(self):
        self.__chats: dict[int, Chat] = {}
        self.__chatless: list[Chat] = []
    
    def create_chat(self, system_prompt: str | None = None, show_reasoning: bool = True, json_schema: JsonSchema | None = None) -> int: 
        """
        Initializes a chat holder where system prompt and messages will be stored.
        Returns a chat id to be used in prompt(...) method.
        """

        LLMClient.__chat_id_c += 1
        chat_id = LLMClient.__chat_id_c
        
        self.__chats[chat_id] = Chat(system_prompt, show_reasoning, json_schema)
        return chat_id

    def prompt(self, content: Any | list[Any], chat_id: int | None = None) -> Iterator[str]: 
        """
        Performs a prompt to LLM with content(s). If no chat_id is provided, the message will be simply sent stateless.
        Retuns a line strings stream (an iterator) that LLM returns, in a simple text way:

            <if present>        Reasoning:
            <if present>        [tokens from reasoning]
            /n/n
            <always present>    [tokens from final response]
        """

        if content is None or not (isinstance(content, (str, Iterable)) and not isinstance(content, Mapping)): 
            raise LLMClientException("Unsupported content type")
        elif not self.ping(): raise LLMClientException("LLM client is not available")
        else:
            chat: Chat | None = None
            support_images = self.support_images()

            if chat_id and chat_id in self.__chats: 
                chat = self.__chats[chat_id]
            else:
                chat = Chat()
                self.__chatless.append(chat)

            chat.interrupted = False
            new_content: list[Content] = []

            if isinstance(content, str): 
                content = str(content)
                if content.startswith("data:image"): 
                    if support_images: new_content.append(Content("image", content))
                    else: raise LLMClientException("Client (model) does not support images")
                else: new_content.append(Content("text", content))
            else:
                for content_element in content:
                    content_element = str(content_element)
                    if content_element.startswith("data:image"): 
                        if support_images: new_content.append(Content("image", content_element))
                        else: raise LLMClientException("Client (model) does not support images")
                    else: new_content.append(Content("text", content_element))
            
            send_messages = list(chat.messages)
            new_message = Message("user", new_content)
            send_messages.append(new_message)
            
            reasoning_tokens = []
            response_tokens = []
            has_yield_reasoning = False
            has_response_title = False

            for interrupt_identity, token_type, token in self._prompt(send_messages, chat.system_prompt, chat.json_schema):
                if chat.interrupted: 
                    self._interrupt(interrupt_identity)
                    return
                
                if "reasoning" == token_type:
                    reasoning_tokens.append(token)
                    if chat.show_reasoning:
                        yield token
                    elif not has_yield_reasoning:
                        yield "Reasoning...\n"
                    has_yield_reasoning = True
                elif "response" == token_type:
                    response_tokens.append(token)
                    if not has_response_title and has_yield_reasoning: 
                        yield "\nResponse:\n"
                        has_response_title = True
                    yield token
            
            yield "\n"

            if len(reasoning_tokens) > 0 or len(response_tokens) > 0: 
                response_content = "".join(response_tokens)
                reasoning_content = "".join(reasoning_tokens)
                chat.add_message(new_message)
                chat.add_message(Message("assistant", Content("text", response_content), reasoning_content if len(reasoning_content.strip()) > 0 else None))

    def prompt_and_wait(self, content: Any | list[Any], chat_id: int | None = None) -> str:
        """
        Wrapper around prompt(...) that collect all response from its iterator and return the response.
        """

        buf = StringIO()
        for part in self.prompt(content, chat_id):
            buf.write(part)
        return buf.getvalue()

    def interrupt(self, chat_id: int | None = None): 
        """
        Interrupts LLM's response generation by chat_id. Current user message and partitional generated content won't be saved if running.
        If no chat_id is provided, interrupts all current response generations.
        """
        
        if (chat_id):
            if chat_id in self.__chats: self.__chats[chat_id].interrupted = True
        else:
            for chat in self.__chats.values():
                chat.interrupted = True
            for chat in self.__chatless:
                chat.interrupted = True

    @abstractmethod
    def support_images(self) -> bool:
        """
        Flags if LLM support accepting images (vision)
        """

        pass

    @abstractmethod
    def ping(self) -> bool: 
        """
        Pings the LLM availability.
        """
        
        pass
    
    @abstractmethod
    def _prompt(self, messages: list[Message], system_prompt: str | None = None, json_schema: JsonSchema = None) -> Iterator[tuple[Any, str, str]]: 
        """
        Performs the actual prompt to LLM.
        Returns an object that is used for underlying generation interruption and actual generated values iterator, first for reasoning, other for a final response.
        For internal usage (inheritance).
        """
        
        pass

    @abstractmethod
    def _interrupt(self, identity: Any):
        """
        Interrupts the actual underlying generation.
        For internal usage (inheritance).

        """
        pass

class OpenAICompatibleClient(LLMClient): 
    __request_id = 0

    def __init__(self, api_key: str, host: str, port: int | None = None):
        super().__init__()
        self.__url = host + f"{(':' + str(port)) if port else ''}"
        self.__api_key = api_key
        self.__requests = {}
    
    def support_images(self) -> bool:
        properties_object = requests.get(url=f"{self.__url}/props", headers={"Authorization": f"Bearer {self.__api_key}"}).json();
        return properties_object.get("modalities") and properties_object.get("modalities").get("vision") == True

    def ping(self) -> bool: 
        response = requests.get(
            url=f"{self.__url}/models",
            headers={"Authorization": f"Bearer {self.__api_key}"},
            timeout=30,
        )
        return response.status_code == 200
    
    def _prompt(self, messages: list[Message], system_prompt: str | None = None, json_schema: JsonSchema = None) -> Iterator[tuple[Any, str, str]]: 
        OpenAICompatibleClient.__request_id += 1
        interrupt_identity = OpenAICompatibleClient.__request_id
        self.__requests[interrupt_identity] = True

        payload = {
                "stream": True,
                "return_progress": True,
                "reasoning_format": "auto",
                "backend_sampling": False,
                "timings_per_token": True,
                "messages": []
        }

        if system_prompt: 
            payload["messages"].append({"role": "system", "content": system_prompt})

        if json_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": json_schema.name,
                    "schema": json_schema.schema,
                }
            }
            
        for message in messages:
            message_object = {"role": message.role, "content": []}
            if message.has_reasoning_content(): message_object["reasoning_content"] = message.reasoning_content


            for content in message.content:
                if content.type == "image":
                    message_object["content"].append({"type": "image_url", "image_url": {"url": content.content}})
                else:
                    message_object["content"].append({"type": "text", "text": content.content})

            payload["messages"].append(message_object)

        response = requests.post(url=f"{self.__url}/v1/chat/completions", headers={"Authorization": f"Bearer {self.__api_key}", "Content-Type": "application/json"}, data=json.dumps(payload), stream=True)
        if response.status_code != 200: raise LLMClientException("Server finished response with code: " + response.status_code)

        for line in response.iter_lines(decode_unicode=True):
            if interrupt_identity not in self.__requests: 
                response.close()
                return
            if line:
                line = str(line).removeprefix("data: ")
                for choice in json.loads(line)["choices"]:
                    if choice["finish_reason"] == "stop": 
                        del self.__requests[interrupt_identity]
                        response.close()
                        return
                    
                    if "reasoning_content" in choice["delta"]: yield (interrupt_identity, "reasoning", choice["delta"]["reasoning_content"])
                    elif "content" in choice["delta"] and choice["delta"]["content"]: yield (interrupt_identity, "response", choice["delta"]["content"])

    def _interrupt(self, identity: Any):
        if (identity and identity in self.__requests): del self.__requests[identity]
        else: raise LLMClientException("Interruption identity is null or not present")

class OpenAIClient(LLMClient):
    __request_id = 0

    def __init__(self, model: str, api_key: str):
        super().__init__()
        self.__model = model
        self.__api_key = api_key
        self.__base_url = "https://api.openai.com/v1"
        self.__requests: dict[int, bool] = {}

    def __headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.__api_key}",
            "Content-Type": "application/json",
        }

    def support_images(self) -> bool:
        model_name = self.__model.lower()

        # OpenAI multimodal model families.
        vision_prefixes = (
            "gpt-5.6",
            "gpt-5.5",
            "gpt-5.4",
            "gpt-5.3",
            "gpt-5.2",
            "gpt-5.1",
            "gpt-5",
            "gpt-4.1",
            "gpt-4o",
            "o1",
            "o3",
            "o4",
        )

        return model_name.startswith(vision_prefixes)

    def ping(self) -> bool:
        response = requests.get(
            url=f"{self.__base_url}/models/{self.__model}",
            headers=self.__headers(),
            timeout=30,
        )
        return response.status_code == 200

    def _prompt(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        json_schema: JsonSchema | None = None
    ) -> Iterator[tuple[Any, str, str]]:
        OpenAIClient.__request_id += 1
        interrupt_identity = OpenAIClient.__request_id
        self.__requests[interrupt_identity] = True

        payload: dict[str, Any] = {
            "model": self.__model,
            "stream": True,
            "messages": [],
        }

        if system_prompt:
            payload["messages"].append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        if json_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": json_schema.name,
                    "schema": json_schema.schema,
                }
            }

        for message in messages:
            message_object: dict[str, Any] = {
                "role": message.role,
                "content": [],
            }

            for content in message.content:
                if content.type == "image":
                    message_object["content"].append(
                        {
                            "type": "image_url",
                            "image_url": {"url": content.content},
                        }
                    )
                else:
                    message_object["content"].append(
                        {
                            "type": "text",
                            "text": content.content,
                        }
                    )

            payload["messages"].append(message_object)

        response = requests.post(
            url=f"{self.__base_url}/chat/completions",
            headers=self.__headers(),
            data=json.dumps(payload),
            stream=True,
            timeout=300,
        )

        if response.status_code != 200:
            try:
                error_payload = response.json()

            except Exception:
                error_payload = response.text

            response.close()
            raise LLMClientException(
                f"Server finished response with code: {response.status_code}; "
                f"details: {error_payload}"
            )

        try:
            for line in response.iter_lines(decode_unicode=True):
                if interrupt_identity not in self.__requests:
                    response.close()
                    return

                if not line:
                    continue

                line = str(line).removeprefix("data: ").strip()

                if line == "[DONE]":
                    if interrupt_identity in self.__requests:
                        del self.__requests[interrupt_identity]
                    response.close()
                    return

                chunk = json.loads(line)

                for choice in chunk.get("choices", []):
                    finish_reason = choice.get("finish_reason")
                    if finish_reason == "stop":
                        if interrupt_identity in self.__requests:
                            del self.__requests[interrupt_identity]
                        response.close()
                        return

                    delta = choice.get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield (interrupt_identity, "response", content)

                    refusal = delta.get("refusal")
                    if refusal:
                        yield (interrupt_identity, "response", refusal)

        finally:
            if interrupt_identity in self.__requests:
                del self.__requests[interrupt_identity]
            response.close()

    def _interrupt(self, identity: Any):
        if identity and identity in self.__requests:
            del self.__requests[identity]
        else:
            raise LLMClientException("Interruption identity is null or not present")
    