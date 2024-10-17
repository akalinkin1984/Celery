import time

import requests


resp = requests.post('http://127.0.0.1:5000/upscale', files={
    'file': 'images\\lama_300px.png'
})

resp_data = resp.json()
task_id = resp_data.get('task_id')
print(resp_data)
print(task_id)


status = None

while status not in ('SUCCESS', 'FAILURE'):
    resp = requests.get(f'http://127.0.0.1:5000/tasks/{task_id}')
    print(resp.json())
    status = resp.json().get('status')
    time.sleep(3)

resp = requests.get('http://127.0.0.1:5000/processed/result_image.png')
binary_file = resp.content
print(resp.status_code)
