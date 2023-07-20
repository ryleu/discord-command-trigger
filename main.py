import discord
import json
import os
import io

# pull the config data. this does not need to be updated live
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

# this bot requires the message content intent
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"logged in as {client.user}")


@client.event
async def on_message(message):
    # make sure the message is from an valid user in a valid channel
    if (
        message.channel.id not in config["channel_ids"]
        or message.author.id not in config["owner_ids"]
    ):
        return

    # we don't store the flows because we want to be able to live update them
    flows = {}
    with open("flows.json") as file:
        flows = json.loads(file.read())

    for name in flows:
        if message.content == name:
            # split out all of the data from the dict to variables for easy access
            flow = flows[name]
            steps = flow.get(
                "steps", [f"echo 'The flow `{name}` has no associated steps.'"]
            )
            file_format = flow.get("format", "ansi")
            description = flow.get("description", "*No description.*")
            to_run = "\n".join(steps)

            # initial message informing the user what they just ran
            await message.channel.send(
                f"## description:\n> {description}\n"
                + f"## running commands:\n```sh\n{to_run}\n```"
            )

            # combine all steps into a single command
            msg = os.popen(" ; ".join(steps)).read()

            # we send it as a file if the response is over 1000 characters
            # so that it doesn't take up too much space
            if len(msg) < 1000:
                # special exception for the `discord` format to allow for
                # pings and channel mentions
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
