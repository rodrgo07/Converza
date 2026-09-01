"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatCurrency, formatPhone } from "@/lib/api";
import { KanbanColumn, Opportunity, PipelineStage, Customer } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Pipeline.module.css";
import {
  Plus,
  DollarSign,
  User,
  Calendar,
  MessageSquare,
  Clock,
  MoreVertical,
  Trash2,
  X,
  Target
} from "lucide-react";

export default function PipelinePage() {
  const [columns, setColumns] = useState<KanbanColumn[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal Create Opportunity
  const [showModal, setShowModal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | "">("");
  const [selectedStageId, setSelectedStageId] = useState<number | "">("");
  const [oppTitle, setOppTitle] = useState("");
  const [oppValue, setOppValue] = useState("");
  const [oppProbability, setOppProbability] = useState(70);
  const [oppNotes, setOppNotes] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const { success, error } = useToast();

  useEffect(() => {
    loadKanban();
    loadCustomers();
  }, []);

  const loadKanban = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch<KanbanColumn[]>("/pipeline/kanban");
      setColumns(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const loadCustomers = async () => {
    try {
      const data = await apiFetch<Customer[]>("/customers");
      setCustomers(data);
      if (data.length > 0) setSelectedCustomerId(data[0].id);
    } catch {
      // ignore
    }
  };

  const handleDragStart = (e: React.DragEvent, oppId: number, fromStageId: number) => {
    e.dataTransfer.setData("oppId", oppId.toString());
    e.dataTransfer.setData("fromStageId", fromStageId.toString());
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (e: React.DragEvent, targetStageId: number) => {
    e.preventDefault();
    const oppIdStr = e.dataTransfer.getData("oppId");
    const fromStageIdStr = e.dataTransfer.getData("fromStageId");
    if (!oppIdStr) return;

    const oppId = parseInt(oppIdStr, 10);
    const fromStageId = parseInt(fromStageIdStr, 10);
    if (fromStageId === targetStageId) return;

    setColumns((prevColumns) => {
      const sourceCol = prevColumns.find((c) => c.stage.id === fromStageId);
      const opp = sourceCol?.opportunities.find((o) => o.id === oppId);
      if (!opp) return prevColumns;

      return prevColumns.map((col) => {
        if (col.stage.id === fromStageId) {
          const nextOpps = col.opportunities.filter((o) => o.id !== oppId);
          return {
            ...col,
            opportunities: nextOpps,
            count: nextOpps.length,
            total_value: nextOpps.reduce((acc, curr) => acc + curr.value, 0),
          };
        }
        if (col.stage.id === targetStageId) {
          const updatedOpp = { ...opp, stage_id: targetStageId };
          const nextOpps = [updatedOpp, ...col.opportunities];
          return {
            ...col,
            opportunities: nextOpps,
            count: nextOpps.length,
            total_value: nextOpps.reduce((acc, curr) => acc + curr.value, 0),
          };
        }
        return col;
      });
    });

    try {
      await apiFetch(`/pipeline/opportunities/${oppId}`, {
        method: "PUT",
        body: JSON.stringify({ stage_id: targetStageId }),
      });
      success("Etapa salva no PostgreSQL!");
    } catch {
      error("Erro ao mover oportunidade.");
      loadKanban();
    }
  };

  const handleCreateOpportunity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !oppTitle.trim() || !selectedStageId) {
      error("Preencha todos os campos obrigatórios.");
      return;
    }

    try {
      setIsSaving(true);
      await apiFetch("/pipeline/opportunities", {
        method: "POST",
        body: JSON.stringify({
          customer_id: Number(selectedCustomerId),
          stage_id: Number(selectedStageId),
          title: oppTitle.trim(),
          value: parseFloat(oppValue) || 0.0,
          probability: oppProbability,
          notes: oppNotes.trim() || undefined,
        }),
      });

      success("Oportunidade criada no banco de dados!");
      setShowModal(false);
      setOppTitle("");
      setOppValue("");
      setOppNotes("");
      loadKanban();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao criar oportunidade.";
      error(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const totalOppsCount = columns.reduce((acc, col) => acc + col.count, 0);

  return (
    <div className={styles.page}>
      <Header
        title="Pipeline de Vendas"
        subtitle="Gerencie suas negociações do WhatsApp em formato Kanban visual"
      />

      <div className={styles.content}>
        <div className={styles.topBar}>
          <div className={styles.pipelineStats}>
            <span className={styles.statLabel}>Total em Negociação:</span>
            <span className={styles.statVal}>
              {formatCurrency(
                columns.reduce((sum, col) => sum + col.total_value, 0)
              )}
            </span>
          </div>

          <button
            onClick={() => {
              if (columns.length > 0) setSelectedStageId(columns[0].stage.id);
              setShowModal(true);
            }}
            className={styles.addOppBtn}
          >
            <Plus size={16} />
            <span>Criar Oportunidade</span>
          </button>
        </div>

        {/* Kanban Board Container */}
        <div className={styles.boardTrack}>
          {columns.map((col) => (
            <div
              key={col.stage.id}
              className={styles.kanbanColumn}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, col.stage.id)}
            >
              <div className={styles.columnHeader} style={{ borderTopColor: col.stage.color }}>
                <div className={styles.columnTitleRow}>
                  <span className={styles.columnName}>{col.stage.name}</span>
                  <span className={styles.columnCount}>{col.count}</span>
                </div>
                <span className={styles.columnTotalVal}>{formatCurrency(col.total_value)}</span>
              </div>

              <div className={styles.cardsContainer}>
                {col.opportunities.map((opp) => (
                  <div
                    key={opp.id}
                    className={styles.kanbanCard}
                    draggable
                    onDragStart={(e) => handleDragStart(e, opp.id, col.stage.id)}
                  >
                    <div className={styles.cardHeader}>
                      <span className={styles.cardCustomer}>{opp.customer?.name}</span>
                      <span className={styles.cardValue}>{formatCurrency(opp.value)}</span>
                    </div>

                    <p className={styles.cardTitle}>{opp.title}</p>

                    <div className={styles.cardFooter}>
                      <div className={styles.userBadge}>
                        <User size={12} />
                        <span>{opp.assigned_user?.name?.split(" ")[0] || "Equipe"}</span>
                      </div>
                      <Link
                        href={`/inbox?customer_id=${opp.customer_id}`}
                        className={styles.chatShortcut}
                        title="Ir para o WhatsApp"
                      >
                        <MessageSquare size={13} />
                      </Link>
                    </div>
                  </div>
                ))}

                {col.opportunities.length === 0 && (
                  <div className={styles.emptyColDropzone}>
                    <span>Nenhuma oportunidade nesta etapa</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal Nova Oportunidade */}
      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Nova Oportunidade de Venda</h3>
              <button
                onClick={() => setShowModal(false)}
                className={styles.modalCloseBtn}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateOpportunity} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Cliente do WhatsApp *</label>
                {customers.length > 0 ? (
                  <select
                    required
                    value={selectedCustomerId}
                    onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
                    className={styles.modalSelect}
                  >
                    <option value="">Selecione um cliente...</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({formatPhone(c.phone)})
                      </option>
                    ))}
                  </select>
                ) : (
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Nenhum cliente cadastrado ainda. Cadastre um cliente primeiro em <Link href="/customers" style={{ color: "var(--brand-primary)", textDecoration: "underline" }}>Clientes</Link>.
                  </div>
                )}
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Título da Oportunidade / Produto *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Orçamento de Serviço / Venda de Produto"
                  value={oppTitle}
                  onChange={(e) => setOppTitle(e.target.value)}
                  className={styles.modalInput}
                />
              </div>

              <div className={styles.modalGrid}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>Valor Estimado (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0,00"
                    value={oppValue}
                    onChange={(e) => setOppValue(e.target.value)}
                    className={styles.modalInput}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Etapa Inicial *</label>
                  <select
                    required
                    value={selectedStageId}
                    onChange={(e) => setSelectedStageId(Number(e.target.value))}
                    className={styles.modalSelect}
                  >
                    {columns.map((c) => (
                      <option key={c.stage.id} value={c.stage.id}>
                        {c.stage.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Observações da Proposta</label>
                <textarea
                  placeholder="Detalhes da negociação..."
                  value={oppNotes}
                  onChange={(e) => setOppNotes(e.target.value)}
                  className={styles.modalTextarea}
                  rows={2}
                />
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className={styles.modalCancelBtn}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSaving || customers.length === 0}
                  className={styles.modalSubmitBtn}
                >
                  {isSaving ? "Salvando no PostgreSQL..." : "Salvar no Pipeline"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}