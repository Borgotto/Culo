from discord.ext import commands
from discord import Member

class Censura(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    lista_censura = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("Censura caricata!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return        
        
        if message.author.id in self.lista_censura:
            await message.delete()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id in self.lista_censura:
            await member.move_to(None)
    
    @commands.command(name="censura", aliases=['zittisci'], help="Censura un utente (disabilita messaggi e chat vocale)")
    @commands.has_permissions(administrator=True)
    async def censura(self, ctx, user : Member):
        if user.id == self.bot.user.id: 
            await ctx.send(f"Stai davvero cercando di censurare il bot?")
            return  

        if user.id in self.lista_censura:
            self.lista_censura.remove(user.id)
            await ctx.send(f"{user.name} rimosso dalla censura")
        else:
            self.lista_censura.append(user.id)
            await ctx.send(f"{user.name} aggiunto dalla censura")
            await user.move_to(None)

def setup(bot):
    bot.add_cog(Censura(bot))