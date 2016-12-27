import codecs
import time
from utils.TextCleaner import string_trim


def fetch_and_save_feature(desc_file, feature_file, connection):
    feed_id_list = []
    type_dict = {}
    next_type = 0

    cursor = connection.cursor()
    cursor.execute("select feedid, translated, location_type, created from features_t", connection)

    with codecs.open(desc_file, 'w') as ft:
        with codecs.open(feature_file, 'w') as ff:
            epoch = 0
            for feed_id, translated, l_type, create_time in cursor.fetchall():
                trimmed = string_trim(translated)
                if len(trimmed) == 0:
                    continue

                ft.write(trimmed + "\n")
                time_from = time.mktime(create_time.timetuple()) - epoch
                if epoch == 0:
                    epoch = time_from
                    time_from = 0
                lb_time = str(int(time_from / (3600 * 24 * 30 * 6)))
                feed_id_list.append(feed_id)
                if l_type not in type_dict:
                    type_dict[l_type] = next_type
                    next_type += 1
                ff.write("f_loc=" + str(type_dict[l_type]) + " f_time=" + lb_time + "\n")

    return feed_id_list
