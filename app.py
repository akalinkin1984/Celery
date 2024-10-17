import os

import flask
from flask.views import MethodView
from flask import request, jsonify, send_file
# from celery import Celery
from celery.result import AsyncResult

from celery_app import celery, upscale
# from upscale.upscale import upscale


app = flask.Flask('app')
app.config['UPLOAD_FOLDER'] = 'result'
# celery = Celery(
#     'app',
#     backend='redis://localhost:6379/0',
#     broker='redis://localhost:6379/1',
#     broker_connection_retry=True,
#     broker_connection_retry_on_startup=True
# )

celery.conf.update(app.config)


class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask


# @celery.task()
# def upscale_file(path_1, path_2):
#     upscale(path_1, path_2)


class UpscaleView(MethodView):

    def post(self):
        origin_file_path, result_file_path = self.save_file()
        task = upscale.delay(origin_file_path, result_file_path)
        return jsonify({'task_id': task.id})


    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        if task.status != 'SUCCESS':
            return jsonify({'status': task.status})
        return jsonify({'status': task.status,
                        'link': f'http://127.0.0.1:5000/processed/result_image.png'
                        })

    def save_file(self):
        image = request.files.get('file')
        extension = image.filename.split('.')[-1]
        # origin_file_path = os.path.join('upscale', image.filename)
        origin_file_path = image
        result_file_path = os.path.join('result', f'result_image.{extension}')
        image.save(result_file_path)
        return origin_file_path, result_file_path


class ProcessedView(MethodView):
    def get(self, file_name):
        return send_file(f'result\\{file_name}')


upscale_view = UpscaleView.as_view('upscale')
processed_view = ProcessedView.as_view('processed')

app.add_url_rule('/upscale', view_func=upscale_view, methods=['POST'])
app.add_url_rule('/tasks/<string:task_id>', view_func=upscale_view, methods=['GET'])
app.add_url_rule('/processed/<string:file_name>', view_func=processed_view, methods=['GET'])

if __name__ == '__main__':
    app.run()
