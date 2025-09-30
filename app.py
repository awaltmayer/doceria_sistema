import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# --- Configuração da Aplicação ---
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Configuração da Base de Dados (Vercel Postgres ou SQLite local) ---
DATABASE_URL = os.environ.get('POSTGRES_URL')

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DATABASE_URL = 'sqlite:///' + os.path.join(instance_dir, 'doceria.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)

# --- Modelos da Base de Dados ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Trufa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float, nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    user = db.relationship('User', backref=db.backref('pedidos', lazy=True))
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade="all, delete-orphan")

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    trufa_nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

# --- Decorador para Proteger Rotas ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Autenticação ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('cardapio'))
        else:
            flash('Utilizador ou password incorretos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Este nome de utilizador já existe.', 'danger')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Conta criada com sucesso! Por favor, faça login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão terminada.', 'info')
    return redirect(url_for('login'))

# --- Rotas da Loja ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('cardapio'))
    return redirect(url_for('login'))

@app.route('/cardapio')
@login_required
def cardapio():
    trufas = Trufa.query.all()
    return render_template('cardapio.html', trufas=trufas)

@app.route('/adicionar_carrinho', methods=['POST'])
@login_required
def adicionar_carrinho():
    trufa_id = request.form.get('trufa_id')
    quantidade = int(request.form.get('quantidade'))
    
    if 'carrinho' not in session:
        session['carrinho'] = {}
    
    carrinho = session['carrinho']
    id_str = str(trufa_id)
    
    if quantidade > 0:
        carrinho[id_str] = quantidade
    elif id_str in carrinho:
        del carrinho[id_str]
        
    session['carrinho'] = carrinho
    return redirect(url_for('cardapio'))

@app.route('/ver_carrinho')
@login_required
def ver_carrinho():
    carrinho_session = session.get('carrinho', {})
    itens_carrinho = []
    total_geral = 0
    
    for trufa_id, quantidade in carrinho_session.items():
        trufa = Trufa.query.get(trufa_id)
        if trufa:
            subtotal = trufa.preco * quantidade
            total_geral += subtotal
            itens_carrinho.append({
                'id': trufa.id,
                'nome': trufa.nome,
                'preco': trufa.preco,
                'quantidade': quantidade,
                'subtotal': subtotal
            })
            
    return render_template('carrinho.html', itens_carrinho=itens_carrinho, total_geral=total_geral)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    carrinho_session = session.get('carrinho', {})
    if not carrinho_session:
        return redirect(url_for('cardapio'))

    total_pedido = 0
    itens_para_pedido = []
    for trufa_id, quantidade in carrinho_session.items():
        trufa = Trufa.query.get(trufa_id)
        if trufa:
            total_pedido += trufa.preco * quantidade
            itens_para_pedido.append({'trufa': trufa, 'quantidade': quantidade})

    novo_pedido = Pedido(user_id=session['user_id'], total=total_pedido)
    db.session.add(novo_pedido)
    db.session.flush()

    for item in itens_para_pedido:
        novo_item_pedido = ItemPedido(
            pedido_id=novo_pedido.id,
            trufa_nome=item['trufa'].nome,
            quantidade=item['quantidade'],
            preco_unitario=item['trufa'].preco
        )
        db.session.add(novo_item_pedido)
    
    db.session.commit()
    session.pop('carrinho', None)
    
    return redirect(url_for('obrigado', pedido_id=novo_pedido.id))

@app.route('/obrigado/<int:pedido_id>')
@login_required
def obrigado(pedido_id):
    pedido = Pedido.query.filter_by(id=pedido_id, user_id=session['user_id']).first_or_404()
    return render_template('obrigado.html', pedido=pedido)


# --- Rota Secreta para Configuração da Base de Dados ---
@app.route('/setup-database-12345')
def setup_database():
    with app.app_context():
        # Apaga tudo para garantir um estado limpo
        db.drop_all()
        # Cria as tabelas novamente com a estrutura correta
        db.create_all()
        
        if Trufa.query.count() == 0:
            trufas_iniciais = [
                Trufa(nome='Brigadeiro', descricao='Trufa de brigadeiro tradicional', preco=5.00),
                Trufa(nome='Ninho', descricao='Trufa de leite em pó', preco=5.00),
                Trufa(nome='Ninho+Brigadeiro', descricao='Combinação de ninho e brigadeiro', preco=5.00),
                Trufa(nome='Sensação', descricao='Chocolate com recheio de morango', preco=5.00),
                Trufa(nome='Coco', descricao='Trufa de coco fresco', preco=5.00),
                Trufa(nome='Amendoim', descricao='Trufa de pasta de amendoim', preco=5.00)
            ]
            db.session.add_all(trufas_iniciais)
            db.session.commit()
            return "Base de dados recriada e populada com sucesso!", 200
        else:
            return "Base de dados já populada.", 200

# --- Inicialização Automática do Banco de Dados ---
def init_database():
    """Inicializa o banco de dados se necessário"""
    try:
        # Cria as tabelas se elas não existem
        db.create_all()
        
        # Verifica se as trufas já estão populadas
        if Trufa.query.count() == 0:
            trufas_iniciais = [
                Trufa(nome='Brigadeiro', descricao='Trufa de brigadeiro tradicional', preco=5.00),
                Trufa(nome='Ninho', descricao='Trufa de leite em pó', preco=5.00),
                Trufa(nome='Ninho+Brigadeiro', descricao='Combinação de ninho e brigadeiro', preco=5.00),
                Trufa(nome='Sensação', descricao='Chocolate com recheio de morango', preco=5.00),
                Trufa(nome='Coco', descricao='Trufa de coco fresco', preco=5.00),
                Trufa(nome='Amendoim', descricao='Trufa de pasta de amendoim', preco=5.00)
            ]
            db.session.add_all(trufas_iniciais)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")

# Inicializa o banco de dados ao iniciar a aplicação
with app.app_context():
    init_database()

# --- Entry point para Vercel ---
if __name__ == '__main__':
    app.run(debug=True)

