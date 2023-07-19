import discord
import json
import os
import io

working_directory = os.getcwd()

config = {}
with open("config.json") as file:
    config = json.loads(file.read())

# config.json example
"""
{
    "token": "token here",
    "owner_ids": [
        587967909641584661,
        600130839870963725
    ],
    "channel_ids": [
        795651596709003295
    ]
}
"""

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if (
        message.author == client.user
        or message.channel.id not in config["channel_ids"]
        or message.author.id not in config["owner_ids"]
    ):
        return

    flows = {}
    with open("flows.json") as file:
        flows = json.loads(file.read())

    for name in flows:
        if message.content.startswith(name):
            os.system(f"cd {working_directory}")

            to_run = "\n".join(flows[name])
            await message.channel.send(f"running commands:\n```sh\n{to_run}\n```")

            msg = os.popen(" ; ".join(flows[name])).read()

            if len(msg) < 1000:
                await message.channel.send(f"command output:\n```\n{msg}\n```")
            else:
                await message.channel.send(
                    "command output:",
                    file=discord.File(filename="output.txt", fp=io.BytesIO(msg.encode())),
                )


client.run(config["token"])
