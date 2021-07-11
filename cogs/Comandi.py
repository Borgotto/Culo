from discord.ext import commands
from discord import Embed, Member, VoiceChannel
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, element
import requests

#given parent 'div' it returns the concat. of its children's text
#set 'href' to True if you want hrefs to be included in the string
def get_str_from_div(div, href=False, string=""):
    for content in div.contents:
        if type(content) is element.NavigableString:
            string += content
        elif type(content) is element.Tag:
            if content.name == 'a':
                if href is True:
                    string += '['+content.text+'](https://www.urbandictionary.com'+content.attrs['href']+')'
                else:
                    string += content.text
            if content.name == 'br':
                string += '\n'
    return string

#given the WOTD div it returns Info on that Word Of The Day
def get_wotd_from_div(div, href=False):
    day = div.contents[0].text
    word = get_str_from_div(div.contents[1], href)
    meaning = get_str_from_div(div.contents[2], href)
    example = get_str_from_div(div.contents[3], href)
    gif = contributor = None
    try: #gif could be missing
        gif = div.contents[4].contents[0].contents[0].attrs['src']
        contributor = get_str_from_div(div.contents[5], href=False)
    except AttributeError:
        contributor = get_str_from_div(div.contents[4], href=False)
    return {'day': day, 'word': word, 'meaning': meaning, 'example': example, 'gif': gif, 'contributor': contributor}

class Comandi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):        
        print("Comandi caricati!")


    @commands.command(name="temperatura", aliases=['temp'], help="Se il bot gira su un raspberry ritorna la temperatura della CPU")
    @commands.is_owner()
    async def temperatura(self, ctx):
        try:
            with open('/sys/class/thermal/thermal_zone0/temp') as file:
                temperatura = float(file.readline(3))/10
                emoji = ':fire:' if temperatura > 56 else ':ice_cube:'
                await ctx.send(f"*Temperatura:*  **{temperatura}** *°C*  {emoji}")
        except:
            await ctx.send(f"C'è stato un errore nel leggere la temperatura, il bot sta eseguendo su un raspberry? :thinking:")


    @commands.command(name="chisono", aliases=['whoami'], help="Ti ricorda chi sei veramente")
    async def chisono(self, ctx):
        await ctx.send(f"Sei un trimone {ctx.message.author.mention}")


    @commands.command(name="scorreggia", aliases=["scoreggia", "cagati"], help="Comando inutile, provare per credere")
    async def scorreggia(self, ctx):
        await ctx.send(f"Oh no mi sono cagato addosso")


    @commands.command(name="pinga", aliases=["pinga_utente", "ping"], help="Pinga un utente")
    async def pinga(self, ctx, user : Member, amount=1): 
        if (amount > 5):
                await ctx.send("Oh ma sei impazzito? Non posso pingare tutte quelle volte")
        else:                
            for x in range(0, amount):
                await ctx.send(f"{user.mention}")


    @commands.command(name="raduna", aliases=["radunata", "meeting"], help="Raduna tutti gli utenti in chat vocale nello stesso canale")
    @commands.has_permissions(administrator=True)
    async def raduna(self, ctx, canale : VoiceChannel=None):
        if canale is None:
            if ctx.author.voice is None:
                return await ctx.send(f"{ctx.author.mention} Devi essere in un canale vocale o specificare quale canale in cui radunare la gente")
            else:
                canale = ctx.author.voice.channel

        for channel in ctx.guild.voice_channels:
            for member in channel.members:
                await member.move_to(canale)


    @commands.command(name="cancella", aliases=["delete","canc"],help="Cancella # messaggi")
    @commands.has_permissions(manage_messages=True)
    async def cancella(self, ctx, amount : int, mode="messaggi"):
        if amount < 1:
            return await ctx.send("Inserisci un valore valido per la quantità di messaggi da eliminare")

        if (mode == "messaggi" or mode == "mess"):
            if (amount > 100):
                return await ctx.send("Oh ma sei impazzito? Non posso cancellare tutti quei messaggi")
            else:    
                await ctx.channel.purge(limit=int(amount)+1)

        elif (mode in ['minuto','minuti','min','m','ora','ore','h','o','giorno','giorni','g','d']):
            if mode in ['ora','ore','h','o']: amount = amount * 60
            if mode in ['giorno','giorni','g','d']: amount = amount * 1440

            if amount > 4320: 
                return await ctx.send(f"Oh ma sei impazzito? Non posso cancellare tutti quei messaggi")

            data_comando = ctx.channel.last_message.created_at
            differenza = timedelta(minutes=amount)
            messaggi = await ctx.channel.history(after=(data_comando-differenza)).flatten()
            await ctx.channel.delete_messages(messaggi)

        else:
            await ctx.send("Puoi cancellare gli ultimi # messaggi con:\n\t``` cancella # messaggi```\nOppure cancellare i messaggi inviati negli ultimi minuti/ore/giorni con:\n\t``` cancella 5 minuti  /  cancella 1 ora  /  cancella 2 giorni```")


    @commands.command(name="wotd", aliases=["parola", "pdg", "word of the day", "parola del giorno"],help="Ti dice la parola del giorno")
    async def wotd(self, ctx, tutte=False):
        print("wotd")
        html = requests.get("https://www.urbandictionary.com/")
        soup = BeautifulSoup(html.content, "lxml")
        print(soup.prettify())
        wotd_div = soup.find_all('div', class_='def-panel')
        wotd = get_wotd_from_div(wotd_div[0], True)
        print(wotd)
        
        embed=Embed(title=wotd['day'].upper(), color=0xffffff)
        if wotd['gif'] is not None: embed.set_image(url=wotd['gif'])
        embed.add_field(name='Word:\n', value='***'+wotd['word']+'***', inline=False)
        embed.add_field(name='Meaning:\n', value='***'+wotd['meaning']+'***', inline=False)
        embed.add_field(name='Example:', value='***'+wotd['meaning']+'***', inline=False)
        embed.set_footer(text='Definition '+wotd['contributor'])
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Comandi(bot))