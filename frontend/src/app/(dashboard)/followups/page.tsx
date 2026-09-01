"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatPhone } from "@/lib/api";
import { FollowUp, Customer } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Followups.module.css";
import {
  CalendarClock,
  Plus,
  Clock,
  CheckCircle,
  MessageSquare,
  AlertCircle,
  Calendar,
  X,
  Check
} from "lucide-react";

export default function FollowUpsPage() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [activeTab, setActiveTab] = useState<"pending" | "completed">("pending");
  const [isLoading, setIsLoading] = useState(true);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | "">("");
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [dueDateType, setDueDateType] = useState<"today" | "tomorrow" | "next_week" | "custom">("today");
  const [customDate, setCustomDate] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const { success, error } = useToast();

  useEffect(() => {
    loadFollowUps();
    loadCustomers();
  }, []);

  const loadFollowUps = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch<FollowUp[]>("/followups");
      setFollowUps(data);
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

  const handleToggleComplete = async (fu: FollowUp) => {
    const nextStatus = fu.status === "pending" ? "completed" : "pending";
    try {
      await apiFetch(`/followups/${fu.id}`, {
        method: "PUT",
        body: JSON.stringify({ status: nextStatus }),
      });

      setFollowUps((prev) =>
        prev.map((item) => (item.id === fu.id ? { ...item, status: nextStatus as any } : item))
      );
      success(nextStatus === "completed" ? "Follow-up concluído!" : "Follow-up reaberto!");
    } catch {
      error("Erro ao atualizar follow-up.");
    }
  };

  const handleCreateFollowUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !title) {
      error("Preencha o cliente e o título.");
      return;
    }

    let calculatedDate = new Date();
    if (dueDateType === "today") {
      calculatedDate.setHours(calculatedDate.getHours() + 3);
    } else if (dueDateType === "tomorrow") {
      calculatedDate.setDate(calculatedDate.getDate() + 1);
      calculatedDate.setHours(10, 0, 0);
    } else if (dueDateType === "next_week") {
      calculatedDate.setDate(calculatedDate.getDate() + 7);
      calculatedDate.setHours(10, 0, 0);
    } else if (dueDateType === "custom" && customDate) {
      calculatedDate = new Date(customDate);
    }

    try {
      setIsSaving(true);
      const created = await apiFetch<FollowUp>("/followups", {
        method: "POST",
        body: JSON.stringify({
          customer_id: Number(selectedCustomerId),
          title,
          notes: notes || undefined,
          due_date: calculatedDate.toISOString(),
        }),
      });

      setFollowUps([created, ...followUps]);
      success("Lembrete de follow-up agendado com sucesso!");
      setShowModal(false);
      setTitle("");
      setNotes("");
    } catch (err: any) {
      error(err.message || "Erro ao agendar.");
    } finally {
      setIsSaving(false);
    }
  };

  const filtered = followUps.filter((f) => f.status === activeTab);

  return (
    <div className={styles.page}>
      <Header
        title="Follow-ups & Retornos"
        subtitle="Nunca mais esqueça de responder ou cobrar um cliente no WhatsApp"
      />

      <div className={styles.content}>
        <div className={styles.topBar}>
          <div className={styles.tabGroup}>
            <button
              className={`${styles.tabBtn} ${activeTab === "pending" ? styles.active : ""}`}
              onClick={() => setActiveTab("pending")}
            >
              Pendentes ({followUps.filter((f) => f.status === "pending").length})
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === "completed" ? styles.active : ""}`}
              onClick={() => setActiveTab("completed")}
            >
              Concluídos ({followUps.filter((f) => f.status === "completed").length})
            </button>
          </div>

          <button onClick={() => setShowModal(true)} className={styles.addBtn}>
            <Plus size={16} />
            <span>Novo Follow-up</span>
          </button>
        </div>

        <div className={styles.list}>
          {filtered.map((fu) => (
            <div key={fu.id} className={`${styles.card} ${fu.status === "completed" ? styles.cardDone : ""}`}>
              <button
                className={`${styles.checkCircle} ${fu.status === "completed" ? styles.checkDone : ""}`}
                onClick={() => handleToggleComplete(fu)}
                title="Marcar como concluído"
              >
                {fu.status === "completed" && <Check size={14} />}
              </button>

              <div className={styles.infoCol}>
                <div className={styles.cardHeader}>
                  <span className={styles.customerName}>{fu.customer?.name}</span>
                  <span className={styles.phoneBadge}>{formatPhone(fu.customer?.phone || "")}</span>
                </div>
                <h4 className={styles.title}>{fu.title}</h4>
                {fu.notes && <p className={styles.notes}>"{fu.notes}"</p>}
              </div>

              <div className={styles.timeCol}>
                <div className={styles.timeBadge}>
                  <Clock size={13} />
                  <span>
                    {new Date(fu.due_date).toLocaleDateString("pt-BR")} às{" "}
                    {new Date(fu.due_date).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              </div>

              <div className={styles.actionCol}>
                <Link
                  href={`/inbox?customer_id=${fu.customer_id}`}
                  className={styles.openChatBtn}
                  title="Abrir WhatsApp"
                >
                  <MessageSquare size={14} />
                  <span>Conversar</span>
                </Link>
              </div>
            </div>
          ))}

          {filtered.length === 0 && (
            <div className={styles.emptyState}>
              <CalendarClock size={40} className={styles.emptyIcon} />
              <h3>Nenhum follow-up {activeTab === "pending" ? "pendente" : "concluído"}</h3>
              <p>Mantenha seus clientes sempre aquecidos criando lembretes de contato.</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal Criar Follow-up */}
      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Agendar Follow-up</h3>
              <button onClick={() => setShowModal(false)} className={styles.modalCloseBtn}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateFollowUp} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Cliente *</label>
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
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>O que você precisa retornar? *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Enviar link de pagamento e confirmar tamanho"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={styles.modalInput}
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Quando retornar?</label>
                <div className={styles.quickDateGrid}>
                  <button
                    type="button"
                    className={`${styles.dateOption} ${dueDateType === "today" ? styles.selectedDate : ""}`}
                    onClick={() => setDueDateType("today")}
                  >
                    Hoje (em 3h)
                  </button>
                  <button
                    type="button"
                    className={`${styles.dateOption} ${dueDateType === "tomorrow" ? styles.selectedDate : ""}`}
                    onClick={() => setDueDateType("tomorrow")}
                  >
                    Amanhã
                  </button>
                  <button
                    type="button"
                    className={`${styles.dateOption} ${dueDateType === "next_week" ? styles.selectedDate : ""}`}
                    onClick={() => setDueDateType("next_week")}
                  >
                    Próxima Semana
                  </button>
                  <button
                    type="button"
                    className={`${styles.dateOption} ${dueDateType === "custom" ? styles.selectedDate : ""}`}
                    onClick={() => setDueDateType("custom")}
                  >
                    Personalizado
                  </button>
                </div>
                {dueDateType === "custom" && (
                  <input
                    type="datetime-local"
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    className={styles.modalInput}
                    style={{ marginTop: 8 }}
                  />
                )}
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Notas / Contexto</label>
                <textarea
                  placeholder="Observações úteis para o momento do contato..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
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
                  disabled={isSaving}
                  className={styles.modalSubmitBtn}
                >
                  {isSaving ? "Agendando..." : "Salvar Follow-up"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}