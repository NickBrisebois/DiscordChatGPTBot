import asyncio
import json

from openai import RateLimitError
from chat_ai.chatai import ChatAI

BATCH_SIZE = 2


async def get_message(chat_ai: ChatAI, line: str):
    out = await chat_ai.get_training_data_response(line)
    return line, out


def get_output(prompt: str, line: str) -> dict:
    output = {}
    output["messages"] = [
        {
            "role": "system",
            "content": "You are a chat bot"
        },
        {
            "role": "user",
            "content": prompt,
        },
        {
            "role": "assistant",
            "content": line
        }
    ]
    return output


async def main():
    chat_ai = ChatAI()
    with open("dump-el-general-chat.csv") as fp, open("output.jsonl", mode="a+") as out:
        index = 0

        batch_index = 0
        lines = []
        for line in fp:
            if index < 65323:
                index += 1
                continue

            if len(line) < 10 or len(line) > 600:
                print(f"skipping line {line} for being too short or too long (len {len(line)})")
                index += 1
                continue

            if line == "\n":
                index += 1
                continue

            line = line.replace("\n", "")

            lines.append(line)
            batch_index += 1

            if batch_index == BATCH_SIZE:

                tasks = []
                async with asyncio.TaskGroup() as tg:
                    for batch_line in lines:
                        tasks.append(tg.create_task(get_message(chat_ai=chat_ai, line=batch_line)))

                output_lines = []
                for task in tasks:
                    result = task.result()
                    print(f"Writing prompt {result[1]} for line {result[0]}")
                    output_lines.append(
                        json.dumps(get_output(prompt=result[1], line=result[0])) + "\n"
                    )
                out.writelines(output_lines)
                out.flush()
                batch_index = 0
                lines = []
                print("sleeping for 1 second")
                await asyncio.sleep(1)
                print("done sleeping")

            index += 1
            print("Index: " + str(index))


if __name__ == "__main__":
    asyncio.run(main())
