import discord as disc
from discord.ext import commands
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncpg
import os

load_dotenv()

token = os.getenv("DISCORD_TOKEN")

intents = disc.Intents.default()
intents.typing = True
intents.messages = True
intents.presences = False
intents.members = True
intents.message_content = True


bot = commands.Bot(command_prefix="!", intents=intents)
pontos = {}
horas_em_call = {}
relatorio_dicionario = {}
nomes_cadastrados = []
canais_coworking = {}


def formatar_hora(horas):
    total_em_segundos = int(horas.total_seconds())
    horas_separadas = total_em_segundos / 3600
    minutos = (total_em_segundos % 60) / 60
    segundos = total_em_segundos % 60
    return horas_separadas, minutos, segundos


@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')



@bot.event
async def on_entry(member):
    try:
        await member.send("Bem vindo.")
    except Exception as e:
        print("DEU ERRADO")

@bot.event
async def on_voice_state_update(member, before, after):
    canal_before = before
    canal_after = after
    if before.channel is None and after.channel:
        print(f"{member.id} entrou no canal {after.channel.id}")
        await entrada_usuario(member, canal_after.channel)
    elif before.channel and after.channel is None:  # Membro saiu do canal
        print(f"{member.id} saiu do canal {before.channel.id}")
        await saida_usuario(member, canal_before.channel)

async def entrada_usuario(member, canal):
    if canal.id not in canais_coworking:
        canais_coworking[canal.id] = {}
    
    membros_canal = canal.members

    if len(membros_canal) < 2:
        return
    
    if not canais_coworking[canal.id]:
        for membro in membros_canal:
            canais_coworking[canal.id][membro.id] = datetime.now()
        
        print("coworking iniciado")
    else:
        canais_coworking[canal.id][member.id] = datetime.now()
        print(f'{member.id} adicionado ao coworking')

async def saida_usuario(member, canal):
    if canal.id not in canais_coworking:
        return
    
    membros_canal = canal.members

    if member.id in canais_coworking[canal.id]:
        hora_inicio_membro = canais_coworking[canal.id][member.id]
        tempo_total = datetime.now() - hora_inicio_membro
        horas, minutos, segundos = formatar_hora(tempo_total)
        await member.send(f'Você esteve em call por {horas:.0f} horas, {minutos:.0f} minutos, {segundos:.0f} segundos')
        del canais_coworking[canal.id][member.id]
    
    if len(membros_canal) < 2:
        for membro in membros_canal:
            if membro.id in canais_coworking[canal.id]:
                hora_inicio_membro = canais_coworking[canal.id][membro.id]
                tempo_total = datetime.now() - hora_inicio_membro
                horas, minutos, segundos = formatar_hora(tempo_total)
                await membro.send(f'Você esteve em call por {horas:.0f} horas, {minutos:.0f} minutos, {segundos:.0f} segundos')
                del canais_coworking[canal.id][membro.id]
        del canais_coworking[canal.id]


@bot.command(name='entrada')
async def entrada(ctx, *args):
    user = ctx.author
    nome = ' '.join(args)
    if not nome in nomes_cadastrados:
        await ctx.send(f'{user.mention}, verifique se você digitou o seu nome corretamente ou registre-se')
        return
    if user not in pontos:
        pontos[user] = {'entrada': datetime.now(), 'saida': None}
        await ctx.send(f'{user.mention} registrou sua entrada às {pontos[user]["entrada"].strftime("%H:%M:%S")}')
    else:
        await ctx.send(f'{user.mention} já registrou sua entrada às {pontos[user]["entrada"].strftime("%H:%M:%S")}')


@bot.command(name='saida')
async def saida(ctx, *args):
    user = ctx.author
    nome = ' '.join(args)
    if not nome in nomes_cadastrados:
        await ctx.send(f'{user.mention}, verifique se você digitou o seu nome corretamente ou registre-se')
        return
    if user in pontos and pontos[user]['saida'] is None:
        entrada = pontos[user]['entrada']
        pontos[user]['saida'] = saida = datetime.now()
        horas_trabalhadas = saida - entrada
        relatorio_dicionario[user] = {'horas' : horas_trabalhadas}
        await ctx.send(f'{user.mention} registrou sua saída às {pontos[user]["saida"].strftime("%H:%M:%S")}')
        del pontos[user]
    else:
        await ctx.send(f'{user.mention}, você ainda não registrou sua entrada ou já registrou a saída.')


@bot.command(name='relatorio')
async def relatorio(ctx, *args):
    user = ctx.author
    nome = ' '.join(args)
    if not nome in nomes_cadastrados:
        await ctx.send(f'{user.mention}, verifique se você digitou o seu nome corretamente ou registre-se')
        return
    if user in relatorio_dicionario:
        dados_usuario = relatorio_dicionario.get(user, {})
        horas, minutos, segundos = formatar_hora(dados_usuario.get('horas', timedelta(0)))
        await ctx.send(f'{user.mention}, você trabalhou por {horas:.0f} horas, {minutos:.0f} minutos e {segundos:.0f} segundos.')
    else:
        await ctx.send(f'{user.mention}, o registro está incompleto ou não registrado.')


@bot.command(name='registro')
async def registro(ctx, *args):
    user = ctx.author
    nome = ' '.join(args)
    if not nome:
        await ctx.send(f'{user.mention}, você deve adicionar o seu nome')
        return None
    if len(nome) < 2 or len(nome) > 60:
        await ctx.send(f'{user.mention}, nome deve ter de 2 a 60 letras')
        return None
    if nome in nomes_cadastrados:
        await ctx.send(f'{user.mention}, nome já está cadastrado')
        return None
    
    nomes_cadastrados.append(nome)
    await ctx.send(f'{user.mention}, registro feito com sucesso')
    return nome

bot.run(token)
