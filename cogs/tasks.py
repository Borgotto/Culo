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
    @tasks.loop(time=datetime.time(hour=5, minute=15))
    async def oraesatta(self):
        with open('./config/ora_esatta.json', 'r') as f:
            ora_esatta_config = json.load(f)
            sponsor = random.choice(ora_esatta_config['sponsors'])
            channels_id = ora_esatta_config['channels_id']
            video_url = ora_esatta_config['video_url']
            time = datetime.datetime.now().strftime('%H:%M')

        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(video_url) as resp:
                video = await resp.read()

        with io.BytesIO(video) as video_file:
            for id in channels_id:
                channel = self.bot.get_channel(id)
                if channel is None: continue # Skip invalid channel id
                await channel.send(f"L'ora esatta è offerta da: **{sponsor}**\
                                   \nSono le **{time}**",
                                    file=discord.File(video_file, filename='ora_esatta.mp4'))


async def setup(bot):
    await bot.add_cog(Tasks(bot))