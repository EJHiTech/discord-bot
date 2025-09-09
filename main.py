import os
import discord as disc
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
import asyncpg
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

token = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))      # ID do servidor
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID do canal onde a mensagem será enviada

intents = disc.Intents.default()
intents.typing = True
intents.messages = True
intents.presences = False
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
pontos = {}

# inicializar o scheduler
scheduler = AsyncIOScheduler()

dias_map = {
    "SEG": "mon",
    "TER": "tue",
    "QUA": "wed",
    "QUI": "thu",
    "SEX": "fri",
    "SAB": "sat",
    "DOM": "sun",
}

# Lista para guardar os agendamentos
agendamentos = []

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

    # Só iniciar o scheduler depois que o bot estiver pronto
    if not scheduler.running:
        scheduler.start()

@bot.command(name="agendar")
async def agendar(ctx, mensagem: str, horario: str, dias: str, *emojis):
    """
    Exemplo:
    !agendar "Texto da msg" 12:00 SEG,TER,QUA 1️⃣ 2️⃣ 3️⃣
    """

    try:
        hora, minuto = map(int, horario.split(":"))
    except ValueError:
        await ctx.send("❌ Formato de horário inválido. Use: HH:MM (ex: 12:30)")
        return

    dias_semana = []
    for d in dias.split(","):
        d = d.strip().upper()
        if d not in dias_map:
            await ctx.send("❌ Dia inválido. Use SEG,TER,QUA,QUI,SEX,SAB,DOM")
            return
        dias_semana.append(dias_map[d])

    canal_id = ctx.channel.id

    async def job():
        canal = bot.get_channel(canal_id)
        if canal:
            msg = await canal.send(f"@everyone {mensagem}")
            for emoji in emojis:
                await msg.add_reaction(emoji)

    # registrar no scheduler
    scheduler.add_job(
        job,
        "cron",
        day_of_week=",".join(dias_semana),
        hour=hora,
        minute=minuto,
    )

    await ctx.send(f"✅ Agendamento criado: {mensagem} às {horario} nos dias {dias}")


@bot.command(name="listar_agendamentos")
async def listar_agendamentos(ctx):
    if not agendamentos:
        await ctx.send("Nenhum agendamento registrado.")
        return

    texto = "**Agendamentos:**\n"
    for a in agendamentos:
        texto += f"- {a['mensagem']} em {a['horario']} (repetição: {a['repeticao']})\n"

    await ctx.send(texto)


@bot.command(name="cancelar_agendamento")
async def cancelar_agendamento(ctx, job_id: str):
    if job_id not in jobs_registrados:
        await ctx.send("❌ ID de agendamento não encontrado.")
        return

    scheduler.remove_job(job_id)
    removido = jobs_registrados.pop(job_id)
    await ctx.send(
        f"🗑️ Agendamento removido: {removido['mensagem']} ({removido['dias']} às {removido['horario']})"
    )


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
