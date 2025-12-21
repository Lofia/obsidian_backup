Sebastian Raschka
https://github.com/rasbt/LLMs-from-scratch/tree/main?tab=readme-ov-file

## Token Embedding
Use a vector to represent a word/token, with its position in the context. The linear mappings (ignore the softmax function) from token to vector are trainable.
![](Pasted%20image%2020251221215946.png)

## Attention Mechanism
Find the context vector for each word/token, using the query/key/value separation model, where each of the linear mappings within the model is trainable.
![](Pasted%20image%2020251221220040.png)
Overall code: ![](multihead-attention.pdf)