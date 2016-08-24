# Twitter Buffer
A Twitter buffer consisting of a configurable streaming daemon, a database and a RESTful API


# Runtime

## Setup virtualenv:
```
$ cd $HOME/TwitterBuffer && source env.sh
```

## Set a crontab to run streamCatcher.py
```
SHELL=/bin/bash
# m h  dom mon dow   command
*/5 * * * * cd $HOME/TwitterBuffer/ && source env.sh && streamCatcher.py >>/home/openfilter/streamCatcher.log 2>&1
```

## Start / Stop / Restart Web Service
```
$ run.sh {start|stop|restart}
```
