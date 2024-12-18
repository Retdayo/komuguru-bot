import discord
from discord.ext import commands, tasks
import os
import asyncio
import aiohttp
import traceback

# Botのトークンを環境変数から取得
BOT_TOKEN = 'MTMxNzc3MzcyOTI4MzE3ODUxNg.GJKyyn.1EQDB6zP5gKRwQ7lWY1LiJchc_RrTQSakOHFpk'  # セキュリティのため、トークンは環境変数または外部ファイルから取得することを推奨します。

# エラーログ用のチャンネルIDを設定
ERROR_LOG_CHANNEL_ID = 1282508053471559770  # ここに実際のチャンネルIDを設定してください

# Botのインスタンスを作成
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# グローバル変数としてHTTPセッションを追加
http_session = None

# コマンドをロードする関数
async def load_commands():
    commands_dir = './commands'
    for filename in os.listdir(commands_dir):
        if filename.endswith('.py'):
            try:
                command_name = filename[:-3]
                bot.load_extension(f'commands.{command_name}')
                print(f'コマンドを正常に読み込みました: {filename}')
            except Exception as e:
                print(f'コマンドの読み込みに失敗しました {filename}: {e}')
                await log_error(e, command_name)

# エラーログを保存し、指定チャンネルに送信する関数
async def log_error(error, command_name=None):
    try:
        error_dir = './ERROR'
        if not os.path.exists(error_dir):
            os.makedirs(error_dir)
            print('ディレクトリを作成しました: /ERROR')
        log_filename = os.path.join(error_dir, f'{command_name}_error.log' if command_name else 'error.log')
        with open(log_filename, 'a') as f:
            f.write(f'{str(error)}\n{traceback.format_exc()}\n')
        print(f'エラーをログに記録しました: {log_filename}')

        # エラーを指定のチャンネルに送信
        error_channel = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if error_channel:
            error_message = f"```py\n{traceback.format_exc()}\n```"
            await error_channel.send(error_message)
    except Exception as log_error:
        print(f'エラーの記録に失敗しました: {log_error}')

# コマンド実行時のエラーハンドリング
@bot.event
async def on_command_error(ctx, error):
    await log_error(error, ctx.command.name)
    await ctx.send(f'An error occurred: {error}')

@bot.event
async def on_ready():
    print("Botは正常に起動しました！")
    print(bot.user.name)
    print(bot.user.id)
    print(discord.__version__)
    print('------')
    change_activity.start()
                        
async def get_user_count():
    async with bot.db.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT COUNT(*) FROM users')
            result = await cursor.fetchone()
            return result[0]

@tasks.loop(seconds=40)
async def change_activity():
    await bot.change_presence(activity=discord.Game(name="Help: /help"))
    await asyncio.sleep(10)
    await bot.change_presence(activity=discord.Game(name='制作者: れと'))

CREATOR_ID = 955957505782067291

@bot.slash_command(name="reload", description="コマンドをリロードします")
async def discord_reload_commands(ctx, filename: str = None):
    if ctx.author.id != CREATOR_ID:
        await ctx.respond('このコマンドを実行する権限がありません。', ephemeral=True)
        return

    if filename:
        if filename.endswith('.py'):
            command_name = filename[:-3]
            extension_name = f'commands.{command_name}'
            
            if extension_name in bot.extensions:
                bot.unload_extension(extension_name)
                await ctx.respond(f'コマンドをアンロードしました: {filename}', ephemeral=True)
                
            try:
                bot.load_extension(extension_name)
                await ctx.respond(f'コマンドを再度ロードしました: {filename}', ephemeral=True)
            except Exception as e:
                await ctx.respond(f'コマンドの再ロードに失敗しました {filename}: {e}', ephemeral=True)
                await log_error(e, command_name)
        else:
            await ctx.respond('ファイル名が正しくありません。拡張子は .py である必要があります。', ephemeral=True)
    else:
        for filename in os.listdir('./commands'):
            if filename.endswith('.py'):
                command_name = filename[:-3]
                extension_name = f'commands.{command_name}'
                
                if extension_name in bot.extensions:
                    bot.unload_extension(extension_name)
                    await ctx.respond(f'コマンドをアンロードしました: {filename}', ephemeral=True)
                    
                try:
                    bot.load_extension(extension_name)
                    await ctx.respond(f'コマンドを再度ロードしました: {filename}', ephemeral=True)
                except Exception as e:
                    await ctx.respond(f'コマンドの再ロードに失敗しました {filename}: {e}', ephemeral=True)
                    await log_error(e, command_name)

# メイン関数
async def main():
    async with bot:
        await load_commands()
        await bot.start(BOT_TOKEN)

# Botのシャットダウン処理
async def shutdown():
    await bot.close()

# プログラムを実行
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("シャットダウンしています...")
    asyncio.run(shutdown())
    print("Botは正常に終了しました。")
