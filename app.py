import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "trufaria.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "uma-chave-secreta-muito-dificil"

db = SQLAlchemy(app)

# --- MODELOS DO BANCO DE DADOS ---
class Trufa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sabor = db.Column(db.String(100), nullable=False, unique=True)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(250))
    disponivel = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(250), nullable=True) # URL da imagem da trufa

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_usuario = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    pedidos = db.relationship("Pedido", backref="cliente", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    data_pedido = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    detalhes_pedido = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Pendente")

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# --- ROTAS ---
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        telefone = request.form["phone"]
        password = request.form["password"]

        existing_user = Cliente.query.filter_by(email=email).first()
        if existing_user:
            flash("Este e-mail já está cadastrado. Por favor, use outro.")
            return redirect(url_for("register"))

        new_client = Cliente(nome_usuario=username, email=email, telefone=telefone)
        new_client.set_password(password)
        db.session.add(new_client)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Faça login para continuar.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        client = Cliente.query.filter_by(email=email).first()
        if client and client.check_password(password):
            session["client_id"] = client.id
            session["client_username"] = client.nome_usuario
            flash("Login realizado com sucesso!")
            return redirect(url_for("cardapio")) # Redirecionar para a área do cliente
        else:
            flash("E-mail ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("client_id", None)
    session.pop("client_username", None)
    flash("Você foi desconectado.")
    return redirect(url_for("login"))

@app.route("/cardapio")
def cardapio():
    if "client_id" not in session:
        flash("Você precisa estar logado para acessar o cardápio.")
        return redirect(url_for("login"))
    trufas = Trufa.query.all()
    return render_template("cardapio.html", trufas=trufas)

@app.route("/fazer_pedido", methods=["POST"])
def fazer_pedido():
    if "client_id" not in session:
        flash("Você precisa estar logado para fazer um pedido.")
        return redirect(url_for("login"))

    cliente_id = session["client_id"]
    detalhes_pedido = []
    for key, value in request.form.items():
        if key.startswith("trufa_") and int(value) > 0:
            trufa_id = key.split("_")[1]
            trufa = Trufa.query.get(trufa_id)
            if trufa:
                detalhes_pedido.append(f"{trufa.sabor} (x{value})")
    
    if not detalhes_pedido:
        flash("Selecione pelo menos uma trufa para fazer o pedido.")
        return redirect(url_for("cardapio"))

    novo_pedido = Pedido(cliente_id=cliente_id, detalhes_pedido=", ".join(detalhes_pedido))
    db.session.add(novo_pedido)
    db.session.commit()
    flash("Pedido realizado com sucesso!")
    return redirect(url_for("cardapio"))

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin_user = Admin.query.filter_by(username=username).first()
        if admin_user and check_password_hash(admin_user.password_hash, password):
            session["admin_logged_in"] = True
            flash("Login de administrador realizado com sucesso!")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Usuário ou senha de administrador inválidos.")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        flash("Você precisa estar logado como administrador para acessar esta página.")
        return redirect(url_for("admin_login"))
    pedidos = Pedido.query.all()
    return render_template("admin_dashboard.html", pedidos=pedidos)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Você foi desconectado do painel de administrador.")
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Garante que todas as tabelas sejam criadas primeiro

        # Adicionar admin se não existir
        if not Admin.query.filter_by(username="admin").first():
            admin_user = Admin(username="admin", password_hash=generate_password_hash("admin_password"))
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário admin criado.")
        
        # Limpar trufas existentes e adicionar as novas
        # É importante que db.create_all() já tenha sido chamado
        Trufa.query.delete() # Limpa todas as trufas existentes
        db.session.commit()

        produtos = [
            Trufa(sabor="Brigadeiro", preco=5.00, descricao="Trufa de brigadeiro tradicional", image_url="static/images/trufa_chocolate_recheada.jpg"),
            Trufa(sabor="Ninho", preco=5.00, descricao="Trufa de leite em pó", image_url="static/images/trufas_variadas_1.jpg"),
            Trufa(sabor="Ninho+brigadeiro", preco=5.00, descricao="Combinação de ninho e brigadeiro", image_url="static/images/trufas_variadas_2.jpg"),
            Trufa(sabor="Sensação", preco=5.00, descricao="Chocolate com recheio de morango", image_url="static/images/trufas_variadas_1.jpg"),
            Trufa(sabor="Côco", preco=5.00, descricao="Trufa de coco fresco", image_url="static/images/trufas_variadas_2.jpg"),
            Trufa(sabor="Amendoim", preco=5.00, descricao="Trufa de pasta de amendoim", image_url="static/images/trufas_variadas_1.jpg"),
            Trufa(sabor="Oreo", preco=5.00, descricao="Trufa com pedaços de Oreo", image_url="static/images/trufas_variadas_2.jpg"),
            Trufa(sabor="Limão", preco=5.00, descricao="Mousse de limão com chocolate branco", image_url="static/images/trufas_variadas_1.jpg"),
            Trufa(sabor="Napolitana", preco=5.00, descricao="Combinação de chocolate, morango e creme", image_url="static/images/trufas_variadas_2.jpg"),
            Trufa(sabor="Brigadeiro de morango", preco=5.00, descricao="Brigadeiro com sabor de morango", image_url="static/images/trufas_variadas_1.jpg"),
            Trufa(sabor="Brigadeiro de maracujá", preco=5.00, descricao="Brigadeiro com sabor de maracujá", image_url="static/images/trufas_variadas_2.jpg"),
            Trufa(sabor="Morango", preco=6.00, descricao="Trufa com pedaços de morango fresco", image_url="static/images/trufas_variadas_1.jpg"),
            Trufa(sabor="Uva", preco=6.00, descricao="Trufa com uva verde sem semente", image_url="static/images/trufas_variadas_2.jpg"),
            Trufa(sabor="Palha Italiana", preco=7.00, descricao="Doce de brigadeiro com biscoito", image_url="static/images/palha_italiana_gourmet.jpg")
        ]

        db.session.add_all(produtos)
        db.session.commit()
        print('Cardápio atualizado com sucesso!')

    app.run(debug=True)
