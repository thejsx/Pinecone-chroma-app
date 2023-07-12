import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
from langchain.prompts import PromptTemplate
from langchain.chat_models.openai import ChatOpenAI
import shutil

## Chroma embeddings, creates a file (persist_directory) to store embeddings, texts have to be documents

load_dotenv()
OpenAI_API_Key = os.getenv('OPENAI_API_KEY')
embeddings = OpenAIEmbeddings(openai_api_key=OpenAI_API_Key)

def add_chroma_docs(persist_directory, split_text, metadata):

  client_settings = chromadb.config.Settings(
    chroma_db_impl="duckdb+parquet", 
    persist_directory = f'./tmp/chroma_indices/{persist_directory}', 
    anonymized_telemetry = False)
  vector_store = Chroma(
    collection_name="langchain", 
    embedding_function= embeddings, 
    client_settings= client_settings, 
    persist_directory= f'.venv\\chroma_indices\\{persist_directory}')
  vector_store.add_texts(texts=split_text, metadatas=metadata, embedding=embeddings)
  vector_store.persist()

## from Chroma embedding, prompt:
def query_chroma(persist_directory, query, num_docs):
  client_settings = chromadb.config.Settings(
    chroma_db_impl="duckdb+parquet", 
    persist_directory = f'./tmp/chroma_indices/{persist_directory}', 
    anonymized_telemetry = False)
  vector_store = Chroma(
    collection_name="langchain", 
    embedding_function=embeddings, 
    client_settings=client_settings, 
    persist_directory= f'./tmp/chroma_indices/{persist_directory}')
  print(vector_store)
  docs = vector_store.similarity_search(query=query, k=num_docs)
  print(docs)
  return docs

# result = query_chroma('chromadb', 'What are some striking similarities between the technocrats’ treatment of students and treatment of the poor.')
# print(result)
