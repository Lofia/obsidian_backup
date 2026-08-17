- Model structure:
```python
MODEL_NAME = "distilbert/distilbert-base-uncased"
LABEL_NAMES = ["World", "Sports", "Business", "Sci/Tech"]

def main():
    raw = load_from_disk(...)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_batch(examples):
        return tokenizer(
            examples['text'],
            truncation = True,
            max_length = ...
        )

    tokenized_data = raw.map(tokenize_batch, batched = True)

    data_collactor = DataCollatorWithPadding(tokenizer = tokenizer)

    id2label = { index: name for index, name in enumerate(LABEL_NAMES)}
    label2id = {...}
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, 
        num_labels = 4, 
        id2label = id2label, 
        label2id = label2id)

    accuracy_metric = evaluate.load('accuracy')
    f1_metric = evaluate.load('f1')

    def metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis = -1)
        accuracy = accuracy_metric.compute(
            predictions,
            references = labels)['accuracy']
        macro_f1 = f1_metric.compute(
            predictions,
            references = labels,
            average = 'macro')['f1']
        return {accuracy, macro_f1}

    training_args = TrainingArguments(...)

    trainer = Trainer(
        model,
        args = training_args, 
               train_dataset = tokenized_data['train'], 
               eval_dataset = tokenized_data['validation'],
               compute_metrics = metrics,
               processing_class = tokenizer,
               data_collactor = data_collactor)

    train_result = trainer.train()

    test_metrics = trainer.evaluate(
        tokenized_data['test'],
        metric_key_prefix = 'test'
    )
    print(test_metrics)

if __name__ == '__main__':
    main()
```

- Set $v(x)\propto$ token length

| Model               | Train n | Test Accuracy | Test Macro-F1 |
| ------------------- | ------: | ------------: | ------------: |
| Original baseline   |    2000 |        0.9100 |        0.9097 |
| Same-size unshifted |    1956 |        0.9088 |        0.9087 |
| Shifted unweighted  |    1956 |        0.9100 |        0.9097 |
| Shifted + oracle IW |    1956 |               |               |

- change to $v(x)\propto\text{margin}(T)$ 

| Model               | Train n | Test Accuracy | Test Macro-F1 |
| ------------------- | ------: | ------------: | ------------: |
| Original baseline   |    2000 |        0.9100 |        0.9097 |
| Same-size unshifted |    1956 |        0.9075 |        0.9072 |
| Shifted unweighted  |    1956 |        0.9162 |        0.9158 |
| Shifted + oracle IW |    1956 |               |               |

- change to $v(x)\propto1-\text{margin}(T)$ 

| Model               | Train n | Test Accuracy | Test Macro-F1 |
| ------------------- | ------: | ------------: | ------------: |
| Original baseline   |    2000 |        0.9100 |        0.9097 |
| Same-size unshifted |    1936 |        0.9000 |        0.8994 |
| Shifted unweighted  |    1936 |        0.8963 |        0.8963 |
| Shifted + oracle IW |    1936 |        0.9125 |        0.9119 |

| Seed | Control F1 | Shifted F1 | Oracle F1 |
| ---: | ---------: | ---------: | --------: |
|    1 |            |     0.9007 |    0.8958 |
|    2 |            |     0.8984 |    0.9021 |
|    3 |            |     0.9010 |    0.9011 |
|    4 |            |     0.9002 |    0.9015 |
|    5 |            |     0.8983 |    0.9021 |
| Mean |            |            |           |
|   SD |            |            |           |

- freeze loaded encoder

| Model                   | Encoder | Weight   | Validation Macro-F1 | Test Macro-F1 |
| ----------------------- | ------- | -------- | ------------------: | ------------: |
| Frozen control          | Frozen  | none     |              0.8866 |        0.8901 |
| Frozen shifted          | Frozen  | none     |              0.8770 |        0.8923 |
| Frozen shifted + Oracle | Frozen  | true (w) |              0.8839 |        0.8897 |

- change to $v(x)\propto P(\text{Business}|T)$ <- indeed how?

| Model            | Val Loss | Val F1 | Test Loss | Test Accuracy | Test F1 |
| ---------------- | -------: | -----: | --------: | ------------: | ------: |
| Frozen control   |    0.378 |  0.877 |     0.342 |         0.886 |   0.886 |
| Frozen shifted   |    0.369 |  0.887 |     0.332 |         0.893 |   0.892 |
| Frozen Oracle IW |    0.365 |  0.885 |     0.329 |         0.890 |   0.890 |

| Method     | Target Loss | Accuracy | Macro-F1 |
| ---------- | ----------: | -------: | -------: |
| Unweighted |             |          |          |
| Oracle     |             |          |          |
| Your IW    |             |          |          |
| uLSIF      |             |          |          |