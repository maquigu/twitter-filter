import simplejson as json
from flask import Blueprint, request, jsonify

# Import the database object from the main app module
from app import db

# Import models
from app.models import Stream, Lot, Owner

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
            'lots': [],
            'stream_name': stream_name
        }
        stream_obj = Stream(name=stream_name)
        stream_lists = req.get('lists', [])
        for lot_dict in stream_lists:
            if not isinstance(lot_dict, dict):
                continue
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
        celery_tasks.on_create_stream(req)
        return  jsonify(response=resp, message='success')
    else:
        return jsonify(stream_name=None, message='stream_name required.')
    


