from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

from discord.ext.commands import Bot


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/ko-fi":
            pass

        self.send_response(200)


class Accountant:
    def __init__(self, bot: Bot):
        self.bot = bot

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="./cert.pem", keyfile="./key.pem")
        context.check_hostname = False

        self.context = context

        with HTTPServer(("0.0.0.0", 4443), WebhookHandler) as httpd:
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            httpd.serve_forever()

