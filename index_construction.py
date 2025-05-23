import os
import re
import json
import sys
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
from collections import defaultdict, Counter

# STOPWORDS = {
#     'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
#     'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
#     'can\'t', 'cannot', 'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t',
#     'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t',
#     'having', 'he', 'he\'d', 'he\'ll', 'he\'s', 'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his',
#     'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m', 'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s',
#     'its', 'itself', 'let\'s', 'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off',
#     'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan\'t',
#     'she', 'she\'d', 'she\'ll', 'she\'s', 'should', 'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'that\'s',
#     'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'there\'s', 'these', 'they', 'they\'d', 'they\'ll',
#     'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn\'t',
#     'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve', 'were', 'weren\'t', 'what', 'what\'s', 'when', 'when\'s', 'where',
#     'where\'s', 'which', 'while', 'who', 'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t', 'would', 'wouldn\'t',
#     'you', 'you\'d', 'you\'ll', 'you\'re', 'you\'ve', 'your', 'yours', 'yourself', 'yourselves'
# }

# common_w = {}

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
    if len(sys.argv) != 3:
        print("Usage: python indexer.py <corpus_dir> <output_index.json>")
        sys.exit(1)
    data_dir   = sys.argv[1]
    out_index  = sys.argv[2]
    
    term_ids, doc_ids, index = build_index(data_dir)
    
    save_json(term_ids, "terms.json")
    save_json(invert_map(doc_ids), "docs.json")
    save_json(index, "index.json")

