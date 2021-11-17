from discord.ext import commands
from discord import Member, Embed, Colour
from discord.utils import find
from typing import Optional
from difflib import get_close_matches

class Immagini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Immagini caricate!")

    @commands.command(name="avatar", aliases=['profilepic', 'pp'], help="Mostra l'immagine di profilo di un utente")
    async def avatar(self, ctx, user : Optional[Member], username : Optional[str]):
        if user is None:
            if username == None or username == "":
                user = ctx.author
            else:
                members = ctx.guild.members
                usernames = [member.name for member in members] + [member.nick for member in members if member.nick is not None]
                username = next(iter(get_close_matches(next(iter(get_close_matches(username.lower(), [username.lower() for username in usernames], 1, 0.3)), None), usernames, 1, 0.3)), None)
                if username is None:
                    return await ctx.send(":warning: Unable to find that user.", reference=ctx.message, mention_author=False)
                else:
                    user = find(lambda member: member.name == username or member.nick == username, members)

        colors = {'online':Colour(0x43B582), 'idle':Colour(0xFAA81A), 'dnd':Colour(0xF04747), 'offline':Colour(0x747F8D)}
        embed = Embed(colour=colors.get(user.raw_status))
        embed.set_author(name=user.name+'#'+user.discriminator, url="https://discord.com/users/"+str(user.id), icon_url="https://cdn.discordapp.com"+user.avatar_url._url)
        embed.set_image(url="https://cdn.discordapp.com"+user.avatar_url._url)

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)



def setup(bot):
    bot.add_cog(Immagini(bot))