import re
import codecs
import collections
import settings


def is_english(s):
    for c in s:
        if ord(c) >= 128:
            return False
    return True


def string_trim(doc):
    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())
    regular_word = collections.defaultdict(int)
    doc = doc.replace('\n', ' ').replace('\r', ' ')
    doc = re.sub(r"http\S+", "", doc)
    doc = re.sub(r"\d+", "", doc)
    doc = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', doc)
    # doc = re.sub(r'[^\p{Latin}]', u'', doc)
    wordlist = [w for w in doc.lower().split() if w not in stoplist and len(w) > 1 and len(w)<16 and is_english(w)]
    for w in wordlist:
        regular_word[w] += 1
    doc = ' '.join(wordlist)
    wordlist = [w for w in doc.split() if regular_word[w] > 3]
    return ' '.join(wordlist)
