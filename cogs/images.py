import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Images(commands.Cog, name='images'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='avatar')
    @app_commands.describe(user='the user to get the avatar of (leave blank to get your own avatar)')
    async def avatar(self, i: Interaction, user: discord.Member = None):
        """Shows a user's avatar"""
        user = user or i.user

        colors = {'online': discord.Colour(0x43B582),
                  'idle':   discord.Colour(0xFAA81A),
                  'dnd':    discord.Colour(0xF04747),
                  'offline':discord.Colour(0x747F8D)}

        embed = discord.Embed(colour=colors.get(user.raw_status, colors['offline']))
        embed.set_author(name=f'{user.name}#{user.discriminator}', url=f'https://discord.com/users/{user.id}', icon_url=user.display_avatar.url)
        embed.set_image(url=user.display_avatar.url)

        await i.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Images(bot))