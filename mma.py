import os
import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import pytz
import time
time.sleep(10)  # Startverzögerung von 10 Sekunden


from discord.ext import tasks
from flask import Flask
from threading import Thread
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is still running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()
    
TIMEZONE = pytz.timezone("Europe/Berlin")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def ping(ctx):
    """Testet, ob der Bot online ist."""
    latency = round(bot.latency * 1000)  # Latenz in Millisekunden
    await ctx.send(f'🏓 Pong! Der Bot antwortet in {latency}ms.')

LOOTDROP_IMAGE_URL = "https://i.postimg.cc/ncr1dhGF/MMA-Logo-im-kantigen-Design-removebg-preview.png"
ANNOUNCE_CHANNEL_ID = 1364775098266947614
AUFSTELLUNG_CHANNEL_ID = 1363970859429007470
BOT_OWNER_ID = 985580954854756372
LOOTDROP_TIMES = ["12:30", "13:30", "14:30", "16:00", "18:20", "23:20", "01:20", "04:00"]

GANGWAR_CHANNEL_ID = 1362866021815292130 # <- Channel-ID für Gangwar Erinnerungen
GANGWAR_TIMES = {"18:45": "19:00", "23:45": "00:00"}  # Erinnerung -> Tatsächliche GW-Zeit

manual_votes = set()  
current_votes = {}  

@tasks.loop(minutes=1)
async def check_lootdrop_votes():
    now = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone("Europe/Berlin")).strftime("%H:%M")
    print(f"🔍 [DEBUG] Überprüfung um {now}")

    for loot_time in LOOTDROP_TIMES:
        await asyncio.sleep(1)
        reminder_time = calc_reminder_time(loot_time)
        print(f"⏳ [DEBUG] Lootdrop {loot_time} - Erinnerung um {reminder_time}")

        if now == reminder_time:
            print(f"🚀 [DEBUG] Starte Abstimmung für {loot_time}!")
            await post_vote(loot_time)

        elif now == loot_time and loot_time in current_votes:
            print(f"✅ [DEBUG] Poste Teilnehmerliste für {loot_time}!")
            await post_participants(loot_time)

@tasks.loop(minutes=1)
async def check_gangwar_reminders():
    now = datetime.datetime.now(TIMEZONE).strftime("%H:%M")
    await asyncio.sleep(1)
    print(f"🔍 [DEBUG] Gangwar-Reminder Check um {now}")  # Debug-Print

    if now in GANGWAR_TIMES:
        actual_gw_time = GANGWAR_TIMES[now]
        print(f"🚨 [DEBUG] Gangwar-Erinnerung für {actual_gw_time} gesendet!")  # Debug-Print
        await send_gangwar_reminder(actual_gw_time)

async def send_gangwar_reminder(actual_gw_time):
    channel = bot.get_channel(GANGWAR_CHANNEL_ID)
    if not channel:
        print(f"⚠️ Gangwar-Channel mit ID {GANGWAR_CHANNEL_ID} nicht gefunden.")
        return

    guild = channel.guild
    role = discord.utils.get(guild.roles, name="MMA")
    role_mention = role.mention if role else "**@MMA**"  # Falls die Rolle nicht gefunden wird

    embed = discord.Embed(
        title=f"🚨 GANGWAR ERINNERUNG: {actual_gw_time} UHR",
        description=f"{role_mention}\n\n"
                    f"**VERGESST NICHT DEN GANGWAR UM {actual_gw_time} UHR!**\n"
                    f"**Bereitmachen!🔥**",
        color=0x04241d,  
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=LOOTDROP_IMAGE_URL)  
    embed.set_footer(text="Gangwar Reminder", icon_url=LOOTDROP_IMAGE_URL)

    await channel.send(f"{role_mention}", embed=embed)

def calc_reminder_time(loot_time):
    hour, minute = map(int, loot_time.split(":"))
    now = datetime.datetime.now(TIMEZONE)
    
    reminder_time = now.replace(hour=hour, minute=minute) - datetime.timedelta(hours=1)

    if reminder_time.day < now.day:
        reminder_time += datetime.timedelta(days=1)

    return reminder_time.strftime("%H:%M")

    return debug_time

def get_announce_channel():
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if not channel:
        print(f"⚠️ [DEBUG] Fehler: `get_announce_channel()` konnte Kanal mit ID {ANNOUNCE_CHANNEL_ID} nicht finden!")
    return channel

async def post_vote(loot_time):
    global manual_votes

    print(f"📌 [DEBUG] `post_vote` aufgerufen mit {loot_time}")
    print(f"📌 [DEBUG] `manual_votes` aktuell: {manual_votes}")

    if loot_time in manual_votes:
        print(f"⚠️ [DEBUG] `post_vote` wird NICHT ausgeführt, da {loot_time} in `manual_votes` ist.")
        return

    channel = get_announce_channel()  # 🔍 Hier wird der Channel geholt

    if not channel:  # Falls der Kanal nicht existiert, gib eine Warnung aus
        print(f"⚠️ [DEBUG] Channel mit ID {ANNOUNCE_CHANNEL_ID} nicht gefunden! `post_vote` abgebrochen.")
        return

    guild = channel.guild
    role = discord.utils.get(guild.roles, name="MMA")
    role_mention = role.mention if role else ""

    today = datetime.datetime.now().strftime("%d.%m.%Y")

    embed = discord.Embed(
        title=f"**Lootdrop Abstimmung für {loot_time} Uhr ({today})**",
        description="**Reagiere, um teilzunehmen:**\n"
                    "♂️ für **Männer** (max. **15**)\n"
                    "♀️ für **Frauen** (max. **2**)\n"
                    "Die Abstimmung wird live aktualisiert.",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=LOOTDROP_IMAGE_URL)
    embed.set_footer(text="Made by izzyy.gg")  

    embed.add_field(name="♂️ Männer (max. 15)", value="-", inline=True)
    embed.add_field(name="♀️ Frauen (max. 2)", value="-", inline=True)

    print(f"✅ [DEBUG] Abstimmung für {loot_time} gestartet!")
    
    message = await channel.send(f"{role_mention} 📢 Neue Lootdrop-Abstimmung!", embed=embed)

    await asyncio.sleep(0.5)
    await message.add_reaction("♂️")
    await asyncio.sleep(0.5)
    await message.add_reaction("♀️")

    current_votes[loot_time] = {
        "♂️": [],
        "♀️": [],
        "message": message
    }

    print(f"✅ [DEBUG] Abstimmung für {loot_time} erstellt und in `current_votes` gespeichert.")
    print(f"📌 [DEBUG] `manual_votes` nach `post_vote`: {manual_votes}")

    asyncio.create_task(schedule_participant_post(loot_time))

async def schedule_participant_post(loot_time):
    now = datetime.datetime.now(TIMEZONE)
    lootdrop_time = datetime.datetime.strptime(loot_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=TIMEZONE
    )

    if lootdrop_time < now:
        lootdrop_time += datetime.timedelta(days=1)

    delay = (lootdrop_time - now).total_seconds()
    print(f"⏳ [DEBUG] Teilnehmerliste für {loot_time} wird in {delay} Sekunden gepostet.")

    await asyncio.sleep(delay)

    if loot_time in current_votes:
        print(f"🕒 [DEBUG] Lootdrop-Zeit erreicht! Poste Teilnehmerliste für {loot_time}.")
        await post_participants(loot_time)

async def post_participant_list(channel, loot_time):
    embed = discord.Embed(
        title=f"📜 Teilnehmerliste für {loot_time} Uhr",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="♂️ Männer (max. 15)", value="-", inline=True)
    embed.add_field(name="♀️ Frauen (max. 2)", value="-", inline=True)
    embed.set_footer(text="Diese Liste wird live aktualisiert.")

    message = await channel.send(embed=embed)
    return message
    
    print(f"✅ [DEBUG] `current_votes` nach Start: {current_votes}")


async def update_participant_list(loot_time):
    if loot_time not in current_votes:
        await asyncio.sleep(0.5)
        return

    votes = current_votes[loot_time]
    message = votes["message"]

    males = "\n".join([f"**{name}**" for name in votes["♂️"]]) if votes["♂️"] else "-"
    females = "\n".join([f"**{name}**" for name in votes["♀️"]]) if votes["♀️"] else "-"

    embed = message.embeds[0]  # Den existierenden Embed holen und aktualisieren
    embed.set_field_at(0, name="♂️ Männer (max. 15)", value=males, inline=True)
    embed.set_field_at(1, name="♀️ Frauen (max. 2)", value=females, inline=True)

    await message.edit(embed=embed)

async def close_vote(loot_time):
    if loot_time not in current_votes:
        print(f"⚠️ [DEBUG] `{loot_time}` wurde bereits automatisch beendet.")
        return

    await post_participants(loot_time)

    if loot_time in current_votes:
        del current_votes[loot_time]

    manual_votes.discard(loot_time)

async def post_participants(loot_time):
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)

    if loot_time not in current_votes:
        print(f"⚠️ [DEBUG] `{loot_time}` existiert nicht mehr in `current_votes`!")
        return  # Stoppt die Funktion, damit kein Fehler auftritt

    votes = current_votes.pop(loot_time, None)  # Sicher entfernen

    if not votes:
        print(f"⚠️ [DEBUG] Keine Votes für `{loot_time}` gefunden!")
        return

    males = "\n".join([f"**{name}**" for name in votes["♂️"]]) if votes["♂️"] else "-"
    females = "\n".join([f"**{name}**" for name in votes["♀️"]]) if votes["♀️"] else "-"

    embed = discord.Embed(
        title=f"✅ Teilnehmerliste für Lootdrop um {loot_time} Uhr",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
        )
    embed.add_field(name="♂️ Männer (max. 15)", value=males, inline=True)
    embed.add_field(name="♀️ Frauen (max. 2)", value=females, inline=True)
    embed.set_thumbnail(url=LOOTDROP_IMAGE_URL)
    embed.set_footer(text="Lootdrop - Teilnehmerliste", icon_url=LOOTDROP_IMAGE_URL)

    await channel.send(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    guild = reaction.message.guild
    member = await guild.fetch_member(user.id)

    loot_time = get_loot_time_from_embed(reaction.message)
    if not loot_time or loot_time not in current_votes:
        return

    # Falls alle Plätze belegt sind, entferne die Reaktion
    if reaction.emoji == "♂️" and len(current_votes[loot_time]["♂️"]) >= 15:
        await reaction.message.remove_reaction(reaction.emoji, user)
        return
    elif reaction.emoji == "♀️" and len(current_votes[loot_time]["♀️"]) >= 2:
        await reaction.message.remove_reaction(reaction.emoji, user)
        return

    added = False
    if reaction.emoji == "♂️":
        if member.display_name not in current_votes[loot_time]["♂️"]:
            current_votes[loot_time]["♂️"].append(member.display_name)
            added = True
    elif reaction.emoji == "♀️":
        if member.display_name not in current_votes[loot_time]["♀️"]:
            current_votes[loot_time]["♀️"].append(member.display_name)
            added = True

    if added:
        await update_participant_list(loot_time)

    if len(current_votes[loot_time]["♂️"]) == 15 and len(current_votes[loot_time]["♀️"]) == 2:
        print(f"✅ [DEBUG] Alle Plätze belegt! Beende Abstimmung für {loot_time}.")
        await close_vote(loot_time)

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    guild = reaction.message.guild
    member = guild.get_member(user.id)

    loot_time = get_loot_time_from_embed(reaction.message)
    if not loot_time or loot_time not in current_votes:
        return

    removed = False
    if reaction.emoji == "♂️":
        if member.display_name in current_votes[loot_time]["♂️"]:
            current_votes[loot_time]["♂️"].remove(member.display_name) 
            removed = True
    elif reaction.emoji == "♀️":
        if member.display_name in current_votes[loot_time]["♀️"]:
            current_votes[loot_time]["♀️"].remove(member.display_name)
            removed = True

    if removed:
        await update_participant_list(loot_time)
       
def get_loot_time_from_embed(message):
    if not message.embeds:
        return None
    embed = message.embeds[0]
    for loot_time in LOOTDROP_TIMES:
        if loot_time in embed.title:
            return loot_time
    return None

@bot.event
async def on_message(message):
    global manual_votes  # ✅ Nutzt die globale Variable
    print(f"🧐 [DEBUG] `manual_votes` aktuell: {manual_votes}")
    await bot.process_commands(message)  # Damit andere Befehle weiterhin funktionieren

    """Überprüft, ob eine Lootdrop-Abstimmung gelöscht wurde und entfernt sie aus `current_votes`."""
    if not message.embeds:
        return  # Falls die gelöschte Nachricht kein Embed war, ignoriere sie.

    embed = message.embeds[0]
    loot_time = get_loot_time_from_embed(message)

    if loot_time and loot_time in current_votes:
        print(f"🗑 [DEBUG] Abstimmung für {loot_time} wurde gelöscht. Entferne aus `current_votes`.")
        del current_votes[loot_time]  # Löscht die Abstimmung aus dem Speicher

ALLOWED_ROLE_IDS = {1362866020695408805, 1362866020695408807, 1362866020649271571, 1362866020695408804}

@bot.command(name="startdrop")
async def startdrop(ctx, loot_time: str):
    global manual_votes

    print(f"📌 [DEBUG] `startdrop` aufgerufen mit {loot_time}")
    print(f"📌 [DEBUG] `manual_votes` VORHER: {manual_votes}")

    if loot_time in manual_votes:
        await ctx.send(f"⚠️ Abstimmung für {loot_time} läuft bereits!")
        return

    await post_vote(loot_time)  # ✅ Erst die Abstimmung posten
    manual_votes.add(loot_time)  # 🔥 Dann `manual_votes` setzen!

    print(f"📌 [DEBUG] `manual_votes` NACHHER: {manual_votes}")
    user_role_ids = {role.id for role in ctx.author.roles}

    if not (user_role_ids & ALLOWED_ROLE_IDS) and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("🚫 Du hast keine Berechtigung, eine Abstimmung zu starten!")
        return

    try:
        target_time = datetime.datetime.strptime(loot_time, "%H:%M").replace(
            year=datetime.datetime.now().year,
            month=datetime.datetime.now().month,
            day=datetime.datetime.now().day,
            tzinfo=TIMEZONE
        )
    except ValueError:
        await ctx.send("⚠️ Ungültiges Zeitformat! Bitte gib die Uhrzeit im Format HH:MM an (z. B. `!startdrop 14:30`).")
        return

    now = datetime.datetime.now(TIMEZONE)

    if target_time < now:
        print(f"⚠️ [DEBUG] Zeit liegt in der Vergangenheit! Starte Abstimmung sofort für {loot_time}.")
        manual_votes.add(loot_time)
        await post_vote(loot_time)
        return

    manual_votes.add(loot_time)  
    print(f"📌 [DEBUG] `manual_votes` NACHHER: {manual_votes}")

    await post_vote(loot_time)

    delay = (target_time - now).total_seconds()
    print(f"⏳ [DEBUG] Warte {delay} Sekunden, bevor die Abstimmung geschlossen wird.")

    async def delayed_post():
        await asyncio.sleep(delay)
        await close_vote(loot_time)  

@bot.command(name="checkrole")
async def check_role(ctx):
    """Prüft, ob der Benutzer eine berechtigte Rolle hat."""
    ALLOWED_ROLE_IDS = {1362866020695408805, 1362866020695408807, 1362866020649271571, 1362866020695408804}

    user_role_ids = {role.id for role in ctx.author.roles}  # IDs der Rollen des Nutzers

    print(f"🔍 [DEBUG] {ctx.author} hat folgende Rollen-IDs: {user_role_ids}")
    if user_role_ids & ALLOWED_ROLE_IDS:
        await ctx.send(f"✅ {ctx.author.mention}, du hast die Berechtigung, den Bot zu nutzen!")
    else:
        await ctx.send(f"🚫 {ctx.author.mention}, du hast **keine** Berechtigung für diesen Bot!")

@bot.command(name="resetdrop")
async def resetdrop(ctx, loot_time: str):
    global manual_votes  # ✅ Greift auf die globale Variable zu
    if loot_time in manual_votes:
        manual_votes.discard(loot_time)
        await ctx.send(f"✅ Manuelle Abstimmung für {loot_time} wurde zurückgesetzt!")
    else:
        await ctx.send(f"⚠️ Es gibt keine gespeicherte manuelle Abstimmung für {loot_time}.")

@bot.command(name="endpoll")
async def end_poll(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        await ctx.send("🚫 Du hast keine Berechtigung, diese Abstimmung zu beenden!")
        return

    if not current_votes:
        await ctx.send("⚠️ Es gibt derzeit keine laufenden Abstimmungen!")
        return

    # Nimmt die erste laufende Abstimmung aus dem Dictionary
    loot_time = next(iter(current_votes))

    await close_vote(loot_time)

@bot.command(name="gw")
async def gw(ctx, time: str):

    allowed_roles = ["Rang 12", "Rang 11", "Rang 10", "*"]  # Die erlaubten Rollen
    user_roles = [role.name for role in ctx.author.roles]  # Alle Rollen des Benutzers

    if not any(role in user_roles for role in allowed_roles) and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("🚫 Du hast keine Berechtigung, manuelle Erinnerungen zu erstellen!")
        return
    try:
        # Überprüfen, ob die Zeit im Format "HH:MM" ist
        hour, minute = map(int, time.split(":"))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
    except ValueError:
        await ctx.send("⚠️ Bitte gib eine gültige Zeit im Format `HH:MM` ein.")
        return

    formatted_reminder_time = f"{hour:02}:{minute:02}"

    gangwar_channel = await bot.fetch_channel(GANGWAR_CHANNEL_ID)  # Channel ID für die Gangwar-Erinnerung
    
    # Gangwar-Erinnerung embed erstellen
    embed = discord.Embed(
        title=f"**GANGWAR Erinnerung für {formatted_reminder_time} Uhr**",
        description=f"**GANGWAR beginnt demnächst! 💥 Bereit machen!**",
        color=discord.Color(0x04241d), 
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=LOOTDROP_IMAGE_URL)  # Thumbnail für das Embed, das gleiche wie das Lootdrop
    embed.set_footer(text="Gangwar - Erinnerung!", icon_url=LOOTDROP_IMAGE_URL)

    guild = ctx.guild
    role = discord.utils.get(guild.roles, name="MMA")
    role_mention = role.mention if role else ""

    # Erinnerung posten
    await gangwar_channel.send(f"{role_mention}", embed=embed)


@bot.command(name="gwmarathon")
async def gw_marathon(ctx):
    """Startet sofort eine Erinnerung für den Gangwar-Marathon."""
    
    allowed_roles = ["Capitano", "11er", "10er", "Leaderschaft"]
    user_roles = [role.name for role in ctx.author.roles]

    if not any(role in user_roles for role in allowed_roles) and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("🚫 Du hast keine Berechtigung, einen Gangwar-Marathon zu starten!")
        return

    gangwar_channel = bot.get_channel(GANGWAR_CHANNEL_ID)
    if not gangwar_channel:
        await ctx.send("⚠️ Fehler: Gangwar-Kanal nicht gefunden!")
        return

    guild = ctx.guild
    role = discord.utils.get(guild.roles, name="MMA")
    role_mention = role.mention if role else ""

    embed = discord.Embed(
        title="🚨 **GANGWAR-MARATHON GESTARTET!**",
        description="🔥 **Der Gangwar-Marathon beginnt JETZT!**\n\n"
                    "⚔️ **Jeder bereitmachen und joinen!**",
        color=0x3d0006,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=LOOTDROP_IMAGE_URL)
    embed.set_footer(text="made by izzyy.gg")

    await gangwar_channel.send(f"{role_mention}", embed=embed)

AUFSTELLUNG_CHANNEL_ID = 1363970859429007470  # Aufstellungschannel
MENTION_ROLE = "MMA"  # Rolle, die erwähnt wird
ALLOWED_ROLES = ["Rang 12", "Rang 11", "Rang 10", "*"]
AUFSTELLUNG_IMAGE_URL = "https://i.postimg.cc/ncr1dhGF/MMA-Logo-im-kantigen-Design-removebg-preview.png"
EMBED_COLOR = 0x04241d
letzte_aufstellung = None
aktuelle_aufstellung = None

def has_permission(member):
    return any(role.name in ALLOWED_ROLES for role in member.roles)

@bot.command(name="aufstellung")
async def aufstellung(ctx, uhrzeit: str = None, *, plan_text: str = ""):
    await ctx.message.delete()

    if not has_permission(ctx.author):
        await ctx.send("🚫 Du hast keine Berechtigung, eine Aufstellung zu starten!", delete_after=5)
        return

    if not uhrzeit:
        await ctx.send("❌ Bitte gib eine Uhrzeit an! Beispiel: `!aufstellung 20:00 [Plan-Text]`", delete_after=5)
        return

    heute = datetime.datetime.now().strftime("%d.%m.%Y")
    uhrzeit_display = f"{uhrzeit} Uhr"

    channel = bot.get_channel(AUFSTELLUNG_CHANNEL_ID)
    if not channel:
        await ctx.send("⚠️ Fehler: Aufstellungschannel nicht gefunden!", delete_after=5)
        return

    role = discord.utils.get(ctx.guild.roles, name=MENTION_ROLE)
    mention_text = role.mention if role else ""

    global alle_gucci_member
    alle_gucci_member = [(member.id, member.display_name) for member in role.members] if role else []

    plan_display = f"### **Plan:** {plan_text}" if plan_text else "### **Plan:** —"

    embed = discord.Embed(
        title=":bangbang: **__AUFSTELLUNG__** :bangbang:",
        description=f"## *Es herrscht Reaktions- & Abmeldungspflicht! *\n\n"
                    f"### **Uhrzeit:** __{uhrzeit}__\n"
                    f"### **Datum:** __{heute}__\n"
                    f"{plan_display}\n\n"
                    f"**__Bitte reagieren:__**\n"
                    f":white_check_mark: **Ja, ich bin da.**\n"
                    f":x: **Nein, ich kann nicht** (Grund im Abmeldungschannel angeben)\n"
                    f":hourglass: **Verspätet** (Dauer im Abmeldungschannel angeben)",
        color=EMBED_COLOR
    )
    embed.set_thumbnail(url=LOOTDROP_IMAGE_URL)  # Sicherstellen, dass das gleiche Bild genutzt wird

    message = await channel.send(mention_text, embed=embed)
    
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    await message.add_reaction("⌛")


    nicht_reagiert = [name for id, name in alle_gucci_member]
    embed.add_field(name="✅ Ja (0)", value="—", inline=True)
    embed.add_field(name="❌ Nein (0)", value="—", inline=True)
    embed.add_field(name="⌛ Verspätet (0)", value="—", inline=True)
    embed.add_field(name=f"❓ Nicht reagiert ({len(nicht_reagiert)})", value="\n".join(nicht_reagiert) if nicht_reagiert else "—", inline=True)
    await message.edit(embed=embed)

    global letzte_aufstellung
    letzte_aufstellung = message

    aufstellung_time = datetime.datetime.strptime(uhrzeit, "%H:%M").replace(
        year=datetime.datetime.now().year,
        month=datetime.datetime.now().month,
        day=datetime.datetime.now().day,
        tzinfo=TIMEZONE
    )
    now = datetime.datetime.now(TIMEZONE)

    # Erinnerung 30 Minuten vorher
    reminder_time = (aufstellung_time - datetime.timedelta(minutes=30))
    reminder_delay = (reminder_time - now).total_seconds()
    if reminder_delay > 0:
        asyncio.create_task(poste_aufstellungs_erinnerung_nach_delay(reminder_delay, channel, uhrzeit))

async def poste_aufstellungs_erinnerung_nach_delay(delay, channel, uhrzeit):
    await asyncio.sleep(delay)

    role = discord.utils.get(channel.guild.roles, name=MENTION_ROLE)
    mention_text = role.mention if role else ""
    heute = datetime.datetime.now().strftime("%d.%m.%Y")

    embed = discord.Embed(
        title="⏰ **ERINNERUNG: Aufstellung bald!**",
        description=f"🔔 **Die Aufstellung beginnt bald!**\n"
                    f"🕒 **Uhrzeit:** {uhrzeit} Uhr\n"
                    f"📅 **Datum:** {heute}\n\n"
                    f"**Bitte alle pünktlich erscheinen!**",
        color=EMBED_COLOR,
        timestamp=datetime.datetime.now()
    )
    embed.set_footer(text="Automatische Erinnerung - made by izzyy.gg")

    await channel.send(f"{mention_text}", embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    await update_aufstellung_embed(payload.message_id, payload.guild_id)

@bot.event
async def on_raw_reaction_remove(payload):
    await update_aufstellung_embed(payload.message_id, payload.guild_id)


async def update_aufstellung_embed(message_id, guild_id):
    if letzte_aufstellung is None or message_id != letzte_aufstellung.id:
        return

    guild = bot.get_guild(guild_id)
    channel = bot.get_channel(AUFSTELLUNG_CHANNEL_ID)
    message = await channel.fetch_message(message_id)

    ja, nein, verspaetet = [], [], []

    reagiert_set = set()

    for reaction in message.reactions:
        async for user in reaction.users():
            if user.bot:
                continue
            member = guild.get_member(user.id)
            full_name = member.display_name if member else user.name
            reagiert_set.add(full_name)

            if reaction.emoji == "✅":
                ja.append(full_name)
            elif reaction.emoji == "❌":
                nein.append(full_name)
            elif reaction.emoji == "⌛":
                verspaetet.append(full_name)

    # ✅ NEU: Nicht reagiert berechnen
    global alle_gucci_member
    reagiert = set(ja + nein + verspaetet)
    alle_ids_dict = {name: id for id, name in alle_gucci_member}
    nicht_reagiert = [name for id, name in alle_gucci_member if name not in reagiert_set]

    embed = message.embeds[0]
    embed.clear_fields()

    embed.add_field(name=f"✅ Ja ({len(ja)})", value="\n".join(ja) if ja else "—", inline=True)
    embed.add_field(name=f"❌ Nein ({len(nein)})", value="\n".join(nein) if nein else "—", inline=True)
    embed.add_field(name=f"⌛ Verspätet ({len(verspaetet)})", value="\n".join(verspaetet) if verspaetet else "—", inline=True)
    embed.add_field(name=f"❓ Nicht reagiert ({len(nicht_reagiert)})", value="\n".join(nicht_reagiert) if nicht_reagiert else "—", inline=True)

    await message.edit(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot ist gestartet als {bot.user}")
    check_lootdrop_votes.start() 
    check_gangwar_reminders.start()
 
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
keep_alive()
bot.run(token)
