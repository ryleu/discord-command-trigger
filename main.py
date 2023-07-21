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


async def parse_flow(message, flow, name):
    # split out the data from the dict to variables for easy access
    steps = flow.get("steps", [f"echo 'The flow `{name}` has no associated steps.'"])
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

    if stdout:
        if len(stdout) < config["max_codeblock_length"]:
            # special exception for the `discord` format to allow for
            # pings and channel mentions
            if file_format == "discord":
                content += f"\n{stdout.decode()}"
            else:
                content += f"\n```{file_format}\n{stdout.decode()}\n```"
        else:
            files.append(
                discord.File(filename=f"stdout.{file_format}", fp=io.BytesIO(stdout))
            )

    # add stderr as a file if we have any error
    if stderr:
        files.append(discord.File(filename=f"stderr.ansi", fp=io.BytesIO(stderr)))

    await message.channel.send(
        content, files=files, allowed_mentions=discord.AllowedMentions.none()
    )


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
            await parse_flow(message, flows[name], name)
            return

    # the same goes for templates
    templates = {}
    with open("templates.json") as file:
        templates = json.loads(file.read())

    for name in templates:
        split = message.content.split(" ")
        template_args = split[1:]
        if split[0] == name:
            template = templates[name]

            # ensure that there are the correct number of arguments
            # and that each argument has a valid value
            replacements = template["replacements"]
            for i in range(len(replacements)):
                replacement = replacements[i]
                try:
                    if template_args[i] not in replacement["values"]:
                        return await message.channel.send(
                            f"Error: `{template_args[i]}` is not a valid value for "
                            + f"`{replacement['name']}` in `{name}`. "
                            + f"Valid values: `{'`, `'.join(replacement['values'])}`."
                        )
                except IndexError:
                    return await message.channel.send(
                        f"Error: `{name}` requires {len(replacements)} argument(s) "
                        + f"({len(template_args)} provided): "
                        + f"`{'`, `'.join([ x['name'] for x in replacements])}`. "
                    )

            # build a dict to format the template with
            to_format = {
                key: value
                for key, value in zip(
                    [ x["name"] for x in template["replacements"] ], template_args
                )
            }

            # build the flow from the formatted template
            flow = {
                "steps": [
                    template["steps"][x].format(**to_format)
                    for x in range(len(template["steps"]))
                ]
            }

            for key in ["description", "format"]:
                if key in template:
                    flow[key] = template[key]

            await parse_flow(message, flow, name)


if __name__ == "__main__":
    print(copyright_notice)
    bot.run(config["token"])
