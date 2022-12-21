import json
import aiohttp
import io
import random
import datetime

import discord
from discord.ext import commands, tasks
from discord.utils import get

class Tasks(commands.Cog, name='tasks'):
    def __init__(self, bot):
        self.bot = bot
        self.nicknames.start()
        self.oraesatta.start()

    #Loop to rename some users
    @tasks.loop(minutes=15)
    async def nicknames(self):
        with open('./config/users_to_rename.json', 'r') as f:
            users_to_rename = json.load(f)
        extensions = users_to_rename["extensions"]
        users_id = users_to_rename["users_id"]

        for id in users_id:
            user = get(self.bot.get_all_members(), id=id)
            if user is None: continue
            user_nick = user.display_name.split(".")[0]
            random_extension = random.choice(extensions)
            if len(user_nick+"."+random_extension) > 32: continue
            try:
                await user.edit(nick=user_nick+"."+random_extension)
            except discord.Forbidden:
                continue

    #Loop to send the "ora esatta" video at 7:15 AM (UTC+1)
    @tasks.loop(time=datetime.time(hour=8, minute=15))
    async def oraesatta(self):
        with open('./config/ora_esatta.json', 'r') as f:
            ora_esatta_config = json.load(f)

        sponsor = random.choice(ora_esatta_config['sponsors'])

        async with aiohttp.ClientSession() as session:
            async with session.get(ora_esatta_config['video_url']) as resp:
                video = await resp.read()

        with io.BytesIO(video) as file:
            for id in ora_esatta_config['channels_id']:
                channel = self.bot.get_channel(id)
                if channel is None: continue
                await channel.send(f"L'ora esatta è offerta da: **{sponsor}**\
                                   \nSono le **{datetime.datetime.now().strftime('%H:%M')}**",
                                    file=discord.File(file, filename='oraesatta.mp4'))


async def setup(bot):
    await bot.add_cog(Tasks(bot))