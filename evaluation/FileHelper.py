import codecs
import time
import collections
import settings
import re
import codecs


def is_english(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        print("it was not a ascii-encoded unicode string")
        return False


def trim_str(s, stopwords):
    s = s.replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r"http\S+", "", s)
    s = re.sub(r"\d+", "", s)
    s = re.sub(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', ' ', s)
    wordlist = [w for w in s.lower().split() if
                (w not in stopwords) & (len(w) > 1) & (len(w) < 16)]
    return wordlist


def fetch_and_save_feature(desc_file, feature_file, connection):
    """
    从数据库features_t中读取特征和文本并形成文件
    :param desc_file:
    :param feature_file:
    :param connection:
    :return:
    """
    type_dict = {}
    next_type = 0
    cursor = connection.cursor()
    cursor.execute("select feedid, doc, location_type, created from features_t", connection)

    with codecs.open(settings.DEFINITIONS_ROOT + '/resource/stopwords.txt', 'r') as f:
        stoplist = set(f.read().split())

    result_dict = {}
    epoch = 0
    regular_word = collections.defaultdict(int)
    for feed_id, doc, l_type, create_time in cursor.fetchall():

        # 时间
        time_from = time.mktime(create_time.timetuple()) - epoch
        if epoch == 0:
            epoch = time_from
            time_from = 0
        lb_time = str(int(time_from / (3600 * 24 * 30 * 6)))

        # 地点
        if l_type not in type_dict:
            type_dict[l_type] = next_type
            next_type += 1

        # 词
        wordlist = trim_str(doc, stoplist) if is_english(doc) else []
        for w in wordlist:
            regular_word[w] += 1

        result_dict[feed_id] = (lb_time, type_dict[l_type], wordlist)

    # 检查词频是否满足要求，分别存放到text.in和features.in中
    feed_id_list = []
    with codecs.open(desc_file, 'w') as ft:
        with codecs.open(feature_file, 'w') as ff:
            for feed_id, (lb_time, l_type, wordlist) in result_dict.items():
                final_words = " ".join([w for w in wordlist if regular_word[w] > 2])
                if len(final_words) > 1:
                    feed_id_list.append(feed_id)
                    ft.write(final_words + "\n")
                    ff.write("f_time=" + lb_time + "\n")
                    # ff.write("f_loc=" + str(l_type) + " f_time=" + lb_time + "\n")

    regular_set = set([w for w, c in regular_word.items() if c > 2])
    return feed_id_list, regular_set
