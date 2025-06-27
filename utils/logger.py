import discord
from datetime import datetime
import pytz
import json

# Fonction de log pour les commandes slash
async def log_slash_command(bot, interaction: discord.Interaction, commande: str, couleur: discord.Color = discord.Color.blue()):
    # Log dans le channel de Discord
    logs_channel = bot.get_channel(1369379460696248361)  # ID du channel de logs
    user = interaction.user
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    timestamp = discord.utils.utcnow().astimezone(pytz.timezone("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")

    # Log dans le fichier `.log`
    log_line = f"[{timestamp}] {user} ({user.id}) a exécuté /{commande} → {'✅ success' if couleur == discord.Color.green() else '❌ failed'}\n"
    with open("json/logs.log", "a", encoding="utf-8") as f:
        f.write(log_line)

def load_permissions():
    with open("json/permissions.json", "r", encoding="utf-8") as f:
        permissions = json.load(f)
    return permissions


def check_role_autorise(command: str):
    async def predicate(interaction: discord.Interaction) -> bool:
        permissions = load_permissions()  # Charger les permissions à chaque appel

        if command in permissions:
            authorized_roles = permissions[command]["roles"]  # Liste de str

        
            # Comparer des chaînes : str(role.id)
            return any(str(role.id) in authorized_roles for role in interaction.user.roles)

        print(f"[DEBUG] La commande '{command}' n'a pas été trouvée dans les permissions.")
        return False

    return discord.app_commands.check(predicate)



# Vérification du channel autorisé pour les commandes
def check_channel_autorise(CHANNEL_AUTORISE_ID):
    async def predicate(interaction: discord.Interaction) -> bool:
        # ID du canal autorisé
        return interaction.channel.id == CHANNEL_AUTORISE_ID
    return discord.app_commands.check(predicate)
