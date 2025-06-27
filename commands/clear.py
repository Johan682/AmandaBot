import discord
from discord import app_commands
from utils.logger import log_slash_command, check_role_autorise

# Commande /clear
@app_commands.command(name="clear", description="Supprime un certain nombre de messages")
@check_role_autorise("clear")
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Veuillez spécifier un nombre entre 1 et 100.", ephemeral=True)
        await log_slash_command(interaction.client, interaction, "/clear", discord.Color.red())  # Log en rouge pour une mauvaise entrée
        return

    try:
        await interaction.response.defer(ephemeral=True)

        # Purge avec +1 pour inclure le message de la commande si besoin
        deleted = await interaction.channel.purge(limit=amount)

        # Message de confirmation après la purge
        await interaction.followup.send(f"{len(deleted)} message(s) ont été supprimés.", ephemeral=True)
        
        # Log en vert pour une exécution réussie
        await log_slash_command(interaction.client, interaction, "/clear", discord.Color.green())

    except discord.errors.NotFound as e:
        print(f"Erreur: {e}")
        try:
            await interaction.followup.send("Erreur lors de la purge des messages.", ephemeral=True)
        except discord.errors.NotFound:
            print("Le message de suivi n'a pas pu être envoyé. Interaction expirée ou invalide.")
        except Exception as e:
            print(f"Erreur inconnue lors de l'envoi du message de suivi: {e}")
        
        # Log en rouge pour une erreur d'exécution
        await log_slash_command(interaction.client, interaction, "/clear", discord.Color.red())

    except Exception as e:
        print(f"Erreur inconnue: {e}")
        try:
            await interaction.followup.send("Une erreur inconnue est survenue lors de la suppression des messages.", ephemeral=True)
        except discord.errors.NotFound:
            print("Le message de suivi n'a pas pu être envoyé. Interaction expirée ou invalide.")
        except Exception as ex:
            print(f"Erreur inconnue lors de l'envoi du message de suivi: {ex}")
        
        # Log en rouge pour une erreur générale
        await log_slash_command(interaction.client, interaction, "/clear", discord.Color.red())
