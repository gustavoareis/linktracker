from flask import Flask, request, redirect, render_template, jsonify, session, url_for
import pandas as pd
from datetime import datetime
import pytz
from user_agents import parse
import os

app = Flask(__name__)

app.secret_key = os.urandom(24)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,  # Mudar para True em produção com HTTPS!
    PERMANENT_SESSION_LIFETIME=3600
)

BASE_DOMAIN = os.environ.get('FLASK_BASE_DOMAIN', 'https://mkt.ocenergy.com.br')
TRACKING_PATH_PREFIX = 'rota'

#Proteção de Rotas
@app.before_request
def proteger_rotas():
    rotas_publicas = ['/login', '/logout']
    if request.path.startswith(f'/{TRACKING_PATH_PREFIX}/'):
        return None

    if request.path not in rotas_publicas and not session.get('logged_in'):
        return redirect(url_for('login'))

#Rota para exibir cliques detalhados
@app.route('/cliques')
def cliques_detalhados():
    try:
        df = pd.read_csv('data/cliques_detalhados.csv', dtype=str)
        cliques = df.to_dict(orient='records')
    except FileNotFoundError:
        cliques = []
    except pd.errors.EmptyDataError:
        cliques = []
    return render_template('cliques.html', cliques=cliques)

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # --- APENAS UM USUÁRIO: admin / admin ---
        if username == "admin" and password == "admin":
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Usuário ou senha inválidos.')
    
    return render_template('login.html')

#Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

#Main
@app.route('/')
def index():
    return render_template('index.html', base_domain=BASE_DOMAIN, tracking_path_prefix=TRACKING_PATH_PREFIX)

#Rota para rastrear e redirecionar qualquer link com código único
@app.route(f'/{TRACKING_PATH_PREFIX}/<codigo_unico>', methods = ['GET'])
def home(codigo_unico):
    try:
        df = pd.read_csv('data/codigos_uuid.csv', sep=';', dtype=str)
        if codigo_unico in df['uuid'].values:
            # Coletar informações detalhadas do clique
            from user_agents import parse as parse_ua
            import pandas as pd
            from datetime import datetime
            user_agent_str = request.headers.get('User-Agent', '')
            user_agent = parse_ua(user_agent_str)
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            navegador = user_agent.browser.family
            plataforma = user_agent.device.family
            os_info = user_agent.os.family
            referer = request.headers.get('Referer', '')
            clique_info = pd.DataFrame([{
                'data_hora': datetime.now().isoformat(),
                'ip': ip,
                'navegador': navegador,
                'plataforma': plataforma,
                'codigo_unico': codigo_unico,
                'referer': referer,
                'os': os_info
            }])
            clique_info.to_csv('data/cliques_detalhados.csv', mode='a', header=False, index=False)
            # envio de email removido
            url_destino = df[df['uuid'] == codigo_unico]['link'].iloc[0]
            if pd.isna(url_destino):
                print(f"URL de destino para {codigo_unico} é nula/vazia no CSV. Redirecionando para fallback.")
                return 'URL de destino não encontrada para este código.', 404
            print(f"Redirecionando {codigo_unico} para {url_destino}")
            return redirect(url_destino, code=302)
        else:
            print(f"Link não reconhecido: {codigo_unico}")
            return 'link não reconhecido', 400
    except FileNotFoundError:
        print("Arquivo codigos_uuid.csv não encontrado.")
        return 'Sistema de links não inicializado.', 500
    except Exception as e:
        print(f"Erro ao processar a rota /{TRACKING_PATH_PREFIX}/<codigo_unico>: {e}")
        import traceback
        traceback.print_exc()
        return 'Erro interno do servidor ao processar o link.', 500

#Rota para criar novos links via API
@app.route('/criar', methods = ['POST'])
def criar_link():
    novo_registro = request.get_json()
    print("Dados recebidos para criação:", novo_registro)
    nova_linha = pd.DataFrame({k: [v] for k, v in novo_registro.items()})
    file_exists = os.path.isfile('data/codigos_uuid.csv')
    nova_linha.to_csv('data/codigos_uuid.csv', mode='a', header=not file_exists, index=False, sep=';')
    print("Novo link adicionado ao codigos_uuid.csv:", nova_linha)
    return 'Dados adicionados com sucesso!', 200

#Rota para listar os links existentes
@app.route('/get_links', methods=['GET'])
def get_existing_links():
    try:
        df = pd.read_csv('data/codigos_uuid.csv', sep=';', dtype=str, keep_default_na=False)
        links_list = df.to_dict(orient='records')
        return jsonify(links_list), 200
    except FileNotFoundError:
        print("Arquivo codigos_uuid.csv não encontrado ao tentar listar links. Retornando lista vazia.")
        return jsonify([]), 200
    except pd.errors.EmptyDataError:
        print("Arquivo codigos_uuid.csv está vazio. Retornando lista vazia.")
        return jsonify([]), 200
    except Exception as e:
        print(f"Erro ao ler codigos_uuid.csv para listar links: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)