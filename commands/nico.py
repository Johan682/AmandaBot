import discord
from discord import app_commands
from utils.logger import log_slash_command, check_role_autorise
# Commande /nico
@app_commands.command(name="nico", description="Dit bonjour à Yotano")
@check_role_autorise("nico")
async def nico(interaction: discord.Interaction):
    try:
        # Réponse à la commande
        await interaction.response.send_message("test")

        # Log en vert pour un succès
        await log_slash_command(interaction.client, interaction, "/nico", discord.Color.green())

    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande /nico : {e}")

        # Log en rouge pour un échec
        await log_slash_command(interaction.client, interaction, "/nico", discord.Color.red())
