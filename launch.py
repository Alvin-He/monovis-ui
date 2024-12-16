import subprocess
import os
import sys
import time
import webbrowser

HEALTH_CHECK_INTERVAL_SECONDS = 1

PORT = 8080
ADDR = "127.0.0.1"

API_ADDR = ADDR
API_PORT = PORT + 1

clientside_dir = f"{os.path.dirname(__file__)}/clientside/"
server_dir = f"{os.path.dirname(__file__)}/server/"
def start_http_server():
    process = subprocess.Popen([sys.executable, "-m", "http.server", "--b", str(ADDR), "-d", clientside_dir, str(PORT)], bufsize=-1, cwd=clientside_dir)
    print(f"launch.py INFO: HTTP Server started on PID {process.pid}")
    return process
def start_api_server():
    process =  subprocess.Popen([sys.executable, "-m", "flask", "-A", "server", "run", "-h", str(API_ADDR), "-p", str(API_PORT)], bufsize=-1, cwd=server_dir)
    print(f"launch.py INFO: API Server started on PID {process.pid}")
    return process

http_server: subprocess.Popen = start_http_server() 
api_server:subprocess.Popen = start_api_server()

time.sleep(0.1)
webbrowser.open(f"http://{ADDR}:{PORT}/", 2)
print(f"launch.py INFO: open browser and go to http://{ADDR}:{PORT}/ to access monovis-ui")

print(f"launch.py INFO: Starting Health Check on interval of {HEALTH_CHECK_INTERVAL_SECONDS}sec")
while True:
    time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    httpServerStatus = http_server.poll()
    if httpServerStatus != None:
        print(f"launch.py CRITICAL: HTTP Server Terminated Unexpectedly with code {httpServerStatus}")
        http_server = start_http_server()
        print("launch.py INFO: Restarting HTTP server")

    apiServerStatus = api_server.poll()
    if apiServerStatus != None:
        print(f"launch.py CRITICAL: API Server Terminated Unexpectedly with code {apiServerStatus}")
        api_server = start_api_server()
        print("launch.py INFO: Restarting API server")