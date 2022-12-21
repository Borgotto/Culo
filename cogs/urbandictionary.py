import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.utils import escape_markdown

import requests
import urllib.parse
from bs4 import BeautifulSoup, element


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

    embed=discord.Embed(title=escape_markdown(word.name),
            description=word.meaning,
            url=word.url,
            color=0x134FE6)
    if word.example: embed.add_field(name='Example:', value=word.example, inline=False)
    embed.set_footer(text='Definition '+word.contributor)
    return embed


class UrbanDictionary(commands.Cog, name="urbandictionary"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='wotd')
    async def wotd(self, i: Interaction):
        """Get the Word of the Day from Urban Dictionary"""
        await i.response.defer(thinking=True)
        ud_query = UrbanDictionaryQuery(markdown=True)
        wotd = ud_query.word
        embed = word_to_embed(wotd)
        await i.edit_original_response(content=f"**Here's today's Word of the Day!**",embed=embed)

    @app_commands.command(name='define')
    @app_commands.describe(query="The word you want the definition of")
    async def define(self, i: Interaction, query: str):
        """Get the definition of a word from Urban Dictionary"""
        await i.response.defer(thinking=True)
        query = " ".join(query)
        ud_query = UrbanDictionaryQuery(query=query, markdown=True)
        definition = ud_query.word
        if definition is None:
            return await i.edit_original_response(content=f"**¯\_(ツ)_/¯**\nSorry, we couldn't find the definition of: `{query}`")
        embed = word_to_embed(definition)
        await i.edit_original_response(content=f"**Definition of:** `{query}`", embed=embed)

    @app_commands.command(name='random_word')
    async def random_word(self, i: Interaction):
        """Get a random word from Urban Dictionary"""
        await i.response.defer(thinking=True)
        ud_query = UrbanDictionaryQuery(random=True, markdown=True)
        definition = ud_query.word
        embed = word_to_embed(definition)
        await i.edit_original_response(content=f"**Here's a random word from Urban Dictionary**",embed=embed)


async def setup(bot):
    await bot.add_cog(UrbanDictionary(bot))