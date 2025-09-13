import json
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

from discord.ext.commands import Bot

from commands.messages import p_embed_kofi


class WebhookHandler(BaseHTTPRequestHandler):
    bot: Bot = None

    def __init__(self, *args, bot: Bot = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    def do_POST(self):
        if self.path == "/ko-fi":
            if self.bot is None:
                self.send_response(500)
                return

            owner = self.bot.get_user(self.bot.owner_id)

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = post_data.decode('utf-8')
            json_data = json.loads(data)

            print(json_data)

            if json_data["verification_token"] != "bba50b8f-46ee-46c9-8e62-507bdc36eee2":
                self.send_response(403)
                return

            embed = p_embed_kofi(json_data)

            owner.send(embed=embed)

            self.send_response(200)
            return

        self.send_response(404)


class Accountant:
    def __init__(self, bot: Bot):
        self.bot = bot

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="./cert.pem", keyfile="./key.pem")
        context.check_hostname = False

        self.context = context

        handler = partial(WebhookHandler, bot=self.bot)

        with HTTPServer(("0.0.0.0", 4443), handler) as httpd:
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            httpd.serve_forever()

