import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import json
import random
import string
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000")
SECRET = os.getenv("SERVER_SECRET", "changeme123")
ALLOWED_ROLE_IDS = {1517444647067189290, 1518460266189295756}
PENDING_ROLE_IDS = {1517436221930868788, 1517436223009067018, 1517436225622114335, 1517436227031138387}
SETCUSTOM_USER_IDS = {1298387865457266820, 1512838374803636236}
PENDING_CHANNEL_ID = 1517436384665665617
GUILD_ID = 1517435995975585862
VERIFIED_ROLE_NAME = "Verified"
VERIFY_FILE = "verified_users.json"
LOG_WEBHOOK = "https://discord.com/api/webhooks/1520535522647474266/U0PoN4ab9r_c__QnxvmVBwfVB_etHxHJP8P4RLL_D3uRSIRFpr1-O-trhcZwpZuCN6zR"
BOT_NAME = "South Bronx"

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Verified DB ---
def load_verified():
    if not os.path.exists(VERIFY_FILE):
        return {}
    with open(VERIFY_FILE, "r") as f:
        return json.load(f)

def save_verified(data):
    with open(VERIFY_FILE, "w") as f:
        json.dump(data, f, indent=2)

pending_verifications = {}  # discord_id -> {code, roblox_id, roblox_name}


def has_permission(interaction: discord.Interaction) -> bool:
    return any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles)

def has_pending_permission(interaction: discord.Interaction) -> bool:
    return any(r.id in PENDING_ROLE_IDS for r in interaction.user.roles)


async def resolve_userid(userid: str) -> tuple[str, str]:
    """If userid is a username (not all digits), look up the real ID. Returns (userid, username)."""
    if userid.isdigit():
        # Already an ID, fetch username
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://users.roblox.com/v1/users/{userid}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return userid, data.get("name", userid)
        return userid, userid
    else:
        # It's a username, fetch the ID
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [userid], "excludeBannedUsers": False}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        user = data["data"][0]
                        return str(user["id"]), user["name"]
        return None, None


async def push(data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SERVER_URL}/push",
            json=data,
            headers={"x-secret": SECRET}
        ) as resp:
            return resp.status, await resp.json()


@bot.tree.command(name="setcustom", description="Set a custom display name for a Roblox user")
@app_commands.describe(userid="Roblox user ID or username", custom_name="The custom name to display (emojis allowed)")
async def setcustom(interaction: discord.Interaction, userid: str, custom_name: str):
    if not (has_permission(interaction) or interaction.user.id in SETCUSTOM_USER_IDS):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    uid, uname = await resolve_userid(userid)
    if not uid:
        await interaction.followup.send(f"❌ Could not find Roblox user `{userid}`")
        return
    status, body = await push({"type": "CustomName", "userid": uid, "value": custom_name})
    if status == 200:
        await interaction.followup.send(f"✅ Set custom name for `{uname}` (`{uid}`) → **{custom_name}**")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="settag", description="Set a custom tag for a Roblox user")
@app_commands.describe(userid="Roblox user ID or username", tag="Tag text (e.g. Founder)", r="Red 0-255", g="Green 0-255", b="Blue 0-255")
async def settag(interaction: discord.Interaction, userid: str, tag: str, r: int, g: int, b: int):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    uid, uname = await resolve_userid(userid)
    if not uid:
        await interaction.followup.send(f"❌ Could not find Roblox user `{userid}`")
        return
    status, body = await push({"type": "UserTag", "userid": uid, "tag": tag, "r": r, "g": g, "b": b})
    if status == 200:
        await interaction.followup.send(f"✅ Set tag for `{uname}` (`{uid}`) → **{tag}** RGB({r},{g},{b})")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="setranktag", description="Set a custom rank tag color for a Roblox user")
@app_commands.describe(userid="Roblox user ID or username", r="Red 0-255", g="Green 0-255", b="Blue 0-255")
async def setranktag(interaction: discord.Interaction, userid: str, r: int, g: int, b: int):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    uid, uname = await resolve_userid(userid)
    if not uid:
        await interaction.followup.send(f"❌ Could not find Roblox user `{userid}`")
        return
    status, body = await push({"type": "RankTagColor", "userid": uid, "r": r, "g": g, "b": b})
    if status == 200:
        await interaction.followup.send(f"✅ Set rank color for `{uname}` (`{uid}`) → RGB({r},{g},{b})")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="setusername", description="Set a custom rank username for a Roblox user")
@app_commands.describe(userid="Roblox user ID or username", username="The custom username")
async def setusername(interaction: discord.Interaction, userid: str, username: str):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    uid, uname = await resolve_userid(userid)
    if not uid:
        await interaction.followup.send(f"❌ Could not find Roblox user `{userid}`")
        return
    status, body = await push({"type": "CustomUsername", "userid": uid, "value": username})
    if status == 200:
        await interaction.followup.send(f"✅ Set username for `{uname}` (`{uid}`) → **{username}**")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="removecustom", description="Remove all customs for a Roblox user")
@app_commands.describe(userid="Roblox user ID or username")
async def removecustom(interaction: discord.Interaction, userid: str):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    uid, uname = await resolve_userid(userid)
    if not uid:
        await interaction.followup.send(f"❌ Could not find Roblox user `{userid}`")
        return
    status, body = await push({"type": "Remove", "userid": uid})
    if status == 200:
        await interaction.followup.send(f"✅ Removed all customs for `{uname}` (`{uid}`)")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="pending", description="Submit a custom name for approval")
@app_commands.describe(userid="Roblox user ID or username", custom_name="The custom name to request")
async def pending(interaction: discord.Interaction, userid: str, custom_name: str):
    if not has_pending_permission(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    uid, uname = await resolve_userid(userid)
    if not uid:
        await interaction.followup.send(f"❌ Could not find Roblox user `{userid}`")
        return

    channel = bot.get_channel(PENDING_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("❌ Pending channel not found.")
        return

    embed = discord.Embed(title="📋 Pending Custom Name", color=0xffcc00)
    embed.add_field(name="Submitted By", value=interaction.user.mention, inline=False)
    embed.add_field(name="Roblox Username", value=f"`{uname}`", inline=True)
    embed.add_field(name="Roblox User ID", value=f"`{uid}`", inline=True)
    embed.add_field(name="Custom Name", value=f"**{custom_name}**", inline=False)
    embed.set_footer(text="Use /setcustom to approve")

    await channel.send(embed=embed)
    await interaction.followup.send(f"✅ Pending request sent for `{uname}` (`{uid}`) → **{custom_name}**")


@bot.tree.command(name="complete", description="Apply all pending customs, purge channel, and notify restart")
async def complete(interaction: discord.Interaction):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
        return

    await interaction.response.defer()

    channel = bot.get_channel(PENDING_CHANNEL_ID)
    if not channel:
        await interaction.followup.send("❌ Pending channel not found.")
        return

    # Collect all pending embeds sent by the bot
    applied = []
    failed = []

    async for message in channel.history(limit=200):
        if message.author.id != bot.user.id:
            continue
        if not message.embeds:
            continue
        embed = message.embeds[0]
        if embed.title != "📋 Pending Custom Name":
            continue

        # Extract fields from embed
        uid = None
        custom_name = None
        for field in embed.fields:
            if field.name == "Roblox User ID":
                uid = field.value.strip("`")
            if field.name == "Custom Name":
                custom_name = field.value.strip("**")

        if uid and custom_name:
            status, body = await push({"type": "CustomName", "userid": uid, "value": custom_name})
            if status == 200:
                applied.append(f"`{uid}` → **{custom_name}**")
            else:
                failed.append(f"`{uid}` → {body}")

    # Purge the pending channel
    await channel.purge(limit=500)

    # Send completion embed
    done_embed = discord.Embed(
        title="✅ Customs Complete",
        description=f"**{len(applied)}** done! You should have your custom\n\nCompleted by: {interaction.user.mention}",
        color=0x00ff88
    )
    if applied:
        done_embed.add_field(name="Applied", value="\n".join(applied[:20]), inline=False)
    if failed:
        done_embed.add_field(name="❌ Failed", value="\n".join(failed[:10]), inline=False)
    done_embed.set_footer(text="SBPB Datastore")

    await channel.send(embed=done_embed)
    await interaction.followup.send(f"✅ Done — applied {len(applied)} custom(s) and purged pending channel.", ephemeral=True)


@bot.tree.command(name="setgrouptag", description="Set a tag for a Roblox group")
@app_commands.describe(group_id="Roblox Group ID", tag="Tag text (e.g. OGZ)", r="Red 0-255", g="Green 0-255", b="Blue 0-255")
async def setgrouptag(interaction: discord.Interaction, group_id: str, tag: str, r: int, g: int, b: int):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    status, body = await push({"type": "GroupTag", "userid": group_id, "tag": tag, "r": r, "g": g, "b": b})
    if status == 200:
        await interaction.followup.send(f"✅ Set group tag for group `{group_id}` → **{tag}** RGB({r},{g},{b})")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="removegrouptag", description="Remove a group tag by Roblox Group ID")
@app_commands.describe(group_id="Roblox Group ID")
async def removegrouptag(interaction: discord.Interaction, group_id: str):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return
    await interaction.response.defer()
    status, body = await push({"type": "RemoveGroup", "userid": group_id})
    if status == 200:
        await interaction.followup.send(f"✅ Removed group tag for group `{group_id}`")
    else:
        await interaction.followup.send(f"❌ Failed: {body}")


@bot.tree.command(name="verify", description="Link your Discord to your Roblox account")
@app_commands.describe(username="Your Roblox username")
async def verify(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)

    uid, uname = await resolve_userid(username)
    if not uid:
        await interaction.followup.send("❌ Could not find that Roblox username.")
        return

    # Check if already verified
    verified = load_verified()
    discord_id = str(interaction.user.id)
    if discord_id in verified:
        rb = verified[discord_id]
        await interaction.followup.send(f"⚠️ You're already verified as **{rb['roblox_name']}**. Use `/unverify` first to re-link.")
        return

    # Generate code
    code = "SBFT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    pending_verifications[discord_id] = {"code": code, "roblox_id": uid, "roblox_name": uname}

    embed = discord.Embed(title="🔐 Roblox Verification", color=0x5865f2)
    embed.add_field(name="Step 1", value=f"Go to your Roblox profile: [roblox.com/users/{uid}/profile](https://www.roblox.com/users/{uid}/profile)", inline=False)
    embed.add_field(name="Step 2", value=f"Put this code **anywhere** in your bio/description:\n```{code}```", inline=False)
    embed.add_field(name="Step 3", value="Run `/checkverify` to confirm", inline=False)
    embed.set_footer(text="Code expires in 10 minutes")
    await interaction.followup.send(embed=embed)

    # Auto-expire after 10 min
    await asyncio.sleep(600)
    if discord_id in pending_verifications and pending_verifications[discord_id]["code"] == code:
        del pending_verifications[discord_id]


@bot.tree.command(name="checkverify", description="Check your bio and complete verification")
async def checkverify(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    discord_id = str(interaction.user.id)
    if discord_id not in pending_verifications:
        await interaction.followup.send("❌ No pending verification. Run `/verify` first.")
        return

    pending = pending_verifications[discord_id]
    code = pending["code"]
    uid = pending["roblox_id"]
    uname = pending["roblox_name"]

    # Fetch Roblox profile description
    bio = ""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://users.roblox.com/v1/users/{uid}") as resp:
            if resp.status == 200:
                data = await resp.json()
                bio = data.get("description", "")

    if code not in bio:
        await interaction.followup.send(f"❌ Code `{code}` not found in your Roblox bio yet. Make sure you saved your profile!")
        return

    # Verified — save and assign role
    verified = load_verified()
    verified[discord_id] = {"roblox_id": uid, "roblox_name": uname}
    save_verified(verified)
    del pending_verifications[discord_id]

    # Assign Verified role
    guild = interaction.guild
    role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
    if role:
        try:
            await interaction.user.add_roles(role)
        except discord.Forbidden:
            pass

    # Rename to Roblox username
    try:
        await interaction.user.edit(nick=uname)
    except discord.Forbidden:
        pass

    embed = discord.Embed(title="✅ Verified!", color=0x00ff88)
    embed.add_field(name="Roblox Account", value=f"**{uname}** (`{uid}`)", inline=False)
    embed.set_footer(text="You can now remove the code from your bio")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="whois", description="Look up the Roblox account linked to a Discord user")
@app_commands.describe(member="The Discord user to look up")
async def whois(interaction: discord.Interaction, member: discord.Member):
    if not has_permission(interaction):
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    verified = load_verified()
    entry = verified.get(str(member.id))
    if not entry:
        await interaction.response.send_message(f"❌ **{member.display_name}** is not verified.", ephemeral=True)
        return

    embed = discord.Embed(title="🔍 Whois", color=0x5865f2)
    embed.add_field(name="Discord", value=member.mention, inline=True)
    embed.add_field(name="Roblox", value=f"**{entry['roblox_name']}** (`{entry['roblox_id']}`)", inline=True)
    embed.add_field(name="Profile", value=f"[View Profile](https://www.roblox.com/users/{entry['roblox_id']}/profile)", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="unverify", description="Unlink your Discord from your Roblox account")
async def unverify(interaction: discord.Interaction):
    verified = load_verified()
    discord_id = str(interaction.user.id)
    if discord_id not in verified:
        await interaction.response.send_message("❌ You're not verified.", ephemeral=True)
        return

    rb = verified.pop(discord_id)
    save_verified(verified)

    # Remove Verified role
    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
    if role and role in interaction.user.roles:
        try:
            await interaction.user.remove_roles(role)
        except discord.Forbidden:
            pass

    await interaction.response.send_message(f"✅ Unlinked from **{rb['roblox_name']}**.", ephemeral=True)


async def log_command(interaction: discord.Interaction, command_name: str):
    try:
        opts = []
        if interaction.data and interaction.data.get("options"):
            for o in interaction.data["options"]:
                if "value" in o:
                    opts.append(f"**{o['name']}:** {o['value']}")
        args_text = "\n".join(opts) if opts else "none"
        where = f"#{interaction.channel}" if interaction.channel else "DM"
        embed = {
            "title": "📝 Command Used",
            "color": 0x5865f2,
            "fields": [
                {"name": "Bot", "value": BOT_NAME, "inline": True},
                {"name": "Command", "value": f"/{command_name}", "inline": True},
                {"name": "User", "value": f"{interaction.user} (`{interaction.user.id}`)", "inline": False},
                {"name": "Arguments", "value": args_text, "inline": False},
                {"name": "Channel", "value": where, "inline": True},
            ],
        }
        async with aiohttp.ClientSession() as session:
            await session.post(LOG_WEBHOOK, json={"embeds": [embed]})
    except Exception as e:
        print(f"[log] failed: {e}")


@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command):
    await log_command(interaction, command.name)


async def log_error(interaction: discord.Interaction, error):
    try:
        cmd = interaction.command.name if interaction.command else "unknown"
        embed = {
            "title": "⚠️ Command Failed",
            "color": 0xff5555,
            "fields": [
                {"name": "Bot", "value": BOT_NAME, "inline": True},
                {"name": "Command", "value": f"/{cmd}", "inline": True},
                {"name": "User", "value": f"{interaction.user} (`{interaction.user.id}`)", "inline": False},
                {"name": "Error", "value": str(error)[:1000], "inline": False},
            ],
        }
        async with aiohttp.ClientSession() as session:
            await session.post(LOG_WEBHOOK, json={"embeds": [embed]})
    except Exception as e:
        print(f"[log error] failed: {e}")


@bot.tree.error
async def on_tree_error(interaction: discord.Interaction, error):
    await log_error(interaction, error)
    try:
        if interaction.response.is_done():
            await interaction.followup.send("❌ Something went wrong.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Something went wrong.", ephemeral=True)
    except Exception:
        pass


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"✅ Bot ready as {bot.user} — synced {len(synced)} commands globally")


bot.run(TOKEN)
