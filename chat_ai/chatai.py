import enum
from dataclasses import asdict, dataclass, field

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

MAX_TOKENS = 500


class ChatAIException(Exception):
    pass


class Role(enum.Enum):
    assistant = "assistant"
    system = "system"
    user = "user"


@dataclass
class AIParameters:
    temperature: float = field(default=0.75)
    top_p: float = field(default=0.9)
    frequency_penalty: float = field(default=0.7)
    presence_penalty: float = field(default=0.4)


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
            name=self._clean_username_for_openai(self.username),
        )


class ChannelMemory:
    channel_id: str
    max_length: int

    system_prompts: list[ChannelMemoryItem]
    _messages: list[ChannelMemoryItem]

    def __init__(
        self,
        channel_id: str,
        system_prompts: list[ChannelMemoryItem],
        messages: list[ChannelMemoryItem] | None = None,
        max_length: int = 50,
    ):
        self.channel_id = channel_id
        self.max_length = max_length
        self.system_prompts = system_prompts
        self._messages = messages or []

    def append_message(self, message: ChannelMemoryItem) -> None:
        self._messages.append(message)
        if len(self._messages) > self.max_length:
            self._messages.pop(0)

    @property
    def messages(self) -> list[ChannelMemoryItem]:
        return self._messages + self.system_prompts

    def export_as_openai_type(self) -> list[ChatCompletionMessageParam]:
        return [item.to_openai_type() for item in self.messages]

    def clear(self) -> None:
        self._messages = []


class ChatAI:
    _conversation_history: dict[str, ChannelMemory]
    _primary_system_prompts: list[ChannelMemoryItem]
    _ai_parameters: AIParameters

    def __init__(
        self,
        bot_name: str,
        model_name: str,
        chat_history_length: int,
        initial_prompt: str | None = None,
        ai_parameters: AIParameters = AIParameters(),
        debug: bool = False,
    ):
        if not initial_prompt:
            initial_prompt = (
                f"Your name is {bot_name}. Reply directly to the most recent user message."
                "Stay on topic unless the user explicitly asks for randomness."
                "Use casual Discord tone and humor when appropriate."
                "Do not ignore the user's question."
            )

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
                username=self._bot_name,
                text=text,
            ),
            # ChannelMemoryItem(
            #     role=Role.system,
            #     username=self._bot_name,
            #     text=(
            #         "If you notice that you are repeating the same response or wording, you MUST change your "
            #         "answer, add new information, or acknowledge the repetition explicitly."
            #     ),
            # ),
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

    async def get_response(
        self, channel_id: str, message_text: str, reply_to_username: str | None = None
    ) -> str:
        try:
            self._append_channel_history(
                channel_id, Role.user, message_text, reply_to_username
            )
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=self._conversation_history[channel_id].export_as_openai_type(),
                max_completion_tokens=MAX_TOKENS,
                response_format={"type": "text"},
                **asdict(self._ai_parameters),
            )

            response_text = (
                response.choices[0].message.content
                or f"I, sir {self._bot_name}, could not generate a response"
            )

            self._append_channel_history(channel_id, Role.assistant, response_text)
            if self._debug:
                response_text = f"DEBUG: {response_text}"

            return response_text
        except Exception as e:
            print(f"{__name__} get_response error: {e}")
            raise ChatAIException(f"error generating response: {e}")
