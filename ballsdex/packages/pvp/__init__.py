from typing import TYPE_CHECKING

from .cog import PvP  # Make sure the file is named pvp.py

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


async def setup(bot: "BallsDexBot"):
    await bot.add_cog(PvP(bot))
