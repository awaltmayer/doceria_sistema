import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

# Inicialização do App Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_e_dificil_de_adivinhar'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CONFIGURAÇÃO DO BANCO DE DADOS (PARA VERCEL E LOCAL) ---
# Tenta pegar a URL do banco de dados do ambiente Vercel
DATABASE_URL = os.environ.get('POSTGRES_URL')

# Se encontrar a URL do Vercel, ajusta o protocolo para o SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Se NÃO encontrar (estamos rodando localmente), usa o banco de dados SQLite
if not DATABASE_URL:
    print("AVISO: Usando banco de dados SQLite local para desenvolvimento.")
    # Garante que a pasta 'instance' exista para guardar o arquivo .db
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DATABASE_URL = 'sqlite:///' + os.path.join(instance_dir, 'doceria.db')

# Define a configuração final do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# --- FIM DA CONFIGURAÇÃO DO BANCO ---

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)


# --- MODELOS DO BANCO DE DADOS ---
class Trufa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefone_cliente = db.Column(db.String(20), nullable=False)
    endereco_cliente = db.Column(db.String(255), nullable=False)
    total = db.Column(db.Float, nullable=False)
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade="all, delete-orphan")

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    trufa_nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)


# --- FUNÇÃO PARA POPULAR O BANCO ---
def create_db_and_populate():
    """Cria as tabelas e adiciona os dados iniciais se o banco estiver vazio."""
    with app.app_context():
        # Cria todas as tabelas que ainda não existem
        db.create_all()
        
        # Só adiciona as trufas se a tabela estiver vazia
        if Trufa.query.count() == 0:
            print("Populando o banco de dados com as trufas iniciais...")
            trufas_iniciais = [
                Trufa(nome='Brigadeiro', descricao='Trufa de brigadeiro tradicional', preco=5.00, image_url='brigadeiro.jpg'),
                Trufa(nome='Ninho', descricao='Trufa de leite em pó', preco=5.00, image_url='ninho.jpg'),
                Trufa(nome='Ninho+brigadeiro', descricao='Combinação de ninho e brigadeiro', preco=5.00, image_url='ninho_brigadeiro.jpg'),
                Trufa(nome='Sensação', descricao='Chocolate com recheio de morango', preco=5.00, image_url='sensacao.jpg'),
                Trufa(nome='Côco', descricao='Trufa de coco fresco', preco=5.00, image_url='coco.jpg'),
                Trufa(nome='Amendoim', descricao='Trufa de pasta de amendoim', preco=5.00, image_url='amendoim.jpg')
            ]
            db.session.add_all(trufas_iniciais)
            db.session.commit()
            print("Banco de dados populado com sucesso!")
        else:
            print("O banco de dados já contém dados. Nenhuma ação foi tomada.")


# --- ROTAS PRINCIPAIS DO SITE ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cardapio')
def cardapio():
    try:
        trufas = Trufa.query.all()
        # Se a lista de trufas estiver vazia, mostra uma mensagem
        if not trufas:
            flash('O cardápio ainda não foi cadastrado. Tente criar o banco de dados.', 'warning')
        return render_template('cardapio.html', trufas=trufas)
    except OperationalError:
        flash('Erro de conexão com o banco de dados. As tabelas podem não ter sido criadas.', 'danger')
        return render_template('cardapio.html', trufas=[])
    except Exception as e:
        flash(f'Ocorreu um erro inesperado: {e}', 'danger')
        return render_template('cardapio.html', trufas=[])

# (As outras rotas como adicionar_carrinho, ver_carrinho, etc., continuam aqui)
@app.route('/adicionar_carrinho', methods=['POST'])
def adicionar_carrinho():
    trufa_id = request.form.get('trufa_id')
    quantidade = int(request.form.get('quantidade', 0))
    
    if 'carrinho' not in session:
        session['carrinho'] = {}
    
    trufa = Trufa.query.get(trufa_id)
    if not trufa:
        flash('Trufa não encontrada!', 'danger')
        return redirect(url_for('cardapio'))

    carrinho = session['carrinho']
    id_str = str(trufa_id)
    
    if quantidade > 0:
        carrinho[id_str] = {
            'nome': trufa.nome,
            'preco': trufa.preco,
            'quantidade': quantidade
        }
        flash(f'{quantidade}x {trufa.nome} adicionado(s) ao carrinho!', 'success')
    elif id_str in carrinho:
        del carrinho[id_str]
        flash(f'{trufa.nome} removido do carrinho.', 'info')

    session['carrinho'] = carrinho
    return redirect(url_for('cardapio'))

@app.route('/ver_carrinho')
def ver_carrinho():
    carrinho = session.get('carrinho', {})
    total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    return render_template('carrinho.html', carrinho=carrinho, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    carrinho = session.get('carrinho', {})
    if not carrinho:
        flash('Seu carrinho está vazio!', 'warning')
        return redirect(url_for('cardapio'))

    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente')
        telefone_cliente = request.form.get('telefone_cliente')
        endereco_cliente = request.form.get('endereco_cliente')
        
        total_pedido = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
        
        try:
            novo_pedido = Pedido(
                nome_cliente=nome_cliente,
                telefone_cliente=telefone_cliente,
                endereco_cliente=endereco_cliente,
                total=total_pedido
            )
            db.session.add(novo_pedido)
            db.session.flush()

            for item_id, item_info in carrinho.items():
                novo_item = ItemPedido(
                    pedido_id=novo_pedido.id,
                    trufa_nome=item_info['nome'],
                    quantidade=item_info['quantidade'],
                    preco_unitario=item_info['preco']
                )
                db.session.add(novo_item)
            
            db.session.commit()
            session.pop('carrinho', None)
            flash('Pedido realizado com sucesso! Obrigado!', 'success')
            return redirect(url_for('obrigado', pedido_id=novo_pedido.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar pedido: {e}', 'danger')
            return redirect(url_for('ver_carrinho'))

    total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    return render_template('checkout.html', carrinho=carrinho, total=total)
    
@app.route('/obrigado/<int:pedido_id>')
def obrigado(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('obrigado.html', pedido=pedido)

# --- ROTA SECRETA TEMPORÁRIA PARA CRIAR O BANCO NA VERCEL ---
# (Pode apagar este bloco de código depois que tudo funcionar)
@app.route('/CRIAR-O-BANCO-DE-DADOS-AGORA-12345')
def setup_database():
    try:
        print("--- ROTA SECRETA ACESSADA: INICIANDO CRIAÇÃO DO BANCO ---")
        create_db_and_populate() 
        print("--- ROTA SECRETA: BANCO CRIADO E POPULADO COM SUCESSO ---")
        return "BANCO DE DADOS CRIADO E POPULADO COM SUCESSO!", 200
    except Exception as e:
        print(f"--- ROTA SECRETA: ERRO AO CRIAR BANCO: {e} ---")
        return f"Ocorreu um erro ao criar o banco: {e}", 500
# --- Fim da Rota Secreta ---


# --- Bloco de execução para ambiente local ---
if __name__ == '__main__':
    # Esta função será chamada apenas quando você rodar "python app.py"
    create_db_and_populate()
    app.run(debug=True, port=5000)
    