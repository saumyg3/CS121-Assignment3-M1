import os
import re
import json
import sys
import math
import heapq

from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import defaultdict, Counter

def extract_tokens(text) -> list:
    unprocessed_tokens = re.findall(r"\w+", text.lower())
    filtered = [token for token in unprocessed_tokens if token.isalnum() and token.isascii()]
    porter_stemmer = PorterStemmer()
    stemmed_words = [porter_stemmer.stem(token) for token in filtered]
    return stemmed_words    


def build_index(corpus_dir: str) -> tuple[dict, int]:
    index = defaultdict(list)
    term_ids = {}
    doc_ids = {}
    df_counter = Counter()
    
    term_id = 0
    doc_id = 0
    file_count = 0
    partial_count = 0
    partial_files = []
    
    for root, _, files in os.walk(corpus_dir):
        for fname in sorted(files):
            if not fname.lower().endswith(".json"):
                continue
            
            fullpath = os.path.join(root, fname)
            print(fullpath) # debug
    
            with open(fullpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            url   = data.get("url", "").strip()
            html  = data.get("content")
            if not url:
                continue
            
            content = parse_content(html)
            
            if not content:
                continue
            
            if url not in doc_ids:
                doc_ids[url] = doc_id
                doc_id += 1

            tokens = extract_tokens(content.get_text())
            tf = Counter(tokens)

            for term, freq in tf.items():
                if term not in term_ids:
                    term_ids[term] = term_id
                    term_id += 1
                tid = term_ids[term]
                index[tid].append([doc_ids[url], freq])
                
            unique_tokens = set(tokens)
            
            for term in unique_tokens:
                tid = term_ids[term]
                df_counter[tid] += 1
                
            file_count += 1
            
            if file_count % 1000 == 0:
                print(f"Saving to partial_index_{partial_count}")
                tfidf_index = convert_tf_to_tfidf(index, df_counter, doc_id)
                name = f"partial_index_{partial_count}.txt"
                save_index(tfidf_index, name)
                partial_files.append(name)
                
                index.clear()
                df_counter.clear()
                partial_count += 1

    if index:
        print(f"Saving to partial_index_{partial_count}")
        tfidf_index = convert_tf_to_tfidf(index, df_counter, doc_id)
        name = f"partial_index_{partial_count}.txt"
        save_index(tfidf_index, name)
        partial_files.append(name)

    return term_ids, doc_ids, partial_files

def save_index(obj, filename):
    mmap = {}
    
    with open(filename, 'w', encoding='utf-8') as f:
        for term_id in sorted(obj.keys()):
            mmap[term_id] = f.tell()
            postings = " ".join(f"{doc_id},{tf}" for doc_id, tf in obj[term_id])
            f.write(f"{term_id} : {postings}\n")

def convert_tf_to_tfidf(index, df_counter, total_docs):
    tfidf_index = {}
    for tid, postings in index.items():
        df = df_counter[tid]

        idf = math.log(total_docs / df)
        
        tfidf_index[tid] = []
        for doc_id, tf in postings:
            score = (1 + math.log(tf)) * idf
            score = round(score, 5)
            tfidf_index[tid].append([doc_id, score])
            
    return tfidf_index
            
def save_terms(term_ids, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for term, tid in term_ids.items():
            f.write(f"{term}\t{tid}\n")
            
def save_docs(doc_ids, filename):
    inverted = invert_map(doc_ids)
    with open(filename, 'w', encoding='utf-8') as f:
        for doc_id, url in inverted.items():
            f.write(f"{doc_id}\t{url}\n")

def compute_index_size(filepath):
    return os.path.getsize(filepath) / 1024

def parse_content(content):
    try:
        soup = BeautifulSoup(content, 'html.parser')
        return soup
    except:
        try:
            soup = BeautifulSoup(content, 'lxml')
            return soup
        except:
            return None
    
def invert_map(in_map):
    inverted_map = {}
    for j, k in in_map.items():
        inverted_map[k] = j
    return inverted_map

def merge_partial_indexes(partial_files, final_index="index.txt", mmap_file="mmap.txt"):
    file_handles = [open(fname, "r", encoding="utf-8") for fname in partial_files] # open every partial file
    heap = []

    for i, f in enumerate(file_handles): # for every opened file
        line = f.readline() # read the first line
        if line: 
            tid = int(line.split(":", 1)[0].strip()) # given that this is a prtia lposting, the first value when split will be the term id
            heapq.heappush(heap, (tid, line, i)) # push that line into the heap

    with open(final_index, "w", encoding="utf-8") as index_out, open(mmap_file, "w", encoding="utf-8") as mmap_out:
        current_tid = None
        current_postings = []

        while heap:
            tid, line, file_idx = heapq.heappop(heap) # get the first value in the heap, based on the term id
            _, postings_str = line.strip().split(":", 1) # get the string of postings from that tid
            postings = [[int(doc), float(score)] for doc, score in (p.split(",") for p in postings_str.strip().split())] # make int docid to score pair 

            if current_tid is None:
                current_tid = tid
                current_postings = postings
            elif tid == current_tid:
                current_postings.extend(postings) # add to list
            else:
                offset = index_out.tell() # get bit position in index tid is at
                current_postings.sort(key=lambda x: x[0]) # sort by doc id
                merged_str = " ".join(f"{int(doc_id)},{round(score, 5)}" for doc_id, score in current_postings) # convert to correct string format
                index_out.write(f"{current_tid} : {merged_str}\n") # write merged posting to index
                mmap_out.write(f"{current_tid}\t{offset}\n") # write term id : offset pair to mmap for seeking

                current_tid = tid # move to next tid
                current_postings = postings

            next_line = file_handles[file_idx].readline() # read next line and push to heap
            if next_line:
                next_tid = int(next_line.split(":", 1)[0].strip())
                heapq.heappush(heap, (next_tid, next_line, file_idx))

        if current_tid is not None: # merge the final tid
            offset = index_out.tell()
            merged_str = " ".join(f"{int(doc_id)},{round(score, 5)}" for doc_id, score in current_postings)
            index_out.write(f"{current_tid} : {merged_str}\n")
            mmap_out.write(f"{current_tid}\t{offset}\n")

    for f in file_handles: # close all files
        f.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python indexer.py <corpus_dir>")
        sys.exit(1)
    data_dir   = sys.argv[1]
    
    term_ids, doc_ids, partial_files = build_index(data_dir)
    
    merge_partial_indexes(partial_files, final_index="index.txt", mmap_file="mmap.txt")
    
    save_terms(term_ids, "terms.txt")
    save_docs(doc_ids, "docs.txt")
    
    for f in partial_files:
        os.remove(f)

