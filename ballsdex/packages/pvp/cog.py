import discord
from discord import app_commands
from discord.ext import commands
from ballsdex.core.utils.transformers import BallInstanceTransform
from typing import Optional
import random

MAXSTATS = [30000, 30000]

class PvP(commands.GroupCog, name="pvp"):
    def __init__(self, bot):
        self.bot = bot
        self.pvp_matches = {}

    def get_user_match(self, user_id):
        for (a, b), match in self.pvp_matches.items():
            if user_id in (a, b):
                return match
        return None

    def adjusted_hp(self, ball):
        hp = ball.health
        description = ball.description(short=True)
        if "✨" in description: hp += 2500
        elif "👑" in description: hp += 6500
        elif "🌟" in description: hp += 5000
        elif "🏆" in description: hp += 3000
        elif "💎" in description: hp += 6000
        elif "🏳️‍⚧️" in description: hp += 1500
        return min(hp, MAXSTATS[1])

    def adjusted_attack(self, ball):
        atk = ball.attack
        description = ball.description(short=True)
        if "✨" in description: atk += 2500
        elif "👑" in description: atk += 6500
        elif "🌟" in description: atk += 5000
        elif "🏆" in description: atk += 3000
        elif "💎" in description: atk += 6000
        elif "🏳️‍⚧️" in description: atk += 1500
        return min(atk, MAXSTATS[0])

    def calculate_team_attack(self, team):
        return sum(self.adjusted_attack(b) for b in team) + random.randint(500, 1500)

    @app_commands.command()
    async def challenge(self, interaction: discord.Interaction, opponent: discord.User):
        if opponent.bot or opponent.id == interaction.user.id:
            return await interaction.response.send_message("Invalid challenge target.", ephemeral=True)

        self.pvp_matches[(interaction.user.id, opponent.id)] = {
            "challenger": interaction.user.id,
            "opponent": opponent.id,
            "challenger_team": [],
            "opponent_team": [],
            "accepted": False,
            "state": "pending"
        }
        await interaction.response.send_message(f"You have challenged {opponent.mention} to a PvP match!")

    @app_commands.command()
    async def add(self, interaction: discord.Interaction, ball: BallInstanceTransform):
        match = self.get_user_match(interaction.user.id)
        if not match:
            return await interaction.response.send_message("You're not in an active challenge.", ephemeral=True)

        team = match["challenger_team"] if interaction.user.id == match["challenger"] else match["opponent_team"]

        if len(team) >= 3:
            return await interaction.response.send_message("You've already added 3 countryballs.", ephemeral=True)

        if ball in team:
            return await interaction.response.send_message("This ball is already added.", ephemeral=True)

        team.append(ball)
        await interaction.response.send_message(f"{ball} has been added to your team.")

    @app_commands.command()
    async def accept(self, interaction: discord.Interaction):
        match = self.get_user_match(interaction.user.id)
        if not match or match["opponent"] != interaction.user.id:
            return await interaction.response.send_message("You are not being challenged.", ephemeral=True)

        if len(match["challenger_team"]) < 3 or len(match["opponent_team"]) < 3:
            return await interaction.response.send_message("Both players need 3 countryballs selected.", ephemeral=True)

        match["accepted"] = True
        match["state"] = "active"
        match["turn"] = match["challenger"]
        match["hp"] = {
            match["challenger"]: sum(self.adjusted_hp(b) for b in match["challenger_team"]),
            match["opponent"]: sum(self.adjusted_hp(b) for b in match["opponent_team"]),
        }

        await interaction.response.send_message("PvP match accepted! Let the battle begin.")

    @app_commands.command()
    async def attack(self, interaction: discord.Interaction):
        match = self.get_user_match(interaction.user.id)
        if not match or match["state"] != "active":
            return await interaction.response.send_message("No active battle found.", ephemeral=True)

        if interaction.user.id != match["turn"]:
            return await interaction.response.send_message("It's not your turn.", ephemeral=True)

        attacker = interaction.user.id
        defender = match["opponent"] if attacker == match["challenger"] else match["challenger"]

        damage = self.calculate_team_attack(match[f"{'challenger' if attacker == match['challenger'] else 'opponent'}_team"])
        match["hp"][defender] -= damage

        await interaction.channel.send(
            f"<@{attacker}> attacks <@{defender}> for **{damage}** damage! <@{defender}> now has **{max(0, match['hp'][defender])}** HP left."
        )

        if match["hp"][defender] <= 0:
            await interaction.channel.send(f"<@{attacker}> has won the PvP match!")
            del self.pvp_matches[(match['challenger'], match['opponent'])]
            return

        match["turn"] = defender

    @app_commands.command()
    async def status(self, interaction: discord.Interaction):
        match = self.get_user_match(interaction.user.id)
        if not match:
            return await interaction.response.send_message("No ongoing match.", ephemeral=True)

        desc = f"**State:** {match['state'].capitalize()}\n"
        if match['state'] == "active":
            desc += f"**Challenger HP:** {match['hp'][match['challenger']]}\n"
            desc += f"**Opponent HP:** {match['hp'][match['opponent']]}\n"
            desc += f"**Current Turn:** <@{match['turn']}>"

        await interaction.response.send_message(desc)

    @app_commands.command()
    async def forfeit(self, interaction: discord.Interaction):
        match = self.get_user_match(interaction.user.id)
        if not match:
            return await interaction.response.send_message("You are not in an active match.", ephemeral=True)

        opponent = match["opponent"] if interaction.user.id == match["challenger"] else match["challenger"]
        await interaction.channel.send(f"<@{interaction.user.id}> has forfeited the match. <@{opponent}> wins!")
        del self.pvp_matches[(match['challenger'], match['opponent'])]


async def setup(bot):
    await bot.add_cog(PvP(bot))
