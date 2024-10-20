import tornado.ioloop
import tornado.web
import tornado.websocket

class IndexHandler(tornado.web.RequestHandler):
    def post(self):
        self.write("Index")

    def get(self):
        self.write("Index Info")

class NotificationHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        print("Message received: {}".format(message))
        self.write_message("Echo: {}".format(message))

    def on_close(self):
        print("WebSocket closed")


class TopupHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template/topup.html")


class MerchantHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Merchant Page")


class PaymentHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Payment Page")


def make_app():
    return tornado.web.Application([
        (r"/index", IndexHandler),
        (r"/topup", TopupHandler),
        (r"/payment", PaymentHandler),
        (r"/merchant", MerchantHandler),
        (r"/notification", NotificationHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8090)
    tornado.ioloop.IOLoop.current().start()
