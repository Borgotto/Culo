import discord
from discord.ext import commands
from discord import Intents
import os
import sys
import json

###################
#    bot setup    #
###################
def get_token():
    if os.getenv('BOT_TOKEN') is not None:
        return os.environ.get("BOT_TOKEN")
    if len(sys.argv) > 1:
        return sys.argv[1]
    try:
        with open('token') as file:
            return file.readline()
    except IOError:
        print("\nTi manca il TOKEN del bot!\nPassalo come argomento\nOppure imposta una variabile d'ambiente 'BOT_TOKEN'\nOppure crea un file 'TOKEN' con all'interno il token\n")
        quit()

#function that returns the bot prefix by the guild id
def get_prefix(client, message):
    with open('prefixes.json', 'r') as file:
        prefixes = json.load(file)
    return prefixes[str(message.guild.id)]  

#updates prefixes.json with the right prefixes, deleting unnecessary ones and adding missing ones
def update_prefixes():
    with open('prefixes.json', 'r') as file: 
        prefixes = json.load(file)     
    
        updated_prefixes = { }

        for guild in bot.guilds:
            try:
                updated_prefixes[str(guild.id)] = str(prefixes[str(guild.id)])
            except KeyError:
                updated_prefixes[str(guild.id)] = '🍑 '

    with open('prefixes.json', 'w') as file: 
        json.dump(updated_prefixes, file, indent=4)

#create the prefixes.json file if it doesn't exist
try:
    file = open('prefixes.json', 'r'); file.close()
except IOError:
    file = open('prefixes.json', 'w'); file.write("{}"); file.close()

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
    with open('prefixes.json', 'r') as file: 
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
    with open('prefixes.json', 'r') as file: 
        prefixes = json.load(file) 

    prefixes[str(guild.id)] = '🍑' #default prefix

    with open('prefixes.json', 'w') as file: 
        json.dump(prefixes, file, indent=4) 
    
    #updates to bot presence
    #await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

@bot.event
async def on_guild_remove(guild): 
    with open('prefixes.json', 'r') as file: 
        prefixes = json.load(file)

    prefixes.pop(str(guild.id)) 

    with open('prefixes.json', 'w') as file:
        json.dump(prefixes, file, indent=4)

    #updates to bot presence
    #await bot.change_presence(status = discord.Status.online, activity = (discord.Activity(name= f"alle bestemmie di {len(bot.guilds)} server...", type=discord.ActivityType.listening)))

@bot.command(name="cambia_prefisso", aliases=["prefisso"], help="Cambia il prefisso per i comandi del bot")
@commands.has_permissions(administrator=True) 
async def cambia_prefisso(ctx, prefisso : str): 
    with open('prefixes.json', 'r') as file:
        prefixes = json.load(file)

    prefixes[str(ctx.guild.id)] = prefisso

    with open('prefixes.json', 'w') as file: 
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
print()



################################
#    command error handling    #
################################
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return await ctx.send(f'Comando sconosciuto :peach: :poop:')

    if isinstance(error, commands.MissingPermissions):
        return await ctx.send(f'Non hai i permessi per usare questo comando...\nCosa pensavi di fare eh? :peach: :poop:')

    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f'Manca qualche argomento per usare questo comando... :peach: :thinking:')

    return await ctx.send("C'è stato un errore con il comando, hai inserito i giusti parametri? :peach: :weary:")

@bot.command(help="Genera un errore")
@commands.is_owner()
async def errore(ctx):
    raise commands.ArgumentParsingError




#####################
#    run the bot    #
#####################
bot.run(get_token())