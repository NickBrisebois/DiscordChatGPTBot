from transformers import GPTNeoForCausalLM, GPT2Tokenizer, AutoTokenizer


class ChatAI:
    def __init__(self):
        ...

    def load_model(self):
        self._model = GPTNeoForCausalLM.from_pretrained("EleutherAI/gpt-neo-1.3B")
        self._tokenizer = GPT2Tokenizer.from_pretrained("EleutherAI/gpt-neo-1.3B")
        print("loaded model")

    def get_response(self, user_id: int, input_text: str) -> str:
        print(f"getting response for input {input_text}")
        split_input_text = input_text.split("<@764569134792048660>")
        if len(split_input_text) > 1:
            input_text = split_input_text[1]
        else:
            input_text = split_input_text[0]
        input_text = (
            f"I am Shrek from the hit anime Shrek the third. I will reply to every question as if "
            f"the person asking the question is named donkey. "
            f"I am now responding to the following "
            f"question: '{input_text}' My response is:"
        )
        # input_text = (
        #     "[Name='Shrek']\n"
        #     "[Traits='snarky, hates donkey']\n"
        #     f"Respond to the following question: '{input_text}\n"
        #     "My response is:"
        # )
        input_ids = self._tokenizer.encode(
            input_text,
            return_tensors="pt",
            max_length=150,
            truncation=True,
            return_overflowing_tokens=True,
        )
        output = self._model.generate(
            inputs=input_ids, num_beams=1, max_length=150, no_repeat_ngram_size=2
        )
        decoded_output = self._tokenizer.decode(output[0], skip_special_tokens=True)
        split_text = decoded_output.split(input_text)
        return split_text[1] if len(split_text) > 1 else split_text[0]
