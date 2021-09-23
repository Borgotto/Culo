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
                string += content.text
        elif type(content) is element.Tag and content.name == 'br':
            string += '\n'
    return string.replace("\r","")

#given the WOTD div it returns Info on that Word Of The Day
def get_word_from_div(div, href=False):
    day = div.contents[0].text.upper()
    word = get_str_from_div(div.contents[1], href)
    meaning = get_str_from_div(div.contents[2], href)
    example = get_str_from_div(div.contents[3], href)

    gif = contributor = ""
    if div.contents[4].attrs['class'][0] == 'gif':
        gif = div.contents[4].contents[0].contents[0].attrs['src']
        contributor = get_str_from_div(div.contents[5], href=False)
    elif div.contents[4].attrs['class'][0] == 'contributor':
        contributor = get_str_from_div(div.contents[4], href=False)

    return {'day': day, 'word': word, 'meaning': meaning, 'example': example, 'gif': gif, 'contributor': contributor}

#given word it returns the embed ready to be sent
def word_to_embed(word):
    for key in word:
        if len(word[key]) > 1023:
            while len(word[key]) > 861:
                word[key] = word[key].rsplit(' ', 2)[0]
            word[key] += ' [...]\n[(open in the browser for the complete definition)]('+word['word'].split('(')[1]

    embed=Embed(title=word['word'].split(']')[0][1:],
                description=word['meaning'],
                url=word['word'].split('(')[1][:-1],
                color=0xFFFFFF)
    if word['gif']: embed.set_image(url=word['gif'])
    embed.add_field(name='Example:', value=word['example'], inline=False)
    embed.set_footer(text='Definition '+word['contributor'])
    return embed

#given the urban dictionary url it returns the words on that page
def get_divs_from_url(url, limit=7):
    html = get_html(url)
    soup = BeautifulSoup(html.content, "lxml")
    if limit == 1:
        return soup.find('div', class_='def-panel')
    elif limit > 1:
        wotd_div = soup.find_all('div', class_='def-panel')
        return wotd_div[:limit]



###################
#    cog class    #
###################
class UrbanDictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot        
        try:
            file = open('config/wotd_settings.json', 'r'); file.close()
        except IOError:
            file = open('config/wotd_settings.json', 'w'); file.write('{\n\t"last_wotd": "",\n\t"channel_ids": {\n\t}\n}'); file.close()

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
        with open('config/wotd_settings.json', 'r') as file:
            wotd_settings = json.load(file)

        words_to_send = []
        wotd_divs = get_divs_from_url("https://www.urbandictionary.com/")
        for div in wotd_divs:
            if div.contents[1].text != wotd_settings["last_wotd"]:
                words_to_send.append(get_word_from_div(div, href=True))
            else: break

        if len(words_to_send) > 0:
            wotd_settings["last_wotd"] = wotd_divs[0].contents[1].text
            with open('config/wotd_settings.json', 'w') as file:
                json.dump(wotd_settings, file, indent=4) 
            if len(words_to_send) < 7:
                for id in wotd_settings["channel_ids"].values():       
                    channel = self.bot.get_channel(id)
                    if channel is not None: 
                        #await channel.send("**New WOTD dropped**")
                        for wotd in reversed(words_to_send):
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

        await ctx.send(f'Channel set to: <#{channel[2:-1]}>') 

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
        wotd_div = get_divs_from_url("https://www.urbandictionary.com/", limit=1)
        wotd = get_word_from_div(wotd_div, True)
        embed = word_to_embed(wotd)
        await ctx.send(f"**Here's today's Word of the Day!**",embed=embed)

    @commands.command(name="define", aliases=["definisci", "definition", "definizione"],help="Get the urban definition of a word")
    async def definisci(self, ctx, *query):
        query = " ".join(query)
        encodedURL = 'https://www.urbandictionary.com/define.php?term=' + quote(query)
        word_div = get_divs_from_url(encodedURL, limit=1)
        if word_div is None: return await ctx.send("**¯\_(ツ)_/¯**\nSorry, we couldn't find the definition of: `"+ query +"`")
        word = get_word_from_div(word_div, True)
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