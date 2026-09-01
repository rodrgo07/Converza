import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal, Base, engine
from app.models import (
    Company, User, Tag, Customer, CustomerTag, PipelineStage, PipelineStageType,
    Opportunity, Conversation, Message, FollowUp, Task, QuickReply, WhatsAppAccount,
    Notification, Subscription, UserRole, MessageDirection, MessageType, MessageStatus,
    FollowUpStatus, TaskStatus
)
from app.core.security import get_password_hash

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    existing_user = db.query(User).filter(User.email == 'rodrigo@lojadodigo.com.br').first()
    if existing_user:
        print('Database already seeded.')
        db.close()
        return

    print('Seeding demo data for Converza CRM...')

    # 1. Company
    company = Company(
        name='Loja do Rodrigo Multimarcas',
        segment='Loja de Roupas & Calçados',
        team_size='2 a 3 pessoas',
        whatsapp_usage='Vendas e Atendimento',
        phone='+55 11 98888-7777'
    )
    db.add(company)
    db.flush()

    # 2. Subscription
    sub = Subscription(
        company_id=company.id,
        plan='essential',
        status='active',
        max_users=3,
        max_customers=1000,
        price_cents=3990,
        current_period_end=datetime.now(timezone.utc) + timedelta(days=28)
    )
    db.add(sub)

    # 3. Users
    admin_user = User(
        company_id=company.id,
        name='Rodrigo Alcantara',
        email='rodrigo@lojadodigo.com.br',
        phone='+55 11 98888-7777',
        hashed_password=get_password_hash('Converza2026!'),
        role=UserRole.ADMIN,
        onboarding_completed=True,
        theme_preference='system'
    )
    db.add(admin_user)
    db.flush()

    sales_user = User(
        company_id=company.id,
        name='Juliana Vendedora',
        email='juliana@lojadodigo.com.br',
        phone='+55 11 97777-6666',
        hashed_password=get_password_hash('Converza2026!'),
        role=UserRole.SALES,
        onboarding_completed=True,
        theme_preference='system'
    )
    db.add(sales_user)
    db.flush()

    # 4. WhatsApp Account
    wa = WhatsAppAccount(
        company_id=company.id,
        phone_number_id='10928374619283',
        business_account_id='8372619402918',
        display_phone_number='+55 11 98888-7777',
        verified_name='Loja do Rodrigo Oficial',
        access_token='EAAB_demo_token_valid',
        is_connected=True,
        status='connected',
        webhook_verify_token=f'converza_token_{company.id}'
    )
    db.add(wa)

    # 5. Pipeline Stages
    stages_data = [
        ('Novo contato', PipelineStageType.NEW, 0, '#3B82F6'),
        ('Interessado', PipelineStageType.INTERESTED, 1, '#10B981'),
        ('Orçamento enviado', PipelineStageType.QUOTE, 2, '#F59E0B'),
        ('Em negociação', PipelineStageType.NEGOTIATION, 3, '#8B5CF6'),
        ('Venda fechada', PipelineStageType.SALE, 4, '#10B981'),
        ('Pós-venda', PipelineStageType.POST_SALE, 5, '#06B6D4'),
        ('Perdido', PipelineStageType.LOST, 6, '#EF4444'),
    ]
    stages = []
    for name, stype, order, color in stages_data:
        stage = PipelineStage(
            company_id=company.id,
            name=name,
            stage_type=stype,
            order=order,
            color=color
        )
        db.add(stage)
        stages.append(stage)
    db.flush()

    # 6. Tags
    tags_data = [
        ('Novo cliente', '#3B82F6'),
        ('VIP', '#F59E0B'),
        ('Interessado', '#10B981'),
        ('Aguardando resposta', '#EC4899'),
        ('Orçamento pendente', '#8B5CF6'),
        ('Instagram Direct', '#E1306C'),
        ('Indicação', '#14B8A6'),
    ]
    tags = []
    for name, color in tags_data:
        t = Tag(company_id=company.id, name=name, color=color)
        db.add(t)
        tags.append(t)
    db.flush()

    # 7. Quick Replies
    qrs = [
        ('/ola', 'Saudação Padrão', 'Olá! Tudo bem? Seja muito bem-vindo(a) à Loja do Rodrigo. Como posso te ajudar hoje? 😊'),
        ('/orcamento', 'Solicitar Medidas/Modelo', 'Claro! Para eu te passar as fotos e valores certinhos dos modelos disponíveis, qual seu tamanho e cor de preferência? 👟👕'),
        ('/pagamento', 'Formas de Pagamento e Pix', 'Trabalhamos com Pix com 5% de desconto à vista, ou parcelamento em até 6x sem juros no cartão! 💳 Chave Pix CNPJ: 12.345.678/0001-90'),
        ('/frete', 'Envio e Rastreio', 'Enviamos para todo o Brasil via Sedex ou transportadora expressa. Se você for da capital, entregamos via motoboy no mesmo dia! 🛵📦'),
        ('/posvenda', 'Satisfação Pós-compra', 'Olá! Vi aqui que seu pedido chegou. Deu tudo certo com os produtos e o tamanho? Qualquer dúvida estamos 100% à disposição! 🌟')
    ]
    for sc, tit, cont in qrs:
        qr = QuickReply(company_id=company.id, shortcut=sc, title=tit, content=cont)
        db.add(qr)

    # 8. Customers & Conversations
    customers_data = [
        {
            'name': 'Carlos Eduardo Silva',
            'phone': '+55 11 99123-4567',
            'email': 'carlos.silva@email.com',
            'company_name': 'Silva Advocacia',
            'notes': 'Cliente interessado em camisas sociais e tênis casual. Prefere entrega rápida.',
            'total_spent': 1250.0,
            'orders_count': 3,
            'tags': [tags[1], tags[6]], # VIP, Indicacao
            'stage': stages[3], # Negociacao
            'opp_title': 'Kit 4 Camisas Slim Fit + Sapato Casual',
            'opp_value': 890.0,
            'last_msg': 'Queria saber o preço daquele modelo que você postou no status.',
            'unread': 1,
            'assigned': admin_user
        },
        {
            'name': 'Mariana Souza Dias',
            'phone': '+55 11 98234-5678',
            'email': 'mariana.souza@gmail.com',
            'company_name': '',
            'notes': 'Comprou vestido de festa no mês passado. Excelente compradora.',
            'total_spent': 2450.0,
            'orders_count': 5,
            'tags': [tags[1], tags[2]], # VIP, Interessado
            'stage': stages[4], # Venda Fechada
            'opp_title': 'Coleção Primavera / Vestido Floral',
            'opp_value': 620.0,
            'last_msg': 'Muito obrigada pelo atendimento impecável de sempre!',
            'unread': 0,
            'assigned': sales_user
        },
        {
            'name': 'Lucas Fernandes Costa',
            'phone': '+55 21 97345-6789',
            'email': 'lucas.costa@techsol.com.br',
            'company_name': 'TechSol Informática',
            'notes': 'Quer orçar uniformes polo bordados para 8 funcionários.',
            'total_spent': 0.0,
            'orders_count': 0,
            'tags': [tags[0], tags[4]], # Novo, Orcamento pendente
            'stage': stages[2], # Orcamento
            'opp_title': '16 Polos Bordadas Logo Empresa',
            'opp_value': 1440.0,
            'last_msg': 'Conseguiu fechar a proposta com o desconto que te pedi?',
            'unread': 2,
            'assigned': admin_user
        },
        {
            'name': 'Beatriz Mendes Rocha',
            'phone': '+55 31 99456-7890',
            'email': 'beatriz.mendes@uol.com.br',
            'company_name': 'Studio Bea Hair',
            'notes': 'Veio do anúncio do Instagram procurando calçados confortáveis.',
            'total_spent': 0.0,
            'orders_count': 0,
            'tags': [tags[0], tags[5]], # Novo, Instagram
            'stage': stages[1], # Interessado
            'opp_title': 'Tênis Ortopédico Confort Plus Feminino',
            'opp_value': 299.90,
            'last_msg': 'Tem o número 37 na cor bege ainda disponível?',
            'unread': 0,
            'assigned': sales_user
        },
        {
            'name': 'Roberto Oliveira Santos',
            'phone': '+55 41 98567-8901',
            'email': 'roberto.santos@curitiba.com',
            'company_name': 'Santos Logística',
            'notes': 'Cliente antigo. Fez pedido semana passada, em fase de pós-venda.',
            'total_spent': 3890.0,
            'orders_count': 8,
            'tags': [tags[1]],
            'stage': stages[5], # Pos-venda
            'opp_title': 'Jaqueta Corta-Vento Térmica',
            'opp_value': 450.0,
            'last_msg': 'O pacote chegou certinho aqui em Curitiba, valeu!',
            'unread': 0,
            'assigned': admin_user
        },
        {
            'name': 'Camila Vasconcelos',
            'phone': '+55 71 99678-9012',
            'email': 'camila.v@salvador.ba.gov.br',
            'company_name': '',
            'notes': 'Lead frio do mês passado.',
            'total_spent': 0.0,
            'orders_count': 0,
            'tags': [tags[3]],
            'stage': stages[6], # Perdido
            'opp_title': 'Kit Acessórios de Couro',
            'opp_value': 350.0,
            'last_msg': 'Acabei comprando em uma loja física aqui perto, obrigado.',
            'unread': 0,
            'assigned': sales_user
        },
        {
            'name': 'Felipe Gabriel Martins',
            'phone': '+55 19 98789-0123',
            'email': 'felipe.martins@agro.com.br',
            'company_name': 'Agro Martins',
            'notes': 'Interessado em botas impermeáveis para campo.',
            'total_spent': 860.0,
            'orders_count': 2,
            'tags': [tags[2], tags[6]],
            'stage': stages[0], # Novo
            'opp_title': '2 Pares Botina Couro Legítimo',
            'opp_value': 580.0,
            'last_msg': 'Boa noite! Vocês têm bota cano médio tamanho 42?',
            'unread': 1,
            'assigned': admin_user
        }
    ]

    for item in customers_data:
        cust = Customer(
            company_id=company.id,
            assigned_user_id=item['assigned'].id,
            name=item['name'],
            phone=item['phone'],
            email=item['email'],
            company_name=item['company_name'],
            notes=item['notes'],
            total_spent=item['total_spent'],
            orders_count=item['orders_count'],
            last_interaction=datetime.now(timezone.utc) - timedelta(minutes=15)
        )
        db.add(cust)
        db.flush()

        for t in item['tags']:
            db.add(CustomerTag(customer_id=cust.id, tag_id=t.id))

        opp = Opportunity(
            company_id=company.id,
            customer_id=cust.id,
            stage_id=item['stage'].id,
            assigned_user_id=item['assigned'].id,
            title=item['opp_title'],
            value=item['opp_value'],
            probability=70,
            expected_close_date=datetime.now(timezone.utc) + timedelta(days=7),
            notes='Oportunidade gerada automaticamente via atendimento de WhatsApp.'
        )
        db.add(opp)

        conv = Conversation(
            company_id=company.id,
            customer_id=cust.id,
            assigned_user_id=item['assigned'].id,
            status='open',
            unread_count=item['unread'],
            last_message_text=item['last_msg'],
            last_message_time=datetime.now(timezone.utc) - timedelta(minutes=25)
        )
        db.add(conv)
        db.flush()

        # Messages history
        m1 = Message(
            conversation_id=conv.id,
            sender_id=None,
            direction=MessageDirection.INBOUND,
            message_type=MessageType.TEXT,
            content='Olá, vi o anúncio de vocês e queria mais informações!',
            created_at=datetime.now(timezone.utc) - timedelta(hours=3)
        )
        m2 = Message(
            conversation_id=conv.id,
            sender_id=item['assigned'].id,
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.TEXT,
            content='Olá! Tudo bem? Que ótimo te receber aqui no nosso canal direto de WhatsApp. Vou te enviar nosso catálogo completo!',
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        m3 = Message(
            conversation_id=conv.id,
            sender_id=None,
            direction=MessageDirection.INBOUND,
            message_type=MessageType.TEXT,
            content=item['last_msg'],
            created_at=datetime.now(timezone.utc) - timedelta(minutes=25)
        )
        db.add_all([m1, m2, m3])

        # Follow Up for active ones
        if item['stage'].stage_type in [PipelineStageType.NEW, PipelineStageType.INTERESTED, PipelineStageType.QUOTE, PipelineStageType.NEGOTIATION]:
            fu = FollowUp(
                company_id=company.id,
                customer_id=cust.id,
                assigned_user_id=item['assigned'].id,
                title=f'Retornar {cust.name.split()[0]} sobre {item["opp_title"]}',
                notes=f'Verificar se aprovou as opções e fechar link de pagamento.',
                due_date=datetime.now(timezone.utc) + timedelta(hours=4),
                status=FollowUpStatus.PENDING
            )
            db.add(fu)

    # 9. Tasks
    tasks_demo = [
        ('Confirmar envio do pedido #1042 pelo Sedex', 'Verificar código de rastreamento no Correios', datetime.now(timezone.utc) + timedelta(hours=2), admin_user.id),
        ('Enviar catálogo de novos lançamentos de Setembro', 'Disparar mensagens para os clientes VIP', datetime.now(timezone.utc) + timedelta(days=1), sales_user.id),
        ('Conferir pagamentos Pix pendentes no banco', 'Cruzar comprovantes com pedidos aprovados', datetime.now(timezone.utc) + timedelta(hours=5), admin_user.id)
    ]
    for t_tit, t_desc, t_due, t_uid in tasks_demo:
        t = Task(
            company_id=company.id,
            assigned_user_id=t_uid,
            title=t_tit,
            description=t_desc,
            due_date=t_due,
            status=TaskStatus.PENDING
        )
        db.add(t)

    # 10. Notifications
    notifs = [
        ('Novo lead pelo WhatsApp', 'Carlos Eduardo Silva enviou uma mensagem pedindo valores.', 'message', '/inbox'),
        ('Follow-up urgente hoje', 'Você tem 3 retornos programados para esta tarde.', 'followup', '/followups'),
        ('Meta de vendas da semana', 'Sua empresa atingiu 80% da meta semanal!', 'sale', '/pipeline'),
    ]
    for n_tit, n_msg, n_tp, n_lk in notifs:
        n = Notification(
            company_id=company.id,
            user_id=admin_user.id,
            title=n_tit,
            message=n_msg,
            notification_type=n_tp,
            link=n_lk,
            is_read=False
        )
        db.add(n)

    db.commit()
    print('Seeding completed successfully! Default login: rodrigo@lojadodigo.com.br / Converza2026!')
    db.close()

if __name__ == '__main__':
    seed()
