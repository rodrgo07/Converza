"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { useTheme } from "@/context/ThemeContext";
import { apiFetch, formatCurrency } from "@/lib/api";
import { WhatsAppAccount, Subscription } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Settings.module.css";
import {
  Settings as SettingsIcon,
  User,
  Building,
  MessageSquare,
  CreditCard,
  Bell,
  Sun,
  Moon,
  Laptop,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  Sparkles
} from "lucide-react";

export default function SettingsPage() {
  const { user, company, refreshCompany, updateUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState<"account" | "company" | "whatsapp" | "subscription" | "appearance">("whatsapp");

  // User form
  const [userName, setUserName] = useState(user?.name || "");
  const [userPhone, setUserPhone] = useState(user?.phone || "");

  // Company form
  const [compName, setCompName] = useState(company?.name || "");
  const [compSegment, setCompSegment] = useState(company?.segment || "");

  // WhatsApp
  const [waAccount, setWaAccount] = useState<WhatsAppAccount | null>(null);
  const [isConnectingWa, setIsConnectingWa] = useState(false);

  // Subscription
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isUpgrading, setIsUpgrading] = useState(false);

  useEffect(() => {
    if (user) {
      setUserName(user.name);
      setUserPhone(user.phone || "");
    }
    if (company) {
      setCompName(company.name);
      setCompSegment(company.segment || "");
    }
    loadWaStatus();
    loadSubscription();
  }, [user, company]);

  const loadWaStatus = async () => {
    try {
      const data = await apiFetch<WhatsAppAccount>("/whatsapp/status");
      setWaAccount(data);
    } catch {
      // ignore
    }
  };

  const loadSubscription = async () => {
    try {
      const sub = await apiFetch<Subscription>("/subscription");
      setSubscription(sub);
    } catch {
      // ignore
    }
  };

  const handleSaveUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch(`/team/${user?.id}`, {
        method: "PUT",
        body: JSON.stringify({ name: userName, phone: userPhone }),
      });
      updateUser({ name: userName, phone: userPhone });
      success("Perfil atualizado com sucesso!");
    } catch {
      error("Erro ao salvar perfil.");
    }
  };

  const handleSaveCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/company", {
        method: "PUT",
        body: JSON.stringify({ name: compName, segment: compSegment }),
      });
      await refreshCompany();
      success("Dados da empresa salvos com sucesso!");
    } catch {
      error("Erro ao salvar empresa.");
    }
  };

  const handleToggleWhatsApp = async () => {
    try {
      setIsConnectingWa(true);
      if (waAccount?.is_connected) {
        const disconnected = await apiFetch<WhatsAppAccount>("/whatsapp/disconnect", { method: "POST" });
        setWaAccount(disconnected);
        success("WhatsApp desconectado.");
      } else {
        const connected = await apiFetch<WhatsAppAccount>("/whatsapp/connect", {
          method: "POST",
          body: JSON.stringify({
            phone_number_id: "10928374619283",
            business_account_id: "8372619402918",
            display_phone_number: "+55 11 98888-7777",
            verified_name: company?.name || "Empresa Oficial",
          }),
        });
        setWaAccount(connected);
        success("WhatsApp Cloud API conectado com sucesso!");
      }
    } catch {
      error("Erro ao alterar conexão do WhatsApp.");
    } finally {
      setIsConnectingWa(false);
    }
  };

  const handleUpgradePlan = async (plan: "free" | "essential" | "professional") => {
    try {
      setIsUpgrading(true);
      const updated = await apiFetch<Subscription>("/subscription/upgrade", {
        method: "POST",
        body: JSON.stringify({ plan }),
      });
      setSubscription(updated);
      success(`Plano alterado para ${plan.toUpperCase()} com sucesso!`);
    } catch {
      error("Erro ao alterar plano.");
    } finally {
      setIsUpgrading(false);
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Configurações"
        subtitle="Gerencie sua integração oficial do WhatsApp, planos e dados da conta"
      />

      <div className={styles.content}>
        <div className={styles.settingsLayout}>
          {/* Settings Sidebar Tabs */}
          <div className={styles.navTabs}>
            <button
              className={`${styles.navTab} ${activeTab === "whatsapp" ? styles.active : ""}`}
              onClick={() => setActiveTab("whatsapp")}
            >
              <MessageSquare size={16} />
              <span>Integração WhatsApp</span>
            </button>
            <button
              className={`${styles.navTab} ${activeTab === "subscription" ? styles.active : ""}`}
              onClick={() => setActiveTab("subscription")}
            >
              <CreditCard size={16} />
              <span>Plano & Assinatura</span>
            </button>
            <button
              className={`${styles.navTab} ${activeTab === "company" ? styles.active : ""}`}
              onClick={() => setActiveTab("company")}
            >
              <Building size={16} />
              <span>Dados da Empresa</span>
            </button>
            <button
              className={`${styles.navTab} ${activeTab === "account" ? styles.active : ""}`}
              onClick={() => setActiveTab("account")}
            >
              <User size={16} />
              <span>Minha Conta</span>
            </button>
            <button
              className={`${styles.navTab} ${activeTab === "appearance" ? styles.active : ""}`}
              onClick={() => setActiveTab("appearance")}
            >
              <Sun size={16} />
              <span>Aparência</span>
            </button>
          </div>

          {/* Settings Tab Content */}
          <div className={styles.tabContentCard}>
            {/* WHATSAPP TAB */}
            {activeTab === "whatsapp" && (
              <div className={styles.tabBody}>
                <h3 className={styles.tabTitle}>WhatsApp Business Platform (Cloud API)</h3>
                <p className={styles.tabSubtitle}>
                  Conexão 100% oficial e segura diretamente com a Meta. Sem risco de banimento.
                </p>

                <div className={styles.statusBox}>
                  <div className={styles.statusRow}>
                    <div className={styles.statusLabel}>
                      <span className={styles.statusDot} style={{ backgroundColor: waAccount?.is_connected ? "#10b981" : "#ef4444" }} />
                      <strong>Status da Conexão:</strong>{" "}
                      {waAccount?.is_connected ? (
                        <span style={{ color: "#10b981", fontWeight: 700 }}>Conectado e Operante</span>
                      ) : (
                        <span style={{ color: "#ef4444", fontWeight: 700 }}>Desconectado</span>
                      )}
                    </div>
                    <button
                      onClick={handleToggleWhatsApp}
                      disabled={isConnectingWa}
                      className={waAccount?.is_connected ? styles.disconnectBtn : styles.connectBtn}
                    >
                      {waAccount?.is_connected ? "Desconectar Número" : "Conectar Número Agora"}
                    </button>
                  </div>

                  {waAccount?.is_connected && (
                    <div className={styles.connectedDetails}>
                      <div className={styles.fieldItem}>
                        <span>Número Conectado:</span>
                        <strong>{waAccount.display_phone_number || "+55 11 98888-7777"}</strong>
                      </div>
                      <div className={styles.fieldItem}>
                        <span>Nome Verificado:</span>
                        <strong>{waAccount.verified_name || company?.name}</strong>
                      </div>
                      <div className={styles.fieldItem}>
                        <span>Webhook Verify Token:</span>
                        <code>{waAccount.webhook_verify_token}</code>
                      </div>
                    </div>
                  )}
                </div>

                <div className={styles.metaNotice}>
                  <Sparkles size={16} className={styles.metaIcon} />
                  <div>
                    <strong>Integração Oficial de WhatsApp</strong>
                    <p>Todas as mensagens enviadas e recebidas respeitam as diretrizes oficiais de entrega instantânea da Meta.</p>
                  </div>
                </div>
              </div>
            )}

            {/* SUBSCRIPTION TAB */}
            {activeTab === "subscription" && (
              <div className={styles.tabBody}>
                <h3 className={styles.tabTitle}>Planos e Preços</h3>
                <p className={styles.tabSubtitle}>
                  Escolha o plano ideal para a escala do seu negócio. Cancele quando quiser.
                </p>

                <div className={styles.plansGrid}>
                  {/* Gratuito */}
                  <div className={`${styles.planCard} ${subscription?.plan === "free" ? styles.currentPlan : ""}`}>
                    <h4 className={styles.planName}>Gratuito</h4>
                    <span className={styles.planPrice}>R$ 0 <span>/mês</span></span>
                    <ul className={styles.planFeatures}>
                      <li>✓ 1 usuário</li>
                      <li>✓ Até 100 clientes</li>
                      <li>✓ CRM e Kanban básico</li>
                      <li>✓ Dashboard em tempo real</li>
                    </ul>
                    <button
                      disabled={subscription?.plan === "free" || isUpgrading}
                      onClick={() => handleUpgradePlan("free")}
                      className={styles.planBtn}
                    >
                      {subscription?.plan === "free" ? "Plano Atual" : "Escolher Gratuito"}
                    </button>
                  </div>

                  {/* Essencial */}
                  <div className={`${styles.planCard} ${styles.highlightedPlan} ${subscription?.plan === "essential" ? styles.currentPlan : ""}`}>
                    <div className={styles.popularBadge}>Mais Popular</div>
                    <h4 className={styles.planName}>Essencial</h4>
                    <span className={styles.planPrice}>R$ 39,90 <span>/mês</span></span>
                    <ul className={styles.planFeatures}>
                      <li>✓ 3 usuários</li>
                      <li>✓ 1.000 clientes</li>
                      <li>✓ WhatsApp Oficial integrado</li>
                      <li>✓ Automações básicas</li>
                      <li>✓ Relatórios e métricas</li>
                    </ul>
                    <button
                      disabled={subscription?.plan === "essential" || isUpgrading}
                      onClick={() => handleUpgradePlan("essential")}
                      className={`${styles.planBtn} ${styles.primaryPlanBtn}`}
                    >
                      {subscription?.plan === "essential" ? "Plano Atual" : "Assinar Essencial"}
                    </button>
                  </div>

                  {/* Profissional */}
                  <div className={`${styles.planCard} ${subscription?.plan === "professional" ? styles.currentPlan : ""}`}>
                    <h4 className={styles.planName}>Profissional</h4>
                    <span className={styles.planPrice}>R$ 79,90 <span>/mês</span></span>
                    <ul className={styles.planFeatures}>
                      <li>✓ 10 usuários</li>
                      <li>✓ Clientes ilimitados</li>
                      <li>✓ Múltiplos números WhatsApp</li>
                      <li>✓ Relatórios avançados</li>
                      <li>✓ Suporte prioritário</li>
                    </ul>
                    <button
                      disabled={subscription?.plan === "professional" || isUpgrading}
                      onClick={() => handleUpgradePlan("professional")}
                      className={styles.planBtn}
                    >
                      {subscription?.plan === "professional" ? "Plano Atual" : "Assinar Profissional"}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* COMPANY TAB */}
            {activeTab === "company" && (
              <form onSubmit={handleSaveCompany} className={styles.tabBody}>
                <h3 className={styles.tabTitle}>Dados da Empresa</h3>
                <p className={styles.tabSubtitle}>Identificação do seu negócio</p>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Nome da Empresa</label>
                  <input
                    type="text"
                    value={compName}
                    onChange={(e) => setCompName(e.target.value)}
                    className={styles.input}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Segmento de Atuação</label>
                  <input
                    type="text"
                    value={compSegment}
                    onChange={(e) => setCompSegment(e.target.value)}
                    className={styles.input}
                  />
                </div>

                <button type="submit" className={styles.saveBtn}>Salvar Empresa</button>
              </form>
            )}

            {/* ACCOUNT TAB */}
            {activeTab === "account" && (
              <form onSubmit={handleSaveUser} className={styles.tabBody}>
                <h3 className={styles.tabTitle}>Minha Conta</h3>
                <p className={styles.tabSubtitle}>Atualize seus dados de contato e login</p>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Seu Nome</label>
                  <input
                    type="text"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    className={styles.input}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Telefone de Contato</label>
                  <input
                    type="text"
                    value={userPhone}
                    onChange={(e) => setUserPhone(e.target.value)}
                    className={styles.input}
                  />
                </div>

                <button type="submit" className={styles.saveBtn}>Salvar Perfil</button>
              </form>
            )}

            {/* APPEARANCE TAB */}
            {activeTab === "appearance" && (
              <div className={styles.tabBody}>
                <h3 className={styles.tabTitle}>Tema da Interface</h3>
                <p className={styles.tabSubtitle}>Alterne entre modo claro, escuro ou automático do sistema</p>

                <div className={styles.themeCardsGrid}>
                  <button
                    className={`${styles.themeSelectCard} ${theme === "light" ? styles.selectedTheme : ""}`}
                    onClick={() => setTheme("light")}
                  >
                    <Sun size={24} />
                    <span>Tema Claro</span>
                  </button>

                  <button
                    className={`${styles.themeSelectCard} ${theme === "dark" ? styles.selectedTheme : ""}`}
                    onClick={() => setTheme("dark")}
                  >
                    <Moon size={24} />
                    <span>Tema Escuro</span>
                  </button>

                  <button
                    className={`${styles.themeSelectCard} ${theme === "system" ? styles.selectedTheme : ""}`}
                    onClick={() => setTheme("system")}
                  >
                    <Laptop size={24} />
                    <span>Padrão do Sistema</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}