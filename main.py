import os
import traceback
import discord
import asyncio
import re

from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument
from dotenv import load_dotenv
from googlefeud.GoogleFeud import GoogleFeud
from googlefeud.LoggerPrint import logger

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

SUPPORT_SERVER_URL = 'https://discord.com/invite/xX5mk8Esg3'

help_command = commands.DefaultHelpCommand(
    no_category = 'Google Feud'
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=['gfeud ', 'gf ', 'Gf ', 'gF ', 'GF '], 
    description='Google Feud is a game much like Family Feud, except the phrases on the wall are Google\'s auto-complete suggestions. Guess what the auto-completes are for a given phrase to win the game!', 
    help_command=help_command, case_insensitive=True, intents=intents)

print = logger(print)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="gf help"))
    print(f"Beep Boop I am ready to serve the humans. Currently serving {len(bot.guilds)} human gatherings")

@bot.command(name='start', help='Starts a game of Google Feud')
async def start_game(ctx):
    try:
        gfeud = GoogleFeud(ctx)
        gfeud.loadSession()
        gfeud.startGame()
    except RuntimeError as error:
        print(ctx, 'Problem starting game: ', error)
        
    response = gfeud.getGFeudBoard()

    await ctx.send(response)

@bot.command(name='end', help='Ends a game of Google Feud')
async def end_game(ctx):
    gfeud = GoogleFeud(ctx)
    gfeud.loadSession()
        
    if gfeud.endGame():
        print(ctx, f'Ended game successfully')
        response = ">>> Ended the game :ok_hand:\nStart again with `gf start`"
    else:
        print(ctx, f'No game to end')
        response = ">>> Game is not in progress :confused:\nStart a game with `gf start`"

    await ctx.send(response)

@bot.command(name='a', help='Provide your auto-complete guess\n\nFor example,\ngf a super neat answer')
async def guess_phrase(ctx, phrase: str):
    try:
        gfeud = GoogleFeud(ctx)
        if not gfeud.loadSession():
            print(ctx, f'Game hasn\'t started yet')
            response = ">>> Game has not started :bangbang:\nStart a game with `gf start`"
            await ctx.send(response)
        else:
            print(ctx, f'Check if "{phrase}" is in auto-complete sentence')
            gfeud.checkPhraseInSuggestions(phrase, ctx.author)

            if gfeud.isGameOver():
                print(ctx, f'Game over')
                gfeud.endGame()
                await ctx.send(gfeud.getGFeudBoard())
                await ctx.send(gfeud.getWinnerResponse())
                gfeud.endGame()
            else:
                await ctx.send(gfeud.getGFeudBoard())
    except Exception as error:
        print(ctx, 'ERROR: Game failed, shutting down game. ', error)
        traceback.print_exc()
        gfeud.endGame()
        await ctx.send('>>> Our bad, something might\'ve broken  :confounded:\nFeel free to report this to the support server: ' + SUPPORT_SERVER_URL)

@bot.command(name='scoreboard', help='Display scores for all players in this game session', no_category='Google Feud')
async def scoreboard(ctx):
    gfeud = GoogleFeud(ctx)
    if not gfeud.loadSession():
        response = ">>> Game has not started :bangbang:\nStart a game with `gf start`"
        await ctx.send(response)
    else:
        await ctx.send(gfeud.getScoreboard())

@bot.command(name='review', hidden=True)
async def review_phrase(ctx):
    check_mark = '✅'
    x_mark = '❌'
    def check(reaction, user):
        return user == ctx.author and (reaction.emoji == check_mark or reaction.emoji == x_mark)

    gfeud = GoogleFeud(ctx)
    if gfeud.isUserAnAdmin():
        response, contribution = gfeud.getSuggestionsFromContribution()
        if response == None:
            await ctx.send('> No contributions to review  :sunglasses:')
            return

        phrase = contribution['phrase']
        user_id = contribution['user_id']

        msg = await ctx.send(response)
        await msg.add_reaction(check_mark)
        await msg.add_reaction(x_mark)

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            if reaction.emoji == check_mark:
                await ctx.send(f"> Added the phrase **{phrase}** to the collection! :grin:")
                gfeud.add_phrase(phrase, user_id)
            elif reaction.emoji == x_mark:
                await ctx.send("> Ok I won't add **" + phrase + '**  :woozy_face:  Rejecting the contribution')
            gfeud.delete_contribution(phrase)
        except asyncio.TimeoutError:
            await ctx.send(f'> The phrase **{phrase}** was not added because you took too long  :rage:')
    else:
        raise CommandNotFound(str(ctx.author) + ' is not authorized to use this command')

@bot.command(name='contribute', help='Help us out by contributing your own Google phrase\n\nFor example,\ngf contribute why do cats')
async def add_phrase(ctx, *, phrase: str):
    check_mark = '✅'
    x_mark = '❌'
    def check(reaction, user):
        return user == ctx.author and (reaction.emoji == check_mark or reaction.emoji == x_mark)

    gfeud = GoogleFeud(ctx)

    clean_phrase = phrase.lower()
    clean_phrase = ' '.join(clean_phrase.split())

    if gfeud.isUserAnAdmin():
        response, _ = gfeud.showSuggestionsOfCandidatePhrase(clean_phrase, True)
        if not response:
            await ctx.send('> This phrase already exists  :confused:')
            return
        msg = await ctx.send(response)
        await msg.add_reaction(check_mark)
        await msg.add_reaction(x_mark)

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            if reaction.emoji == check_mark:
                await ctx.send(f"> Added the phrase **{clean_phrase}** to the collection! :grin:")
                gfeud.add_phrase(clean_phrase, None)
            elif reaction.emoji == x_mark:
                await ctx.send("> Ok I won't add **" + clean_phrase + '**  :woozy_face:')

        except asyncio.TimeoutError:
            await ctx.send(f'> The phrase **{clean_phrase}** was not added because you took too long  :rage:')
    else:
        if not bool(re.match(r'^[A-z0-9 ]+$', clean_phrase)):
            await ctx.send("> Your phrase can only contain alphanumeric characters  :anguished:")
            return

        if len(clean_phrase) > 60:
            await ctx.send("> Your phrase is too long  :mask:")
            return

        num_of_contributions = gfeud.get_num_of_contributions_left()

        if num_of_contributions <= 0:
            await ctx.send("> You've reached your daily limit of contributions. Thank you for your help!  :relaxed:")
            return

        response, suggestions = gfeud.showSuggestionsOfCandidatePhrase(clean_phrase, False)
        if not response:
            await ctx.send('> This phrase already exists  :confused:')
            return
        msg = await ctx.send(response)

        if len(suggestions) < 3:
            return

        await msg.add_reaction(check_mark)
        await msg.add_reaction(x_mark)

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            if reaction.emoji == check_mark:
                await ctx.send(f"> Submitted the phrase **{clean_phrase}**! We'll review it soon. Thanks for the contribution! :grin:")
                gfeud.add_contribution(clean_phrase, suggestions)
                new_num_of_contributions = gfeud.get_num_of_contributions_left()
                await ctx.send(f"> You can contribute **{new_num_of_contributions}** more time(s)")
            elif reaction.emoji == x_mark:
                await ctx.send("> Ok I won't submit **" + clean_phrase + '**  :woozy_face:')

        except asyncio.TimeoutError:
            await ctx.send(f'> The phrase **{clean_phrase}** was not submitted because you took too long  :rage:')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        print(ctx, error)
        response = ">>> Unknown command  :grimacing: Run `gf help` for valid commands"
        await ctx.send(response)
        return

    if isinstance(error, MissingRequiredArgument):
        print(ctx, error)
        if "phrase" == error.param.name:
            response = ">>> Provide a phrase with that command  :wink:\n.e.g `gf a this is my answer`"
        else:
            response = f">>> Unknown command {error.param.name}. Run `gf help` for valid commands"
        await ctx.send(response)
        return

    raise error

@bot.event
async def on_message(message):
    sectioned_msgs = message.content.split(' ')
    if not sectioned_msgs[0] == None and (sectioned_msgs[0].lower() == 'gf' or sectioned_msgs[0].lower() == 'gfeud'):
        print(message, message.content)
    
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)