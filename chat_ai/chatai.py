import enum
from typing import List
from openai import AsyncOpenAI

CHAT_HISTORY_LENGTH = 50
MAX_TOKENS = 500

class Role(enum.Enum):
    assistant = "assistant"
    system = "system"
    user = "user"


class ChatAI:
    _conversation_history = {}

    def __init__(self, bot_name: str, model_name: str):
        self._bot_name = bot_name
        self._system_prompt = {
            "role": "system",
            "content": f"You are a chat bot named {self._bot_name}",
        }
        self._model_name = model_name
        self._client = AsyncOpenAI()
        self.clear_history(clear_all=True)

    def set_system_prompt(self, text: str):
        self._system_prompt = {"role": Role.system.value, "content": text}
        self.clear_history(clear_all=True)

    def clear_history(self, clear_all: bool = False, channels: List[str] | None = None):
        if clear_all:
            self._conversation_history = {}
            return

        for channel in channels:
            self._conversation_history[channel] = [self._system_prompt]

    def append_history(self, channel_id: str, role: Role, message: str) -> None:
        if not self._conversation_history.get(channel_id):
            self._conversation_history[channel_id] = []

        openai_message = {"role": role.value, "content": message}
        self._conversation_history[channel_id].append(openai_message)

    async def get_response(self, channel_id: str, input_text: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=self._conversation_history[channel_id],
            max_tokens=MAX_TOKENS,
        )

        response_text = response.choices[0].message.content

        if len(self._conversation_history[channel_id]) > CHAT_HISTORY_LENGTH:
            self._conversation_history[channel_id].pop(0)
            self._conversation_history[channel_id][0] = self._system_prompt

        return response_text
