#!/bin/sh
 
USAGE="Usage: $0 {start | stop | restart}"

if [ "$#" -lt "1" ]; then
    echo "$USAGE"
    exit 1
fi

start(){
    # For buffer interaction with Twitter API
    celery -A app.celery.buffer_tasks.celery worker -Q twitter_buffer --loglevel=debug -n twitter_buffer &
    # Twitter Streaming API
    celery -A app.celery.catcher_tasks.celery worker -Q twitter_catcher --loglevel=debug -n twitter_catcher &
    twitterBuffer.py &
}

stop(){
    pkill -9 -f twitter_buffer
    pkill -9 -f twitter_catcher
    pkill -9 -f twitterBuffer.py 
}

case "$1" in
    start)
        start
    ;;
    stop)
        stop
    ;;
    restart)
        stop
        start
    ;;
esac
