import os
import uuid

import flask
from flask.views import MethodView
from flask import request, jsonify
from celery import Celery
from celery.result import AsyncResult

from upscale.upscale import upscale


app = flask.Flask('app')
app.config['UPLOAD_FOLDER'] = 'files'
celery_app = Celery(
    'app',
    backend='redis://localhost:6379/0',
    broker='redis://localhost:6379/1',
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True
)

celery_app.conf.update(app.config)


class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery_app.Task = ContextTask


@celery_app.task()
def upscale_photo(path_1, path_2):
    upscale(path_1, path_2)


class UpscaleView(MethodView):

    def post(self):
        photo_pathes = [self.save_photo(field) for field in ('photo_1', 'photo_2')]
        task = upscale_photo.delay(*photo_pathes)
        return jsonify(
            {'task_id': task.id}
        )

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery_app)
        return jsonify({'status': task.status,
                        'result': task.result})

    def save_photo(self, field):
        photo = request.files.get(field)
        extension = photo.filename.split('.')[-1]
        path = os.path.join('files', f'{uuid.uuid4()}.{extension}')
        photo.save(path)
        return path


class ProcessedView(MethodView):
    def post(self):
        pass


upscale_view = UpscaleView.as_view('upscale')
processed_view = ProcessedView.as_view('processed')

app.add_url_rule('/tasks/<string:task_id>', view_func=upscale_view, methods=['GET'])
app.add_url_rule('/upscale', view_func=upscale_view, methods=['POST'])
app.add_url_rule('/processed/{file}', view_func=processed_view, methods=['POST'])

if __name__ == '__main__':
    app.run()