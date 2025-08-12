from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if self.path == '/':
            response = {"message": "Basic HTTP server working!"}
        elif self.path == '/health':
            response = {"status": "healthy"}
        else:
            response = {"error": "Not found"}
            
        self.wfile.write(json.dumps(response).encode())

def handler(request, context):
    return SimpleHandler(request, context)

# For local testing
if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), SimpleHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()
