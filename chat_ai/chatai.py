from openai import AsyncOpenAI

CHAT_HISTORY_LENGTH = 50


class ChatAI:
    def __init__(self):
        self._system_prompt = {
            "role": "system",
            "content": "You are a chat bot named Lez",
        }
        self._client = AsyncOpenAI()
        self.clear_history()

    def set_system_prompt(self, text: str):
        self._system_prompt = {"role": "system", "content": text}
        self.clear_history()

    def clear_history(self):
        self._conversation_history = [self._system_prompt]

    async def get_response(self, user_id: int, input_text: str) -> str:
        self._conversation_history.append({"role": "user", "content": input_text})
        response = await self._client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:biglez-nochatgptresponses:AI6fDiMi",
            messages=self._conversation_history,
            max_tokens=500,
        )
        response_text = response.choices[0].message.content
        self._conversation_history.append(
            {"role": "assistant", "content": response_text}
        )

        if len(self._conversation_history) > CHAT_HISTORY_LENGTH:
            self._conversation_history.pop(0)
            self._conversation_history[0] = self._system_prompt

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
