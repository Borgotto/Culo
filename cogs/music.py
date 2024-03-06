import asyncio
from functools import partial
from urllib.parse import urlparse, quote
from yt_dlp import YoutubeDL
import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, FFmpegPCMAudio, PCMVolumeTransformer

ytdlopts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'cookiefile': '~/.youtubecookies',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 60',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""

class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""

class YTDLSource(PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    def uri_validator(cls, x):
        try:
            result = urlparse(x)
            return all([result.scheme, result.netloc])
        except:
            return False

    @classmethod
    async def create_source(cls, i: Interaction, search: str, *, loop, download=False, add_to_q=True):
        loop = loop or asyncio.get_event_loop()

        # If search is not a URL, url encode it
        if YTDLSource.uri_validator(search) is False:
            for char in ['/', ':']:
                search = search.replace(char, ' ')

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            data = data['entries'][0]

        if add_to_q is True:
            embed = Embed(title="Added to queue:", description=f'[{data["title"]}]({data["webpage_url"]}) [{i.user.mention}]', color=0xfefefe)
            await i.followup.send(embed=embed)

        return {'webpage_url': data['webpage_url'], 'requester': i.user, 'title': data['title']}

    @classmethod
    async def regather_stream(cls, data, *, loop):
        loop =  loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(FFmpegPCMAudio(data['url'], before_options=ffmpegopts['before_options'], options=ffmpegopts['options']), data=data, requester=requester)


class MusicPlayer(commands.Cog):
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, i: Interaction, cog: commands.Cog):
        self.bot = i.client
        self._i = i
        self._guild = i.guild
        self._channel = i.channel
        self._cog = cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = 0.5
        self.current = None

        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                async with asyncio.timeout(120):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f"There was an error in the request.\n"f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            if self._guild.voice_client is not None:
                self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

            embed = Embed(title="Now playing:", description=f'[{source.title}]({source.web_url}) [{source.requester.mention}]', color=0xfefefe)
            self.np = await self._i.followup.send(embed=embed)
            await self.next.wait()

            source.cleanup()
            self.current = None

    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog, name="music"):
    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, i: Interaction):
        try:
            player = self.players[i.guild.id]
        except KeyError:
            player = MusicPlayer(i, self)
            self.players[i.guild.id] = player

        return player

    async def connect_(self, i: Interaction, channel: discord.VoiceChannel):
        try:
            await i.response.defer(thinking=True)
        except discord.InteractionResponded:
            pass

        vc = i.guild.voice_client

        if vc is not None:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                pass
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                pass

    @app_commands.command(name='play')
    @app_commands.describe(search="the video/song you want to play",
                            channel="the voice channel you want to play the music in (optional)")
    @app_commands.checks.cooldown(1, 15.0, key=lambda i: (i.guild_id))
    async def play_(self, i: Interaction, search: str, channel: discord.VoiceChannel = None):
        """Play a video/song from youtube"""
        try:
            await i.response.defer(thinking=True)
        except discord.InteractionResponded:
            pass

        channel = channel or getattr(i.user.voice,'channel', None)
        if channel is None:
            return await i.edit_original_response(content="You need to be in a voice channel or specify one!", ephemeral=True)

        vc = i.guild.voice_client

        if not vc:
            await self.connect_(i, channel)

        player = self.get_player(i)
        player._i = i

        source = await YTDLSource.create_source(i, search, loop=self.bot.loop, download=False, add_to_q=(player.current is not None))

        await player.queue.put(source)

    @app_commands.command(name='pause_resume')
    async def pause_resume_(self, i: Interaction):
        """Pause/Resume the currently playing song"""
        vc = i.guild.voice_client

        if vc is None or not vc or not vc.is_connected():
            return await i.response.send_message("There is nothing playing")

        if vc.is_paused():
            vc.resume()
            return await i.response.send_message("Resumed 🆗")
        if vc.is_playing():
            vc.pause()
            return await i.response.send_message("Paused 🆗")

        await i.response.send_message("There was an error in the request.")

    @app_commands.command(name='skip')
    async def skip_(self, i: Interaction):
        """Skip the current song in the queue"""
        vc = i.guild.voice_client

        if not vc or not vc.is_connected():
            return await i.response.send_message("There is nothing in the queue")

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return await i.response.send_message("There is nothing playing")

        vc.stop()
        await i.response.send_message("Skipped 🆗")

    @app_commands.command(name='stop')
    async def stop_(self, i: Interaction):
        """Stop playing music and clear the queue"""
        vc = i.guild.voice_client

        if vc and vc.is_connected():
            await vc.disconnect()

        await self.cleanup(i.guild)
        await i.response.send_message("Stopped 🆗")

    @app_commands.command(name='queue')
    async def queue_info(self, i: Interaction):
        """Show the current song queue"""
        vc = i.guild.voice_client

        player = self.get_player(i)
        if player.queue.empty():
            return await i.response.send_message("There is nothing in the queue")

        x=0
        description = f"```ml\nSong queue:\n\n\t⬐ next song\n"
        for song in player.queue._queue:
            x+=1
            description += f'{x}) {song["title"]}\n'
        description += '\n\tEnd of queue!```'

        await i.response.send_message(description)

    @app_commands.command(name='now_playing')
    async def now_playing_(self, i: Interaction):
        """Show the currently playing song"""
        vc = i.guild.voice_client

        if not vc or not vc.is_connected():
            return await i.response.send_message("There is nothing playing")

        player = self.get_player(i)
        if not player.current:
            return await i.response.send_message("There is nothing playing")

        embed = Embed(title="Now playing:", description=f'[{vc.source.title}]({vc.source.web_url}) [{i.user.mention}]', color=0xfefefe)
        player.np = await i.response.send_message(embed=embed)

    @app_commands.command(name='volume')
    @app_commands.describe(value="the volume you want to set (0-100)")
    async def change_volume(self, i: Interaction, value: int):
        """Change the player's volume"""
        vc = i.guild.voice_client

        if not vc or not vc.is_connected():
            return await i.response.send_message("I am not currently connected to voice!")

        player = self.get_player(i)

        if value is None:
            value = player.volume*100
        elif not 0 < value < 101:
            return await i.response.send_message("Please enter a value between 0 and 100.")
        elif vc.source:
                vc.source.volume = value / 100
                player.volume = value / 100

        if value >= 80:
            emoji = ':loud_sound:'
        elif 30 < value < 80:
            emoji = ':sound:'
        elif value <=30:
            emoji = ':speaker:'

        embed = Embed(title=f'**Volume:**  {int(value)}  {emoji}:', color=0xfefefe)
        await i.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Resume the player if the bot is moved to a new channel"""
        vc = member.guild.voice_client
        if vc is None or member.voice is None: return

        if self.bot.user.id in [m.id for m in member.voice.channel.members]:
            retry = 0
            while not vc.is_connected() or retry > 100:
                await asyncio.sleep(0.1)

            if not vc.is_paused():
                vc.resume()


async def setup(bot):
    await bot.add_cog(Music(bot))