import discord
import pytz
from datetime import datetime
from utils.logger import log_slash_command, check_role_autorise

class FakeInteraction:
    def __init__(self, user):
        self.user = user

# Fonction qui sera appelée pour gérer l'ajout d'un membre
async def handle_member_join(bot, member: discord.Member):
    role_id = 1358219696712716469  # ID du rôle à attribuer
    logs_channel_id = 1369379460696248361  # ID du channel de logs
    welcome_channel_id = 1349486076812591148  # ID du channel de bienvenue
    regles_channel_id = 1369452916947026000  # ID du channel des règles

    role = member.guild.get_role(role_id)
    welcome_channel = bot.get_channel(welcome_channel_id)

    # Attribution du rôle
    if role:
        try:
            await member.add_roles(role)
            
        except discord.Forbidden:
            print("Permission refusée pour ajouter le rôle.")
        except discord.HTTPException as e:
            print(f"Erreur HTTP : {e}")
    else:
        print("Rôle introuvable.")

    # Utilisation du logger pour enregistrer l'arrivée du membre
    interaction_simulee = FakeInteraction(user=member)
    await log_slash_command(
        bot=bot,
        interaction=interaction_simulee,
        commande="Arrivée sur le serveur (join)",
        couleur=discord.Color.purple()
    )

    # Message de bienvenue
    if welcome_channel:
        await welcome_channel.send(
            f"Bienvenue sur le serveur, {member.mention} ! 🎉 "
            f"N'oublie pas de lire les règles dans <#{regles_channel_id}> pour bien commencer ton aventure ici !"
        )
