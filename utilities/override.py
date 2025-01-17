import discord
from discord.ext import commands
from utilities import views


class BotContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.handled = False

    def is_owner(self):
        """ Checks if the author is one of the owners """
        return self.author.id in self.bot.constants.owners

    def is_admin(self):
        return (
            self.author.id in self.bot.constants.admins
            or self.author.id in self.bot.constants.owners
        )

    async def fail(self, content=None, refer=True, **kwargs):
        if refer:
            return await self.send_or_reply(
                self.bot.emote_dict["failed"] + " " + (content if content else ""),
                **kwargs,
            )
        return await self.send(
            self.bot.emote_dict["failed"] + " " + (content if content else ""), **kwargs
        )

    async def success(self, content=None, **kwargs):
        return await self.send_or_reply(
            self.bot.emote_dict["success"] + " " + (content if content else ""),
            **kwargs,
        )

    async def music(self, content=None, **kwargs):
        return await self.send_or_reply(
            self.bot.emote_dict["music"] + " " + (content if content else ""),
            **kwargs,
        )

    async def send_or_reply(self, content=None, **kwargs):
        if not self.channel.permissions_for(self.me).send_messages:
            return
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return await self.send(
                content, **kwargs, reference=ref.resolved.to_reference()
            )
        return await self.send(content, **kwargs)

    async def safe_send(self, content=None, **kwargs):
        try:
            return await self.send_or_reply(content, **kwargs)
        except Exception:
            return

    async def rep_or_ref(self, content=None, **kwargs):
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return await self.send(
                content, **kwargs, reference=ref.resolved.to_reference()
            )
        return await self.reply(content, **kwargs)

    async def react(self, reaction=None, content=None, **kwargs):
        try:
            return await self.message.add_reaction(reaction)
        except Exception:
            pass

    async def bold(self, content=None, **kwargs):
        return await self.send_or_reply(
            "**" + (content if content else "") + "**", **kwargs
        )

    async def usage(self, usage=None, command=None, **kwargs):
        if command:
            name = command.qualified_name
        else:
            name = self.command.qualified_name
        content = (
            f"Usage: `{self.prefix}{name} "
            + (usage if usage else self.command.signature)
            + "`"
        )
        return await self.send_or_reply(content, **kwargs)

    async def load(self, content=None, **kwargs):
        content = f"{self.bot.emote_dict['loading']} **{content}**"
        return await self.send_or_reply(content, **kwargs)

    async def confirm(self, content="", *, suffix: bool = True, **kwargs):
        content = f"**{content} Do you wish to continue?**" if suffix else content
        return await views.Confirmation(self, content, **kwargs).prompt()

    async def dm(self, content=None, **kwargs):
        try:
            await self.author.send(content, **kwargs)
        except Exception:
            await self.send_or_reply(content, **kwargs)

    async def trigger_typing(self):
        try:
            await super().trigger_typing()
        except Exception:
            return


class BotCommand(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.cooldown_after_parsing = kwargs.pop("cooldown_after_parsing", True)
        self.examples = kwargs.pop("examples", None)
        self.implemented = kwargs.pop("implemented", None)
        self.updated = kwargs.pop("updated", None)
        self.writer = kwargs.pop("writer", 708584008065351681)
        # Maybe someday more will contribute... :((


class BotGroup(commands.Group):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.case_insensitive = kwargs.pop("case_insensitive", True)
        self.cooldown_after_parsing = kwargs.pop("cooldown_after_parsing", True)
        self.invoke_without_command = kwargs.pop("invoke_without_command", False)
        self.examples = kwargs.pop("examples", None)
        self.implemented = kwargs.pop("implemented", None)
        self.updated = kwargs.pop("updated", None)
        self.writer = kwargs.pop("writer", 708584008065351681)


class CustomCooldown:
    def __init__(
        self,
        rate: int = 3,
        per: float = 10.0,
        *,
        alter_rate: int = 0,
        alter_per: float = 0.0,
        bucket: commands.BucketType = commands.BucketType.user,
        bypass: list = [],
    ):
        self.cooldown = (rate, per)

        self.type = bucket
        self.bypass = bypass
        self.default_mapping = commands.CooldownMapping.from_cooldown(rate, per, bucket)
        self.altered_mapping = commands.CooldownMapping.from_cooldown(
            alter_rate, alter_per, bucket
        )
        self.owner_mapping = commands.CooldownMapping.from_cooldown(0, 0, bucket)
        self.owner = 708584008065351681

    def __call__(self, ctx):
        key = self.altered_mapping._bucket_key(ctx.message)
        if key == self.owner:
            bucket = self.owner_mapping.get_bucket(ctx.message)
        elif key in self.bypass:
            bucket = self.altered_mapping.get_bucket(ctx.message)
        else:
            bucket = self.default_mapping.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, self.type)
        return True
