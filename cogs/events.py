from discord.ext import commands

class Events(commands.Cog, name='events'):
    def __init__(self, bot):
        self.bot = bot

    #@commands.Cog.listener()
    #async def on_raw_message_delete(self, payload):
    #    # Remove the message from the messages.json file
    #    await self.bot.get_cog("role_editor").remove_message(payload)
#
    #@commands.Cog.listener()
    #async def on_raw_reaction_add(self, payload):
    #    # Add role to user that clicked the reaction
    #    await self.bot.get_cog("role_editor").edit_role(payload)
#
    #@commands.Cog.listener()
    #async def on_raw_reaction_remove(self, payload):
    #    # Remove role to user that clicked the reaction
    #    await self.bot.get_cog("role_editor").edit_role(payload, remove=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return

        content = message.content.lower()
        replies = {'bravo bot':'UwU grazie','luca gay':'si, luca è gay','borgo gay':'no tu sei gay','stefano sei un ciccione':'sta zitto Nicò','ciao ste':'ciao ste','punta il ferro':'https://imgur.com/BZDUDxp','pablo comunista':'https://imgur.com/mD77kay','pspspsps':'https://imgur.com/TXW54kd','ps ps ps ps':'https://imgur.com/TXW54kd','pspsps':'https://imgur.com/TXW54kd'}

        if content in replies:
            await message.channel.send(replies[content], reference=message, mention_author=False)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Prevent timeouts from being applied to bot authors
        if (after.id in self.bot.owner_ids and after.timed_out_until):
            await after.timeout(None)


async def setup(bot):
    await bot.add_cog(Events(bot))