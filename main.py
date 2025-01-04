import discord
import os
import asyncio

TOKEN = "TOKEN"
CHANNEL_ID = "CHANNEL_ID"

intents = discord.Intents.default()
intents.messages = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}!")

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("Channel not found. Check your CHANNEL_ID.")
        await client.close()
        return

    print(f"Fetching images from #{channel.name}...")

    # Fetch and download images
    async for msg in channel.history(limit=100):
        for attachment in msg.attachments:
            if attachment.filename.endswith(("png", "jpg", "jpeg", "gif")):
                file_path = os.path.join("downloads", attachment.filename)
                await attachment.save(file_path)
                print(f"Saved: {file_path}")

    print("All images downloaded!")
    await client.close()


# Run the bot
client.run(TOKEN)
