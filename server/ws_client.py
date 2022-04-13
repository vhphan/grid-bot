from bots.gridbot import GridBot

if __name__ == '__main__':
    with GridBot(web_socket_url='ws://localhost:9001') as bot:
        bot.run_bot()
