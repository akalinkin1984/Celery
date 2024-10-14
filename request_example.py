import requests
import time


resp = requests.post('http://127.0.0.1:5000/upscale', files={
    'image_1': open('upscale/lama_300px.png', 'rb'),
    'image_2': open('upscale/lama_600px.png', 'wb')
})
resp_data = resp.json()
print(resp_data)
task_id = resp_data.get('task_id')
print(task_id)


# resp = requests.get(f'http://127.0.0.1:5000/comparison/{task_id}')
# print(resp.json())
# time.sleep(3)
#
# resp = requests.get(f'http://127.0.0.1:5000/comparison/{task_id}')
# print(resp.json())