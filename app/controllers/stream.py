import simplejson as json
from flask import Blueprint, request, jsonify

# Import the database object from the main app module
from app import db

# Import models
from app.models import Stream, StreamGroup

# Import celery tasks
from app import celery_tasks

# Define the blueprint: 'stream', set its url prefix: app.url/stream
stream_mod = Blueprint('stream', __name__, url_prefix='/stream')

@stream_mod.route('/', methods=['POST'])
def create():
    req = json.loads(request.data) 
    if isinstance(req, dict) and 'stream_name' in req:
        stream_name = req['stream_name']
        resp = {
            'lists': [],
            'stream_name': stream_name
        }
        stream_obj = Stream(name=stream_name)
        stream_lists = req.get('lists', [])
        for list_dict in stream_lists:
            if not isinstance(list_dict, dict):
                continue
            list_obj = List(
                slug=list_dict.get('slug'),
                name=list_dict.get('name'),
                tw_id=list_dict.get('twitter_id'),
                owner=list_dict.get('owner')
            )
            resp['lists'].append(list_obj.dictify())
            stream_list_obj = StreamList(stream=stream_obj, list=list_obj)
            db.add(stream_list_obj)
        db.commit()
        resp['created'] = True
        celery_tasks.on_create_stream(resp)
        return  jsonify(response=resp, message='success')
    else:
        return jsonify(stream_name=None, message='stream_name required.')
    


