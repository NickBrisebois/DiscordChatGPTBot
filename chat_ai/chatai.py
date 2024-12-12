from typing import Any, Dict, List
from openai import AsyncOpenAI

CHAT_HISTORY_LENGTH = 50


class ChatAI:
    _conversation_history = {}

    def __init__(self):
        self._system_prompt = {
            "role": "system",
            "content": "You are a chat bot named Lez",
        }
        self._client = AsyncOpenAI()
        self.clear_history(clear_all=True)

    def set_system_prompt(self, text: str):
        self._system_prompt = {"role": "system", "content": text}
        self.clear_history(clear_all=True)

    def clear_history(self, clear_all: bool = False, channels: List[str] | None = None):
        if clear_all:
            self._conversation_history = {}
            return

        for channel in channels:
            self._conversation_history[channel] = [self._system_prompt]

    def _append_history(self, channel_id: str, message: Dict[str, Any] = {}) -> None:
        if not self._conversation_history.get(channel_id):
            self._conversation_history[channel_id] = []

        self._conversation_history[channel_id].append(message)

    async def get_response(self, channel_id: str, input_text: str) -> str:
        self._append_history(channel_id=channel_id, message={"role": "user", "content": input_text})

        response = await self._client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:biglez-nochatgptresponses:AI6fDiMi",
            messages=self._conversation_history[channel_id],
            max_tokens=500,
        )

        response_text = response.choices[0].message.content

        self._append_history(channel_id=channel_id, message={"role": "assistant", "content": response_text})

        if len(self._conversation_history[channel_id]) > CHAT_HISTORY_LENGTH:
            self._conversation_history[channel_id].pop(0)
            self._conversation_history[channel_id][0] = self._system_prompt

        return response_text

    async def get_training_data_response(self, input_text: str) -> str:
        response = await self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        """
I'm going to give you a random instant messenger chat message and you will make a guess at what the previous message was. Do NOT write anything other than the previous message. Do not write things like 'this seems like', just give the previous message. I don't care if your guess is wrong, I only want the previous message.
"""
                    ),
                },
                {"role": "user", "content": input_text},
            ],
        )
        return response.choices[0].message.content
