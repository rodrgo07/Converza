<div align="center">

# Converza

### O CRM de WhatsApp para o seu negócio crescer

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://business.whatsapp.com/)

---

**Pare de perder clientes por falta de organização.**
O Converza reúne todas as suas conversas do WhatsApp, Pipeline de vendas, Follow-ups e Equipe em um só lugar — simples, rápido e feito para pequenos negócios.

</div>

---

## Por que o Converza?

Se você ou sua equipe usam WhatsApp para falar com clientes, já sabe como é fácil:

- Mensagens se perdem entre centenas de conversas
- Clientes esquecem de serem contactados de volta
- Não sabe quantas vendas estão「quase fechadas」
- Não tem noção do desempenho da sua equipe

**O Converza resolve tudo isso com uma interface intuitiva que qualquer pessoa consegue usar.**

---

## Funcionalidades

### 📬 Inbox Unificada
Visual estilo WhatsApp com conversas organizadas por cliente. Veja o histórico completo, envie mensagens diretamente pelo sistema e responda rapidamente com **Respostas Rápidas** prontas.

### 🔥 Pipeline de Vendas (Kanban)
Arraste e solte negociações entre etapas: Novo Contato → Interessado → Orçamento → Negociação → Venda Fechada. Saiba exatamente quanto dinheiro está em cada fase do funil.

### ⏰ Follow-ups Inteligentes
Agende lembretes para entrar em contato com clientes. Nunca mais esqueça de fazer um retorno — o sistema avisa quando está na hora.

### 👥 Gestão de Equipe
Convide membros da equipe, defina permissões (Admin, Gerente, Vendedor, Suporte) e acompanhe a performance de cada um.

### 📊 Relatórios e Métricas
Veja em tempo real: valor total em vendas, ticket médio, taxa de conversão e muito mais. Exporte os dados em CSV.

### ✅ Tarefas
Crie e acompanhe tarefas do dia a dia vinculadas a clientes e membros da equipe.

### 🔖 Tags e Organização
Etique seus clientes com tags coloridas (VIP, Novo Cliente, Orçamento Pendente, etc.) para filtrar e encontrar qualquer pessoa rapidamente.

### 🔗 Integração WhatsApp
Conecte sua conta comercial do WhatsApp Business via Meta Cloud API. Envie mensagens de texto e mídia direto pelo Converza.

### 🌙 Modo Escuro
Interface com tema claro, escuro ou que acompanha o sistema do seu computador.

---

## Planos

| | **Gratuito** | **Essencial** | **Profissional** |
|---|---|---|---|
| **Preço** | R$ 0/mês | R$ 39,90/mês | R$ 79,90/mês |
| **Usuários** | 1 | 3 | 10 |
| **Clientes** | 100 | 1.000 | Ilimitado |
| **Pipeline de Vendas** | ✅ | ✅ | ✅ |
| **Follow-ups** | ✅ | ✅ | ✅ |
| **Respostas Rápidas** | ✅ | ✅ | ✅ |
| **Relatórios** | ✅ | ✅ | ✅ |
| **Integração WhatsApp** | ✅ | ✅ | ✅ |

---

## Arquitetura

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────────┐
│   Frontend   │◄─────►│     Backend      │◄─────►│   PostgreSQL    │
│   Next.js    │ REST  │     FastAPI      │       │  / SQLite (dev) │
│   porta 3000 │       │   porta 8000     │       │                 │
└──────────────┘       └──────────────────┘       └─────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ WhatsApp Cloud   │
                     │     API          │
                     └──────────────────┘
```

- **Multi-tenant:** Cada empresa tem seus dados isolados por `company_id`
- **Autenticação JWT:** Login seguro com tokens de 7 dias
- **Docker:** Setup com dois containers (backend + frontend) e volume persistente

---

## Stack Técnica

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, CSS Modules |
| Backend | FastAPI, Python, SQLAlchemy 2.0, Alembic |
| Banco de Dados | PostgreSQL (produção) / SQLite (desenvolvimento) |
| Autenticação | JWT (python-jose) + bcrypt |
| WhatsApp | Meta Cloud API v19.0 via httpx |
| Infraestrutura | Docker Compose |

---

## Como Rodar

### Com Docker (Recomendado)

```bash
git clone https://github.com/rodrgo07/Converza.git
cd Converza
docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Documentação da API: [http://localhost:8000/docs](http://localhost:8000/docs)

### Desenvolvimento Local

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Estrutura do Projeto

```
Converza/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── core/                # Configurações e segurança
│   │   ├── db/                  # Sessão do banco e seeds
│   │   ├── models/              # 12 tabelas SQLAlchemy
│   │   ├── schemas/             # 30+ schemas Pydantic
│   │   ├── api/endpoints/       # Rotas da API
│   │   └── services/            # WhatsApp Cloud API
│   ├── alembic/                 # Migrações do banco
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Pages (Auth + Dashboard)
│   │   ├── components/          # Sidebar, Header
│   │   ├── context/             # Auth, Theme, Toast
│   │   ├── lib/                 # API helpers
│   │   └── types/               # TypeScript types
│   └── package.json
└── README.md
```

---

## Modelos de Dados

| Tabela | Descrição |
|---|---|
| `companies` | Empresa (nome, segmento, telefone, logo) |
| `users` | Membros da equipe (nome, email, cargo) |
| `subscriptions` | Planos e assinaturas |
| `customers` | Clientes e leads |
| `conversations` | Conversas do WhatsApp |
| `messages` | Mensagens (texto, imagem, áudio, vídeo, documento) |
| `pipeline_stages` | Etapas do funil de vendas |
| `opportunities` | Negociações no pipeline |
| `follow_ups` | Lembretes de retorno |
| `tasks` | Tarefas operacionais |
| `quick_replies` | Templates de respostas rápidas |
| `tags` | Etiquetas para organização de clientes |

---

## Licença

Projeto proprietário. Todos os direitos reservados.

---

<div align="center">

**Converza** — Seu WhatsApp organizado. Suas vendas crescendo.

</div>
