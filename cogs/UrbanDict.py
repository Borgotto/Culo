from discord.ext import commands
from discord import Embed, Member, VoiceChannel
from bs4 import BeautifulSoup, element
import requests, lxml
from random import randint

#given parent 'div' it returns the concat. of its children's text
#set 'href' to True if you want hrefs to be included in the string
def get_str_from_div(div, href=False, string=""):
    for content in div.contents:
        if type(content) is element.NavigableString:
            string += content
        elif type(content) is element.Tag and content.name == 'a':
            if href is True:
                string += '['+content.text+'](https://www.urbandictionary.com'+content.attrs['href']+')'
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
    gif = contributor = None
    try: #gif could be missing
        gif = div.contents[4].contents[0].contents[0].attrs['src']
        contributor = get_str_from_div(div.contents[5], href=False)
    except AttributeError:
        contributor = get_str_from_div(div.contents[4], href=False)
    return {'day': day, 'word': word, 'meaning': meaning, 'example': example, 'gif': gif, 'contributor': contributor}

#given word it returns the embed ready to be sent
def word_to_embed(word):
    embed=Embed(title=word['day'], color=0xffffff)
    if word['gif']: embed.set_image(url=word['gif'])
    embed.add_field(name='Word:\n', value='***'+word['word']+'***', inline=False)
    embed.add_field(name='Meaning:\n', value='***'+word['meaning']+'***', inline=False)
    embed.add_field(name='Example:', value='***'+word['example']+'***', inline=False)
    embed.set_footer(text='Definition '+word['contributor'])
    return embed

#given the urban dictionary url it returns the words on that page
def get_divs_from_url(url, limit=1):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, "lxml")
    if limit == 1:
        return soup.find('div', class_='def-panel')
    elif limit > 1:
        wotd_div = soup.find_all('div', class_='def-panel')
        return wotd_div[:limit]

class UrbanDict(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Urban Dictionary caricato!")

    @commands.command(name="wotd", aliases=["pdg"],help="Ti dice la parola del giorno")
    async def wotd(self, ctx):       
        wotd_div = get_divs_from_url("https://www.urbandictionary.com/")
        wotd = get_word_from_div(wotd_div, True)
        embed = word_to_embed(wotd)
        await ctx.send(embed=embed)

    @commands.command(name="definisci", aliases=["define", "definition", "definizione"],help="Ti dice la definizione delle parole inserite")
    async def definisci(self, ctx, *query):
        word_div = get_divs_from_url('https://www.urbandictionary.com/define.php?term=' + " ".join(query))
        word = get_word_from_div(word_div, True)
        embed = word_to_embed(word)
        await ctx.send(embed=embed)

    @commands.command(name="parola_random", aliases=["rand_parola", "rand_word", "parola", "word"],help="Ti dice la definizione di una parola a caso")
    async def rand_word(self, ctx,):   
        word_div = get_divs_from_url('https://www.urbandictionary.com/random.php?page=' + str(randint(2, 999)), limit=7)
        word = get_word_from_div(word_div[randint(0, 6)], True)
        embed = word_to_embed(word)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(UrbanDict(bot))