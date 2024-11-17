import discord
from discord.ext import commands
from discord import app_commands
import random
import string
import requests
from bs4 import BeautifulSoup

# Set up bot with necessary intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

invalid_key = -1
contact_admin = 0
valid_key = 1
PatronRole = 1228050191018492015
ServerID = 1227951289325981696
RoleChannelID = 1228075680890228877
# Generate a random key
def generate_random_key(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view with no timeout

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="verify_button", row=0)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open the verification modal when "Verify" button is clicked
        await interaction.response.send_modal(VerificationModal())

class VerificationModal(discord.ui.Modal, title="Verification Form"):
    name = discord.ui.TextInput(label="Name", placeholder="Enter your character's name", required=True)
    world = discord.ui.TextInput(label="World", placeholder="Enter your character's world", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Generate a random key after verification is submitted
        random_key = generate_random_key()
        if is_valid_world(self.world.value):
            # Send an ephemeral message with the generated key and a "Confirm" button
            await interaction.response.send_message(
                content=f"Thank you, {self.name.value} from {self.world.value}!\nPlease add the following key to your lodestone character profile: `{random_key}`. \n(Make sure to hit submit twice) \nOnce completed hit confirm below.",
                ephemeral=True,
                view=ConfirmButtonView(interaction.user, self.name.value, self.world.value, random_key)
            )
        else:
            await interaction.response.send_message("Invalid World Name Provided", ephemeral=True)


class ConfirmButtonView(discord.ui.View):
    def __init__(self, interaction_user, name, world, key):
        super().__init__(timeout=None)  # Persistent view with no timeout
        self.interaction_user = interaction_user
        self.name = name
        self.world = world
        self.key = key

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, custom_id="confirm_button")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the button is clicked by the same user who initiated the verification
        if interaction.user != self.interaction_user:
            await interaction.response.send_message(
                content="You are not authorized to confirm this verification.",
                ephemeral=True
            )
            return

        patron_role = interaction.guild.get_role(PatronRole)
        channel = bot.get_channel(RoleChannelID)

        # Use self.name, self.world, and self.key to access instance variables
        if XIVAuthed(self.name, self.world, self.key) == valid_key:
            await interaction.user.add_roles(patron_role)
            await interaction.user.edit(nick=self.name)
            await interaction.response.send_message(
                content=f"Confirmation for {self.name}@{self.world} successful! \nYou have been assigned the Patron role and your name has been set to your Lodestone character name.\nYou may now access the rest of the server as you wish. \nPlease select your roles in {channel.mention}.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                content=f"Confirmation failed! Please make sure you have the correct key in the Lodestone profile for {self.name}@{self.world}.",
                ephemeral=True
            )


@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")

    # Register the VerificationView persistently
    bot.add_view(VerificationView())

@bot.tree.command(name="send_verification", description="Send a verification message with a button")
async def send_verification(interaction: discord.Interaction):
    if(interaction.user.guild_permissions.administrator):
        embed = discord.Embed(
            title="Verification Required",
            description="Select the button below to verify",
            color=discord.Color.blue()
        )
        # Send the message with the VerificationView
        await interaction.response.send_message(embed=embed, view=VerificationView())

def XIVAuthed(name, world, key):
    search_url = f"https://na.finalfantasyxiv.com/lodestone/character/?q={name}&worldname={world}"
    # Get the search results and parse the HTML with BeautifulSoup
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the first character's profile link
    character_link = soup.find("a", class_="entry__link")
    if character_link:
        # Construct the full URL for the character's profile
        character_url = "https://na.finalfantasyxiv.com" + character_link['href']

        # Fetch the character's profile page and parse it with BeautifulSoup
        response = requests.get(character_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the profile section on the character's page
        profile_section = soup.find("div", class_="character__selfintroduction")

        if profile_section:
            # Print out each line in the profile section
            lines = profile_section.get_text(separator="\n", strip=True).split("\n")
            for line in lines:
                if(line == str(key)):
                    return valid_key
                else:
                    return invalid_key

        else:
            return contact_admin
    else:
        return contact_admin

def is_valid_world(world_name):
    # List of FFXIV world names (example list; please expand as needed)
    ffxiv_worlds = [
        "Aegis", "Adamantoise", "Alexander", "Anima", "Asura", "Atomos", "Bahamut", "Balmung", 
        "Behemoth", "Belias", "Brynhildr", "Cactuar", "Carbuncle", "Cerberus", "Chocobo", "Coeurl",
        "Diabolos", "Durandal", "Excalibur", "Exodus", "Faerie", "Famfrit", "Fenrir", "Garuda",
        "Gilgamesh", "Goblin", "Golem", "Cuculainn", "Halicarnassus", "Kraken", "Maduin", "Marilith", "Rafflesia", "Seraph", "Gungnir", "Hades", "Hyperion", "Ifrit", "Ixion", "Jenova",
        "Kujata", "Lamia", "Leviathan", "Lich", "Louisoix", "Malboro", "Mandragora", "Masamune",
        "Mateus", "Midgardsormr", "Moogle", "Odin", "Omega", "Pandaemonium", "Phoenix", "Ragnarok",
        "Ramuh", "Ridill", "Sargatanas", "Shinryu", "Shiva", "Siren", "Tiamat", "Titan",
        "Tonberry", "Typhon", "Ultima", "Ultros", "Unicorn", "Valefor", "Yojimbo", "Zalera", "Zeromus", 
        "Zodiark"
    ]
    
    # Check if the provided world_name is in the list of FFXIV worlds
    return world_name in ffxiv_worlds

bot.run('BOT_TOKEN')



