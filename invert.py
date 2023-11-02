from stemmer import PorterStemmer
from collections import defaultdict
import time
import sys

FILENAME = "cacm.all"
#STOPWORDS_FILENAME = "stopwords.txt"
STOPWORDS_FILENAME = "common_words"
DICTIONARY_FILENAME = "dictionary.txt"
POSTINGS_FILENAME = "postings.txt"

class Document:
  def __init__(self, doc, stopwords_on, stemming_on) -> None:
    self.stopwords_on = stopwords_on
    self.stemming_on = stemming_on
    self.doc = doc
    self.id  = None
    self.starting_line = None
    self.title = None
    self.full_title = ""
    self.abstract = None
    self.publication_date = None
    self.author_list = None
    self.terms_list = []
    self.frequency_list = []
    self.get_document_sections()
    self.get_document_terms()
    self.get_full_title()
    if self.stopwords_on:
      self.remove_stopwords_from_terms_list()
    self.terms_only = self.get_terms_only() 
    self.terms_list = self.parse_list(self.terms_list) # combine terms
    
  def get_document_sections(self):
    """Groups sections of a document into sublists."""
    section_dividers = [".I", ".B", ".T", ".W", ".A", ".X", ".N"]
    return_list = []
    sublist = []
    for line in self.doc:
      if line[0][0:2] in section_dividers:
        return_list.append(sublist)
        sublist = [line]
      else:
        sublist.append(line)
    return_list.append(sublist)
    for item in return_list[1:]:
      if item[0][0][:2] == ".I":
        self.id = item[0][0][3:]
        self.starting_line = item[0][1]
      if item[0][0] == ".T" and len(item) > 1:
        self.title = item[1:]
      if item[0][0] == ".W":
        self.abstract = item[1:]
      if item[0][0] == ".B":
        self.publication_date = item[1]
      if item[0][0] == ".A":
        self.author_list = item[1:]
      
  def get_document_terms(self):
    porter_stemmer = PorterStemmer()
    count = 1
    if self.title:
      for line in self.title:
        for word in line[0].split():
          word = "".join(char for char in word if char.isalnum()) # remove non-alphanumeric characters
          word = word.lower()
          if self.stemming_on:
            word = porter_stemmer.stem(word, 0, len(word) - 1)
          self.terms_list.append((word, count))
          count += 1
    if self.abstract:
      for line in self.abstract:
        for word in line[0].split():
          word = "".join(char for char in word if char.isalnum()) # remove non-alphanumeric characters
          word = word.lower()
          if self.stemming_on:
            word = porter_stemmer.stem(word, 0, len(word) - 1)
          self.terms_list.append((word, count))
          count += 1

  def get_full_title(self):
    if self.title and len(self.title) > 1:
      full_title = ""
      for line in self.title:
        full_title = full_title + line[0]
      self.full_title = full_title.lstrip()
    elif self.title and len(self.title) == 1:
      self.full_title = self.title[0][0].lstrip()
    else:
      self.full_title = ""

  def remove_stopwords_from_terms_list(self):
    with open(STOPWORDS_FILENAME, "r") as fp:
      data = fp.readlines() 
    stopwords = [line.rstrip('\n').lower() for line in data]
    for term in self.terms_list:
      if term[0] in stopwords:
        self.terms_list.remove(term)


  def parse_list(self, lst):
      hm = defaultdict(list)
      for word, line_number in lst:
          hm[word].append(line_number)
      return {word: sorted(line_numbers) for word, line_numbers in hm.items()}
  
  def get_terms_only(self):
    return_list = []
    for k,v in self.terms_list:
      return_list.append(k)
    return return_list

class InvertedIndex:
  def __init__(self, FILENAME, stopwords_on: bool, stemming_on: bool):
    self.dict = self.read_lines_from_file(FILENAME)
    self.doc_collection = self.collect_documents(self.dict)
    self.doc_list = [Document(doc, stopwords_on, stemming_on) for doc in self.doc_collection]
    self.doc_list_to_invert = [(Document(doc, stopwords_on, stemming_on).terms_list, Document(doc, stopwords_on, stemming_on).id) for doc in self.doc_collection]
    self.inverted_index = self.invert()
    if stopwords_on:
      self.remove_stopwords()

  def invert(self) -> {Document:[int]}:
    hm = defaultdict(list)
    for word_indices, doc_id in self.doc_list_to_invert:
      for word, _ in word_indices.items():
        hm[word].append(doc_id)
    
    hm = {k:sorted(v) for k, v in hm.items()}
    return {k:v for k,v in sorted(hm.items())}
  
  def remove_stopwords(self) -> None:
    with open(STOPWORDS_FILENAME, "r") as fp:
      data = fp.readlines() 
    stopwords = [line.rstrip('\n').lower() for line in data]
    for stopword in stopwords:
      if self.inverted_index.get(stopword):
        self.inverted_index.pop(stopword)

  def read_lines_from_file(self, file) -> [(str, int)]:
    """Reads file and returns the contents line-by-line as a list of tuples in the form (line, line_number)."""
    with open(file, 'r') as fp:
      data = fp.readlines()
    return_list = []
    line_number = 1
    for line in data:
      line_info = (line.rstrip('\n'), line_number)
      return_list.append(line_info)
      line_number += 1
    return return_list

  def collect_documents(self, list) -> [str]:
    """Collects lines associated with the same document into sublists of a larger list."""
    return_list = []
    sublist = []
    for line in list:
      if line[0][0:2] == ".I":
        # documents start with .I
        # if we find a line that starts with .I, then append the sublist to  return_list and start new sublist
        return_list.append(sublist)
        sublist = [line]
      else:
        sublist.append(line)
    # append anything left over in sublist 
    return_list.append(sublist)
    # remove first empty list
    return return_list[1:]

class LookupSystem:
  def __init__(self, FILENAME, stopwords_on, stemming_on) -> None:
    self.index = InvertedIndex(FILENAME, stopwords_on, stemming_on)
    self.create_dictionary_file(DICTIONARY_FILENAME)
    self.create_postings_file(POSTINGS_FILENAME)
    self.total_query_time = 0
    self.number_of_queries = 0
    self.average_query_time = 0
  
  def lookup(self, term) -> None:
    start_time = time.time()
    if self.index.inverted_index.get(term):
      doc_ids = self.index.inverted_index.get(term)
      for doc_id in doc_ids:
        doc = self.index.doc_list[int(doc_id) - 1] # index will be doc.id - 1
        line_numbers = doc.terms_list.get(term)
        term_frequency = len(line_numbers)
        print()
        print(f"Term: {term}")
        print(f"Document ID: {doc.id}")
        print(f"Title: {doc.full_title}")
        print(f"Frequency: {term_frequency}")
        print("Occurs in position(s):")
        print(", ".join(str(num) for num in line_numbers))
        print()
      print(f"{term} occurs in {len(doc_ids)} document(s).")
    else:
      print("Term not found.")
      print()
    end_time = time.time()
    query_time = end_time - start_time
    self.total_query_time += query_time
    self.number_of_queries += 1
    self.average_query_time = self.total_query_time / self.number_of_queries
    print(f"Query took {query_time} seconds.")
    print()

  def create_dictionary_file(self, filename) -> None:
    """
    Each entry in the dictionary should include a term and its document frequency. 
    You should use a proper data structure to build the dictionary (e.g. hashmap or search tree or others). 
    The structure should be easy for random lookup and insertion of new terms. All the terms should be sorted in alphabetical order. 
    """
    
    with open(DICTIONARY_FILENAME, "w") as file:
      for term, doc_ids in self.index.inverted_index.items():
        file.write(f"Term: {term}\n")
        file.write(f"Document frequency: {len(doc_ids)}\n")

  def create_postings_file(self, filename) -> None:
    """
    Postings list for each term should include postings for all documents the term occurs in (in the order of document ID), 
    and the information saved in a posting includes document ID, term frequency in the document, 
    and positions of all occurrences of the term in the document. 
    There is a one-to-one correspondence between the term in the dictionary file and its postings list in the postings lists file.
    """
    with open(POSTINGS_FILENAME, "w") as file:
      for term, doc_ids in self.index.inverted_index.items():
        file.write(f"Term: {term}\n")
        for doc_id in doc_ids:
          doc = self.index.doc_list[int(doc_id) - 1] # index will be doc.id - 1
          line_numbers = doc.terms_list.get(term)
          term_frequency = len(line_numbers)
          file.write(f"Document ID: {doc_id}\n")
          file.write(f"Frequency: {term_frequency}\n")
          file.write(f"Position(s): {', '.join(str(num) for num in line_numbers)}\n")

if __name__ == '__main__':
  if len(sys.argv) != 4:
    print("Incorrect usage.")
    print("Command uses the format: python3 invert.py {FILENAME} {STEMMING} {STOPWORDS}.")
    print("The flags for STEMMING and STOPWORDS should be passed as 0 for off, or 1 for on.")
  if sys.argv[2] == '0':
    STEMMING_FLAG = False 
  if sys.argv[3] == '0':
    STOPWORDS_FLAG = False 
  FILENAME = sys.argv[1]
  lookup_system = LookupSystem(FILENAME)
  print("Welcome to my inverted index term lookup system.")  
  print("Enter 'ZZEND' to exit the program.")
  print("Please enter a term below:")
  print()
  inp = ""
  porter_stemmer = PorterStemmer()
  while inp != "ZZEND":
    if inp != "":
      inp = inp.lower()
      if STEMMING_FLAG:
        inp = porter_stemmer.stem(inp, 0 , len(inp) - 1)
      lookup_system.lookup(inp)
    inp = input()
  print(f"Average query time is: {lookup_system.average_query_time} seconds.")