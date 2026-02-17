import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

# Wczytanie zmiennych z pliku .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ID ról administratorskich
ADMIN_ROLES = [1473027559594791137, 1473027623163662397]

# Funkcja do sprawdzenia uprawnień administratora
def is_admin(ctx):
    """Sprawdza czy użytkownik ma rolę administratora"""
    user_roles = [role.id for role in ctx.author.roles]
    return any(role_id in user_roles for role_id in ADMIN_ROLES)

# Konfiguracja intencji
intents = discord.Intents.default()
intents.message_content = True

# Tworzenie bota
bot = commands.Bot(command_prefix='!', intents=intents)

# Event: Bot gotowy
@bot.event
async def on_ready():
    print(f'{bot.user} zalogowano pomyślnie!')
    print(f"Komendy: {[cmd.name for cmd in bot.commands]}")
    await bot.tree.sync()

# Event: Nowa wiadomość
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

# Komenda: ping
@bot.command(name='ping')
async def niping(ctx):
    """Sprawdza ping bota"""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# Komenda: hello
@bot.command(name='hello')
async def hello(ctx):
    """Przywitanie"""
    await ctx.send(f'Cześć {ctx.author.mention}! 👋')
# Komenda: test (DEBUG)
@bot.command(name='test')
async def test(ctx):
    """Test"""
    user_roles = [f"{role.name}({role.id})" for role in ctx.author.roles]
    await ctx.send(f"Twoje role: {', '.join(user_roles)}\nJesteś adminem: {is_admin(ctx)}")
# Komenda: info
@bot.command(name='info')
async def info(ctx):
    """Informacje o serwerze"""
    embed = discord.Embed(
        title=f"Serwer: {ctx.guild.name}",
        description=f"Właściciel: {ctx.guild.owner.mention}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Członkowie", value=ctx.guild.member_count)
    embed.add_field(name="Kanały tekstowe", value=len(ctx.guild.text_channels))
    embed.add_field(name="Kanały głosowe", value=len(ctx.guild.voice_channels))
    
    await ctx.send(embed=embed)

# ===== KOMENDY ADMINISTRATORSKIE =====

# Komenda: kick
@bot.command(name='kick')
async def kick(ctx, member: discord.Member, *, reason="Brak powodu"):
    """Wyrzuca użytkownika z serwera"""
    if not is_admin(ctx):
        await ctx.send("❌ Nie masz uprawnień do tej komendy!")
        return
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="✅ Użytkownik wyrzucony",
            description=f"**Użytkownik:** {member.mention}\n**Powód:** {reason}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Błąd: {str(e)}")

# Komenda: ban
@bot.command(name='ban')
async def ban(ctx, member: discord.Member, *, reason="Brak powodu"):
    """Banuje użytkownika z serwera"""
    if not is_admin(ctx):
        await ctx.send("❌ Nie masz uprawnień do tej komendy!")
        return
    
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Użytkownik zbanowany",
            description=f"**Użytkownik:** {member.mention}\n**Powód:** {reason}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Błąd: {str(e)}")

# Komenda: mute
@bot.command(name='mute')
async def mute(ctx, member: discord.Member, *, reason="Brak powodu"):
    """Wycisza użytkownika (dodaje rolę mute)"""
    if not is_admin(ctx):
        await ctx.send("❌ Nie masz uprawnień do tej komendy!")
        return
    
    try:
        mute_role = ctx.guild.get_role(1473038867199426836)
        if mute_role:
            await member.add_roles(mute_role, reason=reason)
            embed = discord.Embed(
                title="🔇 Użytkownik wyciszony",
                description=f"**Użytkownik:** {member.mention}\n**Powód:** {reason}",
                color=discord.Color.greyple()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Rola 'muted' nie istnieje na serwerze!")
    except Exception as e:
        await ctx.send(f"❌ Błąd: {str(e)}")

# Komenda: unban
@bot.command(name='unban')
async def unban(ctx, *, user_name):
    """Odbanuje użytkownika"""
    if not is_admin(ctx):
        await ctx.send("❌ Nie masz uprawnień do tej komendy!")
        return
    
    try:
        banned_users = await ctx.guild.bans()
        for ban_entry in banned_users:
            user = ban_entry.user
            if user.name == user_name:
                await ctx.guild.unban(user)
                embed = discord.Embed(
                    title="✅ Użytkownik odbanowany",
                    description=f"**Użytkownik:** {user.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
        await ctx.send(f"❌ Nie znaleziono użytkownika '{user_name}' na liście banów!")
    except Exception as e:
        await ctx.send(f"❌ Błąd: {str(e)}")

# Uruchomienie bota
bot.run(TOKEN)
