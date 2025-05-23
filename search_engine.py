import json
import sys
from nltk.stem import PorterStemmer

def get_term_id(input):
    out = set()
    
    tokens = input.split()
    porter_stemmer = PorterStemmer()
    stemmed_tokens = [porter_stemmer.stem(token) for token in tokens]
    
    with open("./terms.dict", "r", encoding="utf-8") as f:
        terms = json.load(f)
        
    for token in stemmed_tokens:
        out.add(terms.get(token))
        
    return out
    
def get_doc_id_from_term_ids(ids):
    out = []
    
    with open("./index.json", "r", encoding="utf-8") as f:
        index = json.load(f)
        
    for id in ids:
        out.append(index.get(str(id)))
        
    return out
          
def binary_and(inputs):
    if len(inputs) == 1:
        return inputs[0]

    result = inputs[0]

    for k in range(1, len(inputs)):
        new_result = []
        i = 0
        j = 0
        
        list1 = result
        list2 = inputs[k]

        while i < len(list1) and j < len(list2):
            doc_id_1 = list1[i][0]
            doc_id_2 = list2[j][0]
            tf_1 = list1[i][1]
            tf_2 = list2[j][1]

            if doc_id_1 == doc_id_2:
                new_result.append([doc_id_1, tf_1 + tf_2])  # or [doc1, tf1, tf2] if needed
                i += 1
                j += 1
            elif doc_id_1 < doc_id_2:
                i += 1
            else:
                j += 1

        result = new_result  # Continue with result from this round

        if not result:
            break  # early exit if nothing in common

    return result
        
def get_doc_urls_from_ids(ids):
    out = []

    with open("./docs.dict", "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    ids.sort(key=lambda x: x[1], reverse=True)


    for doc_id, _, in ids[:5]:
        out.append(docs.get(str(doc_id)))
        
    return out

if __name__ == "__main__":
    print("Search Engine:")
    
    while True:
        search = input("Search term: ")
        ids = get_term_id(search)
        doc_ids = get_doc_id_from_term_ids(ids)
        intersect = binary_and(doc_ids)
        doc_urls = get_doc_urls_from_ids(intersect)
        for url in doc_urls:
            print(url)
    