import argparse
import tempfile
import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import zipfile

MAX_ZIP_SIZE = 8 * 1024 * 1024  # 8 MB file limit for discord attachments


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


def get_zip_filename(start_date: str, end_date: str) -> str:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    filename = f"{start_dt.strftime('%d-%m-%Y')} - {end_dt.strftime('%d-%m-%Y')}.zip"
    return filename


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
    if isinstance(date_str, datetime):
        return date_str
    for date_format in valid_formats:
        try:
            return datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise ValueError(f"Date '{date_str}' is not in a recognized format.")


async def send_zip_file(channel: discord.PartialMessageable, zip_filename, zip_counter):
    zip_filename_with_counter = f"{zip_filename}_part{zip_counter}.zip"
    try:
        await channel.send(
            f"🎉 Part {zip_counter} of the images have been downloaded!",
            file=discord.File(zip_filename_with_counter),
        )
        print(f"✅ Sent ZIP file part {zip_counter}")
    except Exception as e:
        print(f"❌ Error sending ZIP file part {zip_counter}: {e}")


# Command to download attachments
async def download_channel_attachments(
    channel: discord.PartialMessageable,
    start_date: str,
    end_date: str,
    extensions: list,
):

    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    await channel.send("⏳ Fetching images...")

    try:
        attachment_count = 0
        total_bytes = 0
        zip_counter = 1

        zip_filename = get_zip_filename(start_date, end_date)

        async for msg in channel.history(limit=10000):
            if (start_dt and msg.created_at < start_dt) or (
                end_dt and msg.created_at > end_dt
            ):
                continue

            for attachment in msg.attachments:
                if any(attachment.filename.endswith(ext) for ext in extensions):
                    try:
                        attachment_data = await attachment.read()

                        # Check if the current ZIP file is too large
                        if total_bytes + len(attachment_data) > MAX_ZIP_SIZE:
                            await send_zip_file(channel, zip_filename, zip_counter)
                            zip_counter += 1
                            total_bytes = 0  # Reset the total bytes for the new ZIP

                        with tempfile.NamedTemporaryFile(
                            suffix=".zip", delete=False
                        ) as temp_zip:
                            zipf = zipfile.ZipFile(
                                temp_zip.name, "w", zipfile.ZIP_DEFLATED
                            )
                            zipf.writestr(attachment.filename, attachment_data)
                            zipf.close()

                        total_bytes += len(attachment_data)
                        attachment_count += 1
                        print(f"✅ Added to ZIP: {attachment.filename}")

                    except Exception as e:
                        print(f"❌ Failed to fetch {attachment.filename}: {e}")

        if attachment_count > 0:
            await send_zip_file(channel, zip_filename, zip_counter)

        print("✅ All attachments have been processed.")

    except Exception as e:
        await channel.send(f"❌ An error occurred: {e}")
        print(f"❌ Error: {e}")

    finally:
        for i in range(1, zip_counter):
            try:
                zip_path = f"{zip_filename}_part{i}.zip"
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception as e:
                print(f"❌ Failed to clean up: {e}")


intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

env_vars = load_env(".env")
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


def parse_options(options: str = ""):
    extensions = ["png", "jpg", "jpeg", "gif"]
    start_date = None
    end_date = None

    for opt in options.split():
        if "=" in opt:
            key, value = opt.split("=", 1)
            if key == "start_date":
                start_date = value
            elif key == "end_date":
                end_date = value
            elif key == "extensions":
                extensions = value.split(",")
        else:
            if opt.isdigit() or "-" in opt or "/" in opt:
                if start_date is None:
                    start_date = opt
                elif end_date is None:
                    end_date = opt
            elif "," in opt:
                extensions = opt.split(",")
            else:
                extensions = [opt]

    if start_date is None:
        start_date = datetime.now().strftime("%Y-%m-%d")

    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    opts = {"start_date": start_date, "end_date": end_date, "extensions": extensions}

    return SimpleNamespace(**opts)


@bot.command()
async def gimme(ctx: commands.Context, *, options: str = ""):
    """
    Downloads attachments based on optional arguments.
    Examples:
    - !gimme
    - !gimme 2024-01-01 2024-02-01 jpg,png
    - !gimme start_date=2024-01-01 end_date=2024-02-01 extensions=jpg,png
    - !gimme extensions=gif,jpg
    """
    await ctx.send("🛠️ Starting download...")
    options = parse_options(options)
    channel = ctx.channel

    await ctx.send(options)

    await download_channel_attachments(
        channel=channel,
        start_date=options.start_date,
        end_date=options.end_date,
        extensions=options.extensions,
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
