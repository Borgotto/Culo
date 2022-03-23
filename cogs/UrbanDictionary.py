from discord.ext import commands, tasks
from discord.utils import escape_markdown, get
from discord import Embed

import requests
import urllib.parse
from bs4 import BeautifulSoup, element
import lxml
from random import randint
import json

#############################
#    auxiliary functions    #
#############################

def _get_string_from_div(div: element.Tag, markdown: bool = False):
    string = ""
    for child in div.children:
        if markdown:
            text = escape_markdown(child.text)
        else:
            text = child.text

        if isinstance(child, element.Tag) and child.name == "a" and markdown:
            string += (f"[{text}]" +
                        "(https://www.urbandictionary.com" +
                       f"{child.attrs['href']})")
        elif isinstance(child, element.Tag) and child.name == "br":
            string += "\n"
        else:
            string += text
    return string

def get_words_from_url(url: str, markdown: bool = False):
    # Static Session object
    try:
        session = get_words_from_url.session
    except AttributeError:
        session = get_words_from_url.session = requests.Session()

    # Fetch all of the html divs containing the words definitions
    response = session.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    divs = soup.findAll("div", class_="definition")
    words: list[Word] = []

    # Foreach definition div extract the Word and append it to the list
    for div in divs:
        word_divs = div.contents[0].contents
        word = Word(url="https://www.urbandictionary.com" +
                        word_divs[0].contents[0].contents[0].attrs["href"],
                    name=_get_string_from_div(word_divs[0], markdown),
                    meaning=_get_string_from_div(word_divs[1], markdown),
                    example=_get_string_from_div(word_divs[2], markdown),
                    contributor=_get_string_from_div(word_divs[3], False))
        words.append(word)
    return words

class Word:
    def __init__(
                 self,
                 url: str,
                 name: str,
                 meaning: str,
                 example: str,
                 contributor: str):
        self.url = url
        self.name = name
        self.meaning = meaning
        self.example = example
        self.contributor = contributor

    def __eq__(self, __o: object) -> bool:
        try:
            return (self.url == __o.url and
                    self.name == __o.name and
                    self.meaning == __o.meaning and
                    self.example == __o.example)
        except AttributeError:
            return False

class UrbanDictionaryQuery:
    def __init__(
                self,
                query: str = None,
                random: bool = False,
                markdown: bool = False,
                caching: bool = True):
        self.query = query.strip() if query and query.strip() else None
        self.is_random = random if not self.query else False
        self.is_markdown = markdown
        self.is_caching = caching
        self.word_index = 0
        self.page_index = 1
        self.pages: dict[int,list[Word]] = {}  # Empty if not is_caching

    @property
    def url(self):
        url = "https://www.urbandictionary.com/"
        if self.query:
            url += f"define.php?term={urllib.parse.quote(self.query)}&"
        elif self.is_random:
            url += "random.php?"
        else:
            url += "?"
        return url + f"page={self.page_index}"

    @property
    def word(self):
        try:
            return self.page[self.word_index]
        except IndexError:
            return None

    @property
    def page(self):
        page = (self.pages.get(self.page_index) or
                get_words_from_url(self.url, self.is_markdown))
        if self.is_caching:
            self.pages[self.page_index] = page
        return page

    @property
    def has_previous_page(self):
        return self.is_random or self.page_index > 1

    @property
    def has_previous_word(self):
        return self.word_index > 0 or self.has_previous_page

    @property
    def has_next_page(self):
        self.page_index += 1
        next_page = self.page
        self.page_index -= 1
        return self.is_random or len(next_page) > 0

    @property
    def has_next_word(self):
        return self.word_index < len(self.page)-1 or self.has_next_page

    def go_to_previous_page(self):
        if not self.has_previous_page:
            raise StopIteration("There isn't a Page prior to the current one")

        self.word_index = 0
        self.page_index -= 1
        return self.page

    def go_to_previous_word(self):
        if not self.has_previous_word:
            raise StopIteration("There isn't a Word prior to the current one")

        if self.word_index > 0:
            self.word_index -= 1
        else:
            self.go_to_previous_page()
            self.word_index = len(self.page)-1
        return self.word

    def go_to_next_page(self):
        if not self.has_next_page:
            raise StopIteration("There isn't a Page after the current one")

        self.word_index = 0
        self.page_index += 1
        return self.page

    def go_to_next_word(self):
        if not self.has_next_word:
            raise StopIteration("There isn't a Word after the current one")

        if self.word_index < len(self.page)-1:
            self.word_index += 1
        else:
            self.go_to_next_page()
        return self.word


#given word it returns the embed ready to be sent
def word_to_embed(word : Word):
    if len(word.name) > 255:
        word.name = word.name[:251]+'...'

    if len(word.meaning) > 4095:
        word.meaning = word.meaning[:3700]
        word.meaning = word.meaning.rsplit(' ', 2)[0]
        word.meaning += ' [...]\n[(open in the browser for the complete definition)]('+word.url+')'

    if len(word.example) > 1023:
        word.example = word.example[:1020]+'...'

    embed=Embed(title=escape_markdown(word.name),
            description=word.meaning,
            url=word.url,
            color=0x134FE6)
    if word.example: embed.add_field(name='Example:', value=word.example, inline=False)
    embed.set_footer(text='Definition '+word.contributor)
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
        pass



    ####################
    #    loop setup    #
    ####################
    @commands.command(name="set_wotd_channel",help="Pass the channel you want the WOTD to be sent every day")
    @commands.has_permissions(administrator=True)
    async def set_wotd_channel(self, ctx, channel):
        if self.bot.get_channel(int(channel[2:-1])) is None:
            return await ctx.send(f"Channel passed is not valid or it's hidden from the bot", reference=ctx.message, mention_author=False)

        with open('config/wotd_settings.json', 'r') as file:
            wotd_settings = json.load(file)

        wotd_settings["channel_ids"][str(ctx.guild.id)] = int(channel[2:-1])

        with open('config/wotd_settings.json', 'w') as file:
            json.dump(wotd_settings, file, indent=4)

        await ctx.send(f'Channel set to: {channel}', reference=ctx.message, mention_author=False)

    @commands.command(name="get_wotd_channel",help="Returns the wotd channel if set")
    @commands.has_permissions(administrator=True)
    async def get_wotd_channel(self, ctx):
        with open('config/wotd_settings.json', 'r') as file:
            wotd_settings = json.load(file)

        wotd_channel_id = wotd_settings["channel_ids"].get(str(ctx.guild.id))
        wotd_channel = get(ctx.guild.text_channels, id=wotd_channel_id)

        if wotd_channel:
            await ctx.send(f'Channel currently set to: {wotd_channel.mention}', reference=ctx.message, mention_author=False)
        else:
            await ctx.send(f'Channel is not set.', reference=ctx.message, mention_author=False)

    @commands.command(name="remove_wotd_channel",help="Unset the channel for the WOTD")
    @commands.has_permissions(administrator=True)
    async def remove_wotd_channel(self, ctx):
        with open('config/wotd_settings.json', 'r') as file:
            wotd_settings = json.load(file)
        try:
            wotd_settings["channel_ids"].pop(str(ctx.guild.id))
            with open('config/wotd_settings.json', 'w') as file:
                json.dump(wotd_settings, file, indent=4)
            await ctx.send(f'Channel unset', reference=ctx.message, mention_author=False)
        except KeyError:
            await ctx.send(f'The channel for the WOTD is not set', reference=ctx.message, mention_author=False)

    @commands.command(name="restart_wotd_loop",help="Restart the WOTD Task")
    @commands.is_owner()
    async def restart_wotd_loop(self, ctx):
        self.wotd_loop.restart()
        await ctx.message.add_reaction("🆗")



    ############################
    #    urbandict commands    #
    ############################
    @commands.command(name="wotd", aliases=["pdg"],help="It tells you the Word of the Day!")
    async def wotd(self, ctx):
        await ctx.trigger_typing()
        query = UrbanDictionaryQuery(markdown=True)
        wotd = query.word
        embed = word_to_embed(wotd)
        await ctx.send(f"**Here's today's Word of the Day!**",embed=embed, reference=ctx.message, mention_author=False)

    @commands.command(name="define", aliases=["definisci", "definition", "definizione"],help="Get the urban definition of a word")
    async def definisci(self, ctx, *query):
        await ctx.trigger_typing()
        query = " ".join(query)
        query = UrbanDictionaryQuery(query=query, markdown=True)
        definition = query.word
        if definition is None: return await ctx.send(f"**¯\_(ツ)_/¯**\nSorry, we couldn't find the definition of: `{query}`", reference=ctx.message, mention_author=False)
        embed = word_to_embed(definition)
        await ctx.send(f"**Definition of:** `{query}`", embed=embed, reference=ctx.message, mention_author=False)

    @commands.command(name="rand_word", aliases=["rand_parola", "parola_random", "random_word", "parola", "word"],help="Feeling lucky? Get a random word")
    async def rand_word(self, ctx):
        await ctx.trigger_typing()
        query = UrbanDictionaryQuery(random=True, markdown=True)
        definition = query.word
        embed = word_to_embed(definition)
        await ctx.send(f"**Here's a random word from Urban Dictionary**",embed=embed, reference=ctx.message, mention_author=False)



def setup(bot):
    bot.add_cog(UrbanDictionary(bot))