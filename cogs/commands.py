from typing import Literal
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands, Interaction

class Commands(commands.Cog, name='commands'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help')
    @app_commands.describe(command='the command name you need help with')
    async def help(self, interaction: Interaction, command: str=None):
        """Get help for a command"""
        if command is None:
            await interaction.response.send_message('This is the help command', ephemeral=True)
        else:
            await interaction.response.send_message(f'Help for {command}', ephemeral=True)

    @app_commands.command(name='reload')
    @app_commands.describe(cog='the cog name you want to reload (leave blank to reload all cogs)')
    @commands.is_owner()
    async def reload(self, interaction: Interaction, cog: str = None):
        """Reloads all cogs"""
        cogs = [cog] if cog else list(self.bot.cogs)
        try:
            for cog in cogs:
                await self.bot.reload_extension('cogs.'+cog)
            await interaction.response.send_message(f'Cogs reloaded! It can take up to a minute to take effect', ephemeral=True)
        except discord.ext.commands.ExtensionError as e:
            await interaction.response.send_message(f'Error when reloading cog: \n```\n{e}\n```', ephemeral=True)
        await self.bot.tree.sync()

    @app_commands.command(name='ping')
    async def ping(self, interaction: Interaction):
        """Get the bot's latency"""
        await interaction.response.send_message(f'Pong! {round(self.bot.latency * 1000)}ms', ephemeral=True)

    @app_commands.command(name='gather')
    @app_commands.describe(channel='the channel to gather everyone in (leave blank to gather everyone in your current channel)')
    @commands.has_permissions(administrator=True)
    async def gather(self, interaction: Interaction, channel: discord.VoiceChannel=None):
        """Move every user in every voice channel to the same channel if they have permissions"""
        channel = channel or interaction.user.voice.channel

        if channel is None:
            return await interaction.response.send_message('You must be in a voice channel or specify which channel to gather everyone in', ephemeral=True)

        for vc in interaction.guild.voice_channels:
            for user in vc.members:
                if user.voice.channel != channel and channel.permissions_for(user).view_channel and channel.permissions_for(user).connect:
                    await user.move_to(channel)

    @app_commands.command(name='delete')
    @app_commands.describe(amount='the amount of messages/minutes/hours/days to delete',
                            mode='decide whether to delete # messages or # minutes/hours/days of messages')
    @commands.has_permissions(administrator=True)
    async def delete(self, i: Interaction, amount: int, mode: Literal['messages', 'minutes', 'hours', 'days']):
        """Delete # messages or # minutes/hours/days of messages"""
        if amount < 1:
            return await i.response.send_message('Amount must be greater than 0', ephemeral=True)

        # Deleting messages is slow, so defer the response
        await i.response.defer(ephemeral=True)
        await i.edit_original_response(content='Deleting messages...')

        try:
            if mode == 'messages':
                deleted_messages = await i.channel.purge(limit=amount)
            else:
                # Get the time in minutes
                if mode == 'minutes': time = amount
                elif mode == 'hours': time = amount * 60
                elif mode == 'days': time = amount * 60 * 24
                # Get current time and subtract 'time' minutes
                delete_after = datetime.now() - timedelta(minutes=time)
                # Delete messages newer than 'delete_after'
                deleted_messages = await i.channel.purge(limit=1000, after=delete_after)
            await i.edit_original_response(content=f'Deleted {len(deleted_messages)} messages')

        except discord.Forbidden:
            return await i.edit_original_response(content='I do not have permission to delete messages in this channel')
        except discord.HTTPException or discord.NotFound:
            return await i.edit_original_response(content='An error occurred while deleting messages')


async def setup(bot):
    await bot.add_cog(Commands(bot))