from discord.ext import commands
from discord import Member

class Censura(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    lista_censura = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("Censure caricate!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return        
        
        if message.author.id in self.lista_censura:
            await message.delete()
    
    @commands.command(name="censura")
    @commands.has_permissions(administrator=True)
    async def censura(self, ctx, user : Member):
        if user.id == self.bot.user: 
            await ctx.send(f"Stai davvero cercando di censurare il bot?")
            return  

        if user.id in self.lista_censura:
            self.lista_censura.remove(user.id)
            await ctx.send(f"{user.name} rimosso dalla censura")
        else:
            self.lista_censura.append(user.id)
            await ctx.send(f"{user.name} aggiunto dalla censura")

def setup(bot):
    bot.add_cog(Censura(bot))