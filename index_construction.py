import os
import re
import json
import sys
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
    term_id = 0
    doc_id = 0
    
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
                
    return term_ids, doc_ids, index

def save_index(obj, filename):
    mmap = {}
    
    with open(filename, 'w', encoding='utf-8') as f:
        for term_id in sorted(obj.keys()):
            mmap[term_id] = f.tell()
            postings = " ".join(f"{doc_id},{tf}" for doc_id, tf in index[term_id])
            f.write(f"{term_id} : {postings}\n")
            
    with open("mmap.json", "w") as f2:
        json.dump(mmap, f2)

def save_json(obj, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(obj, f)

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python indexer.py <corpus_dir>")
        sys.exit(1)
    data_dir   = sys.argv[1]
    
    term_ids, doc_ids, index = build_index(data_dir)
    
    save_json(term_ids, "terms.json")
    save_json(invert_map(doc_ids), "docs.json")
    save_index(index, "index.txt")

