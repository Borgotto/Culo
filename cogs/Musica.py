import itertools
import asyncio
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL
from discord.ext import commands
from discord import Embed, FFmpegPCMAudio, HTTPException, PCMVolumeTransformer

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
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

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
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            data = data['entries'][0]

        await ctx.send(f'```ini\n[ Aggiunto {data["title"]} alla coda ]\n```')

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(FFmpegPCMAudio(source), data=data, requester=ctx.author)

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
            self.np = await self._channel.send(f'**In riproduzione:** `{source.title}` ' f'[`{source.requester}`]')
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

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    #@commands.command(name='connect', aliases=['join'])
    async def connect_(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send('Nessun canale in cui entrare.'); return

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                await ctx.send(f'Spostamento canale: <{channel}> timed out.'); return
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                await ctx.send(f'Connessione al canale: <{channel}> timed out.'); return
        embed = Embed(title="Entrato in chiamata")
        embed.add_field(name="Connesso a:", value=channel, inline=True)

        #await ctx.send(embed=embed)

    @commands.command(name='play', aliases=['riproduci', 'p'], help='Riproduci una canzone')
    async def play_(self, ctx, *, search: str):
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

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
        await ctx.send(f'**`{ctx.author}`** ha pausato la canzone')

    @commands.command(name='riprendi', aliases=['unpause', 'resume'], help="Riprendi la riproduzione della canzone")
    async def resume_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("Non c'è niente in riproduzione!", )
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`** ha ripreso la riproduzione')

    @commands.command(name='skip', aliases=['next'], help="Salta la canzone corrente")
    async def skip_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("Non c'è niente in riproduzione!")

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: ha saltato la canzone')

    @commands.command(name='coda', aliases=['q', 'playlist', 'queue'], help="Mostra la coda delle canzoni")
    async def queue_info(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('Non sono connesso a un canale vocale!')

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('Non ci sono altre canzoni nella coda.')

        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = Embed(title=f'Prossima canzone: {len(upcoming)}', description=fmt)

        await ctx.send(embed=embed)

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

        player.np = await ctx.send(f'**Ora in riproduzione:** `{vc.source.title}` 'f'[`{vc.source.requester}`]') 

    @commands.command(name='volume', aliases=['vol'], help="Cambia il volume della musica")
    async def change_volume(self, ctx, *, vol: float):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('Non sono connesso a un canale vocale!', )

        if not 0 < vol < 101:
            return await ctx.send('Inserisci un valora compreso tra 1 e 100')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = Embed(title="Volume",
        description=f'Volume cambiato da **{ctx.author.name}**')
        embed.add_field(name="Volume: ", value=vol, inline=True)
        await ctx.send(embed=embed)
        # await ctx.send(f'**`{ctx.author}`**: Set the volume to **{vol}%**')

    @commands.command(name='esci', aliases=['stop','leave','fuori'], help="Stoppa la musica (rimuove la coda)")
    async def stop_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send("Non c'è niente in riproduzione!")

        await self.cleanup(ctx.guild)

def setup(bot):
    bot.add_cog(Musica(bot))