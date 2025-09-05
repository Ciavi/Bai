from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/ko-fi":
            pass

        self.send_response(200)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="./cert.pem", keyfile="./key.pem")
context.check_hostname = False

with HTTPServer(("localhost", 4443), WebhookHandler) as httpd:
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()