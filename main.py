import argparse
import tempfile
import discord
from discord.ext import commands
import os
from datetime import datetime, timezone
import asyncio
import io
import zipfile


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


def get_zip_filename(start_date: str = None, end_date: str = None) -> str:
    if start_date and end_date:
        return f"{start_date}_{end_date}.zip"
    if start_date:
        return f"{start_date}.zip"
    if end_date:
        return f"{end_date}.zip"
    return "attachments.zip"


def parse_date(date_str: str):
    """
    Returns a datetime object of a valid date string. Valid formats (%d-%m-%Y, %d/%m/%Y, %Y-%m-%d, "%Y/%m/%d")
    """

    valid_formats = (
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
    )
    for date_format in valid_formats:
        try:
            return datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise ValueError(f"Date '{date_str}' is not in a recognized format.")


# Command to download attachments
async def download_channel_attachments(
    channel: discord.PartialMessageable,
    start_date: str = None,
    end_date: str = None,
    extensions: list = ["png", "jpg", "jpeg", "gif"],
):

    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None

    await channel.send("⏳ Fetching images...")

    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            zip_filename = temp_zip.name

            with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                async for msg in channel.history(limit=10000):
                    if (start_dt and msg.created_at < start_dt) or (
                        end_dt and msg.created_at > end_dt
                    ):
                        continue

                    for attachment in msg.attachments:
                        if any(attachment.filename.endswith(ext) for ext in extensions):
                            try:
                                attachment_data = await attachment.read()
                                zipf.writestr(attachment.filename, attachment_data)
                                print(f"✅ Added to ZIP: {attachment.filename}")
                            except Exception as e:
                                print(f"❌ Failed to fetch {attachment.filename}: {e}")

        filename = get_zip_filename(start_date, end_date)
        await channel.send(
            "🎉 All images have been downloaded!",
            file=discord.File(fp=zip_filename, filename=filename),
        )
        print("✅ Sent ZIP file to user.")

    except Exception as e:
        await channel.send(f"❌ An error occurred: {e}")
        print(f"❌ Error: {e}")
    finally:
        if os.path.exists(zip_filename):
            os.remove(zip_filename)


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
async def gimme(
    channel: commands.Context, start_date: str = None, end_date: str = None
):
    await channel.send("🛠️ Starting download...")

    channel = channel.channel
    await download_channel_attachments(
        channel=channel,
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
