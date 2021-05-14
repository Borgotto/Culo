import discord 
import youtube_dl
from discord.ext import commands
from discord.utils import get

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    players = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Musica caricata!")

    @commands.command(name="play")
    async def play(self, ctx, canale:discord.VoiceChannel=None):
        if canale is None:
            canale = ctx.author.voice.channel
        voce = get(self.bot.voice_clients, guild=ctx.guild)

        if voce and voce.is_connected():
            await voce.move_to(canale)
        else:
            voce = await canale.connect()

    @commands.command(name="leave")
    async def leave(self,ctx, force=None):
        canale = ctx.author.voice.channel
        voce = get(self.bot.voice_clients, guild=ctx.guild)

        if force == "f" or canale and canale == voce.channel:
            await voce.disconnect()
        else:
            await ctx.send("Devi essere nello stesso canale vocale per disconnettermi")



def setup(bot):
    bot.add_cog(Music(bot))