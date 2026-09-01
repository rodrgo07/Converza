import React from "react";
import Link from "next/link";
import styles from "../privacidade/Legal.module.css";
import { FileText, ArrowLeft } from "lucide-react";

export default function TermsPage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link href="/" className={styles.backLink}>
          <ArrowLeft size={16} />
          <span>Voltar ao Converza</span>
        </Link>
        <div className={styles.badge}>
          <FileText size={16} />
          <span>Termos de Serviço</span>
        </div>
      </header>

      <main className={styles.card}>
        <h1 className={styles.title}>Termos de Uso do Converza</h1>
        <span className={styles.updatedAt}>Última atualização: Agosto de 2026</span>

        <section className={styles.section}>
          <h2>1. Objeto do Serviço</h2>
          <p>
            O Converza fornece software como serviço (SaaS) para gestão de conversas, CRM comercial e atendimento via WhatsApp Business Platform oficial. O acesso é concedido mediante assinatura ativa do plano contratado.
          </p>
        </section>

        <section className={styles.section}>
          <h2>2. Responsabilidades do Usuário</h2>
          <p>
            • O usuário compromete-se a utilizar a plataforma em conformidade com as diretrizes e políticas oficiais da Meta/WhatsApp (WhatsApp Business Policy).<br />
            • É estritamente proibido o uso da plataforma para disparo de mensagens não solicitadas (SPAM), envio de conteúdo ilícito, fraudulentos ou lesivos a terceiros.<br />
            • O contratante é responsável pela guarda segura de suas credenciais e senhas de acesso.
          </p>
        </section>

        <section className={styles.section}>
          <h2>3. Planos e Limites de Uso</h2>
          <p>
            Cada plano possui limites técnicos claros de número de usuários e clientes cadastrados. Tentativas de contornar limites técnicos via automação ou scripts externos ensejarão o bloqueio da conta.
          </p>
        </section>

        <section className={styles.section}>
          <h2>4. Disponibilidade e Suporte</h2>
          <p>
            Trabalhamos para manter a plataforma disponível 24/7. Eventuais indisponibilidades decorrentes de manutenção programada ou falhas de infraestrutura de terceiros (Meta Cloud API, provedores de nuvem) serão comunicadas nos canais oficiais.
          </p>
        </section>

        <section className={styles.section}>
          <h2>5. Cancelamento e Encerramento</h2>
          <p>
            O usuário pode cancelar sua assinatura a qualquer momento através do painel de configurações. Os dados vinculados à conta poderão ser exportados ou excluídos conforme a política de privacidade e a LGPD.
          </p>
        </section>
      </main>
    </div>
  );
}
