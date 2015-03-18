#!/usr/bin/python
# encoding: utf-8

import sys
from pprint import pprint
from twitter import *
from client import TwitterBuffer
import config

if len(sys.argv) < 3 or sys.argv[1] == '-h':
    print 'Usage: '+sys.argv[0]+' stream_name {on | off}'
    sys.exit(1)
stream_name = sys.argv[1]
command = sys.argv[2]

tf = TwitterBuffer()
print tf.record(stream_name, command)
