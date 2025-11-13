import os
import discord as disc
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
import asyncpg
import asyncio
from datetime import datetime, timedelta, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json

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

jobs_registrados = {}

async def conectar_db():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            user=os.getenv('POSTGRES_USER'),
            database=os.getenv('POSTGRES_DB'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=5432,
            timeout=30
        )
        
        print("✅ Conectado ao banco de dados com sucesso!")
        
    except Exception as e:
        print(f"erro ao conectar com o banco de dados: {e}")

async def cadastrar_tabelas():
    try:
        if db_pool is None:
            print("❌ Pool de conexão não disponível")
            return
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agendamentos(
                    id SERIAL PRIMARY KEY,
                    texto_mensagem TEXT NOT NULL,
                    horario_execucao TIME NOT NULL,
                    dias_execucao TEXT NOT NULL,
                    emotes_reacao TEXT,
                    canal_id BIGINT NOT NULL
                )
            ''')
    except Exception as e:
        print(f'erro ao criar tabelas: {e}')

async def registrar_agendamento(texto_mensagem, horario_execucao, dias_execucao, emotes_reacao, canal_id):
    try:
        if db_pool is None:
            print("❌ Pool de conexão não disponível")
            return None
        async with db_pool.acquire() as conn:
            emotes_json = json.dumps(emotes_reacao) if emotes_reacao else None

            resultado = await conn.fetchrow('''
                INSERT INTO agendamentos(texto_mensagem, horario_execucao, dias_execucao, emotes_reacao, canal_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            ''', texto_mensagem, horario_execucao, dias_execucao, emotes_json, canal_id)
            return resultado['id']
    except Exception as e:
        print(f'Erro ao registrar agendamento: {e}')
        return None

async def carregar_agendamentos():
    try:
        if db_pool is None:
            print("❌ Pool de conexão não disponível")
            return
        async with db_pool.acquire() as conn:
            agendamentos_db = await conn.fetch('''
                SELECT id, texto_mensagem, horario_execucao, dias_execucao, emotes_reacao, canal_id
                FROM agendamentos
            ''')

            for agendamento in agendamentos_db:
                lista_emotes = json.loads(agendamento['emotes_reacao']) if agendamento['emotes_reacao'] else []

                job_id = str(agendamento['id'])

                async def job(mensagem=agendamento['texto_mensagem'], emotes=lista_emotes, canal_id=agendamento['canal_id']):
                    canal = bot.get_channel(canal_id)
                    if canal:
                        mensagem_enviada = await canal.send(f'@everyone {mensagem}')
                        for emoji in emotes:
                            await mensagem_enviada.add_reaction(emoji)
                
                hora = agendamento['horario_execucao'].hour
                minuto = agendamento['horario_execucao'].minute

                scheduler_job = scheduler.add_job(
                    job,
                    'cron',
                    day_of_week=agendamento['dias_execucao'],
                    hour=hora,
                    minute=minuto,
                    id=job_id
                )

                jobs_registrados[job_id] = {
                    'mensagem': agendamento['texto_mensagem'],
                    'horario': agendamento['horario_execucao'].strftime('%H:%M'),
                    'dias': agendamento['dias_execucao'],
                    'emotes': lista_emotes,
                    'canal_id': agendamento['canal_id'],
                    'job': scheduler_job
                }
            
            print(f'{len(agendamentos_db)} agendamentos carregados do banco de dados')
    except Exception as e:
        print(f'erro ao carregar agendamentos do banco de dados: {e}')

async def remover_agendamento_db(agendamento_id):
    try:
        if db_pool is None:
            print("❌ Pool de conexão não disponível")
            return False
        async with db_pool.acquire() as conn:
            await conn.execute('''
                DELETE FROM agendamentos WHERE id = $1
            ''', agendamento_id)

            return True
    except Exception as e:
        print(f'Erro ao remover agendamento do bacno de dados: {e}')
        return False
            

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    
    try:
        await conectar_db()
        await cadastrar_tabelas()
        await carregar_agendamentos()
        # Só iniciar o scheduler depois que o bot estiver pronto
        if not scheduler.running:
            scheduler.start()
            print("✅ Scheduler iniciado!")
            
    except Exception as e:
        print("Erro na inicialização: {e}")

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

    dias_str = ','.join(dias_semana)
    canal_id = ctx.channel.id
    emojis_list = list(emojis)

    horario_time = time(hora, minuto)

    agendamento_id = await registrar_agendamento(
        mensagem,
        horario_time,
        dias_str,
        emojis_list,
        canal_id
    )

    if agendamento_id is None:
        await ctx.send("Erro ao salvar agendamento no banco de dados")
        return
    
    job_id = str(agendamento_id)

    async def job():
        canal = bot.get_channel(canal_id)
        if canal:
            msg = await canal.send(f"@everyone {mensagem}")
            for emoji in emojis_list:
                await msg.add_reaction(emoji)

    # registrar no scheduler
    scheduler_job = scheduler.add_job(
        job,
        "cron",
        day_of_week=dias_str,
        hour=hora,
        minute=minuto,
        id=job_id
    )

    jobs_registrados[job_id] = {
        'mensagem': mensagem,
        'horario': horario,
        'dias': dias,
        'emotes': emojis_list,
        'canal_id': canal_id,
        'job': scheduler_job
    }

    await ctx.send(f"✅ Agendamento criado: {mensagem} às {horario} nos dias {dias} (ID: {job_id})")


@bot.command(name="listar_agendamentos")
async def listar_agendamentos(ctx):
    if not jobs_registrados:
        await ctx.send("Nenhum agendamento registrado.")
        return

    texto = "**Agendamentos:**\n"
    for job_id, agendamento in jobs_registrados.items():
        texto += f"- ID: {job_id} | {agendamento['mensagem']} às {agendamento['horario']} (repetição: {agendamento['dias']})\n"

    await ctx.send(texto)


@bot.command(name="cancelar_agendamento")
async def cancelar_agendamento(ctx, job_id: str):
    if job_id not in jobs_registrados:
        await ctx.send("❌ ID de agendamento não encontrado.")
        return

    scheduler.remove_job(job_id)

    sucesso = await remover_agendamento_db(int(job_id))
    
    if sucesso:
        removido = jobs_registrados.pop(job_id)
        await ctx.send(
            f"🗑️ Agendamento removido: {removido['mensagem']} ({removido['dias']} às {removido['horario']})"
        )
    else:
        await ctx.send('Erro ao remover agendamento do banco de dados')


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
