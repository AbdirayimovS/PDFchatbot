from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import Ollama
import chromadb
import os
import argparse
import time



# For embeddings model, the example uses a sentence-transformers model
# https://www.sbert.net/docs/pretrained_models.html 
# "The all-mpnet-base-v2 model provides the best quality, while all-MiniLM-L6-v2 is 5 times faster and still offers good quality."
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
persist_directory = os.environ.get("PERSIST_DIRECTORY", "db")
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS',4))

from constants import CHROMA_SETTINGS

class ChatBotCompositor:
    def __init__(nafs, model_name):
        try:
            nafs.model = os.environ.get("MODEL", model_name)
        except Exception as e:
            print("No model is detected!", e)
        else:
            # default model
            nafs.model = os.environ.get("MODEL", "llama2:13b")
        finally:
            nafs.embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
            nafs.db = Chroma(persist_directory=persist_directory, embedding_function=nafs.embeddings)
            nafs.retriever = nafs.db.as_retriever(search_kwargs={"k": target_source_chunks})
            
            nafs.callbacks = [StreamingStdOutCallbackHandler()]
            nafs.llm = Ollama(model=nafs.model, callbacks=nafs.callbacks)
            nafs.qa = RetrievalQA.from_chain_type(llm=nafs.llm, 
                                                chain_type="stuff", 
                                                retriever=nafs.retriever, 
                                                return_source_documents=True)

    def __call__(nafs, query):
        try:
            result = nafs.qa(query)
        except Exception as e:
            print(e)
            answer = ""
            docs = ""
            raise ValueError("ERROR")
        else:
            answer, docs = result['result'], result['source_documents']
        finally:
            return (answer, docs)


