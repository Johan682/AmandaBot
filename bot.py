import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# Imports des commandes simples (slash)
from commands.nico import nico
from commands.regles import regles
from commands.clear import clear
from commands.pfc import pfc

# Gestion des rôles, événements, logs
from commands.roles import Roles  # Ce Cog est chargé dynamiquement, mais peut être importé si nécessaire
from events.join import handle_member_join
from utils.logger import log_slash_command

# Autres extensions (chargées dynamiquement)

# Chargement des variables d'environnement
load_dotenv()

# Création du bot
print("Lancement du bot...")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# Événement : Bot prêt
@bot.event
async def on_ready():
    print("Bot allumé !")
    try:
        await bot.change_presence(activity=discord.Game(name="Pecho Amanda"))

        # Ajout des commandes slash simples
        bot.tree.add_command(nico)
        bot.tree.add_command(regles)
        bot.tree.add_command(clear)
        bot.tree.add_command(pfc)

        # Chargement dynamique des extensions avec setup()
    
        await bot.load_extension("commands.quizz")
        await bot.load_extension("commands.roles")
        await bot.load_extension("commands.pendu")
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors du démarrage : {e}")


# Gestion des erreurs des commandes slash
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    try:
        if isinstance(error, app_commands.CheckFailure):
            msg = "⛔ Vous n'avez pas les permissions nécessaires pour utiliser cette commande ou le channel n'est pas le bon. Veuillez contacter un administrateur si vous pensez que cela est une erreur."
            await log_slash_command(interaction.client, interaction, "no permission", discord.Color.red())
        else:
            msg = "❌ La commande n’a pas fonctionné. Une erreur est survenue."
            print(f"Erreur lors de la commande : {error}")

        # Envoyer la réponse s'il n'y en a pas déjà une
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)

    except discord.InteractionResponded:
        pass  # Évite les doubles réponses


# Événement : Nouveau membre rejoint
@bot.event
async def on_member_join(member: discord.Member):
    await handle_member_join(bot, member)


# Lancement du bot avec le token
bot.run(os.getenv('DISCORD_TOKEN'))
