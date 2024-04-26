import numpy as np
import evaluate
from transformers import (
    TrainingArguments,
    Trainer,
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
from datasets import load_dataset


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)


if __name__ == "__main__":
    dataset = load_dataset(
        "csv",
        data_files={"train": "el-general.csv", "test": "el-general.csv"},
        column_names=["prompt", "text", "rejected_text"]
    )

    model = AutoModelForSequenceClassification.from_pretrained("bigscience/bloom-1b7")
    tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-1b7", add_prefix_space=True)

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            return_tensors="pt",
            padding="max_length",
            max_length=512,
            add_special_tokens=True,
            truncation=True,
            return_attention_mask=True
        )

    tokenized_datasets = dataset.map(tokenize_function, batched=True, batch_size=1000)
    small_train_dataset = (
        tokenized_datasets["train"].shuffle(seed=42).select(range(1000))
    )
    small_eval_dataset = (
        tokenized_datasets["test"].shuffle(seed=42).select(range(1000))
    )

    training_args = TrainingArguments(
        output_dir="test_trainer", evaluation_strategy="epoch"
    )
    metric = evaluate.load("accuracy")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=small_train_dataset,
        eval_dataset=small_eval_dataset,
        compute_metrics=compute_metrics,
    )
    print("training")
    trainer.train()
