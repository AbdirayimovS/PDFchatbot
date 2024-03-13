# How to create custom Ollama model

1. `ollama pull llama2:latest` 
    Create a Modelfile. Check my example here [Modelfile](./Modelfile)


2. `ollama create custom_model_name -f Modelfile`
3. `ollama run custom_model_name`


Tutorials: 
- https://github.com/ollama/ollama
- https://github.com/ollama/ollama/blob/main/docs/modelfile.md