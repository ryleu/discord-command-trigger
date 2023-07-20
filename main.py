copyright_notice = """\
Copyright © 2023 Riley <riley@ryleu.me>.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>. 
"""

import discord
import json
import io
from subprocess import PIPE, Popen

# pull the config data. this does not need to be updated live
config = {}
with open("config.json") as file:
    config = json.loads(file.read())

# this bot requires the message content intent
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"logged in as \u001b[1m{bot.user}\u001b[0m")


@bot.event
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
            # split out the data from the dict to variables for easy access
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

            # combine all steps into a single command & run it
            p = Popen(" ; ".join(steps), shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()

            # we send it as a file if the response is over 1000 characters
            # so that it doesn't take up too much space
            content = "## command output:"
            files = []

            if len(stdout) < 1000:
                # special exception for the `discord` format to allow for
                # pings and channel mentions
                if file_format == "discord":
                    content += f"\n{stdout.decode()}"
                else:
                    content += f"\n```{file_format}\n{stdout.decode()}\n```"
            else:
                files.append(
                    discord.File(
                        filename=f"{name}.{file_format}", fp=io.BytesIO(stdout)
                    )
                )

            # add stderr as a file if we have any error
            if stderr:
                files.append(
                    discord.File(filename=f"error.ansi", fp=io.BytesIO(stderr))
                )

            await message.channel.send(
                content, files=files, allowed_mentions=discord.AllowedMentions.none()
            )
            break


if __name__ == "__main__":
    print(copyright_notice)
    bot.run(config["token"])
