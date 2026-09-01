"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { apiFetch, formatCurrency, formatPhone } from "@/lib/api";
import { DashboardMetrics, FollowUp, Conversation } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Dashboard.module.css";
import {
  MessageSquare,
  Users,
  Target,
  DollarSign,
  CalendarClock,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Clock,
  CheckCircle,
  ExternalLink,
  ChevronRight
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [chartPeriod, setChartPeriod] = useState<"week" | "month">("week");

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch<DashboardMetrics>("/dashboard/metrics");
      setMetrics(data);
    } catch (err) {
      console.error("Failed to load dashboard metrics", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Bom dia";
    if (hour < 18) return "Boa tarde";
    return "Boa noite";
  };

  return (
    <div className={styles.page}>
      <Header
        title={`${getGreeting()}, ${user?.name?.split(" ")[0] || "Empreendedor"}`}
        subtitle="Veja o que está acontecendo com seus clientes hoje no WhatsApp."
      />

      <div className={styles.content}>
        {/* Top 5 Indicators */}
        <div className={styles.kpiGrid}>
          <Link href="/inbox" className={styles.kpiCard}>
            <div className={styles.kpiIconWrapper} style={{ backgroundColor: "#eff6ff", color: "#3b82f6" }}>
              <MessageSquare size={20} />
            </div>
            <div className={styles.kpiData}>
              <span className={styles.kpiValue}>{metrics?.open_conversations ?? 0}</span>
              <span className={styles.kpiLabel}>Conversas Abertas</span>
            </div>
          </Link>

          <Link href="/customers" className={styles.kpiCard}>
            <div className={styles.kpiIconWrapper} style={{ backgroundColor: "#f0fdf4", color: "#10b981" }}>
              <Users size={20} />
            </div>
            <div className={styles.kpiData}>
              <span className={styles.kpiValue}>{metrics?.new_customers_count ?? 0}</span>
              <span className={styles.kpiLabel}>Total de Clientes</span>
            </div>
          </Link>

          <Link href="/pipeline" className={styles.kpiCard}>
            <div className={styles.kpiIconWrapper} style={{ backgroundColor: "#fdf4ff", color: "#c026d3" }}>
              <Target size={20} />
            </div>
            <div className={styles.kpiData}>
              <span className={styles.kpiValue}>{metrics?.active_opportunities_count ?? 0}</span>
              <span className={styles.kpiLabel}>Oportunidades Ativas</span>
            </div>
          </Link>

          <div className={styles.kpiCard}>
            <div className={styles.kpiIconWrapper} style={{ backgroundColor: "#ecfdf5", color: "#059669" }}>
              <DollarSign size={20} />
            </div>
            <div className={styles.kpiData}>
              <span className={styles.kpiValue}>{formatCurrency(metrics?.total_sales_value ?? 0)}</span>
              <span className={styles.kpiLabel}>Vendas Realizadas</span>
            </div>
          </div>

          <Link href="/followups" className={styles.kpiCard}>
            <div className={styles.kpiIconWrapper} style={{ backgroundColor: "#fffbeb", color: "#d97706" }}>
              <CalendarClock size={20} />
            </div>
            <div className={styles.kpiData}>
              <span className={styles.kpiValue}>{metrics?.pending_followups_count ?? 0}</span>
              <span className={styles.kpiLabel}>Follow-ups Pendentes</span>
            </div>
          </Link>
        </div>

        {/* Funil de Vendas do WhatsApp */}
        <div className={styles.funnelSection}>
          <div className={styles.sectionHeader}>
            <div className={styles.sectionTitleRow}>
              <h2 className={styles.sectionTitle}>Seu Funil de Vendas no WhatsApp</h2>
              <span className={styles.sectionSubtitle}>Conversões em tempo real por etapa</span>
            </div>
            <Link href="/pipeline" className={styles.viewMoreLink}>
              Ver Kanban Completo <ChevronRight size={14} />
            </Link>
          </div>

          <div className={styles.funnelTrack}>
            {metrics?.funnel_stages?.map((stage, idx) => (
              <div key={stage.stage_id} className={styles.funnelStep}>
                <div className={styles.funnelStepHeader} style={{ borderTopColor: stage.color }}>
                  <span className={styles.funnelStageName}>{stage.name}</span>
                  <span className={styles.funnelCountBadge}>{stage.count} leads</span>
                </div>
                <div className={styles.funnelStepBody}>
                  <span className={styles.funnelValueText}>{formatCurrency(stage.value)}</span>
                </div>
                {idx < (metrics?.funnel_stages?.length || 0) - 1 && (
                  <div className={styles.funnelDivider}>→</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Middle Section: Chart & Follow-up urgent attention */}
        <div className={styles.dashboardGrid}>
          {/* Sales Chart Box */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <h3 className={styles.cardTitle}>Desempenho de Vendas</h3>
                <span className={styles.cardSubtitle}>Faturamento dos últimos 7 dias</span>
              </div>
              <div className={styles.toggleGroup}>
                <button
                  className={`${styles.toggleBtn} ${chartPeriod === "week" ? styles.active : ""}`}
                  onClick={() => setChartPeriod("week")}
                >
                  Semana
                </button>
                <button
                  className={`${styles.toggleBtn} ${chartPeriod === "month" ? styles.active : ""}`}
                  onClick={() => setChartPeriod("month")}
                >
                  Mês
                </button>
              </div>
            </div>

            <div className={styles.chartContainer}>
              <div className={styles.chartBars}>
                {metrics?.sales_chart_data?.map((item) => {
                  const max = 4000;
                  const pct = Math.min(100, Math.max(15, (item.vendas / max) * 100));
                  return (
                    <div key={item.day} className={styles.barCol}>
                      <span className={styles.barValue}>{formatCurrency(item.vendas)}</span>
                      <div className={styles.barTrack}>
                        <div
                          className={styles.barFill}
                          style={{ height: `${pct}%` }}
                        />
                      </div>
                      <span className={styles.barLabel}>{item.day}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Precisa de Atenção / Follow-ups de Hoje */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div>
                <h3 className={styles.cardTitle}>Você precisa retornar</h3>
                <span className={styles.cardSubtitle}>Leads e orçamentos aguardando resposta</span>
              </div>
              <Link href="/followups" className={styles.viewMoreLink}>
                Ver todos
              </Link>
            </div>

            <div className={styles.followupList}>
              {metrics?.urgent_followups && metrics.urgent_followups.length > 0 ? (
                metrics.urgent_followups.map((fu) => (
                  <div key={fu.id} className={styles.followupItem}>
                    <div className={styles.followupAvatar}>
                      {fu.customer?.name?.charAt(0) || "C"}
                    </div>
                    <div className={styles.followupInfo}>
                      <div className={styles.followupCustomer}>
                        <span className={styles.customerName}>{fu.customer?.name}</span>
                        <span className={styles.followupTime}>
                          <Clock size={12} />
                          Hoje às {new Date(fu.due_date).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <p className={styles.followupTitle}>{fu.title}</p>
                      {fu.notes && <span className={styles.followupNotes}>"{fu.notes}"</span>}
                    </div>
                    <Link
                      href={`/inbox?customer_id=${fu.customer_id}`}
                      className={styles.actionBtn}
                      title="Abrir conversa"
                    >
                      <MessageSquare size={14} />
                      <span>Ver conversa</span>
                    </Link>
                  </div>
                ))
              ) : (
                <div className={styles.emptyFollowups}>
                  <CheckCircle size={24} className={styles.emptyIcon} />
                  <span>Nenhum follow-up pendente para agora. Excelente trabalho!</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Section: Recent WhatsApp Conversations */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <h3 className={styles.cardTitle}>Últimas Mensagens Recebidas</h3>
              <span className={styles.cardSubtitle}>Conversas ativas esperando atendimento</span>
            </div>
            <Link href="/inbox" className={styles.viewMoreLink}>
              Ir para Caixa de Entrada <ArrowRight size={14} />
            </Link>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Telefone</th>
                  <th>Última Mensagem</th>
                  <th>Horário</th>
                  <th>Status</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                {metrics?.urgent_conversations?.map((conv) => (
                  <tr key={conv.id}>
                    <td>
                      <div className={styles.customerCell}>
                        <div className={styles.cellAvatar}>
                          {conv.customer?.name?.charAt(0) || "C"}
                        </div>
                        <div className={styles.cellText}>
                          <span className={styles.customerNameMain}>{conv.customer?.name}</span>
                          <span className={styles.companySub}>{conv.customer?.company_name || "Pessoa Física"}</span>
                        </div>
                      </div>
                    </td>
                    <td className={styles.phoneText}>{formatPhone(conv.customer?.phone || "")}</td>
                    <td className={styles.msgText}>{conv.last_message_text || "Sem mensagens"}</td>
                    <td className={styles.timeText}>
                      {new Date(conv.last_message_time).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td>
                      {conv.unread_count > 0 ? (
                        <span className={styles.unreadBadge}>{conv.unread_count} não lida(s)</span>
                      ) : (
                        <span className={styles.readBadge}>Respondido</span>
                      )}
                    </td>
                    <td>
                      <Link href={`/inbox?conv_id=${conv.id}`} className={styles.openChatBtn}>
                        <MessageSquare size={13} />
                        <span>Atender</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}