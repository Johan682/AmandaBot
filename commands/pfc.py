import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import log_slash_command, check_channel_autorise, check_role_autorise


# Définition des règles
WIN_MAP = {
    "pierre": "ciseaux",
    "feuille": "pierre",
    "ciseaux": "feuille"
}

@app_commands.command(name="pfc", description="Joue à pierre-feuille-ciseaux contre un autre utilisateur.")
@app_commands.describe(adversaire="La personne contre qui tu veux jouer")
@check_channel_autorise(1369686466405597216)
@check_role_autorise('pfc')
async def pfc(interaction: discord.Interaction, adversaire: discord.User):
    joueur1 = interaction.user
    joueur2 = adversaire

    if joueur1 == joueur2:
        await interaction.response.send_message("Tu ne peux pas jouer contre toi-même !", ephemeral=True)
        await log_slash_command(interaction.client, interaction, "/pfc", discord.Color.red())
        return

    await interaction.response.send_message(
        f"{joueur1.mention} a défié {joueur2.mention} à Pierre-Feuille-Ciseaux !", ephemeral=False
    )

    # Création des vues
    view1 = ChoixView(joueur1.id)
    view2 = ChoixView(joueur2.id)

    # Envoi des messages
    msg1 = await interaction.channel.send(f"{joueur1.mention}, fais ton choix :", view=view1)
    msg2 = await interaction.channel.send(f"{joueur2.mention}, fais ton choix :", view=view2)

    # Attente des choix
    await view1.wait()
    await view2.wait()

    choix1 = view1.choix
    choix2 = view2.choix

    # Si un joueur ne répond pas
    if not choix1 or not choix2:
        view1.disable_all()
        view2.disable_all()

        await msg1.edit(
            content=f"{joueur1.mention} n’a pas répondu à temps." if not choix1 else f"{joueur1.mention} a fait son choix.",
            view=view1
        )
        await msg2.edit(
            content=f"{joueur2.mention} n’a pas répondu à temps." if not choix2 else f"{joueur2.mention} a fait son choix.",
            view=view2
        )

        await interaction.followup.send("⏱️ L'un des joueurs n'a pas répondu à temps. Partie annulée.")
        await log_slash_command(interaction.client, interaction, "/pfc", discord.Color.red())
        return

    # Résultat
    if choix1 == choix2:
        resultat = f"Égalité ! Vous avez tous les deux choisi **{choix1}**."
    elif WIN_MAP[choix1] == choix2:
        resultat = f"{joueur1.mention} gagne avec **{choix1}** contre **{choix2}** !"
    else:
        resultat = f"{joueur2.mention} gagne avec **{choix2}** contre **{choix1}** !"

    await interaction.followup.send(resultat)
    await log_slash_command(interaction.client, interaction, "/pfc", discord.Color.green())



# Vue avec boutons pour faire un choix
class ChoixView(discord.ui.View):
    def __init__(self, joueur_id: int):
        super().__init__(timeout=30)
        self.joueur_id = joueur_id
        self.choix = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.joueur_id:
            await interaction.response.send_message("Ce n'est pas ton choix à faire !", ephemeral=True)
            return False
        return True

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    async def disable_buttons(self, interaction: discord.Interaction, emoji: str):
        self.disable_all()
        await interaction.response.edit_message(
            content=f"{interaction.user.mention} a fait son choix.",
            view=self
        )
        self.stop()

    @discord.ui.button(label="🪨", style=discord.ButtonStyle.primary)
    async def pierre(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choix = "pierre"
        await self.disable_buttons(interaction, "🪨")

    @discord.ui.button(label="📄", style=discord.ButtonStyle.primary)
    async def feuille(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choix = "feuille"
        await self.disable_buttons(interaction, "📄")

    @discord.ui.button(label="✂️", style=discord.ButtonStyle.primary)
    async def ciseaux(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choix = "ciseaux"
        await self.disable_buttons(interaction, "✂️")
