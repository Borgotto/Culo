import discord
from discord.ext import commands
import os
import json

###################
#    bot setup    #
###################
def get_token():
    try:
        with open('token') as file:
            return file.readline()
    except IOError:
        print("Insert bot token: ", end="")
        token = str(input())
        with open('token', 'w') as file:
            file.write(token)
        return token

token = get_token()

#function that returns the bot prefix by the guild id
def get_prefix(client, message):
    with open('prefixes.json', 'r') as file:
        prefixes = json.load(file)
    return prefixes[str(message.guild.id)]   

bot = commands.Bot(command_prefix = (get_prefix))

##################
#    on ready    #
##################
@bot.event
async def on_ready():
    print ("\n--------------------------------\n")
    print ("Bot Name:", bot.user.name)
    print ("Bot ID:", bot.user.id)
    #print ("Bot token:", token)
    #print ("Bot prefix:", bot.command_prefix)
    print ("Discord Version:", discord.__version__)
    print ("\n--------------------------------\n")

    #updates to bot presence
    await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

    #print all server names the bot is in and an invite to that server
    print("List of all servers the bot is in:\n")
    for guild in bot.guilds:
        print("Server name:", guild.name)
        print("Server ID:", guild.id, end="\n\n")
    print ("--------------------------------\n")

#########################
#    prefix handling    #
#########################
@bot.event
async def on_guild_join(guild): 
    with open('prefixes.json', 'r') as file: 
        prefixes = json.load(file) 

    prefixes[str(guild.id)] = '🍑 ' #default prefix

    with open('prefixes.json', 'w') as file: 
        json.dump(prefixes, file, indent=4) 
    
    #updates to bot presence
    await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

@bot.event
async def on_guild_remove(guild): 
    with open('prefixes.json', 'r') as file: 
        prefixes = json.load(file)

    prefixes.pop(str(guild.id)) 

    with open('prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

    #updates to bot presence
    await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

@bot.command()
@commands.has_permissions(administrator=True) 
async def cambia_prefisso(ctx, prefix : str): 
    with open('prefixes.json', 'r') as file:
        prefixes = json.load(file)

    prefixes[str(ctx.guild.id)] = prefix

    with open('prefixes.json', 'w') as file: 
        json.dump(prefixes, file, indent=4)

    await ctx.send(f'Prefix changed to: {prefix}') 

#######################
#    cogs handling    #
#######################
@bot.command()
async def attiva(ctx, plugin : str):
    if (ctx.author.id == 289887222310764545):
        bot.load_extension(f'cogs.{plugin.title()}')
        await ctx.send(f'Ho attivato: {plugin.title()}')
    else:
        await ctx.send(f'Solo il mio creatore <@289887222310764545> può attivare o disattivare i moduli')

@bot.command()
async def disattiva(ctx, plugin : str):
    if (ctx.author.id == 289887222310764545):
        bot.unload_extension(f'cogs.{plugin.title()}')
        await ctx.send(f'Ho disattivato: {plugin.title()}')
    else:
        await ctx.send(f'Solo il mio creatore <@289887222310764545> può attivare o disattivare i moduli')

@bot.command()
@commands.has_permissions(administrator=True)
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
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'Comando sconosciuto :peach: :poop:')

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f'Non hai i permessi per usare questo comando...\nCosa pensavi di fare eh? :peach: :poop:')

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Manca qualche argomento per usare questo comando...')

#####################
#    run the bot    #
#####################
bot.run(token)