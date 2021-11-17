import discord
from discord.ext import commands
from discord import Intents
from requests import get
import os
import sys
import json

###################
#    bot setup    #
###################
def get_token():
    if os.getenv('BOT_TOKEN') is not None:
        return os.environ.get("BOT_TOKEN")
    try:
        with open('token') as file:
            return file.readline()
    except IOError:
        print("\nTi manca il TOKEN del bot!\nImposta una variabile d'ambiente 'BOT_TOKEN'\nOppure crea un file 'TOKEN' con all'interno il token\n")
        quit()

#function that returns the bot prefix by the guild id
def get_prefix(client, message):
    if message.guild is None: return '🍑'
    with open('config/prefixes.json', 'r') as file:
        prefixes = json.load(file)
    return prefixes[str(message.guild.id)]

#updates prefixes.json with the right prefixes, deleting unnecessary ones and adding missing ones
def update_prefixes():
    with open('config/prefixes.json', 'r') as file:
        prefixes = json.load(file)

        updated_prefixes = { }

        for guild in bot.guilds:
            try:
                updated_prefixes[str(guild.id)] = str(prefixes[str(guild.id)])
            except KeyError:
                updated_prefixes[str(guild.id)] = '🍑'

    with open('config/prefixes.json', 'w') as file:
        json.dump(updated_prefixes, file, indent=4)

#create config folder if it doesn't exist
if not os.path.exists('./config/'):
    os.makedirs('./config/')

#create the prefixes.json file if it doesn't exist
try:
    file = open('config/prefixes.json', 'r'); file.close()
except IOError:
    file = open('config/prefixes.json', 'w'); file.write("{}"); file.close()

#set the bot prefix to an instance of the get_prefix function
bot = commands.Bot(command_prefix = (get_prefix), owner_id=289887222310764545, intents=Intents.all(), strip_after_prefix=True)



######################
#    on bot ready    #
######################
@bot.event
async def on_ready():
    #updates to bot presence
    await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"🍑 👀", type=discord.ActivityType.watching)))

    #makes sure the different prefixes are up to date with the bot's actual servers
    update_prefixes()

    #print a bunch of info about the bot
    print ("\n--------------------------------\n")
    print ("Bot Name:", bot.user.name)
    print ("Bot ID:", bot.user.id)
    print ("Discord Version:", discord.__version__)
    print ("\n--------------------------------\n")
    #print servers info
    with open('config/prefixes.json', 'r') as file:
        prefixes = json.load(file)
        print(f'The bot is in {len(bot.guilds)} servers!')
        print("List of all servers the bot is in:", end="\n\n")
        for guild in bot.guilds:
            print("Server name:", guild.name)
            print("Server prefix:", prefixes[str(guild.id)], end="\n\n")
    print ("--------------------------------\n")



#########################
#    prefix handling    #
#########################
@bot.event
async def on_guild_join(guild):
    with open('config/prefixes.json', 'r') as file:
        prefixes = json.load(file)

    prefixes[str(guild.id)] = '🍑' #default prefix

    with open('config/prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

    #updates to bot presence
    #await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

@bot.event
async def on_guild_remove(guild):
    with open('config/prefixes.json', 'r') as file:
        prefixes = json.load(file)

    prefixes.pop(str(guild.id))

    with open('config/prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

    #updates to bot presence
    #await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

@bot.command(name="cambia_prefisso", aliases=["prefisso"], help="Cambia il prefisso per i comandi del bot")
@commands.has_permissions(administrator=True)
async def cambia_prefisso(ctx, prefisso : str):
    with open('config/prefixes.json', 'r') as file:
        prefixes = json.load(file)

    prefixes[str(ctx.guild.id)] = prefisso

    with open('config/prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

    await ctx.send(f'Prefisso cambiato a: {prefisso}')




#######################
#    cogs handling    #
#######################
@bot.command(help="Attiva una cog")
@commands.is_owner()
async def attiva(ctx, cog : str):
    bot.load_extension(f'cogs.{cog.title()}')
    await ctx.send(f'Ho attivato: {cog.title()}')

@bot.command(help="Disattiva una cog")
@commands.is_owner()
async def disattiva(ctx, cog : str):
    bot.unload_extension(f'cogs.{cog.title()}')
    await ctx.send(f'Ho disattivato: {cog.title()}')

@bot.command(help="Ricarica tutte le cog")
@commands.is_owner()
async def ricarica(ctx):
    for filename in os.listdir('./cogs'):
        if (filename.endswith('.py')):
            bot.unload_extension(f'cogs.{filename[:-3]}')
            bot.load_extension(f'cogs.{filename[:-3]}')
    await ctx.send(f'Cog ricaricati!')

#carica tutti i cog all'avvio
for filename in os.listdir('./cogs'):
    if (filename.endswith('.py')):
        bot.load_extension(f'cogs.{filename[:-3]}')



################################
#    command error handling    #
################################
@bot.event
async def on_command_error(ctx, error):
    #generic error message, overwritten if a more specific one is found
    error_message = f"C'è stato qualche errore con il comando :peach: :poop:"

    if isinstance(error, commands.CommandNotFound):
        error_message = f"Comando sconosciuto :peach: :poop:"
    if isinstance(error, commands.MissingPermissions):
        error_message = f"Non hai i permessi per usare questo comando...\nCosa pensavi di fare eh? :peach: :poop:"
    if isinstance(error, commands.MissingRequiredArgument):
        error_message = f"Manca qualche argomento per usare questo comando... :peach: :thinking:"

    await ctx.send(error_message, reference=ctx.message, mention_author=False)

    # a more detailed error is sent to the bot owner
    await bot.get_user(bot.owner_id).send(f"**There was an error with the bot!**\n`{error.original}`\n\n\
    **Server:**  `{ctx.guild.name} [{ctx.guild.id}]`\n\
    **Channel:**  `{ctx.channel.name} [{ctx.channel.id}]`\n\
    **Command:**  `{ctx.command.name}`\n\
    **Arguments:**  `{ctx.message.content.split(ctx.command.name)}`\n\
    **Command author:**  {ctx.message.author.mention} `[{ctx.message.author.id}]`\n\
    **Date:**  `{ctx.message.created_at.strftime('%d/%m/%Y - %H:%M:%S')}`\n\
", allowed_mentions=False)


############################
#    debugging commands    #
############################
@bot.command(name="purge", help="Deletes # of the messages sent by the bot")
@commands.is_owner()
async def purge(ctx, amount : int = 7):
    for i in range(amount):
        await discord.utils.get(await ctx.channel.history(limit=100).flatten(), author=bot.user).delete()

@bot.command(name="test_errore", help="Genera un errore")
@commands.is_owner()
async def errore(ctx):
    raise commands.ArgumentParsingError

@bot.command(name="test_messaggio", help="Prova a mandare un messaggio in un canale specifico")
@commands.is_owner()
async def test_messaggio(ctx, channel):
    pass

@bot.command(name="print", help="Print something on stdout")
@commands.is_owner()
async def print_console(ctx, *string : str):
    print(str(*string))
    await ctx.send(f"Printed `{str(*string)}` in terminal")

@bot.command(name="public_ip", help="Returns the public ip of the network hosting the bot")
@commands.is_owner()
async def public_ip(ctx):
    await ctx.send(f"`{get('https://ident.me').text}`", delete_after=3)
    await ctx.message.delete()


#####################
#    run the bot    #
#####################
bot.run(get_token())