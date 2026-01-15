import enum
import re
from dataclasses import asdict, dataclass

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from config import AIParametersConfig


class ChatAIException(Exception):
    pass


class Role(enum.Enum):
    assistant = "assistant"
    system = "system"
    user = "user"


@dataclass
class ChannelMemoryItem:
    text: str
    username: str | None
    role: Role

    def _clean_username_for_openai(self, username: str | None) -> str | None:
        return username.replace(" ", "_").replace("-", "_") if username else None

    def to_openai_type(self) -> ChatCompletionMessageParam:
        return {
            Role.system: ChatCompletionSystemMessageParam,
            Role.user: ChatCompletionUserMessageParam,
            Role.assistant: ChatCompletionAssistantMessageParam,
        }[self.role](
            content=[ChatCompletionContentPartTextParam(type="text", text=self.text)],
            role=self.role.value,
            name=self._clean_username_for_openai(self.username)
            if self.role != Role.system
            else None,
        )


class ChannelMemory:
    channel_id: str
    max_length: int

    system_prompts: list[ChannelMemoryItem]
    _messages: list[ChannelMemoryItem]

    def __init__(
        self,
        bot_name: str,
        channel_id: str,
        system_prompts: list[ChannelMemoryItem],
        messages: list[ChannelMemoryItem] | None = None,
        max_length: int = 50,
    ):
        self.bot_name = bot_name
        self.channel_id = channel_id
        self.max_length = max_length
        self.system_prompts = system_prompts
        self._messages = messages or []

    def append_message(self, message: ChannelMemoryItem) -> None:
        self._messages.append(message)
        if len(self._messages) > self.max_length:
            self._messages = self._messages[-self.max_length :]

    @property
    def messages(self) -> list[ChannelMemoryItem]:
        return self.system_prompts + self._messages

    def export_as_openai_type(
        self, condense: bool = False
    ) -> list[ChatCompletionMessageParam]:
        """
        Export the channel memory as a list of OpenAI chat completion message parameters.

        Args:
            condense (bool): Whether to condense the messages into a single message.

        Returns:
            list[ChatCompletionMessageParam]: The channel memory as a list of OpenAI chat completion message parameters.
        """
        if not condense:
            return [item.to_openai_type() for item in self.messages]

        user_messages: list[str] = []
        for message in self._messages:
            if message.username:
                user_messages.append(f"{message.username}: {message.text}")
            user_messages.append(message.text)

        compiled_message = "\n".join(user_messages) + f"\n{self.bot_name}"
        return [sp.to_openai_type() for sp in self.system_prompts] + [
            {"role": "user", "content": compiled_message}
        ]

    def clear(self) -> None:
        self._messages = []


class ChatAIHandler:
    _conversation_history: dict[str, ChannelMemory]
    _primary_system_prompts: list[ChannelMemoryItem]
    _ai_parameters: AIParametersConfig

    def __init__(
        self,
        bot_name: str,
        model_name: str,
        chat_history_length: int,
        ai_parameters: AIParametersConfig,
        initial_prompt: str | None = None,
        debug: bool = False,
    ):
        if not initial_prompt:
            initial_prompt = f"""
            Your name is {bot_name}. You are a chaotic Discord user in a private friend group.
            You speak casually, joke, riff, misremember things, and behave like a real
            person in a Discord channel. You are not an assistant. You are a participant.
            """

        self._bot_name = bot_name
        self._chat_history_length = chat_history_length

        self.clear_history(clear_all_channels=True)
        self.set_system_prompt(initial_prompt)

        self._model_name = model_name
        self._client = AsyncOpenAI()

        self._ai_parameters = ai_parameters
        self._debug = debug
        print(f"Starting ChatAI with ai_parameters: {asdict(self._ai_parameters)}")

    def _get_system_prompts(self, channel_id: str) -> list[ChannelMemoryItem]:
        return [
            *self._primary_system_prompts,
        ]

    def initialise_channel_history(
        self, channel_id: str, messages: list[ChannelMemoryItem] | None = None
    ) -> None:
        self._conversation_history[channel_id] = ChannelMemory(
            bot_name=self._bot_name,
            channel_id=channel_id,
            system_prompts=self._get_system_prompts(channel_id),
            messages=messages or [],
            max_length=self._chat_history_length,
        )

    def _append_channel_history(
        self,
        channel_id: str,
        role: Role,
        message: str,
        username: str | None = None,
    ) -> None:
        if not self._conversation_history.get(channel_id):
            self.initialise_channel_history(channel_id)

        self._conversation_history[channel_id].append_message(
            ChannelMemoryItem(role=role, text=message, username=username)
        )

    def set_system_prompt(self, text: str) -> None:
        self._primary_system_prompts = [
            ChannelMemoryItem(
                role=Role.system,
                username=None,
                text=text,
            ),
        ]

        for channel_id in self._conversation_history:
            self._conversation_history[
                channel_id
            ].system_prompts = self._get_system_prompts(channel_id)

    def clear_history(
        self, clear_all_channels: bool = False, channels: set[str] | None = None
    ) -> None:
        if clear_all_channels or not channels:
            self._conversation_history = {}
            return

        for channel in channels:
            self.initialise_channel_history(channel)

    def _clean_response(self, text: str) -> str:
        # Remove bot name and colon from response text (not always present but sometimes)
        pattern = rf"^{re.escape(self._bot_name)}\s*:\s*"
        return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    async def get_response(
        self,
        channel_id: str,
        message_text: str,
        reply_to_username: str | None = None,
        skip_history: bool = False,
        retry_attempt: int | None = None,
    ) -> str:
        if not retry_attempt:
            retry_attempt = 0

        try:
            if not skip_history:
                self._append_channel_history(
                    channel_id, Role.user, message_text, reply_to_username
                )
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=self._conversation_history[channel_id].export_as_openai_type(
                    condense=True
                ),
                max_completion_tokens=self._ai_parameters.max_tokens,
                response_format={"type": "text"},
                temperature=self._ai_parameters.temperature,
                top_p=self._ai_parameters.top_p,
                presence_penalty=self._ai_parameters.presence_penalty,
                frequency_penalty=self._ai_parameters.frequency_penalty,
            )

            response_text = self._clean_response(response.choices[0].message.content)
            if not response_text and retry_attempt < 3:
                # Retry generating a response 3 times
                return await self.get_response(
                    channel_id=channel_id,
                    message_text=message_text,
                    reply_to_username=reply_to_username,
                    skip_history=True,
                    retry_attempt=retry_attempt + 1,
                )
            elif retry_attempt == 3:
                # If all retries fail, return a default message
                response_text = (
                    "I have no thoughts on the matter (failed to generate a response)"
                )

            self._append_channel_history(channel_id, Role.assistant, response_text)
            if self._debug:
                response_text = f"DEBUG: {response_text}"

            return response_text
        except Exception as e:
            print(f"{__name__} get_response error: {e}")
            raise ChatAIException(f"error generating response: {e}")
