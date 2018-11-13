import re
from typing import Callable, ClassVar, List, Optional, Pattern, Sequence, Tuple, Union, cast

import discord

from redbot.core import commands

class CustomPredicate(Callable[[discord.Reaction, discord.abc.User], bool]):
    """A collection of predicates for reaction events.

    All checks are combined with :meth:`CustomPredicate.same_context`.

    Examples
    --------
    Confirming a yes/no question with a tick/cross reaction::

        from redbot.core.utils.predicates import CustomPredicate
        from redbot.core.utils.menus import start_adding_reactions

        msg = await ctx.send("Yes or no?")
        start_adding_reactions(msg, CustomPredicate.YES_OR_NO_EMOJIS)

        pred = CustomPredicate.yes_or_no(msg, ctx.author)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result is True:
            # User responded with tick
            ...
        else:
            # User responded with cross
            ...

    Waiting for the first reaction from any user with one of the first
    5 letters of the alphabet::

        from redbot.core.utils.predicates import CustomPredicate
        from redbot.core.utils.menus import start_adding_reactions

        msg = await ctx.send("React to me!")
        emojis = CustomPredicate.ALPHABET_EMOJIS[:5]
        start_adding_reactions(msg, emojis)

        pred = CustomPredicate.with_emojis(emojis, msg)
        await ctx.bot.wait_for("reaction_add", check=pred)
        # pred.result is now the index of the letter in `emojis`

    Attributes
    ----------
    result : Any
        The object which the message content matched with. This is
        dependent on the predicate used - see each predicate's
        documentation for details, not every method will assign this
        attribute. Defaults to ``None``.

    """

    YES_OR_NO_EMOJIS: ClassVar[Tuple[str, str]] = (
        "\N{WHITE HEAVY CHECK MARK}",
        "\N{NEGATIVE SQUARED CROSS MARK}",
    )
    """Tuple[str, str] : A tuple containing the tick emoji and cross emoji, in that order."""

    ALPHABET_EMOJIS: ClassVar[List[str]] = [
        chr(code)
        for code in range(
            ord("\N{REGIONAL INDICATOR SYMBOL LETTER A}"),
            ord("\N{REGIONAL INDICATOR SYMBOL LETTER Z}") + 1,
        )
    ]
    """List[str] : A list of all 26 alphabetical letter emojis."""

    NUMBER_EMOJIS: ClassVar[List[str]] = [
        chr(code) + "\N{COMBINING ENCLOSING KEYCAP}" for code in range(ord("0"), ord("9") + 1)
    ]
    """List[str] : A list of all single-digit number emojis, 0 through 9."""

    def __init__(
        self, predicate: Callable[["CustomPredicate", discord.Reaction, discord.abc.User], bool]
    ) -> None:
        self._pred: Callable[
            ["CustomPredicate", discord.Reaction, discord.abc.User], bool
        ] = predicate
        self.result = None

    def __call__(self, reaction: discord.Reaction, user: discord.abc.User) -> bool:
        return self._pred(self, reaction, user)

    # noinspection PyUnusedLocal
    @classmethod
    def same_context(
        cls, message: Optional[discord.Message] = None, user: Optional[discord.abc.User] = None
    ) -> "CustomPredicate":
        """Match if a reaction fits the described context.

        This will ignore reactions added by the bot user, regardless
        of whether or not ``user`` is supplied.

        Parameters
        ----------
        message : Optional[discord.Message]
            The message which we expect a reaction to. If unspecified,
            the reaction's message will be ignored.
        user : Optional[discord.abc.User]
            The user we expect to react. If unspecified, the user who
            added the reaction will be ignored.

        Returns
        -------
        CustomPredicate
            The event predicate.

        """
        # noinspection PyProtectedMember
        me_id = message._state.self_id
        return cls(
            lambda self, r, u: u.id != me_id
            and (message is None or r.message.id == message.id)
            and (user is None or u.id == user.id)
        )


    @classmethod
    def with_emojis(
        cls,
        emojis: Sequence[Union[str, discord.Emoji, discord.PartialEmoji]],
        message: Optional[discord.Message] = None,
        user: Optional[discord.abc.User] = None,
    ) -> "CustomPredicate":
        """Match if the reaction is one of the specified emojis.

        Parameters
        ----------
        emojis : Sequence[Union[str, discord.Emoji, discord.PartialEmoji]]
            The emojis of which one we expect to be reacted.
        message : discord.Message
            Same as ``message`` in :meth:`same_context`.
        user : Optional[discord.abc.User]
            Same as ``user`` in :meth:`same_context`.

        Returns
        -------
        CustomPredicate
            The event predicate.

        """

        def predicate(self: CustomPredicate, r: discord.Reaction, u: discord.abc.User):
            if u.bot:
                return False
            try:
                self.result = emojis.index(r.emoji)
            except ValueError:
                return False
            else:
                return True

        return cls(predicate)

    @classmethod
    def yes_or_no(
        cls, message: Optional[discord.Message] = None, user: Optional[discord.abc.User] = None
    ) -> "CustomPredicate":
        """Match if the reaction is a tick or cross emoji.

        The emojis used can are in
        `CustomPredicate.YES_OR_NO_EMOJIS`.

        This will assign ``True`` for *yes*, or ``False`` for *no* to
        the `result` attribute.

        Parameters
        ----------
        message : discord.Message
            Same as ``message`` in :meth:`same_context`.
        user : Optional[discord.abc.User]
            Same as ``user`` in :meth:`same_context`.

        Returns
        -------
        CustomPredicate
            The event predicate.

        """
        def predicate(self: CustomPredicate, r: discord.Reaction, u: discord.abc.User) -> bool:
            if u.bot:
                return False
            try:
                self.result = not bool(self.YES_OR_NO_EMOJIS.index(r.emoji))
            except ValueError:
                return False
            else:
                return True

        return cls(predicate)
