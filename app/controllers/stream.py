import simplejson as json
from flask import Blueprint, request, jsonify
import config

# Import the database object from the main app module
from app import db

# Import models
from app.models import (
    Stream, 
    Lot, 
    Owner,
    User,
    Tweet
)

# Import celery tasks
from app.celery import buffer_tasks, catcher_tasks

# Define the blueprint: 'streams', set its url prefix: app.url/streams
stream_mod = Blueprint('streams', __name__, url_prefix='/streams')

@stream_mod.route('/', methods=['POST'])
def create():
    req = json.loads(request.data) 
    if isinstance(req, dict) and 'stream_name' in req:
        stream_name = req['stream_name']
        resp = {
            'lots': [],
            'stream_name': stream_name
        }
        stream_obj = db.session.query(Stream).filter(Stream.name==stream_name).first()
        if stream_obj is None:
            stream_obj = Stream(name=stream_name)
        stream_lists = req.get('lists', [])
        for lot_dict in stream_lists:
            if not isinstance(lot_dict, dict):
                continue
            lot_obj = db.session.query(Lot).filter(Lot.slug==lot_dict.get('slug')).first()
            if lot_obj is None:
                lot_obj = Lot(
                    slug=lot_dict.get('slug'),
                    name=lot_dict.get('name'),
                    tw_id=lot_dict.get('twitter_id'),
                    owner=Owner(screen_name=lot_dict.get('owner'))
                )
            resp['lots'].append(lot_obj.dictify())
            stream_obj.lots.append(lot_obj)
        db.session.add(stream_obj)
        db.session.commit()
        resp['created'] = True
        buffer_tasks.on_create_stream.apply_async(
            args=[req],
            queue=config.CELERY_BUFFER_QUEUE
        )
        return  jsonify(response=resp, message='success')
    else:
        return jsonify(stream_name=None, message='stream_name required.')
    

def _capture_stream_callback(response):
    sys.stderr.write('Returning from Celery: %r\n' % response)

@stream_mod.route('/recorder/', methods=['POST'])
def capture_stream():
    req = json.loads(request.data)
    if isinstance(req, dict) and 'stream_name' in req:
        stream_name = req['stream_name']
        command = req['command']
        if command == 'on':
            async_result_obj = catcher_tasks.catch_stream.apply_async(
                args=[stream_name], 
                queue=config.CELERY_CATCHER_QUEUE, 
                callback=_capture_stream_callback
            )
            #return jsonify(celery_task_id=async_result_obj.id, status=async_result_obj.status, message='success')
            return jsonify(celery_task=repr(async_result_obj), message='success')
    return jsonify(dispatch=None, message='Unable to dispatch')

@stream_mod.route('/<stream_name>/tweets', methods=['GET'])
def get_stream_tweets(stream_name):
    tweets = []
    for response_obj in db.session.query(Tweet).join('user', 'lots', 'streams').filter(Stream.name==stream_name).all():
        tweets.append(json.loads(response_obj.json_str))
    return jsonify(tweets=tweets, message='success') 