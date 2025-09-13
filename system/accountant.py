import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

from discord.ext.commands import Bot

from commands.messages import p_embed_kofi


class WebhookHandler(BaseHTTPRequestHandler):
    bot: Bot

    def __init__(self, *args, bot: Bot, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    def do_POST(self):
        if self.path == "/ko-fi":
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

        def handler(*args, **kwargs) -> WebhookHandler:
            return WebhookHandler(*args, bot=self.bot, **kwargs)

        with HTTPServer(("0.0.0.0", 4443), handler) as httpd:
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            httpd.serve_forever()

