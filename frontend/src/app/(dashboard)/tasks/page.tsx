"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch } from "@/lib/api";
import { Task, Customer } from "@/types";
import Header from "@/components/layout/Header";
import styles from "../followups/Followups.module.css";
import { CheckSquare, Plus, Check, Calendar, X } from "lucide-react";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const { success, error } = useToast();

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch<Task[]>("/tasks");
      setTasks(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (task: Task) => {
    const nextStatus = task.status === "pending" ? "completed" : "pending";
    try {
      await apiFetch(`/tasks/${task.id}`, {
        method: "PUT",
        body: JSON.stringify({ status: nextStatus }),
      });
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: nextStatus as any } : t))
      );
      success("Tarefa atualizada!");
    } catch {
      error("Erro ao atualizar tarefa.");
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;

    try {
      setIsSaving(true);
      const created = await apiFetch<Task>("/tasks", {
        method: "POST",
        body: JSON.stringify({ title, description: description || undefined }),
      });
      setTasks([created, ...tasks]);
      success("Tarefa criada com sucesso!");
      setShowModal(false);
      setTitle("");
      setDescription("");
    } catch (err: any) {
      error("Erro ao criar tarefa.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Tarefas do Dia a Dia"
        subtitle="Organize as pendências operacionais da sua equipe"
      />

      <div className={styles.content}>
        <div className={styles.topBar}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Minhas Tarefas</h3>
          <button onClick={() => setShowModal(true)} className={styles.addBtn}>
            <Plus size={16} />
            <span>Nova Tarefa</span>
          </button>
        </div>

        <div className={styles.list}>
          {tasks.map((t) => (
            <div key={t.id} className={`${styles.card} ${t.status === "completed" ? styles.cardDone : ""}`}>
              <button
                className={`${styles.checkCircle} ${t.status === "completed" ? styles.checkDone : ""}`}
                onClick={() => handleToggle(t)}
              >
                {t.status === "completed" && <Check size={14} />}
              </button>
              <div className={styles.infoCol}>
                <h4 className={styles.title}>{t.title}</h4>
                {t.description && <p className={styles.notes}>{t.description}</p>}
              </div>
            </div>
          ))}

          {tasks.length === 0 && (
            <div className={styles.emptyState}>
              <CheckSquare size={40} className={styles.emptyIcon} />
              <h3>Nenhuma tarefa pendente</h3>
              <p>Tudo organizado e em dia!</p>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Nova Tarefa</h3>
              <button onClick={() => setShowModal(false)} className={styles.modalCloseBtn}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateTask} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Título da Tarefa *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Fazer pós-venda com clientes do Sedex"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Descrição</label>
                <textarea
                  placeholder="Detalhes da tarefa..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={styles.modalTextarea}
                  rows={2}
                />
              </div>
              <div className={styles.modalFooter}>
                <button type="button" onClick={() => setShowModal(false)} className={styles.modalCancelBtn}>
                  Cancelar
                </button>
                <button type="submit" disabled={isSaving} className={styles.modalSubmitBtn}>
                  Salvar Tarefa
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}