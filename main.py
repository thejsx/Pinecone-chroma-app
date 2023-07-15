import re
import os
import PyPDF2
import streamlit as st
import upload_split
import splitter_funcs
import pinecone_funcs 
import random
from langchain.docstore.document import Document
import chroma_funcs
import shutil
import screenshot_text


# Default values
add_pdf_docs = False
make_new_index = False
add_pdf_image = False
pinecone_index = None

query, chroma_query, doc_return, chromadb, pinecone_checkbox, chromadb_checkbox, doc_dir, image_dir, pinecone_index, text, pinecone_newindex_input, pinecone_index_input = None, None, [], None, False, False, None, None, None, None, None, None
directory = 'C:\\Users\\jrsch\\Documents\Visual Studio Code\\Langchain Pinecone ChromaDB\\.venv\\chroma_indices'
folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory,f))]

with st.sidebar.form(key='new_form'):
    if chromadb_checkbox == False:
        pinecone_checkbox = st.sidebar.checkbox('Use Pinecone?', value=False)
    if pinecone_checkbox == False:
        chromadb_checkbox = st.sidebar.checkbox('Use Chromadb?', value=False)

    if pinecone_checkbox == True:
        new_query = None
        embeddings, indices = pinecone_funcs.pinecone_setup()
        if st.sidebar.checkbox('Add/modify pinecone indices?'):
            if st.sidebar.checkbox('Add PDF Docs from folder?', value=False):
                doc_dir_input = st.sidebar.text_input('Specify path for new pdf docs', 'C:\\Users\\jrsch\\Desktop\\Pinecone files\\PDF text')
            if st.sidebar.checkbox('Add PDF images from folder?', value=False):
                img_dir_input = st.sidebar.text_input('Specify path for pdf images', 'C:\\Users\\jrsch\\Desktop\\Pinecone files\\PDF images')
            add_index = st.sidebar.checkbox('Add to existing Pinecone index?', value = False)
            if add_index == True:
                if len(indices) >0:
                    pinecone_index_input = st.sidebar.selectbox('Select Pinecone index',indices)
                else:
                    pinecone_newindex_input = st.sidebar.text_input('Previous index not found, enter a new index name')
            else:
                pinecone_newindex_input = st.sidebar.text_input('Enter a Pinecone index name (if previous index present, it will be deleted)')
            if pinecone_index_input and st.sidebar.button('Enter'):
                # Use the values from the input fields
                doc_dir = doc_dir_input
                image_dir = img_dir_input
                if pinecone_newindex_input:
                    pinecone_funcs.pinecone_make_new_index(True, pinecone_newindex_input)
                    pinecone_index = pinecone_newindex_input
                else:
                    pinecone_index = pinecone_index_input


    if chromadb_checkbox == True:
        add_index = st.sidebar.checkbox('Add documents?', value=False)
        if add_index == False:
            delete_index = st.sidebar.checkbox('Delete chromadb indices?', value = False)
        else:
            delete_index = False
            st.session_state.button_clicked = False
            uploaded_file = st.sidebar.file_uploader("Upload PDF file", type=['pdf'])

            if uploaded_file is not None:
                if st.sidebar.checkbox('Split on chunks? (Default = split on pages)', value=False):
                    chunk_size = st.sidebar.number_input('Chunk size for splits', value = 1000)
                    overlap = st.sidebar.number_input('Character overlap for splits',value=100)
                else:
                    chunk_size, overlap = 0,0
                if st.sidebar.checkbox('Use prior index?', value = False):
                    if len(folders) > 0:
                        chroma_index = st.sidebar.selectbox("Select the chroma index", folders)
                    else:
                        chroma_index = st.sidebar.text_input('No prior index found, type a new index name')
                else:
                    chroma_index = st.sidebar.text_input('Type a new index name')
                image = st.sidebar.checkbox('Is this pdf an image?', value = False)
                if chroma_index and st.sidebar.button('Extract and split text'):
                    st.session_state.button_clicked = True

            if st.session_state.button_clicked == True:
                if image == True:
                    st.sidebar.write(f'Extracting text image..')
                    pdf_text = upload_split.image_pdf_convertor([],uploaded_file,None, None)
                    if chunk_size != 0:
                        st.sidebar.write(f'Concatenating and resplitting for chunks..')
                        split_text,metadata = splitter_funcs.file_split_appender(full_text_dict = {uploaded_file.name:'/n'.join(pdf_text)}, chunk_size=chunk_size,overlap=overlap)
                    else:
                        metadata = splitter_funcs.metadata_builder(uploaded_file.name,pdf_text,divsor='Page')
                        split_text = pdf_text
                else:
                    st.sidebar.write(f'Extracting text document..')
                    if chunk_size != 0:
                        pdf_text = splitter_funcs.extract_text_from_pdf(uploaded_file)
                        pdf_text = pdf_text.replace('\n',' ')
                    else:
                        pdf_text = splitter_funcs.extract_text_bypage_pdf(uploaded_file)
                    st.sidebar.write(f'Splitting text..')
                    split_text,metadata = splitter_funcs.file_split_appender(full_text_dict = {uploaded_file.name:pdf_text}, chunk_size=chunk_size,overlap=overlap)
                
                st.sidebar.write(f'The text has been split into {len(split_text)}', 'chunks' if chunk_size != 0 else 'pages')
                try:
                    chroma_funcs.add_chroma_docs(chroma_index, split_text, metadata)
                    st.sidebar.write(f'Splits of document {uploaded_file.name} successfully added to index {chroma_index}')
                except Exception as e:
                    st.sidebar.write(f'There was an error loading the docs into the index:\n{e}')
                    
        if delete_index == True:
            delete_index = st.sidebar.selectbox("Select the chroma index to delete", folders)
            if delete_index:
                if st.sidebar.button('Delete'):
                    try:
                        shutil.rmtree(os.path.join(directory,delete_index))
                        st.sidebar.write(f"Directory: {delete_index} has been removed successfully")
                    except OSError as e:
                        st.sidebar.write(f"Error: {e.strerror}")

st.title("App to query your documents")
num_docs = st.slider('Number of documents splits to retrieve', 1, 5, 1)
num_tokens = st.number_input('Maximum tokens to use for GPT response', value=200)

if 'key' not in st.session_state:
        st.session_state['key'] = 'key' + str(random.randint(0, 1000000))
st.session_state['query'] = False

st.session_state.query_entered = False

if pinecone_checkbox == True and (pinecone_index != None or len(indices) >0):
    if doc_dir != None or image_dir != None:
        split_text, metadata = upload_split.get_split_pdf_ppt(doc_dir, image_dir)
    else:
        split_text, metadata = None, None
    if pinecone_index == None:
        pinecone_index = st.selectbox('Select a pinecone index to search', indices)

    if pinecone_index != None:
        print('The pinecone index is', pinecone_index)
        doc_store = pinecone_funcs.pinecone_index_build_add(pinecone_index, embeddings, split_text, metadata)
        if doc_store:
            new_query = st.text_input(f'Enter questions for Pinecone index {pinecone_index} or use screenshot tool below')
            button_sent = st.button('Submit')
            if button_sent:
                st.session_state['query'] = True
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                box_height = st.text_input('Input screenshot box height', value = 450)
            with col2:
                box_width = st.text_input('Input screenshot box width', value=1100)
            with col3:
                screen_size = st.selectbox('Input screen monitor size', ['1366x768', '1920x1080', '1536x864', '1440x900', '1280x720', '1600x900', '1280x800', '1280x1024', '1024x768', '768x1024'], index = 1)
                screen_width = screen_size[:screen_size.index('x')]
                screen_height = screen_size[screen_size.index('x')+1:]
            with col4:
                st.write('')
                if st.button('Click to screenshot main screen and input text'):
                    text = screenshot_text.screenshot_text(box_height=int(box_height), box_width=int(box_width), screen_height=int(screen_height), screen_width=int(screen_width))
                    new_query = text
            if text is not None:
                st.write('The query is:', new_query)
            # goes in text_input, second argument to refresh: key=st.session_state['key']
            if new_query and st.session_state['query']:
                query = new_query
                # st.session_state['key'] = 'key' + str(random.randint(0, 1000000))
                doc_return = pinecone_funcs.pinecone_query_docs(query, doc_store, num_docs)
    
if chromadb_checkbox == True:
    chroma_index = st.selectbox("Select the folder/index to query", folders)
    if chroma_index:
        new_query = st.text_input('Enter your query for these documents')
        button_sent = st.button('Submit')
        if button_sent:
            st.session_state['query'] = True
        if new_query and st.session_state['query']:
            query = new_query
            doc_return = chroma_funcs.query_chroma(chroma_index, query, num_docs)

cols = st.columns(len(doc_return)+1)

st.markdown(
    """
    <style>
    .block-container.css-1y4p8pa.e1g8pov64 {
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

for i in range(len(doc_return)):
    with cols[i]:
        st.write(f'Document {i+1}')
        if query:
            st.write(doc_return[i].metadata['document']+' --- '+doc_return[i].metadata['Chunk'])
            st.write(doc_return[i].page_content)

with cols[len(doc_return)]:
    if query:
        st.write('This is the response from GPT:')
        st.write('\n\n')
        gpt_response = pinecone_funcs.query_openAI_withdocs(query if query else chroma_query, doc_return, num_tokens)
        st.write(gpt_response)
