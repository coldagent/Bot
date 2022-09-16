import yt_dlp
import asyncio
import discord
from discord.ext import commands

class YTDLSource(discord.PCMVolumeTransformer):
    # Suppress noise about console usage from errors
    yt_dlp.utils.bug_reports_message = lambda: ''

    ytdl_format_options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'songs/%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes,
        'buffer_size': '1000M'
    }

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
        'options': '-vn'
    }

    ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(url))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename: str = "songs/" + data['title'] + ".mp3"
        filename = filename.replace(" ", "_")
        filename = filename.replace("(", "")
        filename = filename.replace(")", "")
        filename = filename.replace("#", "")
        filename = filename.replace("“", "")
        filename = filename.replace("”", "")
        filename = filename.replace("*", "")
        filename = filename.replace(":", "")
        filename = filename.replace("/", "")
        return cls(source=discord.FFmpegPCMAudio(filename), data=data)

