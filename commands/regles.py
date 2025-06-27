import discord
from discord import app_commands
from utils.logger import log_slash_command, check_role_autorise

# Commande /regles avec restriction de rôle
@app_commands.command(name="regles", description="Publie les règles stylées dans le salon dédié.")
@check_role_autorise('regles')
async def regles(interaction: discord.Interaction):
    try:
        regles_channel_id = 1369452916947026000
        regles_channel = interaction.client.get_channel(regles_channel_id)

        if regles_channel is None:
            await interaction.response.send_message("❌ Salon des règles introuvable.", ephemeral=True)
            await log_slash_command(interaction.client, interaction, "/regles", discord.Color.red())  # Échec
            return

        embed = discord.Embed(
            title="📜 Règlement du Serveur – Amanda's Arc 🌀",
            description="🎮 *Ici, on vit dans un univers parallèle où on a pécho Amanda dans Life is Strange.*\n\nBienvenue dans notre délire collectif, mais même dans les timelines alternatives, il faut des règles ! 👮‍♀️",
            color=discord.Color.gold()
        )

        embed.add_field(name="1️⃣ Respect à Arcadia Bay (et ailleurs)", value="Pas d’insultes ni de comportements toxiques. Amanda (et les autres) méritent la paix.", inline=False)
        embed.add_field(name="2️⃣ Pas de spam temporel", value="Max peut remonter le temps, mais pas pour te faire taire si tu spammes. Donc évite.", inline=False)
        embed.add_field(name="3️⃣ Contenu clean", value="Même si c’est un délire, on évite le NSFW ou contenu choquant. Amanda regarde, fais gaffe.", inline=False)
        embed.add_field(name="4️⃣ Salons = timelines", value="Chaque salon a son ambiance. On ne mélange pas les timelines.", inline=False)
        embed.add_field(name="5️⃣ Obéis au staff (les vrais 'Timekeepers')", value="Le staff gère la continuité de l'univers. Respecte leurs décisions.", inline=False)
        embed.add_field(name="6️⃣ Pseudos et avatars", value="Pas de noms chelous genre 'JeffersonFan69'. On garde ça propre et rigolo.", inline=False)

        embed.set_footer(text="Merci d’avoir lu ! En restant ici, tu acceptes ce règlement... et que Amanda est à NOUS. ❤️")

        await regles_channel.send(embed=embed)
        await interaction.response.send_message("✅ Les règles d’Amanda ont été publiées avec succès !", ephemeral=True)
        await log_slash_command(interaction.client, interaction, "/regles", discord.Color.green())  # Succès
    except Exception as e:
        await log_slash_command(interaction.client, interaction, "/regles", discord.Color.red())  # Échec
        raise e
