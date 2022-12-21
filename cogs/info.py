import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Info(commands.Cog, name='info'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='userinfo')
    @app_commands.describe(user='the user to get the info of (leave blank to get your own info)')
    async def userinfo(self, i: Interaction, user: discord.Member = None):
        """Shows informations about a user"""
        user = user or i.user

        embed = discord.Embed(colour=user.colour)
        embed.set_thumbnail(url=user.display_avatar.url)

        fields = [('Name', str(user), True),
                  ('ID', user.id, True),
                  ('Bot?', user.bot, True),
                  ('Top role', user.top_role.mention, True),
                  ('Status', str(user.status).title(), True),
                  ('Activity', f"{str(user.activity.type).split('.')[-1].title() if user.activity else 'N/A'} {user.activity.name if user.activity else ''}", True),
                  ('Created at', user.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                  ('Joined at', user.joined_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                  ('Boosted', bool(user.premium_since), True)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await i.response.send_message(embed=embed)

    @app_commands.command(name='serverinfo')
    async def serverinfo(self, i: Interaction):
        """Shows informations about this server"""
        embed = discord.Embed(title=f"Server info for {i.guild.name}", colour=i.guild.owner.colour)
        embed.set_thumbnail(url=i.guild.icon.url)

        statuses = [len(list(filter(lambda m: str(m.status) == status, i.guild.members))) for status in ["online", "idle", "dnd", "offline"]]

        fields = [('ID', i.guild.id, True),
                  ('Owner', i.guild.owner, True),
                  ('Created at', i.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                  ('Members', len(i.guild.members), True),
                  ("Statuses", f"🟢 {statuses[0]} 🟠 {statuses[1]} 🔴 {statuses[2]} ⚪ {statuses[3]}", False),
                  ('Roles', len(i.guild.roles), True),
                  ('Bans', len([entry async for entry in i.guild.bans(limit=2000)]), True),
                  ('Text channels', len(i.guild.text_channels), True),
                  ('Voice channels', len(i.guild.voice_channels), True),
                  ('Boosts', i.guild.premium_subscription_count, True),
				  ("\u200b", "\u200b", True)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await i.response.send_message(embed=embed)

    @app_commands.command(name='serverlist')
    @commands.is_owner()
    async def serverlist(self, i: Interaction):
        """Shows the list of servers the bot is in"""
        message = f'The bot is in **{len(self.bot.guilds)}** guilds:\n```\n'
        for guild in self.bot.guilds:
            message = '\n'.join([message, guild.name])
        message += '\n```'

        await i.response.send_message(message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Info(bot))