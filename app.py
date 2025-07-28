from flask import Flask, request, redirect, render_template, jsonify, session, url_for
import pandas as pd
from datetime import datetime
import os
from user_agents import parse as parse_ua
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# --- Configurações do Aplicativo ---
app.secret_key = os.urandom(24) # Chave secreta para sessões, essencial para segurança
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,  # Mudar para True em produção com HTTPS!
    PERMANENT_SESSION_LIFETIME=3600 # Tempo de vida da sessão em segundos (1 hora)
)

# Definindo o domínio base e o prefixo da rota de rastreamento
# Use uma variável de ambiente em produção ou defina diretamente
BASE_DOMAIN = os.environ.get('FLASK_BASE_DOMAIN', 'https://mkt.ocenergy.com.br')
TRACKING_PATH_PREFIX = 'r' # Prefixo curto para o link de rastreamento

# --- Configurações de E-mail ---
# ATENÇÃO: SUBSTITUA COM SEUS DADOS REAIS!
# Para produção, use variáveis de ambiente ou um sistema de segredos.
EMAIL_SENDER = os.environ.get('GMAIL_USER', 'seu_email@gmail.com') # Seu endereço de Gmail
EMAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'sua_senha_de_app_ou_senha_do_gmail') # Use a senha de app aqui
EMAIL_RECEIVER = os.environ.get('NOTIFICATION_EMAIL', 'seu_email@gmail.com') # Para onde a notificação será enviada

# --- Proteção de Rotas (Login) ---
@app.before_request
def proteger_rotas():
    rotas_publicas = ['/login', '/logout']
    # Permite acesso às rotas de rastreamento sem exigir login
    if request.path.startswith(f'/{TRACKING_PATH_PREFIX}/'):
        return None

    # Redireciona para login se a rota não for pública e o usuário não estiver logado
    if request.path not in rotas_publicas and not session.get('logged_in'):
        return redirect(url_for('login'))

# --- Rota para exibir cliques detalhados ---
@app.route('/cliques')
def cliques_detalhados():
    try:
        # Tenta ler o arquivo CSV de cliques
        df = pd.read_csv('data/cliques_detalhados.csv', dtype=str)
        cliques = df.to_dict(orient='records') # Converte para lista de dicionários para o template
    except FileNotFoundError:
        cliques = [] # Se o arquivo não existe, a lista de cliques é vazia
    except pd.errors.EmptyDataError:
        cliques = [] # Se o arquivo está vazio, a lista de cliques é vazia
    return render_template('cliques.html', cliques=cliques)

# --- Login de Usuário ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # --- Credenciais fixas para demonstração: admin / admin ---
        # Em produção, use um sistema de autenticação mais robusto (banco de dados, etc.)
        if username == "admin" and password == "admin":
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index')) # Redireciona para a página principal após login
        else:
            return render_template('login.html', error='Usuário ou senha inválidos.')
    
    return render_template('login.html') # Exibe o formulário de login

# --- Logout de Usuário ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None) # Remove a flag de login da sessão
    session.pop('username', None) # Remove o nome de usuário da sessão
    return redirect(url_for('login')) # Redireciona para a página de login

# --- Página Principal (Criar e Ver Links) ---
@app.route('/')
def index():
    try:
        # Carrega links existentes para exibir na página principal
        df = pd.read_csv('data/links.csv', sep=';', dtype=str, keep_default_na=False)
        links = df.to_dict(orient='records')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        links = [] # Se o arquivo não existe ou está vazio, a lista de links é vazia
    return render_template('index.html', base_domain=BASE_DOMAIN, tracking_path_prefix=TRACKING_PATH_PREFIX, links=links)

# --- Rota para rastrear cliques, notificar e redirecionar ---
@app.route(f'/{TRACKING_PATH_PREFIX}/<campanha>/<codigo>', methods = ['GET'])
def rastrear_e_redirecionar(campanha, codigo):
    try:
        df = pd.read_csv('data/links.csv', sep=';', dtype=str)
        
        # Procura o link original no DataFrame com base na campanha e código
        link_data = df[(df['campanha'] == campanha) & (df['codigo'] == codigo)]
        
        if not link_data.empty:
            url_destino = link_data['link_original'].iloc[0] # Pega a URL de destino
            
            # Coleta informações detalhadas do clique
            user_agent_str = request.headers.get('User-Agent', '')
            user_agent = parse_ua(user_agent_str)
            ip = request.headers.get('X-Forwarded-For', request.remote_addr) # Pega IP real se estiver atrás de proxy
            navegador = user_agent.browser.family
            plataforma = user_agent.device.family
            os_info = user_agent.os.family
            referer = request.headers.get('Referer', '') # URL de onde o clique veio
            
            # Cria um DataFrame temporário com as informações do clique
            clique_info = pd.DataFrame([{
                'data_hora': datetime.now().isoformat(),
                'ip': ip,
                'navegador': navegador,
                'plataforma': plataforma,
                'os': os_info,
                'campanha': campanha,
                'codigo': codigo,
                'link_original': url_destino,
                'referer': referer
            }])
            
            # Salva as informações do clique no CSV de cliques detalhados
            file_exists_cliques = os.path.isfile('data/cliques_detalhados.csv')
            clique_info.to_csv('data/cliques_detalhados.csv', mode='a', header=not file_exists_cliques, index=False)
            
            print(f"Redirecionando /{TRACKING_PATH_PREFIX}/{campanha}/{codigo} para {url_destino}")

            # --- Lógica de Envio de E-mail de Notificação ---
            try:
                msg = MIMEMultipart()
                msg['From'] = EMAIL_SENDER
                msg['To'] = EMAIL_RECEIVER
                msg['Subject'] = f"NOVO CLIQUE NO SEU LINK: {campanha}/{codigo}"

                # Corpo do e-mail com os detalhes do clique
                body = f"""
Olá,

Um novo clique foi registrado no seu link rastreável!

Detalhes do Clique:
- Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- Campanha: {campanha}
- Código: {codigo}
- Link Original: {url_destino}
- IP: {ip}
- Navegador: {navegador}
- Plataforma: {plataforma}
- Sistema Operacional: {os_info}
- Referer: {referer if referer else 'N/A'} (Se o navegador informou)

Acesse seu painel em {BASE_DOMAIN} para mais detalhes.

Atenciosamente,
Seu Sistema de Rastreamento
                """
                msg.attach(MIMEText(body, 'plain'))

                # Conecta ao servidor SMTP do Gmail e envia o e-mail
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                    smtp.send_message(msg)
                print("E-mail de notificação enviado com sucesso!")
            except Exception as email_e:
                print(f"Erro ao enviar e-mail de notificação: {email_e}")
                # Em um sistema real, você registraria esse erro de forma mais robusta

            # --- Fim da Lógica de Envio de E-mail ---

            # Redireciona o usuário para o link de destino
            return redirect(url_destino, code=302)
        else:
            print(f"Link não reconhecido: Campanha '{campanha}', Código '{codigo}'")
            return 'Link não reconhecido', 400
    except FileNotFoundError:
        print("Arquivo links.csv não encontrado.")
        return 'Sistema de links não inicializado.', 500
    except Exception as e:
        print(f"Erro ao processar a rota /{TRACKING_PATH_PREFIX}/<campanha>/<codigo>: {e}")
        import traceback # Para ver a pilha de erro completa no console
        traceback.print_exc()
        return 'Erro interno do servidor ao processar o link.', 500

# --- Rota para criar novos links (via formulário POST) ---
@app.route('/criar_link', methods = ['POST'])
def criar_link():
    # Pega os dados do formulário
    link_original = request.form['link_original']
    campanha = request.form['campanha']
    codigo = request.form['codigo']

    # Validação básica dos campos
    if not link_original or not campanha or not codigo:
        # Você pode renderizar o template com uma mensagem de erro aqui
        return "Todos os campos (Link Original, Campanha, Código) são obrigatórios!", 400

    # Cria o link mascarado no formato desejado
    link_mascarado = f"{BASE_DOMAIN}/{TRACKING_PATH_PREFIX}/{campanha}/{codigo}"

    # Prepara os dados para salvar no CSV
    novo_registro = pd.DataFrame([{
        'link_original': link_original,
        'campanha': campanha,
        'codigo': codigo,
        'link_mascarado': link_mascarado
    }])
    
    # Salva o novo link no arquivo CSV
    file_exists = os.path.isfile('data/links.csv')
    novo_registro.to_csv('data/links.csv', mode='a', header=not file_exists, index=False, sep=';')
    
    print("Novo link adicionado ao links.csv:", novo_registro)
    return redirect(url_for('index')) # Redireciona de volta para a página principal

# --- Execução do Aplicativo ---
if __name__ == '__main__':
    # Garante que a pasta 'data' existe para armazenar os CSVs
    if not os.path.exists('data'):
        os.makedirs('data')
    app.run(debug=True, host='0.0.0.0', port=5000)