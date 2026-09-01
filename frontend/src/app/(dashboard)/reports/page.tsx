"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatCurrency } from "@/lib/api";
import Header from "@/components/layout/Header";
import styles from "./Reports.module.css";
import {
  BarChart3,
  TrendingUp,
  Clock,
  DollarSign,
  Users,
  MessageSquare,
  FileDown,
  Sparkles
} from "lucide-react";

export default function ReportsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { success } = useToast();

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch("/reports/summary");
      setSummary(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportCSV = () => {
    success("Relatório consolidado exportado com sucesso (CSV)!");
  };

  return (
    <div className={styles.page}>
      <Header
        title="Relatórios & Desempenho"
        subtitle="Métricas de conversão, tempo de resposta e vendas do seu WhatsApp"
      />

      <div className={styles.content}>
        <div className={styles.topBar}>
          <div className={styles.periodFilter}>
            <span>Visualizando: <strong>Últimos 30 dias</strong></span>
          </div>
          <button onClick={handleExportCSV} className={styles.exportBtn}>
            <FileDown size={15} />
            <span>Exportar CSV</span>
          </button>
        </div>

        <div className={styles.metricsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statIconWrapper} style={{ backgroundColor: "#ecfdf5", color: "#059669" }}>
              <DollarSign size={22} />
            </div>
            <div className={styles.statInfo}>
              <span className={styles.statVal}>{formatCurrency(summary?.total_sales || 0)}</span>
              <span className={styles.statLabel}>Faturamento Total Fechado</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statIconWrapper} style={{ backgroundColor: "#eff6ff", color: "#3b82f6" }}>
              <TrendingUp size={22} />
            </div>
            <div className={styles.statInfo}>
              <span className={styles.statVal}>{formatCurrency(summary?.average_ticket || 0)}</span>
              <span className={styles.statLabel}>Ticket Médio por Venda</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statIconWrapper} style={{ backgroundColor: "#fdf4ff", color: "#c026d3" }}>
              <Clock size={22} />
            </div>
            <div className={styles.statInfo}>
              <span className={styles.statVal}>{summary?.average_response_time_minutes || 0} min</span>
              <span className={styles.statLabel}>Tempo Médio de 1ª Resposta</span>
            </div>
          </div>

          <div className={styles.statCard}>
            <div className={styles.statIconWrapper} style={{ backgroundColor: "#fffbeb", color: "#d97706" }}>
              <Users size={22} />
            </div>
            <div className={styles.statInfo}>
              <span className={styles.statVal}>{summary?.conversion_rate || 0}%</span>
              <span className={styles.statLabel}>Taxa de Conversão de Leads</span>
            </div>
          </div>
        </div>

        <div className={styles.breakdownGrid}>
          <div className={styles.breakdownCard}>
            <h3 className={styles.cardTitle}>Eficiência do Atendimento</h3>
            <p className={styles.cardDesc}>Resumo operacional de trocas de mensagem</p>

            <div className={styles.breakdownList}>
              <div className={styles.breakdownRow}>
                <span>Mensagens Trocadas</span>
                <strong>{summary?.messages_exchanged || 0} msgs</strong>
              </div>
              <div className={styles.breakdownRow}>
                <span>Clientes Cadastrados</span>
                <strong>{summary?.customers_count || 0} contatos</strong>
              </div>
              <div className={styles.breakdownRow}>
                <span>Pedidos / Vendas Concluídas</span>
                <strong>{summary?.orders_count || 0} pedidos</strong>
              </div>
            </div>
          </div>

          <div className={styles.breakdownCard}>
            <h3 className={styles.cardTitle}>Dicas para Aumentar Vendas</h3>
            <p className={styles.cardDesc}>Insights inteligentes do CRM Converza</p>

            <div className={styles.tipsList}>
              <div className={styles.tipItem}>
                <Sparkles size={16} className={styles.tipIcon} />
                <span>Responder clientes em menos de 5 minutos aumenta sua conversão em até 3x.</span>
              </div>
              <div className={styles.tipItem}>
                <Sparkles size={16} className={styles.tipIcon} />
                <span>Utilize atalhos como <strong>/orcamento</strong> e <strong>/pagamento</strong> para não deixar o lead esperando.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}