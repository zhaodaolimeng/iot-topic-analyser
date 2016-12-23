import re
import codecs
import collections


def string_trim(doc):
    with codecs.open('../resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())
    regular_word = collections.defaultdict(int)
    doc = str(doc)
    doc = doc.replace('\n', ' ')
    doc = re.sub(r"http\S+", "", doc)
    doc = re.sub(r"\d+", "", doc)
    doc = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./>?]', ' ', doc)
    wordlist = [w for w in doc.lower().split() if w not in stoplist and len(w) > 1]
    for w in wordlist:
        regular_word[w] += 1
    return ' '.join(wordlist)
