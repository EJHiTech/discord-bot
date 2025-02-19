import discord as disc
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
import asyncpg
import os

load_dotenv(dotenv_path='credentials.env')
token = os.getenv("DISCORD_TOKEN")

intents = disc.Intents.default()
intents.typing = True
intents.messages = True
intents.presences = False
intents.members = True
intents.message_content = True

async def connect_db():
    try:
        bot.db = await asyncpg.create_pool(  # Cria o pool de conexões
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        print("✅ Conectado ao banco de dados com pool de conexões!")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")


if token is None:
    print("Erro: Token não encontrado.")
else:
    print("Token carregado com sucesso!")


bot = commands.Bot(command_prefix="!", intents=intents)
pontos = {}


@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    await connect_db() 


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command(name="adduser")
async def adduser(ctx, username: str):
    try:
        # Usando o pool de conexões
        async with bot.db.acquire() as conn:  # Pega uma conexão do pool
            await conn.execute(
                "INSERT INTO usuarios (username) VALUES ($1)",
                username
            )
            await ctx.send(f"✅ Usuário `{username}` cadastrado com sucesso!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao cadastrar usuário: {e}")



@bot.event
async def on_entry(member):
    try:
        await member.send("Bem vindo.")
    except Exception as e:
        print("DEU ERRADO")


@bot.command(name='entrada')
async def entrada(ctx):
    user = ctx.author
    if user not in pontos:
        pontos[user] = {'entrada': datetime.now(), 'saida': None}
        await ctx.send(f'{user.mention} registrou sua entrada às {pontos[user]["entrada"].strftime("%H:%M:%S")}')
    else:
        await ctx.send(f'{user.mention} já registrou sua entrada às {pontos[user]["entrada"].strftime("%H:%M:%S")}')


@bot.command(name='saida')
async def saida(ctx):
    user = ctx.author
    if user in pontos and pontos[user]['saida'] is None:
        pontos[user]['saida'] = datetime.now()
        await ctx.send(f'{user.mention} registrou sua saída às {pontos[user]["saida"].strftime("%H:%M:%S")}')
    else:
        await ctx.send(f'{user.mention}, você ainda não registrou sua entrada ou já registrou a saída.')


@bot.command(name='relatorio')
async def relatorio(ctx):
    user = ctx.author
    if user in pontos and pontos[user]['saida'] is not None:
        entrada = pontos[user]['entrada']
        saida = pontos[user]['saida']
        horas_trabalhadas = saida - entrada
        await ctx.send(f'{user.mention}, você trabalhou por {horas_trabalhadas} horas.')
    else:
        await ctx.send(f'{user.mention}, o registro está incompleto ou não registrado.')

bot.run(token)
