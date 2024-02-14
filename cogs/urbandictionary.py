import discord
from discord import ui, ButtonStyle, app_commands, Interaction
from discord.ext import commands
from discord.utils import escape_markdown

import re
import requests
from urllib.parse import quote
from datetime import datetime as dt
from enum import Enum

################################
# Urban Dictionary API Wrapper #
################################

class Word:
    """
    A class describing a word definition from www.urbandictionary.com
    """

    def __init__(self,
                    definition: str,
                    date: str,
                    permalink: str,
                    thumbs_up: int,
                    thumbs_down: int,
                    author: str,
                    word: str,
                    defid: int,
                    current_vote: str,
                    written_on: dt,
                    example: str):
        self.definition = definition
        self.date = date
        self.permalink = permalink
        self.thumbs_up = thumbs_up
        self.thumbs_down = thumbs_down
        self.author = author
        self.word = word
        self.defid = defid
        self.current_vote = current_vote
        self.written_on = written_on
        self.example = example

    def __eq__(self, __o: object) -> bool:
        try:
            return self.defid == getattr(__o, 'defid', None)
        except AttributeError:
            return False

    def __repr__(self):
        return f"Word(definition: {self.definition!r}, date: {self.date!r}, permalink: {self.permalink!r}, thumbs_up: {self.thumbs_up!r}, thumbs_down: {self.thumbs_down!r}, author: {self.author!r}, word: {self.word!r}, defid: {self.defid!r}, current_vote: {self.current_vote!r}, written_on: {self.written_on!r}, example: {self.example!r})"

def get_words_from_url(url: str, markdown: bool = False) -> list[Word]:
    """Utility function to extract the words from any valid url from the
    api.urbandictionary.com endpoints

    Arguments
    -------------
    url: `str`
        the full URL from api.urbandictionary.com
        e.g. https://api.urbandictionary.com/v0/define?term=life&page=1

    markdown: `bool`
        whether to format the string to support markdown

    Return value
    -------------
    A `list` containing the `Word` objects
    """

    # Static Session object
    try:
        session = get_words_from_url.session
    except AttributeError:
        session = get_words_from_url.session = requests.Session()

    # Fetch the json from the url
    response = session.get(url).json()
    if response.get('error') or response.get('list') is None:
        raise Exception(response.get('error') or 'Invalid response')

    # Create markdown links for the words defined in square brackets
    def _format_markdown(string: str):
        regex = '\\[.*?\\]'
        transform_func = lambda x: x.group()+f'(https://www.urbandictionary.com/define.php?term={quote(x.group()[1:-1])})' if markdown else x.group()[1:-1]
        return re.sub(regex, transform_func, string)

    # Create and return a list of Word objects
    return [Word(
            definition=_format_markdown(word.get('definition','')),
            date=word.get('date'),
            permalink=word.get('permalink'),
            thumbs_up=word.get('thumbs_up'),
            thumbs_down=word.get('thumbs_down'),
            author=word.get('author'),
            word=word.get('word'),
            defid=word.get('defid'),
            current_vote=word.get('current_vote'),
            written_on=dt.strptime(word['written_on'],'%Y-%m-%dT%H:%M:%S.%fZ'),
            example=_format_markdown(word.get('example',''))
        ) for word in response['list']]

def auto_complete(query: str) -> list[str]:
    """
    Returns a list of words that auto complete the query, these strings can later be used to query the entire word
    """
    # Static Session object
    try:
        session = auto_complete.session
    except AttributeError:
        session = auto_complete.session = requests.Session()

    # Fetch the json from the url
    response = session.get(f'https://api.urbandictionary.com/v0/autocomplete?term={quote(query)}').json()
    try:
        if response.get('error'):
            raise Exception(response.get('error') or 'Invalid response')
    except AttributeError:
        pass

    return response

def word_to_embed(word : Word):
    if len(word.word) > 255:
        word.word = word.word[:251]+'...'

    if len(word.definition) > 4095:
        word.definition = word.definition[:3700]
        word.definition = word.definition.rsplit(' ', 2)[0]
        word.definition += ' [...]\n[(open in the browser for the complete definition)]('+word.permalink+')'

    if len(word.example) > 1023:
        word.example = word.example[:1020]+'...'

    embed=discord.Embed(title=escape_markdown(word.word),
            description=word.definition,
            url=word.permalink,
            color=0x134FE6)
    if word.example:
        embed.add_field(name='Example:', value=word.example, inline=False)
    embed.set_footer(text='Definition by '+word.author)
    return embed

class UrbanDictionaryQuery:
    """A class to handle queries on https://www.urbandictionary.com/"""

    class query_type(Enum):
        """Enum to handle the different types of queries"""
        EMPTY = None
        WORD = ''
        RANDOM = -1
        WOTD = -2

    def __init__(
                self,
                markdown: bool = False,
                caching: bool = True):
        """
        Arguments
        -------------------------
        markdown: `bool`
            if true `Word`s will be formatted to support markdown

        caching: `bool`
            if true `Word`s will be cached to save time and bandwidth
        """
        self.is_markdown: bool = markdown
        self.is_caching: bool = caching
        self.query = self.query_type.EMPTY
        self.word_index: int = 0
        self.page_index: int = 0
        self.cached_pages: list[list[Word]] = []  # Empty if not is_caching

    @property
    def url(self) -> str:
        """
        the current URL used to query from urbandictionary.com
        e.g. https://www.urbandictionary.com/define.php?term=life
        """
        if self.query == self.query_type.EMPTY: # If no query is set return None
            return ''

        base_url = "https://api.urbandictionary.com/v0/"
        query_str = ''
        if self.query and type(self.query) == str:
            query_str = f"define?term={quote(str(self.query))}&page={self.page_index+1}"
        elif self.query == self.query_type.RANDOM:
            query_str = "random"
        elif self.query == self.query_type.WOTD:
            query_str = f"words_of_the_day?page={self.page_index+1}"

        return base_url + query_str

    @property
    def word(self) -> Word:
        """Returns the current `Word` of the current page"""
        try:
            return self.page[self.word_index]
        except IndexError:
            return None

    @property
    def page(self) -> list[Word]:
        """Returns the current page (`list[Word]`)"""
        if self.query == self.query_type.EMPTY:
            return []

        # Try to get the page from the cache, if it fails get it from the url
        try:
            page = self.cached_pages[self.page_index]
        except IndexError:
            page = get_words_from_url(self.url, self.is_markdown)

        # If caching is enabled, cache the page
        if self.is_caching:
            if self.page_index > len(self.cached_pages)-1:
                self.cached_pages.insert(self.page_index, page)
            else:
                self.cached_pages[self.page_index] = page

        return page

    @property
    def has_previous_page(self) -> bool:
        return self.page_index > 0

    @property
    def has_previous_word(self) -> bool:
        return self.word_index > 0 or self.has_previous_page

    @property
    def has_next_page(self) -> bool:
        self.page_index += 1
        next_page = self.page
        self.page_index -= 1
        return len(next_page) > 0

    @property
    def has_next_word(self) -> bool:
        return self.word_index < len(self.page)-1 or self.has_next_page

    def go_to_previous_page(self) -> list[Word]:
        """
        Move onto the first `Word` of the previous page.

        Return value
        -------------
        The previous page (`list[Word]`) if present

        Raises
        -------------
        `StopIteration` in case there isn't a previous page
        """
        if not self.has_previous_page:
            raise StopIteration("There isn't a Page prior to the current one")

        self.word_index = 0
        self.page_index -= 1
        return self.page

    def go_to_previous_word(self):
        """
        Move onto the previous `Word` of the current page or last `Word`
        of the previous page

        Return value
        -------------
        The previous `Word` if present

        Raises
        -------------
        `StopIteration` in case there isn't a previous word or page
        """
        if not self.has_previous_word:
            raise StopIteration("There isn't a Word prior to the current one")

        if self.word_index > 0:
            self.word_index -= 1
        else:
            self.go_to_previous_page()
            self.word_index = len(self.page)-1
        return self.word

    def go_to_next_page(self) -> list[Word]:
        """
        Move onto the first `Word` of the next page.

        Return value
        -------------
        The next page (`list[Word]`) if present

        Raises
        -------------
        `StopIteration` in case there isn't a next page
        """
        if not self.has_next_page:
            raise StopIteration("There isn't a Page after the current one")

        self.word_index = 0
        self.page_index += 1
        return self.page

    def go_to_next_word(self):
        """
        Move onto the next `Word` of the current page or first `Word` of
        the next page

        Return value
        -------------
        The next `Word` if present

        Raises
        -------------
        `StopIteration` in case there isn't a next word or page
        """
        if not self.has_next_word:
            raise StopIteration("There isn't a Word after the current one")

        if self.word_index < len(self.page)-1:
            self.word_index += 1
        else:
            self.go_to_next_page()
        return self.word

    def _new_query(self, type: query_type, query: str = ''):
        self.query = query if type == self.query_type.WORD else type
        self.page_index = 0
        self.word_index = 0
        self.cached_pages = []
        return self.word

    def get_definition(self, word: str):
        """
        Query for a specific word, a random word or words of the day

        Arguments
        -------------------------
        query: `str`
            the word or phrase to query for

        Return value
        -------------------------
        The first `Word` of the first page
        """
        return self._new_query(self.query_type.WORD, word)

    def get_random_word(self):
        """
        Get random words

        Return value
        -------------
        The first `Word` of the first page
        """
        return self._new_query(self.query_type.RANDOM)

    def get_wotd(self):
        """
        Get a page of the words of the day

        Return value
        -------------
        The first `Word` of the first page
        """
        return self._new_query(self.query_type.WOTD)


######################
# Discord UI Classes #
######################

class WordQueryView(ui.Modal, title="Urban Dictionary search"):
    query = ui.TextInput(label='query', placeholder='Enter a word to search', min_length=1)

    def __init__(self, ud_query: UrbanDictionaryQuery):
        super().__init__(timeout=None)
        self.ud_query = ud_query

    async def on_submit(self, i: Interaction) -> None:
        await i.response.defer()
        self.ud_query.get_definition(self.query.value)

        if self.ud_query.word is None:
            content=f"**¯\\_(ツ)_/¯**\nSorry, we couldn't find the definition of: `{self.query.value}`"
            embed = None
        else:
            content = f"**Definition of:** `{self.ud_query.word.word}`"
            embed = word_to_embed(self.ud_query.word)

        view = WordButtonsView(self.ud_query)
        await i.edit_original_response(content=content, embed=embed, view=view)


class WordButtonsView(ui.View):
    def __init__(self, ud_query: UrbanDictionaryQuery):
        super().__init__()
        self.ud_query = ud_query
        self.update_buttons()

    def update_buttons(self):
        if self.ud_query.query == UrbanDictionaryQuery.query_type.WOTD:
            self.previous_page_button.disabled = not self.ud_query.has_next_page
            self.previous_word_button.disabled = not self.ud_query.has_next_word
            self.next_word_button.disabled = not self.ud_query.has_previous_word
            self.next_page_button.disabled = not self.ud_query.has_previous_page
        else:
            self.previous_page_button.disabled = not self.ud_query.has_previous_page
            self.previous_word_button.disabled = not self.ud_query.has_previous_word
            self.next_word_button.disabled = not self.ud_query.has_next_word
            self.next_page_button.disabled = not self.ud_query.has_next_page

    async def update(self, i: Interaction):
        self.update_buttons()

        if type(self.ud_query.query) == str:
            content = f"**Definition of:** `{self.ud_query.word.word}`"
        elif self.ud_query.query == UrbanDictionaryQuery.query_type.RANDOM:
            content = f"**Here's a random word from Urban Dictionary**"
        elif self.ud_query.query == UrbanDictionaryQuery.query_type.WOTD:
            content = f"**Here's the Word of the Day of {self.ud_query.word.date}**"
        else:
            content = f"There was an error fetching the word, something brokey :("

        if self.ud_query.word:
            embed = word_to_embed(self.ud_query.word)
        else:
            embed = None

        await i.response.edit_message(content=content, embed=embed, view=self)

    # Primary buttons

    @ui.button(emoji='⏪', style=ButtonStyle.primary, custom_id='previous_page')
    async def previous_page_button(self, i: Interaction, b: ui.Button):
        if self.ud_query.query == UrbanDictionaryQuery.query_type.WOTD:
            self.ud_query.go_to_next_page()
        else:
            self.ud_query.go_to_previous_page()
        await self.update(i)

    @ui.button(emoji='◀️', style=ButtonStyle.primary, custom_id='previous_word')
    async def previous_word_button(self, i: Interaction, b: ui.Button):
        if self.ud_query.query == UrbanDictionaryQuery.query_type.WOTD:
            self.ud_query.go_to_next_word()
        else:
            self.ud_query.go_to_previous_word()
        await self.update(i)

    @ui.button(emoji='▶️', style=ButtonStyle.primary, custom_id='next_word')
    async def next_word_button(self, i: Interaction, b: ui.Button):
        if self.ud_query.query == UrbanDictionaryQuery.query_type.WOTD:
            self.ud_query.go_to_previous_word()
        else:
            self.ud_query.go_to_next_word()
        await self.update(i)

    @ui.button(emoji='⏩', style=ButtonStyle.primary, custom_id='next_page')
    async def next_page_button(self, i: Interaction, b: ui.Button):
        if self.ud_query.query == UrbanDictionaryQuery.query_type.WOTD:
            self.ud_query.go_to_previous_page()
        else:
            self.ud_query.go_to_next_page()
        await self.update(i)

    # Secondary buttons / row

    @ui.button(emoji='🔍', style=ButtonStyle.secondary, custom_id='search', row=2)
    async def search_button(self, i: Interaction, b: ui.Button):
        modal = WordQueryView(self.ud_query)
        await i.response.send_modal(modal)

    @ui.button(emoji='🔀', style=ButtonStyle.secondary, custom_id='random', row=2)
    async def random_button(self, i: Interaction, b: ui.Button):
        self.ud_query.get_random_word()
        await self.update(i)

    @ui.button(emoji='📅', style=ButtonStyle.secondary, custom_id='wotd', row=2)
    async def home_button(self, i: Interaction, b: ui.Button):
        self.ud_query.get_wotd()
        await self.update(i)


#####################
# Discord Cog Class #
#####################

class UrbanDictionary(commands.Cog, name="urbandictionary"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='wotd')
    async def wotd(self, i: Interaction):
        """Get the Word of the Day from Urban Dictionary"""
        await i.response.defer(thinking=True)

        ud_query = UrbanDictionaryQuery(markdown=True)
        word = ud_query.get_wotd()
        if word is None:
            return await i.edit_original_response(content=f"There was an error fetching the Word of the Day")

        content = f"**Here's the Word of the Day of {word.date}**"
        embed = word_to_embed(word)
        view = WordButtonsView(ud_query)
        await i.edit_original_response(content=content, embed=embed, view=view)

    @app_commands.command(name='define')
    @app_commands.describe(query="The word you want the definition of")
    async def define(self, i: Interaction, query: str):
        """Get the definition of a word from Urban Dictionary"""
        await i.response.defer(thinking=True)

        ud_query = UrbanDictionaryQuery(markdown=True)
        word = ud_query.get_definition(query)
        if word is None:
            return await i.edit_original_response(content=f"**¯\\_(ツ)_/¯**\nSorry, we couldn't find the definition of: `{query}`")

        content = f"**Definition of:** `{word.word}`"
        embed = word_to_embed(word)
        view = WordButtonsView(ud_query)
        await i.edit_original_response(content=content, embed=embed, view=view)

    @app_commands.command(name='random_word')
    async def random_word(self, i: Interaction):
        """Get a random word from Urban Dictionary"""
        await i.response.defer(thinking=True)

        ud_query = UrbanDictionaryQuery(markdown=True)
        word = ud_query.get_random_word()
        if word is None:
            return await i.edit_original_response(content=f"There was an error fetching a random word")

        content = f"**Here's a random word from Urban Dictionary**"
        embed = word_to_embed(word)
        view = WordButtonsView(ud_query)
        await i.edit_original_response(content=content, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(UrbanDictionary(bot))