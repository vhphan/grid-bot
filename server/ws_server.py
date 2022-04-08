from websocket_server import WebsocketServer
from loguru import logger


# Called for every client connecting (after handshake)
def new_client(client, server):
    logger.info(f"New client connected and was given id %d" % client['id'])
    server.send_message_to_all("Hey all, a new client has joined us")


# Called when a client sends a message
def message_received(client, server, message):
    logger.info(f"Client({client['id']:d}) said: {message}")
    server.send_message_to_all(message)


def main(port=9001):
    server = WebsocketServer(port=port)
    server.set_fn_new_client(new_client)
    server.set_fn_message_received(message_received)
    server.run_forever()


if __name__ == '__main__':
    main()
