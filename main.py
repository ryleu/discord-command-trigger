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
        if message.content == name:
            os.system(f"cd {working_directory}")

            flow = flows[name]
            steps = flow.get(
                "steps", [f"echo 'The flow `{name}` has no associated steps.'"]
            )
            file_format = flow.get("format", "ansi")
            description = flow.get("description", "*No description.*")
            to_run = "\n".join(steps)

            await message.channel.send(
                f"## description:\n> {description}\n"
                + f"## running commands:\n```sh\n{to_run}\n```"
            )

            msg = os.popen(" ; ".join(steps)).read()

            if len(msg) < 1000:
                if file_format == "discord":
                    await message.channel.send(
                        f"## command output:\n{msg}",
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                else:
                    await message.channel.send(
                        f"## command output:\n```{file_format}\n{msg}\n```"
                    )
            else:
                await message.channel.send(
                    "## command output:",
                    file=discord.File(
                        filename=f"{name}.{file_format}", fp=io.BytesIO(msg.encode())
                    ),
                )
            break


client.run(config["token"])
