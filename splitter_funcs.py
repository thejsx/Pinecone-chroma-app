import PyPDF2

def paragraph_reducer(text):
  textcopy= text
  indmod = 0
  for ind, val in enumerate(textcopy):
    if val == '\n':
      if ind < len(textcopy)-1 and textcopy[ind+1] == '\n':
        if ind > len(textcopy)-11:
          text = text[:ind+indmod] + text[ind+1+indmod:]
          indmod -= 1
        elif 'Question ' in textcopy[ind+1:ind+11]:
          continue
        else:
          text = text[:ind+indmod] + text[ind+1+indmod:]
          indmod -= 1
  return text

def extract_text_from_pdf(pdf_file):
  text = []
  if isinstance(pdf_file,str) == True:
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
          page = pdf_reader.pages[page_num]
          text.append(page.extract_text())
        return "\n".join(text)
  else:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text.append(page.extract_text())
    return "\n".join(text)

def extract_text_bypage_pdf(pdf_file):
  text = []
  if isinstance(pdf_file,str) == True:
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text.append(page.extract_text())  
        return  text
  else:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text.append(page.extract_text())
    return text

def my_text_splitter(text, chunk_size = 1000, overlap = 0, split_on = None):
  if overlap/chunk_size > 0.8:
    return print(f'Overlap of {overlap} is too large for the chunk size of {chunk_size}.')
  if overlap > 0:
    split_on = ' '
  else:
    split_on = split_on or '\n'
  split_text, prior_split, n = [], 0, 0
  splits = int(len(text)/chunk_size)

  while True:
    new_text, prior_ind, ind = None, 0, 0
    point = prior_split + chunk_size - (0 if n == 0 else overlap)

    while n > 0 and overlap > 0:
      if text[prior_split - overlap + prior_ind] ==  split_on:
        prior_split = prior_split - overlap + prior_ind
        break
      elif text[prior_split - overlap - prior_ind] ==  split_on:
        prior_split = prior_split - overlap - prior_ind
        break
      else:
        prior_ind += 1

    while ind < chunk_size and point  < len(text):
      if text[min(point + ind,len(text)-1)] == split_on:
        new_text = text[prior_split:point + ind]
        split_text.append(new_text)
        prior_split = point + ind
        break
      elif text[max(point-ind,prior_split)] == split_on and ind <= chunk_size * 0.8:
        new_text = text[prior_split:point-ind]
        split_text.append(new_text)
        prior_split = point - ind
        break
      else:
        ind += 1

    if new_text == None:
      if point >= len(text)-1:
        split_text.append(text[prior_split:])
        return split_text
      elif split_on in text[point:]:
        split_text.append(text[prior_split:text[point:].index(split_on) + point])
        prior_split = text[point:].index(split_on) + point
      else:
        split_text.append(text[prior_split:])
        return split_text
      prior_split = point
    n += 1

def metadata_builder(path,splits, divisor = 'Chunk'):
  metadata = []
  if '/' in path:
    path = path[path.rfind('/')+1:]
  elif "\\" in path:
    path = path[path.rfind('\\')+1:]
  for n in range(splits):
    metadata.append({'document':path, 'Chunk':f'{divisor} {n+1} of {splits}'})
  return metadata

def file_split_appender(full_text_dict={}, pdf_name_list=[], chunk_size = 1000, overlap = 0, split_on = None, metadata_divisor = 'Chunk'):
  split_text, metadata = [], []
  if len(full_text_dict) > 0:
    for key, text in full_text_dict.items():
      print('Text is',key)
      print(type(text))
      if type(text) == str:
        new_splits = my_text_splitter(text,chunk_size=chunk_size, overlap = overlap, split_on = split_on)
      else:
        metadata_divisor = "Page"
        new_splits = text
      print('len of new splits are:', len(new_splits), 'text lens are:', [len(x) for x in new_splits])
      new_meta = metadata_builder(key, len(new_splits),metadata_divisor)
      split_text = split_text + new_splits
      metadata = metadata + new_meta
      print('concatenated len is:',len(split_text))
  if len(pdf_name_list) > 0:
    for name in pdf_name_list:
      print('extracting',name)
      text = extract_text_from_pdf(name)
      new_splits = my_text_splitter(text, chunk_size =  chunk_size, overlap = overlap, split_on = split_on)
      print('len of new splits are:', len(new_splits), 'text lens are:', [len(x) for x in new_splits])
      new_meta = metadata_builder(name, len(new_splits))
      split_text = split_text + new_splits
      metadata = metadata + new_meta
      print('concatenated len is:',len(split_text))
  return split_text, metadata



# split_text = file_split_appender(pdf_name_list = list(uploaded.keys()), chunk_size =1500, overlap = 200, split_on = '\n')
# print([len(x) for x in split_text])
# split_docs = [Document(page_content=x) for x in split_text]


# print(len(split_text))
# print(split_docs)

