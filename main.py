import os
import random
import time

from discord.ext import commands
from dotenv import load_dotenv
from GoogleFeud import GoogleFeud

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

help_command = commands.DefaultHelpCommand(
    no_category = 'Google Feud'
)

bot = commands.Bot(command_prefix='gfeud ', 
    description='Google Feud is a game much like Family Feud, except the phrases on the wall are Google\'s auto-complete suggestions. Guess what the auto-completes they for a given phrase to win the game!', 
    help_command=help_command)

@bot.command(name='start', help='Starts a game of Google Feud')
async def start_game(ctx):
    searches_file = open('google_searches.txt', 'r')
    searches = searches_file.read().split('\n')
    search = random.choice(searches)

    gfeud = GoogleFeud(ctx)
    gfeud.loadSession()
    gfeud.startGame(search)
        
    response = gfeud.getGFeudBoard()

    await ctx.send(response)

@bot.command(name='end', help='Ends a game of Google Feud')
async def end_game(ctx):
    gfeud = GoogleFeud(ctx)
    gfeud.loadSession()
        
    if gfeud.endGame():
        response = ">>> Ended the game :ok_hand:\nStart again with `gfeud start`"
    else:
        response = ">>> Game is not in progress :confused:\nStart a game with `gfeud start`"

    await ctx.send(response)

@bot.command(name='a', help='Provide your auto-complete guess')
async def guess_phrase(ctx, phrase: str):
    gfeud = GoogleFeud(ctx)
    if not gfeud.loadSession():
        response = ">>> Game has not started :bangbang:\nStart a game with `gfeud start`"
        await ctx.send(response)
    else:
        gfeud.checkPhraseInSuggestions(phrase, ctx.author)
        await ctx.send(gfeud.getGFeudBoard())

        if gfeud.isGameOver():
            await ctx.send(gfeud.getWinnerResponse())

@bot.command(name='scoreboard', help='Display scores for all players in this game session', no_category='Google Feud')
async def scoreboard(ctx):
    gfeud = GoogleFeud(ctx)
    if not gfeud.loadSession():
        response = ">>> Game has not started :bangbang:\nStart a game with `gfeud start`"
        await ctx.send(response)
    else:
        await ctx.send(gfeud.getScoreboard())


class DummyContext:
    def __init__(self):
        self.guild = 'my-guild'
        self.channel = 'my-channel'
        self.author = 'Defsin'
        self.message = 'Why am I doing this?'

if __name__ == "__main__":
    # context = DummyContext()

    # gfeud = GoogleFeud(context)
    # gfeud.loadSession()
    # gfeud.startGame("the universe is")
    # time.sleep(2)
    # print(gfeud.getGFeudBoard())
    # time.sleep(5)

    # print(gfeud.getGFeudBoard())
    # print(gfeud.getScoreboard())
    # print(gfeud.getWinnerResponse())
    # if gfeud.isGameOver():
    #     gfeud.endGame()
    #     print('end game')

    bot.run(TOKEN)