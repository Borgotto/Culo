from discord.ext import commands, tasks
from discord import Member, Colour, Permissions
from discord.utils import get
import random

class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.fabio.start()
        print("Loop caricati!")

    #Loop per rinominare Fabio.exe ( id = 192261771380260864 )
    @tasks.loop(seconds=150)
    async def fabio(self):
        fabio = get(self.bot.get_all_members(), id=192261771380260864)

        estensioni = [".carry",".fbi",".alifana",".azz",".storto",".doblo'",".arrosto",".cozze",".sfiga",".polentone",".dove",".7z",".aac",".apk",".appx",".arc",".ass",".bin",".c",".xaml",".deb",".dn",".egg",".exe",".gbp",".gbs",".gif",".gzip",".html",".jpg",".jar",".oar",".osz",".pak",".php",".pyk",".py",".pyw",".rar",".sb",".tar",".uha",".viv",".zip",".iso",".img",".cad",".dwg",".gba",".std",".js",".css",".psd",".ans",".asc",".doc",".docx",".log",".pdf",".xml",".xhtml",".xps",".ico",".bmp",".jpeg",".png",".sym",".url",".dos",".root",".bat",".cpp",".c#",".lua",".obj",".wav",".mpeg",".avi",".flv",".ogg",".webm",".nds",".3ds",".cia",".cur",".bak",".raw",".borgo",""]

        await fabio.edit(nick=fabio.display_name.split(".")[0]+random.choice(estensioni))


def setup(bot):
    bot.add_cog(Loops(bot))