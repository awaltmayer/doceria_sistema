import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

# --- Configuração da Aplicação ---
# Define explicitamente as pastas para evitar erros na Vercel
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte' # Mude isto no futuro
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Configuração da Base de Dados (Funciona Localmente e na Vercel) ---
DATABASE_URL = os.environ.get('POSTGRES_URL')

# Correção para a URL do PostgreSQL no SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Se não estiver na Vercel, usa uma base de dados local SQLite
if not DATABASE_URL:
    print("A usar a base de dados SQLite local.")
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DATABASE_URL = 'sqlite:///' + os.path.join(instance_dir, 'doceria.db')
else:
    print("A usar a base de dados PostgreSQL na nuvem.")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

db = SQLAlchemy(app)

# --- Modelos da Base de Dados ---
class Trufa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

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

# --- Rotas Principais da Aplicação ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cardapio')
def cardapio():
    try:
        trufas = Trufa.query.all()
        return render_template('cardapio.html', trufas=trufas)
    except Exception as e:
        # Mostra um erro útil se a base de dados falhar
        return f"Erro ao aceder à base de dados: {e}"

@app.route('/adicionar_carrinho', methods=['POST'])
def adicionar_carrinho():
    trufa_id = request.form.get('trufa_id')
    quantidade = int(request.form.get('quantidade'))
    
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

    session.modified = True
    return redirect(url_for('cardapio'))

@app.route('/ver_carrinho')
def ver_carrinho():
    carrinho = session.get('carrinho', {})
    total = 0
    itens_carrinho = []
    
    for item_id, item_info in carrinho.items():
        subtotal = item_info['preco'] * item_info['quantidade']
        total += subtotal
        itens_carrinho.append({
            'id': item_id,
            'nome': item_info['nome'],
            'preco': item_info['preco'],
            'quantidade': item_info['quantidade'],
            'subtotal': subtotal
        })
        
    return render_template('carrinho.html', itens_carrinho=itens_carrinho, total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    carrinho = session.get('carrinho', {})
    if not carrinho:
        flash('O seu carrinho está vazio.', 'danger')
        return redirect(url_for('ver_carrinho'))

    try:
        novo_pedido = Pedido(
            nome_cliente=request.form.get('nome_cliente'),
            telefone_cliente=request.form.get('telefone_cliente'),
            endereco_cliente=request.form.get('endereco_cliente'),
            total=sum(item['preco'] * item['quantidade'] for item in carrinho.values())
        )
        db.session.add(novo_pedido)
        db.session.flush()

        for item_info in carrinho.values():
            novo_item = ItemPedido(
                pedido_id=novo_pedido.id,
                trufa_nome=item_info['nome'],
                quantidade=item_info['quantidade'],
                preco_unitario=item_info['preco']
            )
            db.session.add(novo_item)
            
        db.session.commit()
        
        pedido_id = novo_pedido.id
        session.pop('carrinho', None)
        
        return redirect(url_for('obrigado', pedido_id=pedido_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar o seu pedido: {e}', 'danger')
        return redirect(url_for('ver_carrinho'))

@app.route('/obrigado/<int:pedido_id>')
def obrigado(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('obrigado.html', pedido=pedido)

# --- Função para Popular a Base de Dados ---
def popular_base_de_dados():
    with app.app_context():
        db.create_all()
        
        if Trufa.query.count() == 0:
            print("A popular a base de dados com trufas...")
            # CORREÇÃO CRÍTICA: Nomes das imagens em minúsculas
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
            print("Base de dados populada com sucesso!")
        else:
            print("A base de dados já estava populada.")

# --- Rota Secreta para Configuração na Vercel ---
@app.route('/setup-database-12345')
def setup_database():
    try:
        popular_base_de_dados()
        return "Base de dados configurada e populada com sucesso!", 200
    except Exception as e:
        return f"Erro ao configurar a base de dados: {e}", 500

# --- Bloco de Execução Local ---
if __name__ == '__main__':
    popular_base_de_dados()
    app.run(debug=True, port=5000)
