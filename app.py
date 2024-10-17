import os

import flask
from flask.views import MethodView
from flask import request, jsonify, send_file
from celery.result import AsyncResult

from celery_app import celery, upscale


app = flask.Flask('app')
app.config['UPLOAD_FOLDER'] = 'result'

celery.conf.update(app.config)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


class UpscaleView(MethodView):

    def post(self):
        origin_file_path = request.files.get('file').read().decode()
        extension = origin_file_path.split('.')[-1]
        result_file_path = os.path.join('result', f'result_image.{extension}')
        task = upscale.delay(origin_file_path, result_file_path)
        return jsonify({'task_id': task.id})

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        if task.status == 'FAILURE':
            return jsonify({'status': 'Failed to process'})
        elif task.status == 'SUCCESS':
            return jsonify({'status': task.status,
                        'link': f'http://127.0.0.1:5000/processed/result_image.png'
                        })
        return jsonify({'status': task.status})


class ProcessedView(MethodView):
    def get(self, file_name):
        return send_file(f'result\\{file_name}')


upscale_view = UpscaleView.as_view('models')
processed_view = ProcessedView.as_view('processed')

app.add_url_rule('/upscale', view_func=upscale_view, methods=['POST'])
app.add_url_rule('/tasks/<string:task_id>', view_func=upscale_view, methods=['GET'])
app.add_url_rule('/processed/<string:file_name>', view_func=processed_view, methods=['GET'])

if __name__ == '__main__':
    app.run()
