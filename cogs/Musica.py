from discord.ext import commands
from discord.utils import get
from discord import Member, VoiceChannel, FFmpegPCMAudio
from youtube_dl import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.voce = None

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Musica caricata!")

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)
            self.voce.play(FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.next())
        else:
            self.is_playing = False

    @commands.command(name="play")
    async def play(self, ctx, *args):        
        canale = ctx.author.voice.channel
        if canale is None:
            await ctx.send(f"{ctx.author.mention} Devi essere in un canale vocale per mettere la musica"); return

        if len(args) == 0:
            if self.voce is None or not self.voce.is_connected():
                self.voce = await canale.connect()
            if self.voce.is_paused():
                self.voce.resume()                
        else:
            query = " ".join(args)
            canzone = self.search_yt(query)

            await ctx.send("Song added to the queue")
            self.music_queue.append([canzone, canale])

            if self.is_playing == False:
                if self.voce is None or not self.voce.is_connected():
                    self.voce = await self.music_queue[0][1].connect()
                else:
                    await self.voce.move_to(self.music_queue[0][1])
                self.next()

    @commands.command(name="leave")
    async def leave(self,ctx, force=None):
        canale = ctx.author.voice.channel
        voce = get(self.bot.voice_clients, guild=ctx.guild)

        if force == "f" or canale and canale == voce.channel:
            self.is_playing = False
            await voce.disconnect()
        else:
            await ctx.send("Devi essere nello stesso canale vocale per disconnettermi")

    @commands.command(name="skip", help="Salta la canzone corrente")
    async def skip(self, ctx):
        if len(self.music_queue) > 0:
            if self.voce:
                self.voce.stop()
                await self.next()
        else:
            await ctx.send("Cosa skippo se non c'è niente nella codaaaa")

    @commands.command(name="pause", help="Pausa la canzone corrente")
    async def pause(self, ctx):
        if self.is_playing:
            self.voce.pause()
        else:
            await ctx.send("Cosa pauso se non c'è niente in riproduzioneeeeee")

    @commands.command(name="queue", help="Mostra la coda delle canzoni")
    async def queue(self, ctx):
        queue = ""
        for i in range(0, len(self.music_queue)):
            queue += self.music_queue[i][0]['title'] + "\n"

        if queue != "":
            await ctx.send(queue)
        else:
            await ctx.send("La coda è vuota")

def setup(bot):
    bot.add_cog(Music(bot))