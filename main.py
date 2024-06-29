import os
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
import discord
from discord.ext import commands, tasks
import datetime
from discord.ui import Modal, TextInput, View, Button
from discord_interactions import verify_key_decorator

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)


@app.route("/", methods=["POST"])
async def interactions():
    print(f"👉 Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)
class CritiqueModal(Modal):
    def __init__(self, criteres):
        super().__init__(title="My review")
        self.criteres = criteres

        for critere in criteres:
            self.add_item(TextInput(label=critere, required=True))

    async def on_submit(self, interaction: discord.Interaction):
        critique_finale = f"Here are my thoughts by **{interaction.user.name}**:\n\n"
        for i, item in enumerate(self.children):
            critere = self.criteres[i]
            critique_finale += f"**{critere}**: ||{item.value}||\n\n"

        await interaction.response.send_message(critique_finale)

class CritiqueButtonView(View):
    def __init__(self, criteres):
        super().__init__()
        self.criteres = criteres

    @discord.ui.button(label="Write my review!", style=discord.ButtonStyle.primary)
    async def start_critique(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CritiqueModal(self.criteres)
        await interaction.response.send_modal(modal)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.command()
async def review(ctx):
    await ctx.send("Please enter the review criteria, separated by commas:")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
        criteres = [critere.strip() for critere in msg.content.split(',')]

        if not criteres:
            await ctx.send("Aucun critère fourni. Veuillez réessayer.")
            return

        view = CritiqueButtonView(criteres)
        await ctx.send("Tell us your experience:", view=view)

    except Exception as e:
        await ctx.send(f"Erreur: {e}")

# Définir les options d'avancement
avancement_options = {
    "😎": "J'ai commencé et vais finir",
    "🫨": "J'ai pas commencé et vais finir",
    "🥱": "J'ai commencé et ne vais pas finir",
    "🤧": "Je ne vais pas jouer ce mois-ci"
}


class AvancementView(discord.ui.View):
    def __init__(self, options, original_message):
        super().__init__(timeout=None)
        self.options = options
        self.original_message = original_message
        for emote, description in options.items():
            button = discord.ui.Button(label=description, emoji=emote, custom_id=emote, disabled=True)
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        # Ajouter une réaction au message original avec l'emoji correspondant
        emoji = interaction.data['custom_id']
        await self.original_message.add_reaction(emoji)
        await interaction.response.defer()


@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    send_avancement_message.start()


@tasks.loop(time=datetime.time(6, 59))  # Exécuter tous les jours à 20:01
async def send_avancement_message():
    print("Vérification des conditions pour l'envoi du message d'avancement...")

    # Obtenir le serveur et le canal où envoyer le message
    guild = bot.get_guild(1255932501784920076)
    channel = guild.get_channel(1255932502464270387)

    if guild and channel:
        print("Serveur et canal trouvés.")

        # Vérifier si la date est au milieu du mois (adjust the range as needed)
        today = datetime.date.today()
        if 29 <= today.day <= 29:
            print("La date est le 28 du mois, envoi du message.")

            # Construire le message avec les options d'avancement
            message = "**YOUR PROGRESS SO FAR** \n"
            original_message = await channel.send(message)
            view = AvancementView(avancement_options, original_message)
            await original_message.edit(view=view)
            print("Message envoyé avec boutons.")

            # Ajouter automatiquement les réactions
            for emote in avancement_options.keys():
                await original_message.add_reaction(emote)
        else:
            print("Ce n'est pas le jour d'envoi (le 28).")
    else:
        print("Le serveur ou le canal spécifié est introuvable.")

# Lancement du bot
token = "MTI1MDM5ODA2Njc1ODkxMDAwMw.G2GbXg.P1YsiXscB0Rj2SpGx8qUV2KSSW3cPaXG77ghNE"
bot.run(token)