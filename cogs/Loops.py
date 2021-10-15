from os import system
from discord import File
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime
from platform import system
import random

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.fabio.start()
        self.oraesatta.start()
        print("Loop caricati!")

    #Loop per rinominare Fabio.exe ( id = 192261771380260864 )
    @tasks.loop(minutes=10)
    async def fabio(self):
        estensioni = ["ciruzzo","napoli","struzzo","discord","vodkaredbull","sburrino","carry","fbi","alifana","azz","storto","doblo'","arrosto","cozze","sfiga","polentone","dove","7z","aac","apk","appx","arc","ass","bin","c","xaml","deb","dn","egg","exe","gbp","gbs","gif","gzip","html","jpg","jar","oar","osz","pak","php","pyk","py","pyw","rar","sb","tar","uha","viv","zip","iso","img","cad","dwg","gba","std","js","css","psd","ans","asc","doc","docx","log","pdf","xml","xhtml","xps","ico","bmp","jpeg","png","sym","url","os","dos","root","bat","cpp","c#","lua","obj","wav","mpeg","avi","flv","ogg","webm","nds","3ds","cia","cur","bak","raw","borgo",""]
        fabio = get(self.bot.get_all_members(), id=192261771380260864)

        await fabio.edit(nick=fabio.display_name.split(".")[0]+'.'+random.choice(estensioni))

    @tasks.loop(seconds=59)
    async def oraesatta(self):
        orario = datetime.now().strftime("%H:%M")
        if (orario == "07:15"):
            file_path = "/home/pi/ora_esatta.mp4" if system() == "Linux" else "C:/Users/Borgo/Desktop/ora_esatta.mp4"
            for id in [805397632494338091]:
                channel = self.bot.get_channel(id)
                try:
                    await channel.send(f"L'ora esatta è offerta da: ***Culo*** :peach: \nSono le **{orario}**", file=File(file_path))
                except:
                    await channel.send(f"Non sono riuscito a mandare l'ora esatta :/")

def setup(bot):
    bot.add_cog(Loops(bot))