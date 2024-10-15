import os
import uuid

import flask
from flask.views import MethodView
from flask import request, jsonify, send_file
from celery import Celery
from celery.result import AsyncResult

from upscale.upscale import upscale


app = flask.Flask('app')
app.config['UPLOAD_FOLDER'] = 'photos'
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
        file, result_file = self.save_photo()
        task = upscale_photo.delay(file, result_file)
        return jsonify(
            {'task_id': task.id}
        )


    def get(self, task_id):
        task = AsyncResult(task_id, app=celery_app)
        if task.status != 'SUCCESS':
            return jsonify({'status': task.status})
        return jsonify({'status': task.status,
                        'link': f'http://127.0.0.1:5000/processed/{request.json["p"]}',
                        })

    def save_photo(self):
        image = request.files.get('file')
        name, extension = image.filename.split('.')
        file = os.path.join('photos', f'{name}.{extension}')
        result_file = os.path.join('photos', f'{name}_upscale.{extension}')
        image.save(file)
        image.save(result_file)
        return file, result_file




class ProcessedView(MethodView):
    def get(self):
        send_file('upscale/result.png')


upscale_view = UpscaleView.as_view('upscale')
processed_view = ProcessedView.as_view('processed')

app.add_url_rule('/upscale', view_func=upscale_view, methods=['POST'])
app.add_url_rule('/tasks/<string:task_id>', view_func=upscale_view, methods=['GET'])
app.add_url_rule('/processed/<string:file>', view_func=processed_view, methods=['GET'])

if __name__ == '__main__':
    app.run()