import React from "react";
import Link from "next/link";
import styles from "./Legal.module.css";
import { Shield, ArrowLeft } from "lucide-react";

export default function PrivacyPolicyPage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link href="/" className={styles.backLink}>
          <ArrowLeft size={16} />
          <span>Voltar ao Converza</span>
        </Link>
        <div className={styles.badge}>
          <Shield size={16} />
          <span>LGPD • Lei nº 13.709/2018</span>
        </div>
      </header>

      <main className={styles.card}>
        <h1 className={styles.title}>Política de Privacidade e Proteção de Dados</h1>
        <span className={styles.updatedAt}>Última atualização: Agosto de 2026</span>

        <section className={styles.section}>
          <h2>1. Introdução e Compromisso</h2>
          <p>
            O <strong>Converza</strong> é uma plataforma de gestão e relacionamento com clientes via WhatsApp voltada para pequenas e médias empresas brasileiras. A privacidade, segurança e transparência no tratamento de dados pessoais são pilares fundamentais da nossa arquitetura, em estrita observância à Lei Geral de Proteção de Dados Pessoais (LGPD - Lei nº 13.709/2018).
          </p>
        </section>

        <section className={styles.section}>
          <h2>2. Papéis no Tratamento de Dados</h2>
          <p>
            • <strong>Converza (Operador):</strong> Processa os dados cadastrais e mensagens em nome das empresas contratantes para a exclusiva finalidade de viabilizar o atendimento e gestão comercial.<br />
            • <strong>Sua Empresa (Controlador):</strong> É responsável por coletar, gerenciar e definir a base legal adequada (ex: execução de contrato, legítimo interesse ou consentimento) para o contato com seus clientes finais.
          </p>
        </section>

        <section className={styles.section}>
          <h2>3. Dados Pessoais Coletados e Finalidades</h2>
          <p>
            Coletamos apenas os dados estritamente necessários para a prestação do serviço (Minimização de Dados):<br />
            • <strong>Dados Cadastrais do Usuário:</strong> Nome, e-mail de acesso e telefone para autenticação e gestão de equipe.<br />
            • <strong>Dados de Clientes e Atendimento:</strong> Nome, número de WhatsApp, etiquetas de compra e histórico de mensagens para fins de atendimento ao cliente e suporte operacional.<br />
            • <strong>Não coletamos deliberadamente dados pessoais sensíveis</strong> (saúde, biometria, religião, etc.).
          </p>
        </section>

        <section className={styles.section}>
          <h2>4. Direitos dos Titulares (Art. 18 da LGPD)</h2>
          <p>
            O Converza disponibiliza ferramentas técnicas para que os controladores atendam integralmente às requisições dos titulares:<br />
            • <strong>Confirmação e Acesso:</strong> Visualização completa do perfil e histórico.<br />
            • <strong>Portabilidade / Exportação:</strong> Exportação estruturada em JSON de todos os dados vinculados ao titular.<br />
            • <strong>Anonimização e Eliminação:</strong> Mecanismo de anonimização e exclusão irreversível de dados cadastrais e mensagens.
          </p>
        </section>

        <section className={styles.section}>
          <h2>5. Segurança e Isolamento Multi-Tenant</h2>
          <p>
            Todos os dados são isolados por empresa (multi-tenant) no banco de dados e na API. As credenciais e tokens da Meta WhatsApp Cloud API são mantidos protegidos no servidor, nunca trafegando para o navegador do cliente. As senhas são protegidas por hash criptográfico seguro (bcrypt).
          </p>
        </section>

        <section className={styles.section}>
          <h2>6. Contato com o Encarregado de Dados (DPO)</h2>
          <p>
            Para exercer direitos ou tirar dúvidas sobre o tratamento de dados pessoais, entre em contato através do canal de privacidade: <strong>privacidade@converza.com.br</strong>.
          </p>
        </section>
      </main>
    </div>
  );
}
