#!/bin/sh
 
USAGE="Usage: $0 {start | stop | restart}"

if [ "$#" -lt "1" ]; then
    echo "$USAGE"
    exit 1
fi

start(){
    celery -A app.celery_tasks worker --loglevel=debug -n new &
    twitterBuffer.py &
}

stop(){
    pkill -9 -f app.celery_tasks
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
