import discord
import random
from discord import Interaction, app_commands
from discord.ext import commands
import csv
import os
from utils.logger import log_slash_command, check_channel_autorise, check_role_autorise

def charger_mots():
    chemin = os.path.join(os.path.dirname(__file__), "../json/frequence.csv")
    mots = []
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            lecteur = csv.reader(f, delimiter=';')
            for ligne in lecteur:
                if len(ligne) >= 3:
                    mot = ligne[2].strip().lower()
                    if mot.isalpha():  # Ignore les mots non alphabétiques
                        mots.append(mot)
        if not mots:
            raise ValueError("Aucun mot valide trouvé dans le CSV.")
    except Exception as e:
        print(f"[ERREUR] Chargement du CSV échoué : {e}")
        mots = ["erreur"]
    return mots

MOTS_PENDU = charger_mots()
sessions = {}

PENDU_ASCII = [
    "```\n\n\n\n\n_____```",  # 0 erreurs
    "```\n |\n |\n |\n |\n_|___```",  # 1 erreur
    "```\n ______\n |\n |\n |\n |\n_|___```",  # 2 erreurs
    "```\n ______\n |    |\n |    O\n |\n |\n_|___```",  # 3 erreurs
    "```\n ______\n |    |\n |    O\n |    |\n |\n_|___```",  # 4 erreurs
    "```\n ______\n |    |\n |    O\n |   /|\\\n |\n_|___```",  # 5 erreurs
    "```\n ______\n |    |\n |    O\n |   /|\\\n |   / \\\n_|___```",  # 6 erreurs = mort
]

async def safe_send(interaction: Interaction, *args, **kwargs):
    try:
        await interaction.response.send_message(*args, **kwargs)
    except discord.errors.NotFound:
        try:
            await interaction.followup.send(*args, **kwargs)
        except Exception as e:
            print(f"[ERREUR] Impossible d’envoyer le message de fallback : {e}")

class Pendu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @app_commands.command(name="pendu", description="Joue au jeu du pendu !")
    @check_channel_autorise(1384483257432936499)
    @check_role_autorise('pendu')
    async def pendu(self, interaction: Interaction):
        await log_slash_command(interaction.client, interaction, "/pendu", discord.Color.green())

        if interaction.user.id in sessions:
            await safe_send(interaction, "❗ Tu as déjà une partie en cours !", ephemeral=True)
            return

        mot = random.choice(MOTS_PENDU)
        sessions[interaction.user.id] = {
            "mot": mot,
            "lettres_trouvees": set(),
            "lettres_tentees": set(),
            "erreurs": 0,
            "max_erreurs": 6
        }

        mot_affiche = self._affiche_mot(mot, set())
        await safe_send(
            interaction,
            f"🎮 **Jeu du pendu commencé par {interaction.user.mention} !**\n\n"
            f"{PENDU_ASCII[0]}\n"
            f"Mot : `{mot_affiche}`\n"
            "Essaye une lettre avec `/essayer lettre:<ta lettre>`",
            ephemeral=False
        )

    @app_commands.command(name="essayer", description="Essaye une lettre pour le jeu du pendu")
    @app_commands.describe(lettre="Une lettre à essayer (a-z)")
    async def essayer(self, interaction: Interaction, lettre: str):
        await log_slash_command(interaction.client, interaction, "/essayer", discord.Color.green())
        lettre = lettre.lower()

        if len(lettre) != 1 or not lettre.isalpha():
            await safe_send(interaction, "❌ Merci d’entrer **une seule lettre** de a à z.", ephemeral=True)
            return

        session = sessions.get(interaction.user.id)
        if not session:
            await safe_send(interaction, "❗ Tu n'as pas de partie en cours. Lance le jeu avec `/pendu`.", ephemeral=True)
            return

        mot = session["mot"]
        lettres_trouvees = session["lettres_trouvees"]
        lettres_tentees = session["lettres_tentees"]

        if lettre in lettres_tentees:
            await safe_send(interaction, "⚠️ Tu as déjà essayé cette lettre.", ephemeral=True)
            return

        lettres_tentees.add(lettre)

        if lettre in mot:
            lettres_trouvees.add(lettre)
        else:
            session["erreurs"] += 1

        dessin = PENDU_ASCII[min(session["erreurs"], session["max_erreurs"])]

        if session["erreurs"] >= session["max_erreurs"]:
            del sessions[interaction.user.id]
            await safe_send(
                interaction,
                f"{dessin}\n💀 **{interaction.user.mention} a perdu !** Le mot était : **{mot}**",
                ephemeral=False
            )
            return

        if all(l in lettres_trouvees for l in mot):
            del sessions[interaction.user.id]
            await safe_send(
                interaction,
                f"🎉 **{interaction.user.mention} a gagné !** Le mot était : **{mot}**",
                ephemeral=False
            )
            return

        mot_affiche = self._affiche_mot(mot, lettres_trouvees)
        lettres_correctes = ", ".join(sorted(lettres_trouvees)) or "Aucune"
        lettres_fausses = ", ".join(sorted(lettres_tentees - lettres_trouvees)) or "Aucune"

        await safe_send(
            interaction,
            f"{dessin}\n\n"
            f"🔤 **Lettre tentée** : `{lettre}` par {interaction.user.mention}\n"
            f"📌 Mot : `{mot_affiche}`\n"
            f"✅ Lettres correctes : `{lettres_correctes}`\n"
            f"❌ Lettres fausses : `{lettres_fausses}`\n"
            f"🧠 Erreurs : {session['erreurs']} / {session['max_erreurs']}",
            ephemeral=False
        )

    @app_commands.command(name="proposer", description="Propose le mot complet pour tenter de gagner le jeu")
    @app_commands.describe(mot="Le mot complet que tu veux proposer")
    async def proposer(self, interaction: Interaction, mot: str):
        await log_slash_command(interaction.client, interaction, "/proposer", discord.Color.green())
        mot = mot.lower().strip()
        session = sessions.get(interaction.user.id)

        if not session:
            await safe_send(interaction, "❗ Tu n'as pas de partie en cours. Lance le jeu avec `/pendu`.", ephemeral=True)
            return

        mot_correct = session["mot"]

        if mot == mot_correct:
            del sessions[interaction.user.id]
            await safe_send(
                interaction,
                f"🎉 **{interaction.user.mention} a trouvé le mot : `{mot_correct}` ! Victoire immédiate !**",
                ephemeral=False
            )
        else:
            session["erreurs"] += 1
            dessin = PENDU_ASCII[min(session["erreurs"], session["max_erreurs"])]

            if session["erreurs"] >= session["max_erreurs"]:
                del sessions[interaction.user.id]
                await safe_send(
                    interaction,
                    f"{dessin}\n💀 **{interaction.user.mention} a proposé un mauvais mot et a perdu !** Le mot était : **{mot_correct}**",
                    ephemeral=False
                )
            else:
                await safe_send(
                    interaction,
                    f"{dessin}\n❌ Mauvaise proposition `{mot}` par {interaction.user.mention} !\n"
                    f"🧠 Erreurs : {session['erreurs']} / {session['max_erreurs']}",
                    ephemeral=False
                )

    def _affiche_mot(self, mot, lettres_trouvees):
        return " ".join(l if l in lettres_trouvees else "_" for l in mot)

    @app_commands.command(name="stop", description="Arrête ta partie en cours du jeu du pendu")
    async def stop(self, interaction: Interaction):
        await log_slash_command(interaction.client, interaction, "/stop", discord.Color.red())

        session = sessions.get(interaction.user.id)
        if not session:
            await safe_send(interaction, "❗ Tu n’as pas de partie en cours à arrêter.", ephemeral=True)
            return

        del sessions[interaction.user.id]
        await safe_send(interaction, f"🛑 **{interaction.user.mention} a arrêté sa partie du pendu.**", ephemeral=False)

        
async def setup(bot):
    await bot.add_cog(Pendu(bot))
