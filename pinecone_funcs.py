from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import UnstructuredPDFLoader, OnlinePDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.vectorstores import Chroma, Pinecone
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback
import pinecone
from langchain.llms import OpenAI
from langchain import VectorDBQA
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
import os
import streamlit as st
import time

load_dotenv()
Pinecone_API_Key = os.getenv('PINECONE_API_KEY')
OpenAI_API_Key = os.getenv('OPENAI_API_KEY')

# Set variables for OpenAI and Pinecone
def pinecone_setup():
  embeddings = OpenAIEmbeddings(openai_api_key=OpenAI_API_Key)
  pinecone.init(
      api_key= Pinecone_API_Key,
      environment = "asia-northeast1-gcp")
  indices = pinecone.list_indexes()
  return embeddings, indices

def pinecone_make_new_index(new, index):
  output_placeholder = st.sidebar.empty()
  if new == True:
    if index in pinecone.list_indexes():
      output_placeholder.text('Deleting old index of same name..')
      pinecone.delete_index(index)
      output_placeholder.text('Recreating index..')
      pinecone.create_index(index, dimension = 1536, metric = "cosine")
      output_placeholder.text('Index created..')
    else:
      try:
        output_placeholder.write(index, "No index of that name present, creating index..")
        pinecone.create_index(index, dimension = 1536, metric = "cosine")
        output_placeholder.text('Index successfully created')
      except:
        output_placeholder.text('Could not create index')
        output_placeholder = st.sidebar.empty()
        output_placeholder.text("Deleting old indices..")
        for index_name in pinecone.list_indexes():
          pinecone.delete_index(index_name)
        output_placeholder.write(f'Trying again to create index..{index}')
        pinecone.create_index(index, dimension = 1536, metric = "cosine")
        output_placeholder.text('Index created')
          

# Rebuild and create, or create new pinecone index (dont run if adding to existing index)
def pinecone_index_build_add(index, embeddings, split_text=None, metadata=None):
  output_placeholder = st.sidebar.empty()
  if split_text != None:
    output_placeholder.text('Adding text and metadata to index..')
    count, doc_store = 1, None
    while not doc_store and count != 5:
      try:
        doc_store = Pinecone.from_texts(split_text, embeddings, index_name=index, metadatas=metadata)
        output_placeholder.text('Text successfully added to index')
      except:
        output_placeholder.write(f'Trying again in 20 seconds, count {count} of 5')
        time.sleep(20)
        doc_store = Pinecone.from_texts(split_text, embeddings, index_name=index, metadatas=metadata)
        count += 1
  else:
    doc_store = Pinecone.from_existing_index(index, embeddings)
    if doc_store == None:
      output_placeholder.text('Need to add docs to index before use')
  return doc_store


# Add docs to existing pinecone index
def pinecone_add(index, embeddings, split_text, metadata):
  if index not in pinecone.list_indexes():
    raise Exception('That index does not exist in pinecone. If you want to create a new index with that name (replacing any current index), use pinecone_create_recreate() first.')
  
  doc_store = Pinecone.from_texts(split_text,embeddings, index_name=index, metadatas=metadata)
  return doc_store

def pinecone_query_docs(query, doc_store, num_docs_returned):
  doc_return = doc_store.similarity_search(query, k=num_docs_returned)
  return doc_return

def query_openAI_withdocs(query, doc_return, num_tokens):
  llm = ChatOpenAI(temperature = 0, openai_api_key = OpenAI_API_Key, model_name = 'gpt-4', max_tokens = num_tokens)
  chain = load_qa_chain(llm, chain_type = "stuff")
  return chain.run(input_documents = doc_return, question = f'Using the context of the provided documents, answer the following question: {query}')

# query = 'What is the nature of trade'
# index = 'econ-6341-test'
# embeddings = pinecone_setup()
# doc_store = pinecone_index_build_add(index, embeddings, False, None)
# doc_return = pinecone_query_docs(query, doc_store, 1)

# gpt_response = query_openAI_withdocs(query, doc_return)
# print(gpt_response)