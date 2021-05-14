from discord.ext import commands
from discord import Member, VoiceChannel

class Comandi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Comandi caricati!")

    @commands.command(name="chisono")
    async def chisono(self, ctx):
        await ctx.send(f"Sei un trimone {ctx.message.author.name}")

    @commands.command(name="scorreggia", aliases=["scoreggia", "cagati"])
    async def scorreggia(self, ctx):
        await ctx.send(f"Oh no mi sono cagato addosso")

    @commands.command(name="pinga", aliases=["pinga_utente"])
    async def pinga(self, ctx, user : Member, amount=1): 
        if (amount > 10):
                await ctx.send("Oh ma sei impazzito? Non posso pingare tutte quelle volte")
        else:                
            for x in range(0, amount):
                await ctx.send(f"{user.mention}")

    @commands.command(name="raduna", aliases=["radunata", "meeting"])
    @commands.has_permissions(administrator=True)
    async def raduna(self, ctx, canale : VoiceChannel=None):
        if canale is None:
            if ctx.author.voice is None:
                await ctx.send(f"{ctx.author.mention} Devi essere in un canale vocale o specificare quale canale in cui radunare la gente"); return
            else:
                canale = ctx.author.voice.channel

        for channel in ctx.guild.voice_channels:
            for member in channel.members:
                await member.move_to(canale)

    @commands.command(name="cancella")
    @commands.has_permissions(manage_messages=True)
    async def cancella(self, ctx, amount : int, mode="messaggi"):
        if (mode == "messaggi" or mode == "mess"):
            if (amount > 100):
                await ctx.send("Oh ma sei impazzito? Non posso cancellare tutti quei messaggi")
            else:    
                await ctx.channel.purge(limit=int(amount)+1)
        else:
            if (mode == "minuti" or mode == "min"):
                pass
            elif (mode == "ore" or mode == "h"):
                pass
            if (mode == "giorni" or mode == "d"):
                pass

def setup(bot):
    bot.add_cog(Comandi(bot))