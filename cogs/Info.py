from datetime import datetime
from typing import Optional

from discord import Embed, Member
from discord.ext import commands
import json

class Info(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		print("Info caricati!")

	@commands.command(name="userinfo", aliases=["memberinfo", "ui", "mi"], help="Mostra le informazini sull'account discord di un utente")
	async def user_info(self, ctx, target: Optional[Member]):
		target = target or ctx.author

		embed = Embed(title="User information", colour=target.colour, timestamp=datetime.utcnow())

		embed.set_thumbnail(url=target.avatar_url)

		fields = [("Name", str(target), True),
					("ID", target.id, True),
					("Bot?", target.bot, True),
					("Top role", target.top_role.mention, True),
					("Status", str(target.status).title(), True),
					("Activity", f"{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'} {target.activity.name if target.activity else ''}", True),
					("Created at", target.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
					("Joined at", target.joined_at.strftime("%d/%m/%Y %H:%M:%S"), True),
					("Boosted", bool(target.premium_since), True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)

	@commands.command(name="serverinfo", aliases=["guildinfo", "si", "gi"], help="Mostra le informazioni del server discord")
	async def server_info(self, ctx):
		embed = Embed(title="Server information", timestamp=datetime.utcnow())

		embed.set_thumbnail(url=ctx.guild.icon_url)

		statuses = [len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members)))]

		fields = [("ID", ctx.guild.id, True),
					("Owner", ctx.guild.owner, True),
					("Region", ctx.guild.region, True),
					("Created at", ctx.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
					("Members", len(ctx.guild.members), True),
					("Humans", len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
					("Bots", len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
					("Banned members", len(await ctx.guild.bans()), True),
					("Statuses", f"🟢 {statuses[0]} 🟠 {statuses[1]} 🔴 {statuses[2]} ⚪ {statuses[3]}", True),
					("Text channels", len(ctx.guild.text_channels), True),
					("Voice channels", len(ctx.guild.voice_channels), True),
					("Categories", len(ctx.guild.categories), True),
					("Roles", len(ctx.guild.roles), True),
					("Invites", len(await ctx.guild.invites()), True),
					("\u200b", "\u200b", True)]

		for name, value, inline in fields:
			embed.add_field(name=name, value=value, inline=inline)

		await ctx.send(embed=embed)

	@commands.command(name="lista_server", aliases=["lista server", "servers"], help="Stampa la lista di tutti i server in cui il bot fa parte")
	@commands.is_owner()
	async def lista_server(self, ctx):
		message = f""
		with open('prefixes.json', 'r') as file: 
			prefixes = json.load(file) 
			message = message + f'The bot is in {len(self.bot.guilds)} servers!\n'
			message = message + f'List of all servers the bot is in:\n\n'
			for guild in self.bot.guilds:
				message = message + f'Server name:  "{str(guild.name)}"\n'
				message = message + f'Server prefix:  "\\{str(prefixes[str(guild.id)])}"\n\n'
		await ctx.send(message)

def setup(bot):
	bot.add_cog(Info(bot))