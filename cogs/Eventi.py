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

        messaggio = message.content.lower()
        risposta = {'bravo bot':'UwU grazie','luca gay':'si, luca è gay','borgo gay':'no tu sei gay','punta il ferro':'https://imgur.com/BZDUDxp','pablo comunista':'https://imgur.com/mD77kay','pspspsps':'https://imgur.com/TXW54kd','ps ps ps ps':'https://imgur.com/TXW54kd','pspsps':'https://imgur.com/TXW54kd','lavatrice':'https://imgur.com/a/NdQfex2'}

        if messaggio in risposta:
            await message.channel.send(risposta[messaggio], reference=message, mention_author=False)

        if messaggio == 'prefisso?':
            await message.channel.send(f"Il prefisso per i comandi è: `{self.bot.command_prefix(self, message)}`", reference=message, mention_author=False)

def setup(bot):
    bot.add_cog(Eventi(bot))
