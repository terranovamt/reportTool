import os
import json
import socket
import threading
import webbrowser
import http.server
import socketserver
import urllib.parse

PORT = 8000
MAX_PORT = 8800
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(BASE_DIR, "web"))
POST_FILE = os.path.abspath(os.path.join(BASE_DIR, "./post.json"))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/html/index.html'
        elif self.path == '/index.html':
            self.path = '/html/index.html'
        elif self.path == '/about':
            self.path = '/html/about.html'
        elif self.path == '/loading':
            self.path = '/html/loading.html'
        elif self.path == '/log':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            with open('./src/run.log', 'r') as logfile:
                data = logfile.read()
                self.wfile.write(data.encode())
            return
        elif self.path == '/post.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with open(POST_FILE, 'r') as jsonfile:
                data = jsonfile.read()
                self.wfile.write(data.encode())
            return
        else: 
            if not os.path.isfile(os.path.join(WEB_DIR, self.path.lstrip('/'))):
                self.path = '/html/404.html'
        return super().do_GET()

    def do_POST(self):
        try:
            if self.path == '/submit':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                if not post_data:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Empty POST data')
                    return

                data = self.parse_post_data(post_data)
                
                # Check if there is at least one item with 'Run' set to '1'
                if not any(item.get('Run') == "1" for item in data.get('data', [])):
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Select at least one item with Run set to 1')
                    return            
                # Send a successful response
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Successfully processed the data')
                # Process the data
                threading.Thread(target=self.report_generator, args=(data,)).start()
                
            else:
                self.send_response(404)
                self.end_headers()

        except Exception as e:
            print(f"Error: {e}")
        

    def parse_post_data(self, post_data):
        data_str = post_data.decode('utf-8')
        parsed_data = urllib.parse.parse_qs(data_str)
        data = json.loads(parsed_data['data'][0])
        return data


    def report_generator(self, data):
        with open(POST_FILE, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)
        debug = False
        
        from core import generate
        generate(data)
        self.update_run_status()
        

    def update_run_status(self):
        with open(POST_FILE, 'r') as jsonfile:
            data = json.load(jsonfile)
        
        # Iterate through the 'data' list and update 'Run' field
        for item in data.get('data', []):
            if 'Run' in item and item['Run'] == "1":
                item['Run'] = "0"
        
        # Write the updated data back to the JSON file
        with open(POST_FILE, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)

    def log_message(self, format, *args):
        pass  # Override to suppress logging

class ThreadingSimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def start_server(port):
    with ThreadingSimpleServer(("", port), Handler) as httpd:
        ip = socket.gethostbyname(socket.gethostname())
        print(f"Serving at {ip}:{port}")
        httpd.serve_forever()

def find_available_port(start_port, max_port):
    port = start_port
    while port <= max_port:
        try:
            start_server(port)
            break
        except OSError as e:
            if e.errno == socket.errno.EADDRINUSE:
                print(f"Port {port} is already in use. Trying port {port + 2}...")
                port += 2
            else:
                raise

def guihtml():
    if not os.path.isfile(POST_FILE):
        with open(POST_FILE, 'w') as jsonfile:
            json.dump([], jsonfile)

    server_thread = threading.Thread(target=find_available_port, args=(PORT, MAX_PORT))
    server_thread.daemon = True
    server_thread.start()
    
    webbrowser.open(f"http://localhost:{PORT}")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down server.")

if __name__ == "__main__":
    guihtml()