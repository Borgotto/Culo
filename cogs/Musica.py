import itertools
import asyncio
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL
from discord.ext import commands
from discord import Embed, FFmpegPCMAudio, HTTPException, PCMVolumeTransformer, Color

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
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
    async def create_source(cls, ctx, search: str, *, loop, download=False, add_to_q=True):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            data = data['entries'][0]      

        if add_to_q is True:
            embed = Embed(title="Aggiunto alla coda:", description=f'[{data["title"]}]({data["webpage_url"]}) [{ctx.author.mention}]', color=0xfefefe)
            await ctx.send(embed=embed)

        return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

    @classmethod
    async def regather_stream(cls, data, *, loop):
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer(commands.Cog):
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                async with timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f"C'è stato un errore nella richiesta della canzone.\n"f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

            embed = Embed(title="Ora in riproduzione:", description=f'[{source.title}]({source.web_url}) [{source.requester.mention}]', color=0xfefefe)
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

            source.cleanup()
            self.current = None

            try:
                await self.np.delete()
            except HTTPException:
                pass

    def destroy(self, guild):
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Musica(commands.Cog):
    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}
    
    @commands.Cog.listener()
    async def on_ready(self):        
        print("Musica caricata!")

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('Questo comando non può essere usato nei messaggi privati')
            except HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Devi essere in un canale per mettere la musica')

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connetti', aliases=['join','entra','connect','connettiti'], help="Fai connettere il bot al canale vocale")
    async def connect_(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            if ctx.author.voice is None:
                await ctx.send(f"{ctx.author.mention} Devi essere in un canale vocale per mettere la musica")
            raise InvalidVoiceChannel(f'Nessun canale in cui entrare.')            

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Spostamento canale: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connessione al canale: <{channel}> timed out.')
        embed = Embed(title="Entrato in chiamata", color=0xfefefe)
        embed.add_field(name="Connesso a:", value=channel, inline=True)

        #await ctx.send(embed=embed)

    @commands.command(name='play', aliases=['riproduci', 'p'], help='Riproduci una canzone')
    async def play_(self, ctx, *, search: str):
        await ctx.trigger_typing()

        if ctx.author.voice is None:
            return await ctx.send(f"{ctx.author.mention} Devi essere in un canale vocale per mettere la musica")

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False, add_to_q=(player.current is not None))

        await player.queue.put(source)

    @commands.command(name='pausa', aliases=['pause'], help="Pausa la canzone in riproduzione")
    async def pause_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send("Non c'è niente in riproduzione!")
        elif vc.is_paused():
            await ctx.invoke(self.resume_)
            return

        vc.pause()
        await ctx.message.add_reaction("🆗")

    @commands.command(name='riprendi', aliases=['unpause', 'resume'], help="Riprendi la riproduzione della canzone")
    async def resume_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("Non c'è niente in riproduzione!", )
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.message.add_reaction("🆗")

    @commands.command(name='skip', aliases=['next','skippa'], help="Salta la canzone corrente")
    async def skip_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("Non c'è niente in riproduzione!")

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.message.add_reaction("🆗")

    @commands.command(name='coda', aliases=['q', 'playlist', 'queue'], help="Mostra la coda delle canzoni")
    async def queue_info(self, ctx):
        vc = ctx.voice_client

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('Non ci sono canzoni nella coda.')

        #upcoming = list(itertools.islice(player.queue._queue, 0, 5))
        #fmt = '\n'.join(f'[{_["title"]}]({_["webpage_url"]}) [{_["requester"].mention}]' for _ in player.queue._queue)
        #embed = Embed(title=f'Canzoni in coda:', color=0xfefefe, description=fmt)
        x=0
        description = f"```ml\nCoda Canzoni:\n\n\t⬐ prossima traccia\n"
        for song in player.queue._queue:
            x+=1
            description += f'{x}) {song["title"]}\n'
        description += '\n\tFine della coda!```'

        await ctx.send(description)

    @commands.command(name='in_riproduzione', aliases=['np', 'current', 'currentsong', 'playing', 'ir'], help="Mostra la canzone in riproduzione")
    async def now_playing_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('Non sono connesso a un canale vocale!', )

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send("Non c'è niente in riproduzione!")

        try:
            await player.np.delete()
        except HTTPException:
            pass
        
        embed = Embed(title="Ora in riproduzione:", description=f'{vc.source.title} [{ctx.author.mention}]', color=0xfefefe)
        player.np = await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol','v'], help="Cambia il volume della musica")
    async def change_volume(self, ctx, *, vol: float=None):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('Non sono connesso a un canale vocale!', )

        player = self.get_player(ctx)
        
        if vol is None:
            vol = player.volume*100
        elif not 0 < vol < 101:
            return await ctx.send('Inserisci un valora compreso tra 1 e 100')
        elif vc.source:
                vc.source.volume = vol / 100
                player.volume = vol / 100     
        
        if vol >= 80:
            emoji = ':loud_sound:'
        elif 30 < vol < 80:
            emoji = ':sound:'
        elif vol <=30:            
            emoji = ':speaker:'   

        embed = Embed(title=f'**Volume:**  {int(vol)}  {emoji}:', color=0xfefefe)
        await ctx.send(embed=embed)

    @commands.command(name='esci', aliases=['stop','leave','fuori'], help="Stoppa la musica (rimuove la coda)")
    async def stop_(self, ctx):
        vc = ctx.voice_client

        await self.cleanup(ctx.guild)
        await ctx.message.add_reaction("🆗")

def setup(bot):
    bot.add_cog(Musica(bot))