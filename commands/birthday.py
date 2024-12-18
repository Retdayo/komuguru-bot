import discord
from discord.ext import commands, tasks
from discord.ui import Modal, InputText, Button, View
from datetime import datetime, timedelta
import pytz
from utils.file_operations import load_data, save_data
import traceback

BIRTHDAYS_FILE = "birthdays.json"
SETTINGS_FILE = "settings.json"

# 誕生日登録用モーダル
class BirthdayModal(Modal):
    def __init__(self):
        super().__init__(title="誕生日登録")
        self.add_item(InputText(label="誕生日 (月)", placeholder="例: 01"))
        self.add_item(InputText(label="誕生日 (日)", placeholder="例: 15"))
        self.add_item(InputText(label="生まれた年 (任意)", placeholder="例: 2000", required=False))

    async def callback(self, interaction: discord.Interaction):
        try:
            month = self.children[0].value.zfill(2)  # 月を2桁に揃える
            day = self.children[1].value.zfill(2)  # 日を2桁に揃える
            year = self.children[2].value if self.children[2].value else "不明"

            # 誕生日データを保存
            user_id = str(interaction.user.id)
            birthdays = load_data(BIRTHDAYS_FILE)
            birthdays[user_id] = {
                "name": interaction.user.name,
                "month": month,
                "day": day,
                "year": year
            }
            save_data(BIRTHDAYS_FILE, birthdays)

            # Embedで情報を送信
            embed = discord.Embed(title="新しい誕生日登録", color=discord.Color.green())
            embed.add_field(name="ユーザー", value=interaction.user.mention, inline=False)
            embed.add_field(name="誕生日", value=f"{month}月{day}日", inline=True)
            embed.add_field(name="生まれた年", value=year, inline=True)

            settings = load_data(SETTINGS_FILE)
            channel_id = settings.get(str(interaction.guild_id), {}).get("birthday_channel")
            if channel_id:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

            # 誕生日が今日であれば通知を送信
            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst)
            today_str = now.strftime("%m-%d")
            if f"{month}-{day}" == today_str:
                await channel.send(f"🎉 お誕生日おめでとうございます, {interaction.user.mention}！ 🎂")

            await interaction.response.send_message("誕生日を登録しました！", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

# 非Discordユーザー用の誕生日登録モーダル
class BirthdayNonUserModal(Modal):
    def __init__(self):
        super().__init__(title="非Discordユーザーの誕生日登録")
        self.add_item(InputText(label="名前", placeholder="例: 太郎"))
        self.add_item(InputText(label="誕生日 (月)", placeholder="例: 01"))
        self.add_item(InputText(label="誕生日 (日)", placeholder="例: 15"))
        self.add_item(InputText(label="生まれた年 (任意)", placeholder="例: 2000", required=False))

    async def callback(self, interaction: discord.Interaction):
        try:
            name = self.children[0].value
            month = self.children[1].value.zfill(2)
            day = self.children[2].value.zfill(2)
            year = self.children[3].value if self.children[3].value else "不明"

            # 誕生日データを保存（DiscordユーザーIDの代わりに名前をIDとして使用）
            birthdays = load_data(BIRTHDAYS_FILE)
            unique_id = f"non_user_{name}"  # 非Discordユーザーには名前をIDとして使用
            birthdays[unique_id] = {
                "name": name,
                "month": month,
                "day": day,
                "year": year
            }
            save_data(BIRTHDAYS_FILE, birthdays)

            # Embedで情報を送信
            embed = discord.Embed(title="新しい誕生日登録", color=discord.Color.green())
            embed.add_field(name="名前", value=name, inline=False)
            embed.add_field(name="誕生日", value=f"{month}月{day}日", inline=True)
            embed.add_field(name="生まれた年", value=year, inline=True)

            settings = load_data(SETTINGS_FILE)
            channel_id = settings.get(str(interaction.guild_id), {}).get("birthday_channel")
            if channel_id:
                channel = interaction.guild.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

            # 誕生日が今日であれば通知を送信
            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(jst)
            today_str = now.strftime("%m-%d")
            if f"{month}-{day}" == today_str:
                await channel.send(f"🎉 {name}さん、お誕生日おめでとうございます！ 🎂")

            await interaction.response.send_message("誕生日を登録しました！", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

# 誕生日登録ビュー (両方のボタンを一緒に追加)
# 誕生日登録ビュー (両方のボタンを一緒に追加)
class BirthdayView(View):
    def __init__(self):
        super().__init__(timeout=None)  # タイムアウトを無効化

    @discord.ui.button(label="誕生日を登録", style=discord.ButtonStyle.primary, custom_id="register_user_birthday_button_2")
    async def register_user_birthday_button(self, button: Button, interaction: discord.Interaction):
        modal = BirthdayModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="非Discordユーザーの誕生日を登録", style=discord.ButtonStyle.primary, custom_id="register_non_user_birthday_button_2")
    async def register_non_user_birthday_button(self, button: Button, interaction: discord.Interaction):
        modal = BirthdayNonUserModal()
        await interaction.response.send_modal(modal)

class BirthdayManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start()

    @commands.slash_command(name="register_birthday", description="誕生日登録ボタンを送信します")
    async def register_birthday(self, ctx):
        """誕生日登録ボタンと非Discordユーザーの誕生日登録ボタンを同じメッセージで送信"""
        view = BirthdayView()  # 誕生日登録ボタンと非Discordユーザー用ボタンの両方を含むビュー

        # メッセージと一緒にボタンを送信
        await ctx.respond(
            "以下のボタンをクリックして誕生日を登録してください！",
            view=view  # 両方のボタンを同じビューに追加して送信
        )

    @commands.slash_command(name="set_birthday_channel", description="誕生日通知チャンネルを設定します")
    @commands.has_permissions(administrator=True)
    async def set_birthday_channel(self, ctx, channel: discord.TextChannel):
        """誕生日通知用のチャンネルを設定"""
        try:
            settings = load_data(SETTINGS_FILE)
            if str(ctx.guild_id) not in settings:
                settings[str(ctx.guild_id)] = {}
            settings[str(ctx.guild_id)]["birthday_channel"] = channel.id
            save_data(SETTINGS_FILE, settings)
            await ctx.respond(f"誕生日通知チャンネルを {channel.mention} に設定しました！", ephemeral=True)

        except Exception as e:
            await ctx.respond("予期しないエラーが発生しました。詳細はログを確認してください。", ephemeral=True)
            print(f"Error occurred: {str(e)}")
            traceback.print_exc()

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """毎日誕生日をチェックして通知 (日本時間)"""
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst)
        today_str = now.strftime("%m-%d")
        birthdays = load_data(BIRTHDAYS_FILE)

        for guild in self.bot.guilds:
            settings = load_data(SETTINGS_FILE)
            channel_id = settings.get(str(guild.id), {}).get("birthday_channel")
            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            for user_id, data in birthdays.items():
                if f"{data['month']}-{data['day']}" == today_str:
                    if "non_user_" in user_id:
                        await channel.send(f"🎉 {data['name']}さん、お誕生日おめでとうございます！ 🎂")
                    else:
                        user = guild.get_member(int(user_id))
                        if user:
                            await channel.send(f"🎉 お誕生日おめでとうございます, {user.mention}！ 🎂")

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        # 日本時間での次の00:00まで待機
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst)
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await discord.utils.sleep_until(next_midnight)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(BirthdayView())  # 誕生日用ビューを登録

def setup(bot):
    bot.add_cog(BirthdayManager(bot))
