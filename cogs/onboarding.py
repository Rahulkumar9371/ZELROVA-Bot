import discord
from discord.ext import commands


LANGUAGE_ROLES = {
    "Hindi": "Hindi",
    "English": "English",
    "Japanese": "Japanese"
}

INTEREST_ROLES = {
    "Anime": "Anime",
    "Gaming": "Gaming",
    "Coding": "Coding",
    "Music": "Music",
    "Manga": "Manga",
    "Story": "Story Writer"
}


class LanguageSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Hindi", emoji="🇮🇳", description="Hindi community role"),
            discord.SelectOption(label="English", emoji="🇬🇧", description="English learning role"),
            discord.SelectOption(label="Japanese", emoji="🇯🇵", description="Japanese learning role")
        ]

        super().__init__(
            placeholder="Choose your language",
            min_values=1,
            max_values=3,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        added = []

        for value in self.values:
            role_name = LANGUAGE_ROLES.get(value)
            role = discord.utils.get(interaction.guild.roles, name=role_name)

            if role:
                await interaction.user.add_roles(role)
                added.append(role.name)

        text = ", ".join(added) if added else "No matching roles found."

        await interaction.response.send_message(
            f"✅ Language roles updated: {text}",
            ephemeral=True
        )


class InterestSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Anime", emoji="🌸", description="Anime community"),
            discord.SelectOption(label="Gaming", emoji="🎮", description="Gaming community"),
            discord.SelectOption(label="Coding", emoji="💻", description="Coding and development"),
            discord.SelectOption(label="Music", emoji="🎵", description="Music community"),
            discord.SelectOption(label="Manga", emoji="📚", description="Manga community"),
            discord.SelectOption(label="Story", emoji="✍️", description="Story writing community")
        ]

        super().__init__(
            placeholder="Choose your interests",
            min_values=1,
            max_values=6,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        added = []

        for value in self.values:
            role_name = INTEREST_ROLES.get(value)
            role = discord.utils.get(interaction.guild.roles, name=role_name)

            if role:
                await interaction.user.add_roles(role)
                added.append(role.name)

        text = ", ".join(added) if added else "No matching roles found."

        await interaction.response.send_message(
            f"✅ Interest roles updated: {text}",
            ephemeral=True
        )


class RulesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Accept Rules",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="Verified")

        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            "✅ Rules accepted. Welcome to the community!",
            ephemeral=True
        )


class OnboardingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(LanguageSelect())
        self.add_item(InterestSelect())
        self.add_item(RulesButton())


class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def onboarding(self, ctx):
        embed = discord.Embed(
            title="👋 Welcome to ZELROVA Onboarding",
            description=(
                "Complete your server setup below.\n\n"
                "1. Choose your language.\n"
                "2. Choose your interests.\n"
                "3. Accept the rules.\n\n"
                "This system works like a custom Discord-style onboarding flow."
            ),
            color=discord.Color.red()
        )

        embed.add_field(
            name="Languages",
            value="🇮🇳 Hindi\n🇬🇧 English\n🇯🇵 Japanese",
            inline=True
        )

        embed.add_field(
            name="Interests",
            value="🌸 Anime\n🎮 Gaming\n💻 Coding\n🎵 Music\n📚 Manga\n✍️ Story",
            inline=True
        )

        embed.set_footer(text="Powered by ZELROVA Bot")

        await ctx.send(embed=embed, view=OnboardingView())

    @commands.command()
    async def onboardinginfo(self, ctx):
        embed = discord.Embed(
            title="🧭 ZELROVA Onboarding",
            description="Use `!onboarding` to create the custom onboarding panel.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Onboarding(bot))