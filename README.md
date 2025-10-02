# 🍫 Sistema de Doceria - Flask Web App

Uma aplicação web completa para gerenciamento de uma doceria, desenvolvida em Flask com interface moderna e responsiva.

## ✨ Funcionalidades

- **Sistema de Autenticação**: Login e registro de usuários
- **Cardápio Interativo**: Exibição das trufas disponíveis com preços
- **Carrinho de Compras**: Sistema completo para adicionar/remover produtos
- **Processo de Checkout**: Finalização de pedidos com confirmação
- **Interface Responsiva**: Design moderno que funciona em todos os dispositivos
- **Banco de Dados**: Sistema completo com SQLAlchemy (SQLite local / PostgreSQL produção)

## 🚀 Como Usar

### Acesso ao Sistema
1. Acesse o site deployado no Vercel
2. Crie uma conta clicando em "Registe-se aqui"
3. Faça login com suas credenciais
4. Navegue pelo cardápio e adicione trufas ao carrinho
5. Finalize seu pedido e receba a confirmação

### Produtos Disponíveis
- **Brigadeiro** - Trufa de brigadeiro tradicional (R$ 5,00)
- **Ninho** - Trufa de leite em pó (R$ 5,00)  
- **Ninho+Brigadeiro** - Combinação perfeita (R$ 5,00)
- **Sensação** - Chocolate com recheio de morango (R$ 5,00)
- **Coco** - Trufa de coco fresco (R$ 5,00)
- **Amendoim** - Trufa de pasta de amendoim (R$ 5,00)

## 🛠 Tecnologias Utilizadas

### Backend
- **Python 3.12** - Linguagem principal
- **Flask** - Framework web
- **Flask-SQLAlchemy** - ORM para banco de dados
- **Werkzeug** - Utilitários WSGI e hash de senhas
- **Gunicorn** - Servidor WSGI para produção

### Frontend
- **HTML5** - Estrutura das páginas
- **CSS3** - Estilização moderna com gradientes e animações
- **JavaScript** - Interatividade e validações
- **Google Fonts** - Tipografias Dancing Script e Inter

### Banco de Dados
- **SQLite** - Desenvolvimento local
- **PostgreSQL** - Produção (Vercel Postgres)

### Deploy
- **Vercel** - Plataforma de hosting
- **@vercel/python** - Runtime Python no Vercel

## 📁 Estrutura do Projeto

```
doceria_sistema/
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── vercel.json           # Configuração do Vercel
├── README.md             # Documentação
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── login.html        # Página de login
│   ├── register.html     # Página de registro
│   ├── cardapio.html     # Cardápio de produtos
│   ├── carrinho.html     # Carrinho de compras
│   └── obrigado.html     # Confirmação de pedido
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos CSS
│   ├── js/
│   │   └── script.js     # JavaScript interativo
│   └── background.jpg    # Imagem de fundo
└── instance/             # Dados locais (SQLite)
    └── doceria.db        # Banco de dados local
```

## 🔧 Configuração e Deploy

### Configuração no Vercel

1. **Conecte o repositório GitHub ao Vercel**
2. **Configure as variáveis de ambiente** (opcional):
   - `SECRET_KEY` - Chave secreta para sessões
   - `POSTGRES_URL` - URL do banco PostgreSQL (se usar)

3. **Deploy automático**: O Vercel detectará automaticamente as configurações do `vercel.json`

### Configuração do Banco de Dados

O sistema inicializa automaticamente:
- Cria as tabelas necessárias no primeiro acesso
- Popula o cardápio com produtos iniciais
- Para reset manual: acesse `/setup-database-12345`

## 🎨 Design e UX

- **Tema Moderno**: Gradientes coloridos e glassmorphism
- **Animações Suaves**: Transições e hover effects
- **Responsivo**: Funciona perfeitamente em mobile e desktop
- **Acessibilidade**: Contrastes adequados e navegação por teclado
- **Feedback Visual**: Mensagens flash e estados de loading

## 🔒 Segurança

- Senhas hasheadas com Werkzeug
- Proteção de rotas com decoradores
- Validações de formulário client e server-side
- Configuração segura de sessões Flask

## 📱 Funcionalidades Interativas

- Auto-dismiss de mensagens após 5 segundos
- Validação de formulários em tempo real
- Confirmação de checkout
- Atalhos de teclado (Ctrl+Enter, Esc)
- Estados de loading em botões
- Atualização dinâmica do carrinho

## 🚨 Solução de Problemas

### Erro 404 no Vercel
✅ **Resolvido**: A estrutura do projeto foi reorganizada com:
- `vercel.json` atualizado para servir arquivos estáticos
- Templates movidos para pasta `templates/`
- CSS/JS organizados em `static/css/` e `static/js/`

### Banco de Dados
- Local: SQLite criado automaticamente em `instance/`
- Produção: PostgreSQL via `POSTGRES_URL` environment variable

## 📄 Licença

Este projeto é de uso educacional e demonstrativo.

## 👨‍💻 Desenvolvimento

Para executar localmente:

```bash
pip install -r requirements.txt
python app.py
```

Acesse: `http://localhost:5000`

---

**Sistema de Doceria** - Uma experiência completa de e-commerce para doces artesanais! 🍫✨