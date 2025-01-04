import argparse
import discord
import os
from datetime import datetime
import asyncio


async def download_images(
    token: str,
    channel_id: int,
    download_directory: str = None,
    start_date: str = None,
    end_date: str = None,
    extensions: list = ["png", "jpg", "jpeg", "gif"],
):
    if download_directory is None:
        download_directory = ""

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}.")

        channel = client.get_channel(channel_id)
        if channel is None:
            print("Channel not found. Check your CHANNEL_ID.")
            await client.close()
            return

        print(f"Fetching images from #{channel.name}...")

        async for msg in channel.history(limit=10000):
            if (start_dt and msg.created_at < start_dt) or (
                end_dt and msg.created_at > end_dt
            ):
                continue

            for attachment in msg.attachments:
                if any(attachment.filename.endswith(ext) for ext in extensions):
                    file_path = os.path.join(download_directory, attachment.filename)
                    await attachment.save(file_path)
                    print(f"Saved: {file_path}")

        print("🎉 All images downloaded!")
        await client.close()

    await client.start(token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download images from a Discord channel with date filtering."
    )
    parser.add_argument(
        "-t", "--token", type=str, required=True, help="Discord bot token"
    )
    parser.add_argument(
        "-c",
        "--channel_id",
        type=int,
        required=True,
        help="Channel ID to fetch messages from",
    )
    parser.add_argument(
        "-d",
        "--download_directory",
        type=str,
        default=None,
        help="Directory to save images",
    )
    parser.add_argument("-s", "--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("-ed", "--end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "-e",
        "--extensions",
        type=str,
        nargs="*",
        default=["png", "jpg", "jpeg", "gif"],
        help="File extensions to download (e.g., png jpg gif)",
    )

    args = parser.parse_args()

    asyncio.run(
        download_images(
            token=args.token,
            channel_id=args.channel_id,
            download_directory=args.download_directory,
            start_date=args.start_date,
            end_date=args.end_date,
            extensions=args.extensions,
        )
    )
