import os
import subprocess
import sys

def test_face_detector() -> None:
	target_path = os.path.join(os.getcwd(), "tests/examples/example.mp4")
	output_path = os.path.join(os.getcwd(), "tests/examples/output.json")
	output_directory = os.path.join(os.getcwd(), "tests/examples/")
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--only-detector', 'true', '-t', target_path, '-o', output_path, '-od', output_directory, '--reference-frame-number', '5', '--log-level', 'debug' ]
	assert subprocess.run(commands).returncode == 0

test_face_detector()
