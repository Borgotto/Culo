from discord import File, TextChannel
from discord.ext import commands, tasks
from io import BytesIO
from socket import socket, create_server, AF_INET
from typing import Optional

###################
#    cog class    #
###################
class Screenshot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.socket = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("Screenshot caricati!")

    @tasks.loop(seconds=2)
    async def server_task(self, img_channel : TextChannel, img_name : str):
        try:
            (connection, address) = self.socket.accept()
            if (connection.recv(3) == b'BOT'):
                size_b = connection.recv(8)
                size = int.from_bytes(size_b, "big")
                img_bytes = connection.recv(size)
                # immagine arrivata, la invio
                await img_channel.send(file=File(filename=img_name, fp=BytesIO(img_bytes)))
        except BlockingIOError or TimeoutError:
            pass #nessun pacchetto, riprovo tra due secondi

    @commands.command(name="start_server", aliases=['server_start','start_screenshot_server'], help="Avvia il server per ricevere le immagini")
    async def start_server(self, ctx, img_channel : Optional[TextChannel], img_name : Optional[str] = "screenshot.png", ip : Optional[str] = "", port : Optional[int] = 8080):
        if self.server_task.is_running():
            return await ctx.send(f"The server Task is already running!", reference=ctx.message, mention_author=False)
        if img_channel is None: img_channel = self.bot.get_channel(805397632494338091)

        self.socket = create_server((ip, port), family=AF_INET)
        self.socket.setblocking(False)
        self.server_task.start(img_channel, img_name)

        await ctx.send(f"The server Task has been started!", reference=ctx.message, mention_author=False)

    @commands.command(name="stop_server", aliases=['server_stop','stop_screenshot_server'], help="Ferma il server delle immagini")
    async def stop_server(self, ctx):
        if not self.server_task.is_running():
            return await ctx.send(f"The server Task is not running!", reference=ctx.message, mention_author=False)

        self.server_task.cancel()
        self.socket.close()
        self.socket = None

        await ctx.send(f"The server Task has been stopped!", reference=ctx.message, mention_author=False)



def setup(bot):
    bot.add_cog(Screenshot(bot))