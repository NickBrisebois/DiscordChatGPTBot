import enum

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


class ChatAI:
    _conversation_history: dict[str, list[ChatCompletionMessageParam]]

    def __init__(
        self,
        bot_name: str,
        model_name: str,
        chat_history_length: int,
        initial_prompt: str | None = None,
    ):
        if not initial_prompt:
            initial_prompt = (
                f"You are a Discord chat bot with the name: {bot_name}, trained on a private friend group's chat history."
                "Your personality is casual, sarcastic, and sometimes chaotic, but generally helpful."
                "You speak like a human in a group chat on Discord. If you are missing information, you may request "
                "tools using <SEARCH: query>. Only do this when it would genuinely help."
            )

        self._bot_name = bot_name
        self._conversation_history = {}
        self._chat_history_length = chat_history_length

        self.clear_history(clear_all_channels=True)
        self.set_system_prompt(initial_prompt)

        self._model_name = model_name
        self._client = AsyncOpenAI()

    def _initialise_channel_history(self, channel_id: str) -> None:
        self._conversation_history[channel_id] = [
            self._system_prompt,
            ChatCompletionSystemMessageParam(
                role=Role.system.value,
                content=[
                    ChatCompletionContentPartTextParam(
                        type="text",
                        text=f"You are speaking in the Discord channel named {channel_id}",
                    ),
                ],
            ),
        ]

    def _append_channel_history(
        self, channel_id: str, role: Role, message: str
    ) -> None:
        if not self._conversation_history.get(channel_id):
            self._initialise_channel_history(channel_id)

        self._conversation_history[channel_id].append(
            {
                Role.system: ChatCompletionSystemMessageParam,
                Role.user: ChatCompletionUserMessageParam,
                Role.assistant: ChatCompletionAssistantMessageParam,
            }[role](
                role=role.value,
                content=[ChatCompletionContentPartTextParam(type="text", text=message)],
            )
        )

    def set_system_prompt(self, text: str) -> None:
        self._system_prompt = ChatCompletionSystemMessageParam(
            role=Role.system.value,
            content=[ChatCompletionContentPartTextParam(type="text", text=text)],
        )
        self.clear_history(clear_all_channels=True)

    def clear_history(
        self, clear_all_channels: bool = False, channels: set[str] | None = None
    ) -> None:
        if clear_all_channels or not channels:
            self._conversation_history = {}
            return

        for channel in channels:
            self._initialise_channel_history(channel)

    async def get_response(self, channel_id: str, message_text: str) -> str:
        try:
            self._append_channel_history(channel_id, Role.user, message_text)
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=self._conversation_history[channel_id],
                max_completion_tokens=MAX_TOKENS,
                temperature=0.6,
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.1,
                response_format={"type": "text"},
            )

            response_text = (
                response.choices[0].message.content
                or f"I, sir {self._bot_name}, could not generate a response"
            )

            if len(self._conversation_history[channel_id]) > self._chat_history_length:
                self._conversation_history[channel_id].pop(0)
                self._conversation_history[channel_id][0] = self._system_prompt

            self._append_channel_history(channel_id, Role.assistant, response_text)
            return response_text
        except Exception as e:
            print(f"{__name__} get_response error: {e}")
            raise ChatAIException(f"error generating response: {e}")
