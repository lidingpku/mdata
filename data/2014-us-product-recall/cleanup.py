import json
import os
import dateutil.parser
import urlparse
import time
import hashlib
import csv
import collections
import re
from datetime import datetime
import nltk

def datetime_to_timestamp(dt):
    return int(time.mktime(dt.timetuple()) - time.mktime((1970, 1, 1, 0, 0, 0, 0, 0, 0)))

def gen_hash_id(str):
    hash = hashlib.sha1();
    hash.update(str)
    return hash.hexdigest()

data_tag = "2014-us-product-recall"
url_base = "http://www.cpsc.gov/en/Newsroom/CPSC-RSS-Feed/Recalls-RSS/"

filename = os.path.join(os.path.dirname(__file__), "{}.raw.json".format(data_tag))
with open (filename, "r") as f:
    json_data_input = json.load(f)


json_data_output = dict(items=[])
csv_fields = set()
for item in json_data_input["rss"]["channel"]["item"]:
    item_new = {}
    for k, v in item.items():
        if k in ["title","description"]:
            v = v.replace(u'\u2019',"'")
            item_new[k]=v
        elif k in ["link"]:
            item_new["source"]=v
        elif k in ["pubDate"]:
            item_new["datetime:rss"] = v
            dt = dateutil.parser.parse(v)
            print dt.timetuple()
            item_new["datetime:iso"] = dt.isoformat()
            item_new["datetime:unix"] = datetime_to_timestamp(dt)
            item_new["month:iso"] = dt.isoformat()[:7]
            item_new["date:iso"] = dt.isoformat()[:10]
        elif k in ["media:group"]:
            item_new["feature_image"] =  urlparse.urljoin(url_base, v["media:content"]["-url"])
            item_new["feature_image:width"] =v["media:content"]["-width"]
            item_new["feature_image:height"] =v["media:content"]["-height"]
        elif k in ["guid"]:
            item_new["id"] = gen_hash_id(v)


    item_new["tags"] = []
    item_new["label"] = item_new["title"]
    json_data_output["items"].append(item_new)
    csv_fields.update(item_new.keys())
    #print json.dumps(item_new, sort_keys=True, indent=4)

def split_word(str):
    return [x.lower() for x in re.split(r"[\s\('\"\);,]", str)]

cnt_keywords = collections.Counter()
for item in json_data_output["items"]:
    list_word = split_word(item["title"])
    for word in list_word:
        if len(word)>1:
            cnt_keywords[word]+=1

print cnt_keywords.most_common(50)

keywords = set()
for word, freq in cnt_keywords.most_common(50):
    if freq > 5:
        keywords.add(word)
print keywords

#nltk.download()
#from nltk.corpus import stopwords
#stop = stopwords.words('english')

stop = ["and","or", "due", "at", "for", "to", "with", "of", "by", "the", "recall", "recalls", "recalled"]
keywords.difference_update(stop)
print keywords

for item in json_data_output["items"]:
    list_word = split_word(item["title"])
    for xword in keywords:
       if xword in list_word:
            item["tags"].append(xword)

filename_clean = os.path.join(os.path.dirname(__file__), "{}.clean.json".format(data_tag))
with open(filename_clean, "w") as f:
    json.dump(json_data_output, f, sort_keys=True, indent=4)

filename_clean = os.path.join(os.path.dirname(__file__), "{}.clean.csv".format(data_tag))
with open(filename_clean, "w") as f:
    writer = csv.DictWriter(f, sorted(list(csv_fields)))
    writer.writeheader()
    for xitem in json_data_output["items"]:

        writer.writerow(dict((k, v.encode('utf-8') if isinstance(v, unicode) else v ) for k, v in xitem.iteritems()))