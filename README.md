#### بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيْمِ

# PyQt5 PDF Chatbot - OFFLINE and SECURE

This desktop app is built upon the [privateGPT](https://github.com/imartinez/privateGPT) and [Ollama](https://ollama.com/). I have created custom model named pdfLlama2. How to create custom LLM: [More info](/pdfLlama2/README.md)

I have tried to write maintainable and readible code with Adapter design pattern. I have encapsulated the main app to 3 sub classes. I used "Adapter" to allow each class talk to each other.

### Setup

Set up a virtual environment (optional) or conda environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```shell
pip install -r requirements.txt
```

#### Note: Ollama must be installed in your system. Make sure you have downloaded llama2:latest, llama2-uncensored:latest. Do not forget to modify the code to use other models in runtime [Change main.py at 197 line](./main.py)

## DEMO
![alt text](/screenshots/image.png)

