O programa é um sistema web feito com Flask para criar, gerenciar e rastrear links personalizados. Ele funciona assim:

1. Login e Logout: Só quem faz login (usuário: admin, senha: admin) pode acessar as funções protegidas.
2. Criação de links rastreáveis: Você pode criar links únicos via API (rota /criar). Cada link tem um código único e um destino.
3. Rastreamento de acessos: Quando alguém acessa um link do tipo /rota/<codigo_unico>, o sistema:
   -Verifica se o código existe.
   -Coleta informações do acesso (navegador, plataforma, etc.).
   -Salva essas informações no arquivo cliques_detalhados.csv.
   -Redireciona o usuário para o link de destino cadastrado.
4. Listagem de links: Você pode consultar todos os links já criados via API (/get_links), recebendo os dados em formato JSON.
5. Interface web: Tem uma página principal protegida para gerenciamento.
