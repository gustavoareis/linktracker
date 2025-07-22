Este programa é uma aplicação web feita com Flask para rastreamento e gerenciamento de links personalizados.

1. Possui um sistema simples de login (usuário e senha: admin/admin).
2. Permite criar links únicos via API (rota /criar), que são salvos em um arquivo CSV.
3. Quando alguém acessa um link do tipo /rota/<codigo_unico>, o programa verifica se o código existe no CSV, registra o clique (data/hora) em outro CSV e redireciona o usuário para a URL de destino associada.
4. Tem uma rota para listar todos os links existentes (/get_links).
5. Protege as rotas principais exigindo login, exceto as rotas de rastreamento e autenticação.
6. Utiliza arquivos CSV para armazenar os códigos/links e os cliques detalhados.
