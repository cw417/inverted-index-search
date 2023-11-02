import sys
from invert import LookupSystem
from stemmer import PorterStemmer

#FILENAME = "testfile.txt"
FILENAME = "cacm.all"
#STOPWORDS_FILENAME = "stopwords.txt"
STOPWORDS_FILENAME = "common_words"

if __name__ == '__main__':
  stopwords_on = True if sys.argv[1] == "1" else False
  stemming_on = True if sys.argv[2] == "1" else False
  print("Welcome to my inverted index term lookup system.")  
  print("Enter 'ZZEND' to exit the program.")
  print("Please wait while the index is created.")
  lookup_system = LookupSystem('cacm.all', stopwords_on, stemming_on)
  print("Please enter a term below to search the index:")
  print()
  inp = ""
  porter_stemmer = PorterStemmer()
  while inp != "ZZEND":
    if inp != "":
      inp = inp.lower()
      if stemming_on:
        inp = porter_stemmer.stem(inp, 0 , len(inp) - 1)
      lookup_system.lookup(inp)
    inp = input()
  print(f"Average query time is: {lookup_system.average_query_time} seconds.")