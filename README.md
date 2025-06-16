#Bot do discord

#instrução de instalação

Para instalar o bot, deve-se entrar no site de desenvolvimento do discord, https://discord.com/developers/applications, logar com a conta do discord e clicar em New Application, dar um nome, clicar em Bot e em seguida Reset Token. Isso gerará um token que serve para rodar o bot com o python. Após gerar o token, copie-o e crie um arquivo .env no projeto e escreva:
DISCORD_TOKEN= (TOKEN QUE VOCÊ GEROU SEM OS PARÊNTESES)
Em seguida, no site de desenvolvimento ainda na opção bot, você deve marcar as opções PUBLIC BOT, PRESENCE INTENT, SERVER MEMBER INTENT e MESSAGE CONTENT INTENT. Por fim, para adicionar o bot a algum servidor, você deve ir em installation e copiar o link de Install Link e pesquisar no navegador, após isso basta seguir as instruções no navegador.

#instrução para rodar

Você deve ter o docker instalado na sua máquina, você deve abrir o docker desktop e em seguida no terminal, você deve utilizar os comandos:

docker build -t <nome que você escolher para o container sem <>> .

O comando acima cria o container da aplicação, para rodar o container utilize:

docker run <nome que você escolheu para o container sem <>>
