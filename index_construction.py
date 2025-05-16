import os
import re
import json
from bs4 import BeautifulSoup
from collections import Counter

STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can\'t', 'cannot', 'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t',
    'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t',
    'having', 'he', 'he\'d', 'he\'ll', 'he\'s', 'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his',
    'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m', 'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s',
    'its', 'itself', 'let\'s', 'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off',
    'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan\'t',
    'she', 'she\'d', 'she\'ll', 'she\'s', 'should', 'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'that\'s',
    'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'there\'s', 'these', 'they', 'they\'d', 'they\'ll',
    'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn\'t',
    'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve', 'were', 'weren\'t', 'what', 'what\'s', 'when', 'when\'s', 'where',
    'where\'s', 'which', 'while', 'who', 'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t', 'would', 'wouldn\'t',
    'you', 'you\'d', 'you\'ll', 'you\'re', 'you\'ve', 'your', 'yours', 'yourself', 'yourselves'
}

common_w = {}

def extract_tokens(resp) -> list:
    
    tokens = []
    if resp.status != 200 or not hasattr(resp.raw_response, 'content'):
        return tokens
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    text = ' '.join(soup.stripped_strings)
    for word in re.findall(r'\w+', text.lower()):
        if word not in STOPWORDS:
            tokens.append(word)

   
            
    return tokens

def build_index(directory):
    index = {}
    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            text = soup.get_text()
        
        tokens = tokenize(text)
        unique_tokens = set(tokens)
        tf_counts = Counter(tokens)
        
        for token in unique_tokens:
            posting = {
                'doc_id': filename,
                'tf': tf_counts[token]
            }
            if token not in index:
                index[token] = []  # create empty list if token not present
            index[token].append(posting)
    
    return index

def save_index(index, filepath='inverted_index.json'):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

def compute_index_size(filepath):
    return os.path.getsize(filepath) / 1024

if __name__ == "__main__":
    data_dir = 'folder path to be added'
    index = build_index(data_dir)
    save_index(index)
    num_docs = len(set(posting['doc_id'] for postings in index.values() for posting in postings))
    num_tokens = len(index)
    size_kb = compute_index_size('inverted_index.json')
    print(f"Number of Indexed Documents     : {num_docs}")
    print(f"Number of Unique Tokens         : {num_tokens}")
    print(f"Index Size on Disk    : {size_kb:.2f} KB")

