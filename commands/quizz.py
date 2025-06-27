import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import html
from utils.logger import log_slash_command, check_channel_autorise, check_role_autorise
import matplotlib.pyplot as plt
from io import BytesIO

# Charger les questions une seule fois
with open("json/db.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

SCORE_FILE = "json/scores.json"

def load_scores():
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_scores(scores):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=4, ensure_ascii=False)

class QuizView(discord.ui.View):
    def __init__(self, correct_answer, all_answers):
        super().__init__(timeout=30)
        self.correct_answer = correct_answer
        self.answered = False
        self.message = None  # Pour stocker le message envoyé
        random.shuffle(all_answers)

        for answer in all_answers:
            self.add_item(AnswerButton(answer, correct_answer))

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        if self.answered or not self.message:
            return  # Ne rien faire si déjà répondu ou message pas défini

        self.disable_all_items()
        try:
            await self.message.edit(view=self)  # Désactive les boutons
            await self.message.channel.send(f"⏰ Temps écoulé pour la question posée par <@{self.message.interaction.user.id}>.")
        except Exception as e:
            print("Erreur lors du timeout :", e)

class AnswerButton(discord.ui.Button):
    def __init__(self, label, correct_answer):
        super().__init__(label=html.unescape(label), style=discord.ButtonStyle.primary)
        self.correct_answer = html.unescape(correct_answer)

    async def callback(self, interaction: discord.Interaction):
        if self.view.answered:
            await interaction.response.send_message("❗ Cette question a déjà été répondue.", ephemeral=True)
            return

        self.view.answered = True
        self.view.disable_all_items()

        scores = load_scores()
        user_id = str(interaction.user.id)

        if user_id not in scores:
            scores[user_id] = {"correct": 0, "total": 0}

        scores[user_id]["total"] += 1

        if self.label == self.correct_answer:
            scores[user_id]["correct"] += 1
            result_text = f"✅ {interaction.user.mention} a donné la **bonne réponse** ! (+1 point) {self.correct_answer}"
        else:
            result_text = f"❌ {interaction.user.mention} s'est trompé ! La bonne réponse était : **{self.correct_answer}**"

        save_scores(scores)
        await interaction.response.send_message(result_text, ephemeral=False)
        await interaction.message.edit(view=self.view)

class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="quiz", description="Pose une question de quiz aléatoire.")
    @check_role_autorise("quiz")
    @check_channel_autorise(1369684169466052700)
    async def quiz(self, interaction: discord.Interaction):
        try:
            q = random.choice(QUESTIONS)

            question = html.unescape(q["question"])
            correct = html.unescape(q["correct_answer"])
            incorrects = [html.unescape(ans) for ans in q["incorrect_answers"]]
            all_answers = incorrects + [correct]

            embed = discord.Embed(
                title=f"🧠 Catégorie : {q['category']} • Difficulté : {q['difficulty'].capitalize()}",
                description=question,
                color=discord.Color.blurple()
            )

            view = QuizView(correct, all_answers)
            view.interaction_user_id = interaction.user.id
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
            await log_slash_command(interaction.client, interaction, "/quiz", discord.Color.green())  # Succès
        except Exception as e:
            await log_slash_command(interaction.client, interaction, "/quiz", discord.Color.red())  # Échec
            raise e

    @app_commands.command(name="mes_stats", description="Affiche tes statistiques personnelles de quiz.")
    @check_channel_autorise(1369684169466052700)
    async def mes_stats(self, interaction: discord.Interaction):
        try:
            scores = load_scores()
            user_id = str(interaction.user.id)
            user_score = scores.get(user_id)

            if not user_score:
                await interaction.response.send_message("📉 Tu n'as encore jamais participé au quiz.")
                await log_slash_command(interaction.client, interaction, "/mes_stats", discord.Color.green())  # Succès
                return

            correct = user_score["correct"]
            total = user_score["total"]
            ratio = round((correct / total) * 100, 2) if total else 0

            classement = sorted(scores.items(), key=lambda x: x[1]["correct"], reverse=True)
            position = next((i + 1 for i, (uid, _) in enumerate(classement) if uid == user_id), "Non classé")

            embed = discord.Embed(
                title=f"📈 Statistiques de {interaction.user.name}",
                color=discord.Color.green()
            )
            embed.add_field(name="Bonnes réponses", value=f"{correct}", inline=True)
            embed.add_field(name="Participations", value=f"{total}", inline=True)
            embed.add_field(name="Taux de réussite", value=f"{ratio}%", inline=True)
            embed.add_field(name="Classement", value=f"{position}", inline=True)
            file = generate_stats_image(correct, total, interaction.user.name)
            await interaction.response.send_message(embed=embed, file=file)

            await log_slash_command(interaction.client, interaction, "/mes_stats", discord.Color.green())  # Succès
        except Exception as e:
            await log_slash_command(interaction.client, interaction, "/mes_stats", discord.Color.red())  # Échec
            raise e

    @app_commands.command(name="stats_de", description="Affiche les statistiques de quiz d’un utilisateur.")
    @check_channel_autorise(1369684169466052700)
    async def stats_de(self, interaction: discord.Interaction, user: discord.User):
        try:
            scores = load_scores()
            user_id = str(user.id)
            user_score = scores.get(user_id)

            if not user_score:
                await interaction.response.send_message(f"ℹ️ {user.name} n’a encore jamais participé au quiz.")
                await log_slash_command(interaction.client, interaction, "/stats_de", discord.Color.green())  # Succès
                return

            correct = user_score["correct"]
            total = user_score["total"]
            ratio = round((correct / total) * 100, 2) if total else 0

            classement = sorted(scores.items(), key=lambda x: x[1]["correct"], reverse=True)
            position = next((i + 1 for i, (uid, _) in enumerate(classement) if uid == user_id), "Non classé")

            embed = discord.Embed(
                title=f"📊 Statistiques de {user.name}",
                color=discord.Color.teal()
            )
            embed.add_field(name="Bonnes réponses", value=f"{correct}", inline=True)
            embed.add_field(name="Participations", value=f"{total}", inline=True)
            embed.add_field(name="Taux de réussite", value=f"{ratio}%", inline=True)
            embed.add_field(name="Classement", value=f"{position}", inline=True)
            file = generate_stats_image(correct, total, user.name)
            await interaction.response.send_message(embed=embed, file=file)

            await log_slash_command(interaction.client, interaction, "/stats_de", discord.Color.green())  # Succès
        except Exception as e:
            await log_slash_command(interaction.client, interaction, "/stats_de", discord.Color.red())  # Échec
            raise e

    @app_commands.command(name="top_stats", description="Classement détaillé des meilleurs joueurs.")
    @check_channel_autorise(1369684169466052700)
    async def top_stats(self, interaction: discord.Interaction):
        try:
            scores = load_scores()
            sorted_scores = sorted(scores.items(), key=lambda x: x[1]["correct"], reverse=True)

            if not sorted_scores:
                await interaction.response.send_message("📉 Aucun score enregistré.")
                await log_slash_command(interaction.client, interaction, "/top_stats", discord.Color.green())  # Succès
                return

            embed = discord.Embed(
                title="🏆 Top 10 Quiz",
                color=discord.Color.gold()
            )

            for i, (user_id, data) in enumerate(sorted_scores[:10], start=1):
                user = await self.bot.fetch_user(int(user_id))
                correct = data["correct"]
                total = data["total"]
                ratio = round((correct / total) * 100, 2) if total else 0
                embed.add_field(
                    name=f"{i}. {user.name}",
                    value=f"Score : {correct} / {total} → **{ratio}%**",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
            await log_slash_command(interaction.client, interaction, "/top_stats", discord.Color.green())  # Succès
        except Exception as e:
            await log_slash_command(interaction.client, interaction, "/top_stats", discord.Color.red())  # Échec
            raise e

    @app_commands.command(name="reset_score", description="Réinitialise ton score ou celui d’un autre (admin uniquement).")
    @app_commands.describe(user="(Optionnel) Utilisateur à réinitialiser. Par défaut : toi-même.")
    @check_channel_autorise(1369684169466052700)
    @check_role_autorise("reset_score")
    async def reset_score(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            scores = load_scores()
            user_id = str((user or interaction.user).id)

            if user and user != interaction.user and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Tu dois être administrateur pour réinitialiser le score d’un autre utilisateur.", ephemeral=True)
                await log_slash_command(interaction.client, interaction, "/reset_score", discord.Color.red())  # Échec
                return

            if user_id in scores:
                del scores[user_id]
                save_scores(scores)
                await interaction.response.send_message(f"🔁 Le score de {user.name if user else 'toi-même'} a été réinitialisé.")
                await log_slash_command(interaction.client, interaction, "/reset_score", discord.Color.green())  # Succès
            else:
                await interaction.response.send_message("ℹ️ Aucun score à réinitialiser.", ephemeral=True)
                await log_slash_command(interaction.client, interaction, "/reset_score", discord.Color.red())  # Échec
        except Exception as e:
            await log_slash_command(interaction.client, interaction, "/reset_score", discord.Color.red())  # Échec
            raise e

    @app_commands.command(name="reset_all_scores", description="Réinitialise tous les scores (admin uniquement).")
    @check_channel_autorise(1369684169466052700)
    @check_role_autorise("reset_all_scores")
    async def reset_all_scores(self, interaction: discord.Interaction):
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Tu dois être administrateur pour exécuter cette commande.", ephemeral=True)
                await log_slash_command(interaction.client, interaction, "/reset_all_scores", discord.Color.red())  # Échec
                return

            save_scores({})
            await interaction.response.send_message("🧹 Tous les scores ont été réinitialisés.")
            await log_slash_command(interaction.client, interaction, "/reset_all_scores", discord.Color.green())  # Succès
        except Exception as e:
            await log_slash_command(interaction.client, interaction, "/reset_all_scores", discord.Color.red())  # Échec
            raise e


async def setup(bot):
    await bot.add_cog(Quiz(bot))

def generate_stats_image(correct, total, username):
    incorrect = total - correct
    labels = ['Bonnes réponses', 'Mauvaises réponses']
    sizes = [correct, incorrect]
    colors = ['#76c893', '#ef476f']  # Vert doux / Rouge rosé

    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.4, edgecolor='white'),
        textprops=dict(color="#2196F3", fontsize=12)
    )

    # Ajouter un cercle blanc pour effet "donut"
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    ax.set_title(f"Stats de {username}", fontsize=14, fontweight='bold',  color='#2196F3')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    plt.close(fig)

    return discord.File(fp=buf, filename="stats.png")
