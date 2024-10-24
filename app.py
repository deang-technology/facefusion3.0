import json
import logging
import mimetypes
import os.path
import subprocess
import sys
import uuid
import threading

import fastapi.responses
import requests

directory = '/home/ubuntu/facefusion3.0/output'

app = fastapi.FastAPI()

url = "https://api.ipify.org?format=json"
response = requests.get(url)
ip = response.json()["ip"]
logging.info(f"Ip: {ip}")

port = 8000

lock = threading.Lock()


@app.get("/file")
def get_file(file_url: str):
	media_type, _ = mimetypes.guess_type(file_url)
	return fastapi.responses.FileResponse(file_url, media_type=media_type)


@app.get('/face-detect')
def face_detect(file_url: str, type: str):
	with lock:
		file_path = f"{directory}/{str(uuid.uuid4())}"
		if type == "image":
			file_path = f"{file_path}.png"
		if type == "video":
			file_path = f"{file_path}.mp4"
		resp = requests.get(file_url)
		with open(file_path, "wb") as f:
			f.write(resp.content)
		output_path = f"{directory}/{str(uuid.uuid4())}.json"
		commands = [sys.executable,
					'facefusion.py',
					'--face-detector-only',
					'-t',
					file_path,
					'-os',
					output_path,
					'--reference-frame-number',
					'10',
					'-od',
					directory,
					'--execution-providers',
					'cuda',
					'--log-level',
					'debug']
		logging.info(f"command: {commands}")
		with open("nohup.out", "a") as log_file:
			run = subprocess.run(commands, stdout=log_file, stderr=log_file, text=True)
			if run.returncode != 0:
				return {"status": -1, "message": "Error"}
			with open(output_path, "r") as ret_file:
				data = json.load(ret_file)
			data = list(map(lambda x: f"http://{ip}:{port}/file?file_url={x}", data))
			return {"status": 1, "message": "Success", "data": data}


@app.get('/face-swap')
def face_swap(target_url: str, face_urls: str, source_urls: str, type: str):
	with lock:
		target_file = f"{directory}/{str(uuid.uuid4())}"
		output_file = f"{directory}/{str(uuid.uuid4())}"
		if type == "video":
			target_file = f"{target_file}.mp4"
			output_file = f"{output_file}.mp4"
		if type == "image":
			target_file = f"{target_file}.png"
			output_file = f"{output_file}.png"

		resp1 = requests.get(target_url)
		with open(target_file, "wb") as f1:
			f1.write(resp1.content)

		face_files = []
		for face_url in face_urls.split(","):
			face_file = f"{directory}/{str(uuid.uuid4())}.png"
			resp = requests.get(face_url)
			with open(face_file, "wb") as f:
				f.write(resp.content)
			face_files.append(face_file)
		source_files = []
		for source_url in source_urls.split(","):
			source_file = f"{directory}/{str(uuid.uuid4())}.png"
			resp = requests.get(source_url)
			with open(source_file, "wb") as f:
				f.write(resp.content)
			source_files.append(source_file)

		commands = [sys.executable,
					'facefusion.py',
					'--processors',
					'face_swapper',
					'face_enhancer',
					'-t',
					target_file,
					'--log-level',
					'debug',
					'--face-selector-mode',
					'reference_advance',
					'-fs',
					",".join(face_files),
					'-s',
					",".join(source_files),
					'-o',
					output_file,
					'--face-enhancer-blend',
					'100']
		logging.info(f"command: {commands}")
		with open("nohup.out", "a") as log_file:
			run = subprocess.run(commands, stdout=log_file, stderr=log_file, text=True)
			if run.returncode != 0 or not os.path.exists(output_file):
				return {"status": -1, "message": "Error"}
			return {"status": 1, "message": "Success", "data": f"http://{ip}:{port}/file?file_url={output_file}"}
