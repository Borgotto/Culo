import os
import json
import asyncio

import discord
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self, config: dict):
        super().__init__(command_prefix=commands.when_mentioned,
                        owner_ids=config.get('owner_ids',[]),
                        intents=discord.Intents.all(),
                        activity=discord.Activity(name=config.get('activity',''),
                                                type=config.get('activity_type',0)),
                        status=config.get('status','online'))

    async def setup_hook(self):
        # Load all cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        # Sync commands tree
        await self.tree.sync()

def main():
    # Load config from file
    with open('./config/bot_config.json', 'r', encoding='utf8') as config_file:
        config = json.load(config_file)
    # Create the bot
    bot = Bot(config)
    # Get the token from the config file or the environment variable
    token = config.get('token', os.environ.get('TOKEN'))
    # Run the bot
    bot.run(token)

if __name__ == '__main__':
    asyncio.run(main())