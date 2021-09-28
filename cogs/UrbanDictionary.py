from discord.ext import commands, tasks
from discord.utils import escape_markdown
from discord import Embed
from bs4 import BeautifulSoup, element
from requests import get as get_html
from urllib.parse import quote
import lxml
from random import randint
import json

#############################
#    auxiliary functions    #
#############################

#given a url from urban dictionary it returns the div elements containing words
def get_divs_from_url(url):
    html = get_html(url)
    soup = BeautifulSoup(html.content, "lxml")
    return soup.find_all('div', class_='def-panel')

#given parent 'div' it returns the concat. of its children's text
#set 'href' to True if you want hrefs to be included in the string
def get_str_from_div(div, href=False, string=""):
    for content in div.contents:
        if type(content) is element.NavigableString:
            string += escape_markdown(content)
        elif type(content) is element.Tag and content.name == 'a' and 'href' in content.attrs:
            if href is True:
                string += '['+escape_markdown(content.text)+'](https://www.urbandictionary.com'+content.attrs['href']+')'
            else:
                string += escape_markdown(content.text)
        elif type(content) is element.Tag and content.name == 'br':
            string += '\n'
    return string.replace("\r","")

#given the WOTD div it returns Info on that Word Of The Day
def get_word_from_div(div, href=False):
    day = div.contents[0].text
    word = div.contents[1].text
    url = 'https://www.urbandictionary.com'+div.contents[1].contents[0].attrs['href']
    meaning = get_str_from_div(div.contents[2], href=href)
    example = get_str_from_div(div.contents[3], href=href)

    gif = contributor = ""
    if div.contents[4].attrs['class'][0] == 'gif':
        gif = div.contents[4].contents[0].contents[0].attrs['src']
        contributor = get_str_from_div(div.contents[5], href=False)
    elif div.contents[4].attrs['class'][0] == 'contributor':
        contributor = get_str_from_div(div.contents[4], href=False)

    return {'day': day, 'word': word, 'url': url, 'meaning': meaning, 'example': example, 'gif': gif, 'contributor': contributor}

#given word it returns the embed ready to be sent
def word_to_embed(word):
    if len(word['word']) > 255:
        word['word'] = word['word'][:251]+'...'

    if len(word['meaning']) > 4095:
        word['meaning'] = word['meaning'][:3700]
        word['meaning'] = word['meaning'].rsplit(' ', 2)[0]
        word['meaning'] += ' [...]\n[(open in the browser for the complete definition)]('+word['url']+')'

    if len(word['example']) > 1023:
        word['example'] = word['example'][:1020]+'...'

    embed=Embed(title=escape_markdown(word['word']),
            description=word['meaning'], 
            url=word['url'], 
            color=0x134FE6)
    if word['gif']: embed.set_image(url=word['gif'])
    embed.add_field(name='Example:', value=word['example'], inline=False)
    embed.set_footer(text='Definition '+word['contributor'])
    return embed



###################
#    cog class    #
###################
class UrbanDictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_word = ""
        try:
            with open('config/wotd_settings.json', 'r') as file:
                self.last_word = json.load(file)["last_word"]
        except IOError:
            with open('config/wotd_settings.json', 'w') as file:
                json.dump({"last_word": "","channel_ids": {}}, file, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        self.wotd_loop.start()
        print("Urban Dictionary caricato!")



    ###################
    #    wotd loop    #
    ###################
    #sends the wotd every day in the channels from wotd_settings.json
    @tasks.loop(minutes=9)
    async def wotd_loop(self):
        wotd_divs = get_divs_from_url("https://www.urbandictionary.com/")

        words_to_send = []  
        if self.last_word == "":
            words_to_send.append(get_word_from_div(wotd_divs[0], href=True))
        else:            
            for div in wotd_divs:
                if div.contents[1].text != self.last_word:
                    words_to_send.append(get_word_from_div(div, href=True))
                else: break

        if 0 < len(words_to_send) < 6:
            self.last_word = wotd_divs[0].contents[1].text
            with open('config/wotd_settings.json', 'r') as file:
                wotd_settings = json.load(file)
                wotd_settings["last_word"] = self.last_word
            with open('config/wotd_settings.json', 'w') as file:
                json.dump(wotd_settings, file, indent=4) 

            for id in wotd_settings["channel_ids"].values():       
                channel = self.bot.get_channel(id)
                if channel is not None: 
                    await channel.send("**New WOTD dropped**")
                    for wotd in words_to_send:
                        await channel.send(embed=word_to_embed(wotd))



    ####################
    #    loop setup    #
    ####################
    @commands.command(name="set_wotd_channel",help="Pass the channel you want the WOTD to be sent every day")
    @commands.has_permissions(administrator=True) 
    async def set_wotd_channel(self, ctx, channel):
        if self.bot.get_channel(int(channel[2:-1])) is None:
            return await ctx.send(f"Channel passed is not valid or it's hidden from the bot") 
            
        with open('config/wotd_settings.json', 'r') as file:
            wotd_settings = json.load(file)

        wotd_settings["channel_ids"][str(ctx.guild.id)] = int(channel[2:-1])

        with open('config/wotd_settings.json', 'w') as file: 
            json.dump(wotd_settings, file, indent=4)

        await ctx.send(f'Channel set to: {channel}') 

    @commands.command(name="remove_wotd_channel",help="Unset the channel for the WOTD")
    @commands.has_permissions(administrator=True) 
    async def remove_wotd_channel(self, ctx):
        with open('config/wotd_settings.json', 'r') as file:
            wotd_settings = json.load(file)
        try:
            wotd_settings["channel_ids"].pop(str(ctx.guild.id)) 
            with open('config/wotd_settings.json', 'w') as file: 
                json.dump(wotd_settings, file, indent=4)
            await ctx.send(f'Channel unset') 
        except KeyError:
            await ctx.send(f'The channel for the WOTD is not set') 

    @commands.command(name="restart_wotd_loop",help="Restart the WOTD Task")
    @commands.is_owner()
    async def restart_wotd_loop(self, ctx):
        self.wotd_loop.restart()



    ############################
    #    urbandict commands    #
    ############################
    @commands.command(name="wotd", aliases=["pdg"],help="It tells you the Word of the Day!")
    async def wotd(self, ctx):  
        wotd_div = get_divs_from_url("https://www.urbandictionary.com/")
        wotd = get_word_from_div(wotd_div[0], True)
        embed = word_to_embed(wotd)
        await ctx.send(f"**Here's today's Word of the Day!**",embed=embed)

    @commands.command(name="define", aliases=["definisci", "definition", "definizione"],help="Get the urban definition of a word")
    async def definisci(self, ctx, *query):
        query = " ".join(query)
        encodedURL = 'https://www.urbandictionary.com/define.php?term=' + quote(query)
        word_div = get_divs_from_url(encodedURL)
        if word_div == []: return await ctx.send("**¯\_(ツ)_/¯**\nSorry, we couldn't find the definition of: `"+ query +"`")
        word = get_word_from_div(word_div[0], True)
        embed = word_to_embed(word)
        await ctx.send(f"**Definition of: ** `"+ query +"`",embed=embed)

    @commands.command(name="rand_word", aliases=["rand_parola", "parola_random", "parola", "word"],help="Feeling lucky? Get a random word")
    async def rand_word(self, ctx):   
        word_divs = get_divs_from_url('https://www.urbandictionary.com/random.php?page=' + str(randint(2, 999)))
        word = get_word_from_div(word_divs[randint(0, 6)], True)
        embed = word_to_embed(word)
        await ctx.send(f"**Here's a random word from Urban Dictionary**",embed=embed)



def setup(bot):
    bot.add_cog(UrbanDictionary(bot))