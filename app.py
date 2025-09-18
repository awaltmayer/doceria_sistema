import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- NOVA CONFIGURAÇÃO DE BANCO DE DADOS ---
# Pega a URL do banco de dados das variáveis de ambiente do Vercel
DATABASE_URL = os.environ.get('POSTGRES_URL')

# Uma correção necessária para o SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Se não estiver no Vercel (rodando local), use o banco SQLite
if not DATABASE_URL:
    print("Usando banco de dados SQLite local.")
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    DATABASE_URL = 'sqlite:///' + os.path.join(instance_dir, 'doceria.db')
else:
    print("Usando banco de dados Postgres na nuvem.")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# --- FIM DA NOVA CONFIGURAÇÃO ---

db = SQLAlchemy(app)

# --- Modelos ---
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

# --- Rotas ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cardapio')
def cardapio():
    try:
        trufas = Trufa.query.all()
        return render_template('cardapio.html', trufas=trufas)
    except Exception as e:
        # Isso nos ajudará a depurar se o banco falhar no Vercel
        return f"Erro ao conectar ao banco de dados: {e}"

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
    else:
        if id_str in carrinho:
            del carrinho[id_str]
            flash(f'{trufa.nome} removido do carrinho.', 'info')

    session['carrinho'] = carrinho
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

@app.route('/remover_do_carrinho/<item_id>', methods=['POST'])
def remover_do_carrinho(item_id):
    carrinho = session.get('carrinho', {})
    if item_id in carrinho:
        nome_trufa = carrinho[item_id]['nome']
        del carrinho[item_id]
        session['carrinho'] = carrinho
        flash(f'{nome_trufa} removido do carrinho.', 'info')
    return redirect(url_for('ver_carrinho'))

@app.route('/checkout', methods=['POST'])
def checkout():
    nome_cliente = request.form.get('nome_cliente')
    telefone_cliente = request.form.get('telefone_cliente')
    endereco_cliente = request.form.get('endereco_cliente')
    
    carrinho = session.get('carrinho', {})
    if not carrinho:
        flash('Seu carrinho está vazio.', 'danger')
        return redirect(url_for('ver_carrinho'))

    total_pedido = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
    
    try:
        novo_pedido = Pedido(
            nome_cliente=nome_cliente,
            telefone_cliente=telefone_cliente,
            endereco_cliente=endereco_cliente,
            total=total_pedido
        )
        db.session.add(novo_pedido)
        db.session.flush() # Para pegar o ID do novo_pedido antes do commit

        for item_id, item_info in carrinho.items():
            novo_item = ItemPedido(
                pedido_id=novo_pedido.id,
                trufa_nome=item_info['nome'],
                quantidade=item_info['quantidade'],
                preco_unitario=item_info['preco']
            )
            db.session.add(novo_item)
            
        db.session.commit()
        
        # Limpa o carrinho
        session.pop('carrinho', None)
        
        # Passa os detalhes do pedido para a página de obrigado
        return redirect(url_for('obrigado', pedido_id=novo_pedido.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar seu pedido: {e}', 'danger')
        return redirect(url_for('ver_carrinho'))

@app.route('/obrigado/<int:pedido_id>')
def obrigado(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('obrigado.html', pedido=pedido)


# --- Função de popular o banco ---
def create_db_and_populate():
    with app.app_context():
        # Cria as tabelas
        db.create_all()
        
        # Verifica se as trufas já existem antes de adicionar
        if Trufa.query.count() == 0:
            trufa1 = Trufa(nome='Brigadeiro', descricao='Trufa de brigadeiro tradicional', preco=5.00, image_url='brigadeiro.jpg')
            trufa2 = Trufa(nome='Ninho', descricao='Trufa de leite em pó', preco=5.00, image_url='ninho.jpg')
            trufa3 = Trufa(nome='Ninho+brigadeiro', descricao='Combinação de ninho e brigadeiro', preco=5.00, image_url='ninho_brigadeiro.jpg')
            trufa4 = Trufa(nome='Sensação', descricao='Chocolate com recheio de morango', preco=5.00, image_url='sensacao.jpg')
            trufa5 = Trufa(nome='Côco', descricao='Trufa de coco fresco', preco=5.00, image_url='coco.jpg')
            trufa6 = Trufa(nome='Amendoim', descricao='Trufa de pasta de amendoim', preco=5.00, image_url='amendoim.jpg')
            
            db.session.add_all([trufa1, trufa2, trufa3, trufa4, trufa5, trufa6])
            db.session.commit()
            print("Banco de dados criado e populado com sucesso!")
        else:
            print("Banco de dados já populado.")


# --- Bloco de execução ---
if __name__ == '__main__':
    # Este bloco só roda quando você executa "python app.py"
    # Não vai rodar no Vercel
    create_db_and_populate()
    app.run(debug=True, port=5000)