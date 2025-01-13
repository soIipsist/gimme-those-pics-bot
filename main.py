import argparse
import tempfile
import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import zipfile

MAX_ZIP_SIZE = 8 * 1024 * 1024  # 8 MB file limit for discord attachments
valid_extensions = [
    # Image file extensions
    "jpg",
    "jpeg",
    "png",
    "gif",
    "bmp",
    "webp",
    "tiff",
    # Video file extensions
    "mp4",
    "mkv",
    "avi",
    "mov",
    "wmv",
    "flv",
    "webm",
    # Audio file extensions
    "mp3",
    "wav",
    "ogg",
    "flac",
    "aac",
    "m4a",
    # Document file extensions
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "xls",
    "xlsx",
    "txt",
    "rtf",
    "csv",
    # Compressed file extensions
    "zip",
    "rar",
    "7z",
    "tar",
    "gz",
]


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
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    start_str = start_dt.strftime("%d-%m-%Y") if start_dt else None
    end_str = end_dt.strftime("%d-%m-%Y") if end_dt else None

    if start_str and end_str:
        return f"{start_str} - {end_str}.zip"
    elif start_str and not end_str:
        return f"{start_str}.zip"
    elif end_str and not start_str:
        return f"{end_str}.zip"
    else:
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

    if isinstance(date_str, datetime):
        return date_str

    for date_format in valid_formats:
        try:
            return datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise ValueError(f"Date '{date_str}' is not in a recognized format.")


async def send_zip_file(
    channel: discord.PartialMessageable, zip_filepath, zip_filename, zip_counter
):
    try:
        msg = f"✅ Successfully generated zip file ({zip_counter})!"
        await channel.send(
            msg,
            file=discord.File(zip_filepath, zip_filename),
        )
        print(f"✅ Sent ZIP file part {zip_counter}")
    except Exception as e:
        print(f"❌ Error sending ZIP file part {zip_counter}: {e}")


async def find_channel(ctx: commands.Context, channel: str = None):
    """
    Finds a channel by its ID or name within the current guild (server).
    """

    guild = ctx.guild
    if guild is None:
        await ctx.send("❌ This command must be used in a server, not in a DM.")
        return None

    if channel is None:
        return ctx.channel

    # get channel by ID
    try:
        channel_id = int(channel)
        found_channel = guild.get_channel(channel_id)
        if found_channel:
            return found_channel
    except ValueError:
        pass

    # get channel by name
    for ch in guild.text_channels:
        if ch.name == channel:
            return ch

    await ctx.send(f"❌ Channel '{channel}' not found in this server.")
    return None


# Command to download attachments
async def download_channel_attachments(
    ctx_channel: discord.PartialMessageable,
    channel: discord.PartialMessageable,
    start_date: str,
    end_date: str,
    extensions: list,
):
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    msg = (
        f"⏳ Fetching attachments with extensions {', '.join(extensions)} from channel #{channel}..."
        if extensions
        else f"⏳ Fetching all attachments from channel #{channel}..."
    )
    await ctx_channel.send(msg)

    try:
        attachment_count = 0
        total_bytes = 0
        zip_counter = 0
        zip_filename = get_zip_filename(start_dt, end_dt)
        zip_path = None
        zipf = None

        async for msg in channel.history(limit=10000):
            if (start_dt and msg.created_at < start_dt) or (
                end_dt and msg.created_at > end_dt
            ):
                continue

            for attachment in msg.attachments:
                if extensions is None or any(
                    attachment.filename.endswith(ext) for ext in extensions
                ):
                    try:
                        attachment_data = await attachment.read()

                        if total_bytes + len(attachment_data) > MAX_ZIP_SIZE:
                            if zipf:
                                zipf.close()
                                zip_counter += 1

                                await send_zip_file(
                                    ctx_channel,
                                    zip_path,
                                    zip_filename,
                                    zip_counter,
                                )
                                total_bytes = 0
                                zipf = None

                        if zipf is None:
                            temp_zip = tempfile.NamedTemporaryFile(
                                suffix=".zip", delete=False
                            )
                            zipf = zipfile.ZipFile(
                                temp_zip.name, "w", zipfile.ZIP_DEFLATED
                            )
                            zip_path = temp_zip.name

                        # Add the attachment to the zip file
                        zipf.writestr(attachment.filename, attachment_data)
                        total_bytes += len(attachment_data)
                        attachment_count += 1
                        print(f"✅ Added to ZIP: {attachment.filename}")

                    except Exception as e:
                        print(f"❌ Failed to fetch {attachment.filename}: {e}")

        if attachment_count > 0:
            if zipf:
                zipf.close()
                zipf = None
            zip_counter += 1
            await send_zip_file(ctx_channel, zip_path, zip_filename, zip_counter)

        print("✅ All attachments have been processed.")

    except Exception as e:
        await ctx_channel.send(f"❌ An error occurred: {e}")
        print(f"❌ Error: {e}")

    finally:

        try:
            if os.path.exists(zip_filename):
                os.remove(zip_filename)

        except Exception as e:
            print(f"❌ Failed to clean up: {e}")

        for i in range(1, zip_counter):
            try:
                zip_filename_with_counter = f"{zip_filename}_part{i}.zip"
                if os.path.exists(zip_filename_with_counter):
                    os.remove(zip_filename_with_counter)

            except Exception as e:
                print(f"❌ Failed to clean up: {e}")

    await ctx_channel.send(
        f"🎉 Operation successful! \n📎 Attachments found: {attachment_count}\n📁 Zip files created: {zip_counter} "
    )


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
    extensions = None
    start_date = None
    end_date = None
    channel = None

    for opt in options.split():
        if "=" in opt:
            key, value = opt.split("=", 1)
            if key == "start_date":
                start_date = value
            elif key == "end_date":
                end_date = value
            elif key == "extensions":
                extensions = value.split(",")
            elif key == "channel":
                channel = value
        else:
            opt = opt.strip()
            if opt.isdigit():
                channel = opt
            elif "-" in opt or "/" in opt:
                try:
                    parse_date(opt)
                    if start_date is None:
                        start_date = opt
                    elif end_date is None:
                        end_date = opt
                except ValueError:

                    if channel is None:
                        channel = opt
                    else:
                        print(
                            f"⚠️ Channel name '{opt}' ignored due to previous channel setting."
                        )

            elif "," in opt:
                extensions = opt.split(",")
            elif opt in valid_extensions:  # Single extension
                extensions = [opt]
            else:
                channel = opt

    if start_date is None:
        start_date = datetime.now().strftime("%Y-%m-%d")

    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    opts = {
        "start_date": start_date,
        "end_date": end_date,
        "extensions": extensions,
        "channel": channel,
    }

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
    options = parse_options(options)
    channel = await find_channel(ctx, options.channel)

    await download_channel_attachments(
        ctx_channel=ctx.channel,
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
