import json

import tornado.ioloop
import tornado.web
import tornado.websocket

topups = {}
notifications = set()

class IndexHandler(tornado.web.RequestHandler):
    def post(self):
        global topups
        body_json = json.loads(self.request.body)
        print(body_json)
        if body_json['created']:
            for i in body_json['created']:
                print(i[0], i[1], i[2])
                topups.setdefault(i[1], {})
                topups[i[1]][i[0]] = i[2]

        if body_json['spent']:
            for i in body_json['spent']:
                print(i[0], i[1], i[2])
                topups.setdefault(i[1], {})
                print(topups[i[1]][i[0]] - i[2])
                topups[i[1]][i[0]] = i[2]

        self.write("Index")

    def get(self):
        self.finish(topups)

class NotificationHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")
        global notifications
        notifications.add(self)

    def on_message(self, message):
        print("Message received: {}".format(message))
        self.write_message("Echo: {}".format(message))

    def on_close(self):
        print("WebSocket closed")
        notifications.remove(self)


class TopupHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/topup.html")


class MerchantHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/merchant.html")


class PaymentHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/payment.html")


class BalanceHandler(tornado.web.RequestHandler):
    def get(self):
        addr = self.get_argument('addr').lower()
        self.finish(topups.get(addr, {}))


class SendHandler(tornado.web.RequestHandler):
    def post(self):
        # addr = self.get_argument('addr').lower()
        print(self.request.body)
        for i in notifications:
            i.write_message(self.request.body.decode())

        self.finish({})


def make_app():
    return tornado.web.Application([
        (r"/index", IndexHandler),
        (r"/topup", TopupHandler),

        (r"/payment", PaymentHandler),
        (r"/pay", PaymentHandler),
        (r"/balance", BalanceHandler),
        (r"/send", SendHandler),

        (r"/merchant", MerchantHandler),
        (r"/notification", NotificationHandler),

        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8090)
    tornado.ioloop.IOLoop.current().start()
