# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 23:32:36 2016

@author: limeng
"""

"""
计算主题结果和tags之间的相似程度

"""

def similarity(corpus_tag, dictionary_tag, corpus, ldamodel):
    ret = 0
    for doc_idx, doc in enumerate(corpus):
        score = 0
        for tag in corpus_tag[doc_idx]:
            keyword = dictionary_tag[tag[0]]
            
            # 检查tag中每个词是否在文档doc的topic里面出现
            for topic in ldamodel.get_document_topics(doc):
                topic_dict = ldamodel.show_topic(topic[0])
                for topic_pair in topic_dict:
                    if keyword == topic_pair[0]:
                        score += topic[1] * topic_pair[1]
                        break
                    
        if len(corpus_tag[doc_idx]) == 0:
            ret += 0
        else:
            ret += score/len(corpus_tag[doc_idx])
            
        if doc_idx % 1000 == 0:
            print(doc_idx)
            
    return ret

sim = similarity(corpus_tag, dictionary_tag, corpus, ldamodel)
print(sim)
