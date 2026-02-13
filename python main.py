import os 
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime,timedelta
from myserver import server_on

GUILD_ID = 1430038504301264980  # ไอดีเซิร์ฟ
TOKEN=os.getenv("tokenbot")
print("TOKEN =", TOKEN)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="$", intents=intents)

#============ตั้งค่าหลัก============

#=============คำสั้งแอดมิน==========
admin_channels = {}
@bot.event

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot online + global slash synced")

    
@bot.tree.command(
    name="set_admin_channel",
    description="ตั้งห้องแอดมิน",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def set_admin_channel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    admin_channels[interaction.guild.id] = channel.id
    await interaction.response.send_message(
        f"ตั้งห้องแอดมินเป็น {channel.mention} แล้ว",
        ephemeral=True
    )

@set_admin_channel.error
async def set_admin_channel_error(
    interaction: discord.Interaction,
    error
):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "คำสั่งนี้ใช้ได้เฉพาะแอดมินเท่านั้น",
            ephemeral=True
        )


#================ลบข้อความ=================  

@bot.tree.command(
    name= "clear",
    description="ล้างช่องข้อความ",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def clear(
    interaction: discord.Interaction,
    amount:int
):
    await interaction.response.defer(ephemeral=True)
    deleted=await interaction.channel.purge(limit=amount)
    await interaction.followup.send(
        f"ลบข้อความไปแล้ว{len(deleted)} ข้อความ",
        ephemeral=True
    )



#================สร้างช่อง======================
@bot.tree.command(
    name="create_channel",
    description="สร้างห้องใหม่ในหมวดหมู่ที่เลือก",
)
@app_commands.checks.has_permissions(manage_channels=True)
async def create_channel(
    interaction: discord.Interaction,
    name: str,
    category: discord.CategoryChannel
):
    guild = interaction.guild

    # สร้างห้อง text channel ใน category ที่เลือก
    channel = await guild.create_text_channel(
        name=name,
        category=category
    )

    await interaction.response.send_message(
        f"สร้างห้อง {channel.mention} ในหมวด {category.name} เรียบร้อยแล้ว",
        ephemeral=True
    )



#========= แอดมินแก้ฟอร์ม ================
forms={}
forms[GUILD_ID] = [
    "ชื่อตัวละคร",
    "อายุ",
    "เผ่า",
    "ส่วนสูง",
    "ประวัติ"
]
@bot.tree.command(
    name="set_form",
    description="ตั้งหัวข้อฟอร์ม",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def set_form(
    interaction:discord.Interaction,
  field1:str,
  field2:str,
  field3:str,
  field4:str,
  field5:str
):
 forms[interaction.guild.id] = [field1, field2, field3,field4,field5]


 await interaction.response.send_message(
        "ตั้งค่าฟอร์มเรียบร้อยแล้ว",
        ephemeral=True
 )


#========== set role ================
roleplay_role={}
@bot.tree.command(
    name="set_role",
    description="ตั้ง Role ที่จะให้หลังกรอกฟอร์ม (แอดมินเท่านั้น)",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def set_role(
    interaction: discord.Interaction,
    role: discord.Role
):
    roleplay_role[interaction.guild.id] = role.id

    await interaction.response.send_message(
        f"✅ ตั้ง Role เป็น {role.mention} เรียบร้อยแล้ว",
        ephemeral=True
    )

 #========= moduel from ====================
class RoleplayFormModal(discord.ui.Modal):
    def __init__(self, fields: list[str]):
        super().__init__(title="Roleplay Form")
        self.fields = fields
        self.inputs: list[discord.ui.TextInput] = []

        # Discord จำกัด 5 ช่อง
        for field in fields[:5]:
            input_box = discord.ui.TextInput(
                label=field,
                style=discord.TextStyle.short,
                required=True
            )
            self.add_item(input_box)
            self.inputs.append(input_box)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        # เช็กว่าเซิร์ฟตั้งห้องแอดมินไว้ไหม
        if guild_id not in admin_channels:
            await interaction.response.send_message(
                "⚠️ ยังไม่ได้ตั้งห้องแอดมินให้แอดมินใช้ /set_admin_channel ก่อน",
                ephemeral=True
            )
            return

        admin_channel = interaction.guild.get_channel(admin_channels[guild_id])

        # สร้าง Embed ส่งให้แอดมิน
        embed = discord.Embed(
            title="📥 ฟอร์มสมัคร Roleplay",
            description=f"ผู้ส่ง: {interaction.user.mention}",
            color=discord.Color.blue()
        )

        for field, inp in zip(self.fields, self.inputs):
            embed.add_field(name=field, value=inp.value, inline=False)

        await admin_channel.send(embed=embed)

    
        await interaction.response.send_message(
            "✅ ส่งฟอร์มให้แอดมินเรียบร้อยแล้ว! ",
            ephemeral=True
             )
       
 #================เปิดฟอร์ม================
@bot.tree.command(
     name= "roleplay_form",
     description="กรอกฟอร์ม",
 )
async def roleplay_form(interaction: discord.Interaction):
    await interaction.response.send_modal(
        RoleplayFormModal(forms[interaction.guild.id])
    )






reaction_roles = {}  
# รูปแบบ:
# { message_id: { "🔥": role_id } }
@bot.tree.command(name="reaction_role", description="สร้างปุ่มกดอีโมจิรับยศ", )
@app_commands.checks.has_permissions(manage_roles=True)
async def reaction_role(
    interaction: discord.Interaction,
    role: discord.Role,
    emoji: str,
    text: str
):
    msg = await interaction.channel.send(
        f"{text}\n\nกด {emoji} เพื่อรับยศ {role.mention}"
    )
    await msg.add_reaction(emoji)

    reaction_roles[msg.id] = {emoji: role.id}

    await interaction.response.send_message(
        "✅ สร้าง Reaction Role เรียบร้อย",
        ephemeral=True
    )
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    if payload.message_id not in reaction_roles:
        return

    emoji = str(payload.emoji)
    guild = bot.get_guild(payload.guild_id)

    role_id = reaction_roles[payload.message_id].get(emoji)
    if role_id is None:
        return

    Role = guild.get_role(role_id)
    try:
     member = await guild.fetch_member(payload.user_id)
    except:
        return
    if Role and member:
        await member.add_roles(Role, reason="Reaction role")
 


server_on()

bot.run(os.getenv("tokenbot"))
