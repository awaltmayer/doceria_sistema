import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configuração explícita das pastas para a Vercel
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_segura_para_sessoes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CONFIGURAÇÃO DA BASE DE DADOS ---
DATABASE_URL = os.environ.get('POSTGRES_URL')

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DATABASE_URL = 'sqlite:///' + os.path.join(instance_dir, 'doceria.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)

# --- Modelos ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Trufa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float, nullable=False)

# (Os modelos Pedido e ItemPedido continuam iguais)
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

# --- Funções de Autenticação ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para aceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Login/Registo ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login efetuado com sucesso!', 'success')
            return redirect(url_for('cardapio'))
        else:
            flash('Utilizador ou password incorretos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Este nome de utilizador já existe.', 'warning')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Por favor, faça login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout efetuado com sucesso.', 'info')
    return redirect(url_for('login'))

# --- Rotas da Aplicação ---
@app.route('/')
def index():
    # A página inicial agora verifica se o utilizador está logado
    if 'user_id' in session:
        return redirect(url_for('cardapio'))
    return redirect(url_for('login'))

@app.route('/cardapio')
@login_required
def cardapio():
    trufas = Trufa.query.all()
    return render_template('cardapio.html', trufas=trufas)

# (As outras rotas como adicionar_carrinho, ver_carrinho, etc., continuam iguais,
# mas agora estarão protegidas porque o acesso ao cardápio requer login)
@app.route('/adicionar_carrinho', methods=['POST'])
@login_required
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
        carrinho[id_str] = {'nome': trufa.nome, 'preco': trufa.preco, 'quantidade': quantidade}
    elif id_str in carrinho:
        del carrinho[id_str]
    session['carrinho'] = carrinho
    flash(f'{trufa.nome} atualizado no carrinho.', 'success')
    return redirect(url_for('cardapio'))

@app.route('/ver_carrinho')
@login_required
def ver_carrinho():
    carrinho = session.get('carrinho', {})
    total = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    return render_template('carrinho.html', carrinho=carrinho, total=total)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    carrinho = session.get('carrinho', {})
    if not carrinho:
        flash('O seu carrinho está vazio.', 'warning')
        return redirect(url_for('ver_carrinho'))
    novo_pedido = Pedido(
        nome_cliente=request.form.get('nome_cliente'),
        telefone_cliente=request.form.get('telefone_cliente'),
        endereco_cliente=request.form.get('endereco_cliente'),
        total=sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    )
    db.session.add(novo_pedido)
    for item_info in carrinho.values():
        item_pedido = ItemPedido(
            pedido=novo_pedido,
            trufa_nome=item_info['nome'],
            quantidade=item_info['quantidade'],
            preco_unitario=item_info['preco']
        )
        db.session.add(item_pedido)
    db.session.commit()
    session.pop('carrinho', None)
    return redirect(url_for('obrigado', pedido_id=novo_pedido.id))

@app.route('/obrigado/<int:pedido_id>')
@login_required
def obrigado(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('obrigado.html', pedido=pedido)


# --- Função de popular o banco (agora com a tabela User) ---
def create_db_and_populate():
    with app.app_context():
        db.drop_all() # Apaga tudo para garantir uma base de dados limpa
        db.create_all() # Cria as tabelas com a nova estrutura (com User)
        
        trufas = [
            Trufa(nome='Brigadeiro', descricao='Trufa de brigadeiro tradicional', preco=5.00),
            Trufa(nome='Ninho', descricao='Trufa de leite em pó', preco=5.00),
            Trufa(nome='Ninho+brigadeiro', descricao='Combinação de ninho e brigadeiro', preco=5.00),
            Trufa(nome='Sensação', descricao='Chocolate com recheio de morango', preco=5.00),
            Trufa(nome='Coco', descricao='Trufa de coco fresco (sem acento)', preco=5.00),
            Trufa(nome='Amendoim', descricao='Trufa de pasta de amendoim', preco=5.00)
        ]
        db.session.add_all(trufas)
        db.session.commit()
        print("Base de dados recriada e populada com sucesso!")

# --- ROTA SECRETA PARA CRIAR O BANCO NA NUVEM ---
@app.route('/setup-database-12345')
def setup_database():
    try:
        create_db_and_populate()
        return "Base de dados recriada com sucesso!", 200
    except Exception as e:
        return f"Erro ao criar a base de dados: {e}", 500

