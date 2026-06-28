import asyncio
import os
import random
import tempfile
from dataclasses import dataclass

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import requests

from config import Config
from database import db


YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "default_search": "ytsearch10",
    "source_address": "0.0.0.0",
}

FFMPEG_BEFORE = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn -loglevel warning"
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac")

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


@dataclass
class Track:
    title: str
    page_url: str
    stream_url: str = ""
    duration: int = 0
    thumbnail: str = ""
    requester: str = ""
    source: str = "YouTube"


class MusicState:
    def __init__(self):
        self.queue = []
        self.current = None
        self.search_results = []
        self.volume = 0.75
        self.loop = False
        self.stopped = False
        self.panel_message = None
        self.channel = None


class MusicPanel(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Pause", emoji="⏸", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await self.cog.pause_guild(interaction.guild)
        await interaction.followup.send("⏸ Paused.", ephemeral=True)

    @discord.ui.button(label="Resume", emoji="▶️", style=discord.ButtonStyle.secondary)
    async def resume(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await self.cog.resume_guild(interaction.guild)
        await interaction.followup.send("▶️ Resumed.", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭", style=discord.ButtonStyle.primary)
    async def skip(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await self.cog.skip_guild(interaction.guild)
        await interaction.followup.send("⏭ Skipped.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹", style=discord.ButtonStyle.danger)
    async def stop(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await self.cog.stop_music(interaction.guild)
        await interaction.followup.send("⏹ Stopped.", ephemeral=True)

    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary)
    async def queue(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await self.cog.send_queue(interaction)


class SearchSelect(discord.ui.Select):
    def __init__(self, cog, guild_id):
        self.cog = cog
        state = cog.state(guild_id)

        options = []
        for i, track in enumerate(state.search_results[:10], start=1):
            options.append(
                discord.SelectOption(
                    label=track.title[:90],
                    description=f"{i}. {cog.duration(track.duration)}",
                    value=str(i - 1),
                    emoji="🎵",
                )
            )

        super().__init__(
            placeholder="ZELROVA song choose karo",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction):
        state = self.cog.state(interaction.guild.id)
        index = int(self.values[0])

        if index >= len(state.search_results):
            await interaction.response.send_message("❌ Result expired.", ephemeral=True)
            return

        track = state.search_results[index]
        track.requester = str(interaction.user)

        await interaction.response.defer()
        await self.cog.add_or_play(interaction.guild, interaction.user, interaction.channel, track)
        await interaction.followup.send(f"✅ Selected: **{track.title}**", ephemeral=True)


class SearchView(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=120)
        self.add_item(SearchSelect(cog, guild_id))


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.dashboard_url = Config.DASHBOARD_URL.rstrip("/")

    def state(self, guild_id):
        self.states.setdefault(guild_id, MusicState())
        return self.states[guild_id]

    def duration(self, seconds):
        if not seconds:
            return "Unknown"
        return f"{seconds // 60}:{seconds % 60:02d}"

    def music_payload(self, guild_id):
        state = self.state(guild_id)
        current = None

        if state.current:
            current = {
                "title": state.current.title,
                "url": state.current.page_url,
                "duration": state.current.duration,
                "thumbnail": state.current.thumbnail,
                "requester": state.current.requester,
                "source": state.current.source
            }

        return {
            "status": "playing" if current and not state.stopped else "idle",
            "guild_id": str(guild_id),
            "current": current,
            "queue": [
                {
                    "title": t.title,
                    "url": t.page_url,
                    "duration": t.duration,
                    "thumbnail": t.thumbnail,
                    "requester": t.requester,
                    "source": t.source
                }
                for t in state.queue[:25]
            ],
            "volume": int(state.volume * 100),
            "loop": state.loop
        }

    def sync_music_state(self, guild_id):
        payload = self.music_payload(guild_id)
        db.update_music_state(**payload)

        try:
            requests.post(
                f"{self.dashboard_url}/api/music/update",
                json=payload,
                timeout=5
            )
        except Exception:
            pass

    async def extract(self, query):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(query, download=False)
        )

    async def fresh_stream(self, track):
        info = await self.extract(track.page_url or track.title)

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        track.stream_url = info.get("url", track.stream_url)
        track.page_url = info.get("webpage_url", track.page_url)
        track.thumbnail = info.get("thumbnail", track.thumbnail)
        track.duration = info.get("duration", track.duration) or track.duration
        return track

    async def search_tracks(self, query, requester):
        info = await self.extract(f"ytsearch10:{query}")
        results = []

        for item in info.get("entries", []):
            if not item:
                continue

            results.append(
                Track(
                    title=item.get("title", "Unknown Song"),
                    page_url=item.get("webpage_url", ""),
                    duration=item.get("duration", 0) or 0,
                    thumbnail=item.get("thumbnail", ""),
                    requester=requester,
                    source=item.get("extractor_key", "YouTube"),
                )
            )

        return results

    async def ensure_voice(self, interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ Pehle voice channel join karo.", ephemeral=True)
            return None

        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client

        if vc:
            if vc.channel.id != channel.id:
                await vc.move_to(channel)
            return vc

        return await channel.connect()

    async def add_or_play(self, guild, user, channel, track):
        vc = guild.voice_client

        if not vc:
            if not user.voice or not user.voice.channel:
                await channel.send("❌ Pehle voice channel join karo.")
                return
            vc = await user.voice.channel.connect()

        state = self.state(guild.id)
        state.channel = channel

        if vc.is_playing() or vc.is_paused():
            state.queue.append(track)
            self.sync_music_state(guild.id)
            await channel.send(f"➕ **ZELROVA Queue:** {track.title}")
            return

        await self.play_track(guild, channel, track)

    async def play_track(self, guild, channel, track):
        state = self.state(guild.id)
        vc = guild.voice_client

        if not vc:
            return

        state.stopped = False
        state.channel = channel
        track = await self.fresh_stream(track)

        if not track.stream_url:
            await channel.send("❌ Audio stream URL nahi mila.")
            return

        source = discord.FFmpegPCMAudio(
            track.stream_url,
            executable="ffmpeg",
            before_options=FFMPEG_BEFORE,
            options=FFMPEG_OPTIONS,
        )
        source = discord.PCMVolumeTransformer(source, volume=state.volume)

        def after(error):
            asyncio.run_coroutine_threadsafe(
                self.after_track(guild, channel, error),
                self.bot.loop
            )

        state.current = track
        vc.play(source, after=after)
        self.sync_music_state(guild.id)

        if state.panel_message:
            try:
                await state.panel_message.delete()
            except Exception:
                pass

        embed = discord.Embed(
            title="🎧 ZELROVA Premium Music",
            description=f"**{track.title}**",
            color=0xFF2D75,
        )
        embed.add_field(name="⏱ Duration", value=self.duration(track.duration), inline=True)
        embed.add_field(name="👤 Requested By", value=track.requester, inline=True)
        embed.add_field(name="🔊 Volume", value=f"{int(state.volume * 100)}%", inline=True)
        embed.add_field(name="📜 Queue", value=str(len(state.queue)), inline=True)
        embed.add_field(name="🔁 Loop", value=str(state.loop), inline=True)
        embed.add_field(name="🌐 Source", value=track.source, inline=True)

        if track.page_url:
            embed.add_field(name="🔗 Link", value=track.page_url, inline=False)

        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        embed.set_footer(text="ZELROVA Bot • /z music system")

        state.panel_message = await channel.send(embed=embed, view=MusicPanel(self))

    async def after_track(self, guild, channel, error=None):
        state = self.state(guild.id)

        if error:
            print("Music playback error:", error)

        if state.stopped:
            self.sync_music_state(guild.id)
            return

        if state.loop and state.current:
            await self.play_track(guild, channel, state.current)
            return

        if state.queue:
            next_track = state.queue.pop(0)
            await self.play_track(guild, channel, next_track)
            return

        state.current = None
        state.stopped = True
        self.sync_music_state(guild.id)

    async def stop_music(self, guild):
        state = self.state(guild.id)
        state.stopped = True
        state.queue.clear()
        state.current = None

        if guild.voice_client:
            guild.voice_client.stop()
            await guild.voice_client.disconnect()

        if state.panel_message:
            try:
                await state.panel_message.delete()
            except Exception:
                pass
            state.panel_message = None

        self.sync_music_state(guild.id)

    async def pause_guild(self, guild):
        vc = guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            self.sync_music_state(guild.id)
            return "Paused."
        return "Nothing playing."

    async def resume_guild(self, guild):
        vc = guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            self.sync_music_state(guild.id)
            return "Resumed."
        return "Nothing paused."

    async def skip_guild(self, guild):
        vc = guild.voice_client
        if vc:
            vc.stop()
            self.sync_music_state(guild.id)
            return "Skipped."
        return "Nothing playing."

    async def dashboard_pause(self):
        for guild in self.bot.guilds:
            if guild.voice_client:
                return await self.pause_guild(guild)
        return "No active voice client."

    async def dashboard_resume(self):
        for guild in self.bot.guilds:
            if guild.voice_client:
                return await self.resume_guild(guild)
        return "No active voice client."

    async def dashboard_skip(self):
        for guild in self.bot.guilds:
            if guild.voice_client:
                return await self.skip_guild(guild)
        return "No active voice client."

    async def dashboard_stop(self):
        for guild in self.bot.guilds:
            if guild.voice_client:
                await self.stop_music(guild)
                return "Stopped."
        return "No active voice client."

    async def dashboard_volume(self, value):
        value = max(0, min(value, 200))

        for guild in self.bot.guilds:
            state = self.state(guild.id)
            state.volume = value / 100

            if guild.voice_client and guild.voice_client.source:
                guild.voice_client.source.volume = state.volume

            self.sync_music_state(guild.id)

        return f"Volume set to {value}%."

    async def dashboard_loop(self):
        for guild in self.bot.guilds:
            state = self.state(guild.id)
            state.loop = not state.loop
            self.sync_music_state(guild.id)
            return f"Loop: {state.loop}"
        return "No guild found."

    async def dashboard_shuffle(self):
        for guild in self.bot.guilds:
            state = self.state(guild.id)
            random.shuffle(state.queue)
            self.sync_music_state(guild.id)
            return "Queue shuffled."
        return "No guild found."

    async def send_queue(self, interaction):
        state = self.state(interaction.guild.id)

        if not state.queue:
            await interaction.followup.send("📭 Queue empty.", ephemeral=True)
            return

        text = "\n".join(
            [f"`{i}.` {track.title}" for i, track in enumerate(state.queue[:15], start=1)]
        )

        embed = discord.Embed(
            title="📜 ZELROVA Music Queue",
            description=text,
            color=0x7A5CFF,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="zplay", description="ZELROVA music play")
    async def zplay(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        try:
            results = await self.search_tracks(query, str(interaction.user))
        except Exception as e:
            await interaction.followup.send(f"❌ Search failed: `{str(e)[:250]}`")
            return

        if not results:
            await interaction.followup.send("❌ Song nahi mila.")
            return

        await self.add_or_play(interaction.guild, interaction.user, interaction.channel, results[0])
        await interaction.followup.send(f"✅ Playing: **{results[0].title}**", ephemeral=True)

    @app_commands.command(name="zsearch", description="ZELROVA music search")
    async def zsearch(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        state = self.state(interaction.guild.id)

        try:
            state.search_results = await self.search_tracks(query, str(interaction.user))
        except Exception as e:
            await interaction.followup.send(f"❌ Search failed: `{str(e)[:250]}`")
            return

        if not state.search_results:
            await interaction.followup.send("❌ Song nahi mila.")
            return

        embed = discord.Embed(
            title="🔍 ZELROVA Music Search",
            description=f"Results for **{query}**\nDropdown se song choose karo.",
            color=0xFF2D75,
        )
        embed.set_footer(text="Only ZELROVA Bot controls this menu.")

        await interaction.followup.send(
            embed=embed,
            view=SearchView(self, interaction.guild.id)
        )

    @app_commands.command(name="zstop", description="ZELROVA music stop")
    async def zstop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.stop_music(interaction.guild)
        await interaction.followup.send("⏹ Stopped.", ephemeral=True)

    @app_commands.command(name="zpause", description="ZELROVA music pause")
    async def zpause(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await self.pause_guild(interaction.guild)
        await interaction.followup.send(result, ephemeral=True)

    @app_commands.command(name="zresume", description="ZELROVA music resume")
    async def zresume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await self.resume_guild(interaction.guild)
        await interaction.followup.send(result, ephemeral=True)

    @app_commands.command(name="zskip", description="ZELROVA current song skip")
    async def zskip(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await self.skip_guild(interaction.guild)
        await interaction.followup.send(result, ephemeral=True)

    @app_commands.command(name="zqueue", description="ZELROVA queue dekho")
    async def zqueue(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.send_queue(interaction)

    @app_commands.command(name="zvolume", description="ZELROVA volume 0-200")
    async def zvolume(self, interaction: discord.Interaction, value: int):
        await interaction.response.defer(ephemeral=True)

        value = max(0, min(value, 200))
        state = self.state(interaction.guild.id)
        state.volume = value / 100

        if interaction.guild.voice_client and interaction.guild.voice_client.source:
            interaction.guild.voice_client.source.volume = state.volume

        self.sync_music_state(interaction.guild.id)

        await interaction.followup.send(f"🔊 Volume: `{value}%`", ephemeral=True)

    @app_commands.command(name="zloop", description="ZELROVA song loop toggle")
    async def zloop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        state = self.state(interaction.guild.id)
        state.loop = not state.loop

        self.sync_music_state(interaction.guild.id)

        await interaction.followup.send(f"🔁 Loop: `{state.loop}`", ephemeral=True)

    @app_commands.command(name="zshuffle", description="ZELROVA queue shuffle")
    async def zshuffle(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        state = self.state(interaction.guild.id)

        if len(state.queue) < 2:
            await interaction.followup.send("❌ Queue me 2+ songs chahiye.", ephemeral=True)
            return

        random.shuffle(state.queue)
        self.sync_music_state(interaction.guild.id)

        await interaction.followup.send("🔀 Queue shuffled.", ephemeral=True)

    @app_commands.command(name="znowplaying", description="Current ZELROVA song")
    async def znowplaying(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        state = self.state(interaction.guild.id)

        if not state.current:
            await interaction.followup.send("❌ Nothing playing.", ephemeral=True)
            return

        track = state.current

        embed = discord.Embed(
            title="🎵 ZELROVA Now Playing",
            description=f"**{track.title}**",
            color=0xFF2D75,
        )
        embed.add_field(name="Duration", value=self.duration(track.duration))
        embed.add_field(name="Requested By", value=track.requester)

        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="zplayfile", description="Uploaded audio file play")
    async def zplayfile(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer()

        if not file.filename.lower().endswith(AUDIO_EXTENSIONS):
            await interaction.followup.send("❌ Supported: mp3, wav, m4a, flac, ogg, aac", ephemeral=True)
            return

        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        path = os.path.join(tempfile.gettempdir(), file.filename)
        await file.save(path)

        track = Track(
            title=file.filename,
            page_url=path,
            stream_url=path,
            requester=str(interaction.user),
            source="Local File",
        )

        await self.add_or_play(interaction.guild, interaction.user, interaction.channel, track)
        await interaction.followup.send(f"✅ Playing file: **{file.filename}**", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Music(bot))