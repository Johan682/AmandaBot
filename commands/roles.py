import discord
from discord import app_commands
from discord.ext import commands
import json
from utils.logger import check_role_autorise
class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='roles', description='Obtenez la liste des rôles du serveur')
    @check_role_autorise('roles')
    async def roles(self, interaction: discord.Interaction):
        # Récupère les rôles du serveur
        roles = interaction.guild.roles

        # Créer un message de liste des rôles
        role_list = "\n".join([f"{role.name} (ID: {role.id})" for role in roles])

        # Récupère les commandes du bot
        bot_commands = [command.name for command in self.bot.tree.get_commands()]

        # Sauvegarde les rôles et leurs IDs dans un fichier JSON, ainsi que les commandes du bot
        data_dict = {
            "roles": [{"name": role.name, "id": role.id} for role in roles],
            "commands": bot_commands  # Liste des commandes du bot
        }
        with open("json/roles.json", "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)

        # Envoie la liste des rôles et des commandes dans la réponse
        await interaction.response.send_message(f"Voici les rôles du serveur :\n{role_list}\n\nEt voici les commandes du bot :\n" + "\n".join(bot_commands))

async def setup(bot):
    await bot.add_cog(Roles(bot))
