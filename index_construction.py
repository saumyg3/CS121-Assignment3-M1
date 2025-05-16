import os
import re
import json
from bs4 import BeautifulSoup
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

def extract_tokens(resp) -> list:
    
    # tokens = []
    # if resp.status != 200 or not hasattr(resp.raw_response, 'content'):
    #     return tokens
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    text = ' '.join(soup.stripped_strings)
    # for word in re.findall(r'\w+', text.lower()):
    #     if word not in STOPWORDS:
    #         tokens.append(word)

   
            
    # return tokens
    return re.findall(r"\w+", text.lower())

def build_index(corpus_dir: str) -> tuple[dict, int]:
    index = defaultdict(list)
    doc_count = 0
    for root, _, files in os.walk(corpus_dir):
        for fname in sorted(files):
            if not fname.lower().endswith(".json"):
                continue
            fullpath = os.path.join(root, fname)
            with open(fullpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            url   = data.get("url", "").strip()
            html  = data.get("content", "")
            if not url:
                continue

            doc_count += 1
            tokens = extract_tokens(html)
            tf     = Counter(tokens)

            for term, freq in tf.items():
                index[term].append({
                    "doc_id": url,
                    "tf": freq
                })

    return index, doc_count

def save_index(index, filepath='inverted_index.json'):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

def compute_index_size(filepath):
    return os.path.getsize(filepath) / 1024

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python indexer.py <corpus_dir> <output_index.json>")
        sys.exit(1)
    data_dir   = sys.argv[1]
    out_index  = sys.argv[2]
    index, num_docs = build_index(data_dir)
    print(f"1) Number of documents indexed   : {num_docs}")
    save_index(index, out_index)
    num_tokens = len(index)
    print(f"2) Number of unique tokens       : {num_tokens}")
    size_kb = compute_index_size(out_index)
    print(f"3) Index size on disk            : {size_kb:.2f} KB")

