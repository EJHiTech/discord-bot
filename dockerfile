# Use uma imagem base do Python
FROM python:3.10-slim

# Instalar as dependências necessárias (incluindo python-dotenv, discord.py, etc)
RUN pip install discord.py python-dotenv asyncpg psycopg2-binary

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar os arquivos do projeto para dentro do contêiner
COPY . /app/

# Comando para rodar o bot
CMD ["python", "main.py"]
