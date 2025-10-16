# Our objectives:
# - Create a view that handles errors
# - Create a view that disables all components after timeout
# - Make sure that the view only processes interactions from the user who invoked the command

from __future__ import annotations

import typing
import traceback

import discord
from discord.ui.select import BaseSelect

from data.interface import get_raid_leader, set_raid_leader, get_raid_supports, read_raid, set_raid_supports, \
    set_raid_leaders, get_raid_leaders, set_raid_backup_leaders, get_raid_backup_leaders
from data.models import Raid


class BaseView(discord.ui.View):
    interaction: discord.Interaction | None = None
    message: discord.Message | None = None

    def __init__(self, user: discord.User | discord.Member, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        # We set the user who invoked the command as the user who can interact with the view
        self.user = user

    # make sure that the view only processes interactions from users
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.bot:
            return False
        # update the interaction attribute when a valid interaction is received
        self.interaction = interaction
        return True

    # to handle errors we first notify the user that an error has occurred and then disable all components

    def _disable_all(self) -> None:
        # disable all components
        # so components that can be disabled are buttons and select menus
        for item in self.children:
            if isinstance(item, discord.ui.Button) or isinstance(item, BaseSelect):
                item.disabled = True

    # after disabling all components we need to edit the message with the new view
    # now when editing the message there are two scenarios:
    # 1. the view was never interacted with i.e in case of plain timeout here message attribute will come in handy
    # 2. the view was interacted with and the interaction was processed and we have the latest interaction stored in the interaction attribute
    async def _edit(self, **kwargs: typing.Any) -> None:
        if self.interaction is None and self.message is not None:
            # if the view was never interacted with and the message attribute is not None, edit the message
            await self.message.edit(**kwargs)
        elif self.interaction is not None:
            try:
                # if not already responded to, respond to the interaction
                await self.interaction.response.edit_message(**kwargs)
            except discord.InteractionResponded:
                # if already responded to, edit the response
                await self.interaction.edit_original_response(**kwargs)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[BaseView]) -> None:
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        message = f"An error occurred while processing the interaction for {str(item)}:\n```py\n{tb}\n```"
        # disable all components
        self._disable_all()
        # edit the message with the error message
        await self._edit(content=message, view=self)
        # stop the view
        self.stop()

    async def on_timeout(self) -> None:
        # disable all components
        self._disable_all()
        # edit the message with the new view
        await self._edit(view=self)


class RaidView(BaseView):
    async def change_embed(self):
        raid: Raid = read_raid(int(self.raid_id))
        leaders: list[int] = get_raid_leaders(int(self.raid_id))
        supports: list[int] = get_raid_supports(int(self.raid_id))

        old_embed = self.original.embeds[0]

        list_leaders: str = "<@" + ">, <@".join(map(str, leaders)) + ">" if leaders is not None and len(leaders) > 0 else "None"
        list_supports: str = "<@" + ">, <@".join(map(str, supports)) + ">" if supports is not None and len(supports) > 0 else "None"

        new_description = f"""
            {raid.description}
            --------------------------------------
            Leader ({len(leaders) if leaders is not None else 0}/1): <@{list_leaders}>
            Supports ({len(supports) if supports is not None else 0}/19): {list_supports}
        """

        new_embed = discord.Embed(title=raid.title, description=new_description)
        new_embed.description = new_description
        new_embed.set_thumbnail(url=old_embed.thumbnail.url)
        new_embed.set_image(url=old_embed.image.url)
        new_embed.set_footer(text=f"Raid: {raid.id}")

        await self.original.edit(embed=new_embed, view=self)

    def __init__(self, user: discord.User | discord.Member, raid_id: int, message: discord.Message, timeout: float = 60.0):
        super().__init__(user, timeout)
        self.raid_id = raid_id
        self.original = message

        async def cb_leader(interaction: discord.Interaction):
            leaders: list[int] | None = get_raid_leaders(int(interaction.data['custom_id'].split(":")[1]))

            if leaders is not None and len(leaders) > 0 and interaction.user.id not in leaders:
                await interaction.response.send_message(f"<@{leaders[0]}> is already registered as leader for this raid.", ephemeral=True)
                return

            set_raid_leaders(self.raid_id, [interaction.user.id])
            await interaction.response.send_message(f"You un/registered as leader for this raid.", ephemeral=True)
            await self.change_embed()

        async def cb_support(interaction: discord.Interaction):
            supports: list[int] | None = get_raid_supports(int(interaction.data['custom_id'].split(":")[1]))

            if supports is not None and len(supports) == 19 and interaction.user.id not in supports:
                await interaction.response.send_message(f"Raid is already full, please try another time.", ephemeral=True)
                return

            set_raid_supports(self.raid_id, [interaction.user.id])
            await interaction.response.send_message(f"You un/registered as support for this raid.", ephemeral=True)
            await self.change_embed()

        self.add_item(
            discord.ui.Button(
                label="Apply as leader",
                style=discord.ButtonStyle.danger,
                custom_id=f"leader:{raid_id}"
            )
        )

        self.children[0].callback = cb_leader

        self.add_item(
            discord.ui.Button(
                label="Apply as support",
                style=discord.ButtonStyle.blurple,
                custom_id=f"support:{raid_id}"
            )
        )

        self.children[1].callback = cb_support


class ClashView(BaseView):
    async def change_embed(self):
        raid: Raid = read_raid(int(self.raid_id))
        leaders: list[int] = get_raid_leaders(int(self.raid_id))
        backups: list[int] = get_raid_backup_leaders(int(self.raid_id))
        supports: list[int] = get_raid_supports(int(self.raid_id))

        list_leaders: str = "<@" + ">, <@".join(map(str, leaders)) + ">" if leaders is not None and len(leaders) > 0 else "None"
        list_backups: str = "<@" + ">, <@".join(map(str, backups)) + ">" if backups is not None and len(backups) > 0 else "None"
        list_supports: str = "<@" + ">, <@".join(map(str, supports)) + ">" if supports is not None and len(supports) > 0 else "None"

        new_description = f"""
            {raid.description}
            --------------------------------------
            Drivers ({len(leaders) if leaders is not None else 0}/{self.arrays}): {list_leaders}
            Backups ({len(backups) if backups is not None else 0}): {list_backups}
            Supports ({len(supports) if supports is not None else 0}/{4*self.arrays}): {list_supports}
        """

        new_embed = discord.Embed(title=raid.title, description=new_description)
        new_embed.description = new_description
        new_embed.set_footer(text=f"Raid: {raid.id}")

        await self.original.edit(embed=new_embed, view=self)

    def __init__(self, user: discord.User | discord.Member, raid_id: int, message: discord.Message, arrays: int = 3, timeout: float = 60.0):
        super().__init__(user, timeout)
        self.raid_id = raid_id
        self.original = message
        self.arrays = arrays

        async def cb_leader(interaction: discord.Interaction):
            leaders: list[int] | None = get_raid_leaders(int(interaction.data['custom_id'].split(":")[1]))
            supports: list[int] | None = get_raid_supports(int(interaction.data['custom_id'].split(":")[1]))

            if supports is not None and interaction.user.id in supports:
                await interaction.response.send_message(f"You registered as support for this raid.", ephemeral=True)
                return

            if leaders is not None and len(leaders) == arrays and interaction.user.id not in leaders:
                await interaction.response.send_message(f"Raid is already full, adding to backup drivers.", ephemeral=True)
                set_raid_backup_leaders(self.raid_id, [interaction.user.id])
                return

            set_raid_leaders(self.raid_id, [interaction.user.id])
            await interaction.response.send_message(f"You un/registered as driver for this raid.", ephemeral=True)
            await self.change_embed()

        async def cb_support(interaction: discord.Interaction):
            leaders: list[int] | None = get_raid_leaders(int(interaction.data['custom_id'].split(":")[1]))
            supports: list[int] | None = get_raid_supports(int(interaction.data['custom_id'].split(":")[1]))

            if leaders is not None and interaction.user.id in leaders:
                await interaction.response.send_message(f"You registered as driver for this raid.", ephemeral=True)
                return

            if supports is not None and len(supports) == 4*arrays and interaction.user.id not in supports:
                await interaction.response.send_message(f"Raid is already full, please try another time.", ephemeral=True)
                return

            set_raid_supports(self.raid_id, [interaction.user.id])
            await interaction.response.send_message(f"You un/registered as support for this raid.", ephemeral=True)
            await self.change_embed()

        self.add_item(
            discord.ui.Button(
                label="Apply as driver",
                style=discord.ButtonStyle.danger,
                custom_id=f"leader:{raid_id}"
            )
        )

        self.children[0].callback = cb_leader

        self.add_item(
            discord.ui.Button(
                label="Apply as support",
                style=discord.ButtonStyle.blurple,
                custom_id=f"support:{raid_id}"
            )
        )

        self.children[1].callback = cb_support