#!/usr/bin/python
# encoding: utf-8

import sys
from pprint import pprint
#from UnicodeCSV import CSVWriter
from twitter import *
from client import TwitterBuffer
import config

username = 'social_west'
count = 100

auth = OAuth(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET, config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
twitter = Twitter(auth = auth)
tf = TwitterBuffer()

results = twitter.lists.ownerships(screen_name=username, count=count)
list_of_lists = []
for l in results['lists']:
    list_of_lists.append({
        'owner': username, 
        'slug': l['slug'], 
        'name': l['name'], 
        'twitter_id':l['id_str']
    })
stream_dict = {
    'stream_name': 'water',
    'lists': list_of_lists,
}
pprint(stream_dict)
print tf.create_stream(stream_dict)
