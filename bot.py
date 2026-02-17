import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import random
from database import log_opinion, log_verification, log_ban, log_mute

# Wczytanie zmiennych z pliku .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ID ról administratorskich
ADMIN_ROLES = [1473027559594791137, 1473027623163662397]
MUTE_ROLE_ID = 1473038867199426836
VERIFY_ROLE_ID = 1473045046529101824
OPINION_CHANNEL_ID = 1473051804550828233
WELCOME_CHANNEL_ID = None  # Ustaw ID kanału powitalnego (np. 1234567890) lub None = systemowy
GUILD_ID = 1473027558768545963  # ID Twojego serwera Discord

# Funkcja do sprawdzenia uprawnień administratora
def is_admin(interaction):
    """Sprawdza czy użytkownik ma rolę administratora"""
    user_roles = [role.id for role in interaction.user.roles]
    return any(role_id in user_roles for role_id in ADMIN_ROLES)

# Konfiguracja intencji
intents = discord.Intents.default()
intents.members = True  # Wymagane do śledzenia dołączeń

# Tworzenie bota
bot = commands.Bot(command_prefix='/', intents=intents)

# ===== VIEW (PRZYCISKI) =====

class OpinionModal(discord.ui.Modal, title="Formularz Opinii"):
    """Modal do zbierania opinii"""
    product = discord.ui.TextInput(label="Produkt/Usługa", placeholder="Nazwa produktu...")
    realization = discord.ui.TextInput(label="Realizacja", placeholder="Jak był zrealizowany produkt?", style=discord.TextStyle.long)
    stars = discord.ui.TextInput(label="Ocena w gwiazdkach (1-5)", placeholder="Wpisz liczbę 1-5")
    recommend = discord.ui.TextInput(label="Czy polecasz? (tak/nie)", placeholder="tak lub nie")
    
    async def on_submit(self, interaction: discord.Interaction):
        # Sprawdzenie kanału
        if interaction.channel.id != OPINION_CHANNEL_ID:
            await interaction.response.send_message(
                f"❌ Tego kanału nie ma uprawnień do wysyłania opinii!\n"
                f"Spróbuj ponownie na kanale <#{OPINION_CHANNEL_ID}>",
                ephemeral=True
            )
            return
        
        # Walidacja gwiazdek
        try:
            stars_val = int(self.stars.value)
            if stars_val < 1 or stars_val > 5:
                await interaction.response.send_message("❌ Ocena musi być między 1 a 5!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Ocena musi być liczbą!", ephemeral=True)
            return
        
        # Walidacja polecania
        recommend_val = self.recommend.value.lower()
        if recommend_val not in ["tak", "nie", "yes", "no"]:
            await interaction.response.send_message("❌ Wpisz 'tak' lub 'nie'!", ephemeral=True)
            return
        
        recommend_text = "✅ Polecam!" if recommend_val in ["tak", "yes"] else "❌ Nie polecam"
        stars_emoji = "⭐" * stars_val
        
        # Tworzenie embeda
        embed = discord.Embed(
            title=f"⭐ Opinia: {self.product.value}",
            color=discord.Color.gold()
        )
        embed.add_field(name="👤 Autor", value=interaction.user.mention, inline=False)
        embed.add_field(name="📝 Realizacja", value=self.realization.value, inline=False)
        embed.add_field(name="⭐ Ocena", value=f"{stars_emoji} ({stars_val}/5)", inline=True)
        embed.add_field(name="👍 Polecenie", value=recommend_text, inline=True)
        embed.set_footer(text=f"Data: {discord.utils.utcnow().strftime('%d.%m.%Y %H:%M')}")
        
        # Logowanie do bazy
        log_opinion(
            user_id=interaction.user.id,
            username=interaction.user.name,
            product=self.product.value,
            realization=self.realization.value,
            stars=stars_val,
            recommend=recommend_val
        )
        
        # Wysłanie opinii na kanał
        try:
            channel = interaction.guild.get_channel(OPINION_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
                await interaction.response.send_message("✅ Opinia wysłana pomyślnie!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Kanał opinii nie istnieje!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="✅ Weryfikuj się", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        await interaction.response.send_message("📋 Rozpoczynam weryfikację! Wysyłam Ci pytania na PW...", ephemeral=True)
        
        try:
            # Pytanie 1: Wiek
            await user.send("**🔐 WERYFIKACJA SERWERA** 🔐\n\nPytanie 1/2:\n**Ile masz lat?** (wpisz tylko liczbę)")
            
            def check(msg):
                return msg.author == user and isinstance(msg.channel, discord.DMChannel)
            
            # Czeka na odpowiedź - wiek
            try:
                msg_age = await bot.wait_for('message', check=check, timeout=300)
                age_text = msg_age.content.strip()
                
                try:
                    age = int(age_text)
                    if age < 13:
                        await user.send("❌ Musisz mieć co najmniej 13 lat!")
                        return
                except ValueError:
                    await user.send("❌ Wpisz poprawną liczbę!")
                    return
            except Exception as e:
                await user.send(f"⏱️ Czas się skończył! Spróbuj ponownie za chwilę.")
                return
            
            # Pytanie 2: Matematyka
            await user.send("✅ Dobrze! Pytanie 2/2:\n**Ile to 5 + 3?** (wpisz tylko liczbę)")
            
            try:
                msg_math = await bot.wait_for('message', check=check, timeout=300)
                math_text = msg_math.content.strip()
                
                try:
                    answer = int(math_text)
                    if answer != 8:
                        await user.send(f"❌ Błędna odpowiedź! Poprawna to: 8")
                        return
                except ValueError:
                    await user.send("❌ Wpisz poprawną liczbę!")
                    return
            except Exception as e:
                await user.send(f"⏱️ Czas się skończył! Spróbuj ponownie za chwilę.")
                return

            log_ok = log_verification(
                user_id=user.id,
                username=user.name,
                age=age
            )
            print(f"Verification saved: {log_ok} user={user.name} id={user.id}")
            
            # Wszystko OK - daj rolę
            verify_role = interaction.guild.get_role(VERIFY_ROLE_ID)
            if verify_role:
                await user.add_roles(verify_role)
                embed = discord.Embed(
                    title="✅ Weryfikacja Powiodła Się!",
                    description=f"Witaj na serwerze {interaction.guild.name}! 🎉",
                    color=discord.Color.green()
                )
                await user.send(embed=embed)
                
                # Powiadomienie na serwerze
                channel = interaction.guild.system_channel
                if channel:
                    await channel.send(f"🎉 {user.mention} przeszedł weryfikację!")
            else:
                await user.send("❌ Rola weryfikacyjna nie istnieje!")
        
        except Exception as e:
            await user.send(f"❌ Błąd: {str(e)}")
            print(f"Błąd weryfikacji: {e}")

# Event: Bot gotowy
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f'{bot.user} zalogowano pomyślnie!')
        print(f"Zsynchronizowano {len(synced)} komend(y) dla serwera {GUILD_ID}")
    except Exception as e:
        print(f"Błąd synchronizacji: {e}")

# Event: Nowy członek
@bot.event
async def on_member_join(member):
    """Wysyła wiadomość powitalną gdy ktoś dołączy"""
    channel_id = WELCOME_CHANNEL_ID or (member.guild.system_channel.id if member.guild.system_channel else None)
    if not channel_id:
        return

    channel = member.guild.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="👋 Witamy na serwerze!",
            description=f"Cześć {member.mention}! Miło Cię widzieć! 🎉",
            color=discord.Color.green()
        )
        embed.add_field(name="📋 Weryfikacja", value="Przejdź weryfikację, aby uzyskać dostęp do serwera!", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Jesteś {member.guild.member_count}. członkiem!")
        await channel.send(embed=embed)

# ===== SLASH COMMANDS =====

# Komenda: ping
@bot.tree.command(name='ping', description="Sprawdza ping bota")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! {round(bot.latency * 1000)}ms')

# Komenda: hello
@bot.tree.command(name='hello', description="Przywitanie")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f'Cześć {interaction.user.mention}! 👋')

# Komenda: info
@bot.tree.command(name='info', description="Informacje o serwerze")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"Serwer: {interaction.guild.name}",
        description=f"Właściciel: {interaction.guild.owner.mention}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Członkowie", value=interaction.guild.member_count)
    embed.add_field(name="Kanały tekstowe", value=len(interaction.guild.text_channels))
    embed.add_field(name="Kanały głosowe", value=len(interaction.guild.voice_channels))
    
    await interaction.response.send_message(embed=embed)

# ===== KOMENDY ADMINISTRATORSKIE =====

# Komenda: kick
@bot.tree.command(name='kick', description="Wyrzuca użytkownika z serwera")
@app_commands.describe(member="Użytkownik do wyrzucenia", reason="Powód wyrzucenia")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Brak powodu"):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        
        # Logowanie kicka do bazy
        log_ban(
            user_id=member.id,
            username=member.name,
            admin_id=interaction.user.id,
            reason=reason
        )
        
        embed = discord.Embed(
            title="✅ Użytkownik wyrzucony",
            description=f"**Użytkownik:** {member.mention}\n**Powód:** {reason}",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

# Komenda: ban
@bot.tree.command(name='ban', description="Banuje użytkownika z serwera")
@app_commands.describe(member="Użytkownik do zbanowania", reason="Powód banu")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Brak powodu"):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    try:
        await member.ban(reason=reason)
        
        # Logowanie bana do bazy
        log_ban(
            user_id=member.id,
            username=member.name,
            admin_id=interaction.user.id,
            reason=reason
        )
        
        embed = discord.Embed(
            title="🔨 Użytkownik zbanowany",
            description=f"**Użytkownik:** {member.mention}\n**Powód:** {reason}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

# Komenda: mute
@bot.tree.command(name='mute', description="Wycisza użytkownika")
@app_commands.describe(member="Użytkownik do wyciszenia", reason="Powód wyciszenia")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "Brak powodu"):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    try:
        mute_role = interaction.guild.get_role(MUTE_ROLE_ID)
        if mute_role:
            await member.add_roles(mute_role, reason=reason)
            
            # Logowanie mute do bazy
            log_mute(
                user_id=member.id,
                username=member.name,
                admin_id=interaction.user.id,
                reason=reason
            )
            
            embed = discord.Embed(
                title="🔇 Użytkownik wyciszony",
                description=f"**Użytkownik:** {member.mention}\n**Powód:** {reason}",
                color=discord.Color.greyple()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Rola 'muted' nie istnieje na serwerze!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

# Komenda: unmute
@bot.tree.command(name='unmute', description="Odwycisza użytkownika")
@app_commands.describe(member="Użytkownik do odwyciszenia")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    try:
        mute_role = interaction.guild.get_role(MUTE_ROLE_ID)
        if mute_role:
            await member.remove_roles(mute_role)
            embed = discord.Embed(
                title="✅ Użytkownik odwyciszony",
                description=f"**Użytkownik:** {member.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Rola 'muted' nie istnieje na serwerze!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

# Komenda: unban
@bot.tree.command(name='unban', description="Odbanuje użytkownika")
@app_commands.describe(user_name="Nazwa użytkownika do odbanowania")
async def unban(interaction: discord.Interaction, user_name: str):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    try:
        banned_users = await interaction.guild.bans()
        for ban_entry in banned_users:
            user = ban_entry.user
            if user.name == user_name:
                await interaction.guild.unban(user)
                embed = discord.Embed(
                    title="✅ Użytkownik odbanowany",
                    description=f"**Użytkownik:** {user.mention}",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed)
                return
        await interaction.response.send_message(f"❌ Nie znaleziono użytkownika '{user_name}' na liście banów!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

# ===== SYSTEM WERYFIKACJI =====

# Komenda: verify
@bot.tree.command(name='verify', description="Weryfikuj się aby uzyskać dostęp")
async def verify(interaction: discord.Interaction):
    """Uruchamia proces weryfikacji"""
    await interaction.response.defer(ephemeral=True)
    await verify_cmd(interaction)

async def verify_cmd(interaction: discord.Interaction):
    user = interaction.user
    await interaction.followup.send("📋 Rozpoczynam weryfikację! Wysyłam Ci pytania na PW...", ephemeral=True)
    
    try:
        await user.send("**🔐 WERYFIKACJA SERWERA** 🔐\n\nPytanie 1/2:\n**Ile masz lat?** (wpisz tylko liczbę)")
        
        def check(msg):
            return msg.author == user and isinstance(msg.channel, discord.DMChannel)
        
        try:
            msg_age = await bot.wait_for('message', check=check, timeout=300)
            age_text = msg_age.content.strip()
            
            try:
                age = int(age_text)
                if age < 13:
                    await user.send("❌ Musisz mieć co najmniej 13 lat!")
                    return
            except ValueError:
                await user.send("❌ Wpisz poprawną liczbę!")
                return
        except Exception as e:
            await user.send(f"⏱️ Czas się skończył! Spróbuj ponownie za chwilę.")
            return
        
        await user.send("✅ Dobrze! Pytanie 2/2:\n**Ile to 5 + 3?** (wpisz tylko liczbę)")
        
        try:
            msg_math = await bot.wait_for('message', check=check, timeout=300)
            math_text = msg_math.content.strip()
            
            try:
                answer = int(math_text)
                if answer != 8:
                    await user.send(f"❌ Błędna odpowiedź! Poprawna to: 8")
                    return
            except ValueError:
                await user.send("❌ Wpisz poprawną liczbę!")
                return
        except Exception as e:
            await user.send(f"⏱️ Czas się skończył! Spróbuj ponownie za chwilę.")
            return
        
        verify_role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if verify_role:
            await user.add_roles(verify_role)            
            # Logowanie weryfikacji do bazy
            log_verification(
                user_id=user.id,
                username=user.name,
                age=age
            )
            
            embed = discord.Embed(
                title="✅ Weryfikacja Powiodła Się!",
                description=f"Witaj na serwerze {interaction.guild.name}! 🎉",
                color=discord.Color.green()
            )
            await user.send(embed=embed)
            
            channel = interaction.guild.system_channel
            if channel:
                await channel.send(f"🎉 {user.mention} przeszedł weryfikację!")
        else:
            await user.send("❌ Rola weryfikacyjna nie istnieje!")
    
    except Exception as e:
        await user.send(f"❌ Błąd: {str(e)}")
        print(f"Błąd weryfikacji: {e}")

# Komenda: send_verify_message (admin)
@bot.tree.command(name='send_verify_message', description="Wyślij wiadomość weryfikacyjną")
async def send_verify_message(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Nie masz uprawnień!", ephemeral=True)
        return
    
    # Wyślij na kanale gdzie wpisano komendę
    channel = interaction.channel
    
    if not channel:
        await interaction.response.send_message(f"❌ Nie znaleziono kanału!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🔐 WERYFIKACJA SERWERA",
        description="Kliknij poniżej **ZIELONY** przycisk aby się zweryfikować.\n\n"
                    "Proces weryfikacji to:\n"
                    "1️⃣ Pytanie o wiek\n"
                    "2️⃣ Proste pytanie matematyczne\n\n"
                    "Po pomyślnej weryfikacji otrzymasz dostęp do całego serwera!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1995/1995467.png")
    
    try:
        view = VerifyView()
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Wiadomość weryfikacyjna wysłana!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {str(e)}", ephemeral=True)

# ===== SYSTEM OPINII =====

# Komenda: opinia
@bot.tree.command(name='opinia', description="Wyślij opinię o produkcie/usłudze")
async def opinia(interaction: discord.Interaction):
    """Otwiera formularz opinii"""
    # Sprawdzenie kanału
    if interaction.channel.id != OPINION_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ Tego kanału nie ma uprawnień do wysyłania opinii!\n"
            f"Spróbuj ponownie na kanale <#{OPINION_CHANNEL_ID}>",
            ephemeral=True
        )
        return
    
    # Pokaż modal
    modal = OpinionModal()
    await interaction.response.send_modal(modal)

# Uruchomienie bota
def run_bot():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set")
    bot.run(TOKEN)

if __name__ == '__main__':
    run_bot()
