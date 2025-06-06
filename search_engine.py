import re
import time
import mmap
import psutil # used to check memory usage
import os
from nltk.stem import PorterStemmer

def get_term_id(input, terms_file):
    out = set()
    
    tokens = re.findall(r"\w+", input.lower())
    filtered = [token for token in tokens if token.isalnum() and token.isascii()]

    porter_stemmer = PorterStemmer()
    stemmed_tokens = [porter_stemmer.stem(token) for token in filtered]
    
    for token in stemmed_tokens:
        tid = terms_file.get(token)
        if tid is not None:
            out.add(tid)
        
    return out
    
def get_doc_id_from_term_ids(term_ids, toc, mm):
    out = []

    for tid in term_ids:
        if tid is None:
            continue
        
        offset = toc[tid]
        mm.seek(offset)
        line = mm.readline().decode("utf-8").strip()

        _, postings_str = line.split(":", 1)
        postings = [list(map(float, pair.split(","))) for pair in postings_str.strip().split()]
        out.append(postings)
        
    return out
          
def binary_and(inputs):
    if len(inputs) == 1:
        return inputs[0]
    
    inputs.sort(key=len) 

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
                new_result.append([doc_id_1, tf_1 + tf_2]) 
                i += 1
                j += 1
            elif doc_id_1 < doc_id_2:
                i += 1
            else:
                j += 1

        result = new_result  

        if not result:
            break 

    return result
        
def get_doc_urls_from_ids(ids, docs):
    out = []
    
    if len(ids) == 0:
        return []
        
    ids.sort(key=lambda x: x[1], reverse=True)

    for doc_id, _, in ids[:5]:
        out.append(docs[doc_id])
        
    return out

def get_memory_usage_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024**2  # in MB

def load_term_map(path):
    term_map = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            term, tid = line.strip().split("\t")
            term_map[term] = int(tid)
    return term_map

def load_doc_map(path):
    doc_map = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            doc_id, url = line.strip().split("\t", 1)
            doc_map[int(doc_id)] = url
    return doc_map

def load_toc(path):
    toc = {}
    with open(path, "r") as f:
        for line in f:
            tid, offset = line.strip().split("\t")
            toc[int(tid)] = int(offset)
    return toc

if __name__ == "__main__":

    terms = load_term_map("terms.txt")
    docs = load_doc_map("docs.txt")
    toc = load_toc("mmap.txt")
    
    index_file = open("index.txt", "r+b")
    index_mmap = mmap.mmap(index_file.fileno(), 0, access=mmap.ACCESS_READ)
    
    print("Search Engine:")
    
    while True:
        search = input("Search term: ")
        start = time.time()
        ids = get_term_id(search, terms)
        
        if not ids:
            print("No documents found containing those terms.\n")
            continue
        
        t1 = time.time()
        doc_ids = get_doc_id_from_term_ids(ids, toc, index_mmap)
        
        if not any(doc_ids):
            print("No documents found containing those terms.\n")
            continue

        t2 = time.time()
        intersect = binary_and(doc_ids)
        
        if not intersect:
            print("No documents found containing those terms.")
            continue
        
        t3 = time.time()
        doc_urls = get_doc_urls_from_ids(intersect, docs)
        
        t4 = time.time()

        print("\nResults:")
        for url in doc_urls:
            print(url)

        print("\nBenchmark Timing (in seconds):")
        print(f"get_term_id:             {t1 - start:.4f}")
        print(f"get_doc_id_from_term_ids:{t2 - t1:.4f}")
        print(f"binary_and:              {t3 - t2:.4f}")
        print(f"get_doc_urls_from_ids:   {t4 - t3:.4f}")
        print(f"Total:                   {t4 - start:.4f}\n")
        
        process = psutil.Process(os.getpid())
        print(f"Memory usage: {get_memory_usage_mb():.2f} MB")
