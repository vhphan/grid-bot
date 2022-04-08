from bots.gridbot import GridBot

if __name__ == '__main__':
    bot = GridBot(web_socket_url='ws://localhost:9001')
    bot.run_bot()
