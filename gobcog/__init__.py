from .gobcog import GobCog

async def setup(bot):
    await bot.add_cog(GobCog())
    GobCog.bot = bot
