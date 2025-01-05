import argparse
import discord
from discord.ext import commands
import os
from datetime import datetime, timezone
import asyncio


# Load environment variables from .env
def load_env(file_path=".env"):
    env_vars = {}
    if not os.path.exists(file_path):
        print(".env file not found. Skipping...")
        return env_vars

    with open(file_path, "r") as f:
        for line in f:
            if line.strip() == "" or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip()

    return env_vars


# Command to download attachments
async def download_channel_attachments(
    channel: discord.PartialMessageable,
    download_directory: str = "",
    start_date: str = None,
    end_date: str = None,
    extensions: list = ["png", "jpg", "jpeg", "gif"],
):
    if download_directory == "":
        download_directory = "downloads"

    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    start_dt = (
        datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        if start_date
        else None
    )
    end_dt = (
        datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        if end_date
        else None
    )

    await channel.send("⏳ Fetching images...")

    async for msg in channel.history(limit=10000):
        if (start_dt and msg.created_at < start_dt) or (
            end_dt and msg.created_at > end_dt
        ):
            continue

        for attachment in msg.attachments:
            if any(attachment.filename.endswith(ext) for ext in extensions):
                file_path = os.path.join(download_directory, attachment.filename)
                await attachment.save(file_path)
                print(f"✅ Saved: {file_path}")

    await channel.send("🎉 All images have been downloaded!")


intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

env_vars = load_env(".env")
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.command()
async def gimme(ctx: commands.Context, start_date: str = None, end_date: str = None):
    await ctx.send("🛠️ Starting download...")

    channel = ctx.channel
    await download_channel_attachments(
        channel=channel,
        download_directory="",
        start_date=start_date,
        end_date=end_date,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Discord bot to download attachments with optional date filtering."
    )
    parser.add_argument(
        "-t",
        "--token",
        type=str,
        default=env_vars.get("TOKEN"),
        help="Discord bot token",
    )
    args = parser.parse_args()

    bot.run(args.token)
