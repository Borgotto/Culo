from discord.ext import commands

class Eventi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Eventi caricati!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return

        if message.content.lower() == 'sushi':
            await message.channel.send('sushi')

        if message.content.lower() == 'luca gay':
            await message.channel.send('si, luca è gay')

        if message.content.lower() == 'pablo gay' or message.content.lower() == 'borgo gay':
            await message.channel.send('no tu sei gay')

        if message.content.lower() == 'bravo bot' or message.content.lower() == 'bel bot':
            await message.channel.send('UwU grazie')

        if message.content.lower() == 'prefisso?':
            await message.channel.send(self.bot.command_prefix(self, message))

        if message.content.lower() == 'punta il ferro':
            await message.channel.send('luca ti punta il ferro, cosa fai?')
            await message.channel.send('https://imgur.com/BZDUDxp')

        if message.content.lower() == 'amedeo bellissimo':
            await message.channel.send('https://imgur.com/oFAW5Uq')

        if message.content.lower() == 'pablo comunista':
            await message.channel.send('https://imgur.com/mD77kay')


def setup(bot):
    bot.add_cog(Eventi(bot))