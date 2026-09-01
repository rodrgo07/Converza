"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch } from "@/lib/api";
import { QuickReply } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./QuickReplies.module.css";
import { Zap, Plus, Copy, Trash2, Edit2, X } from "lucide-react";

export default function QuickRepliesPage() {
  const [replies, setReplies] = useState<QuickReply[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [shortcut, setShortcut] = useState("");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const { success, error } = useToast();

  useEffect(() => {
    loadReplies();
  }, []);

  const loadReplies = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch<QuickReply[]>("/quick-replies");
      setReplies(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    success("Texto copiado para a área de transferência!");
  };

  const handleDelete = async (id: number) => {
    try {
      await apiFetch(`/quick-replies/${id}`, { method: "DELETE" });
      setReplies((prev) => prev.filter((r) => r.id !== id));
      success("Resposta rápida removida!");
    } catch {
      error("Erro ao remover resposta rápida.");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shortcut || !title || !content) return;

    try {
      setIsSaving(true);
      const created = await apiFetch<QuickReply>("/quick-replies", {
        method: "POST",
        body: JSON.stringify({ shortcut, title, content }),
      });
      setReplies([...replies, created]);
      success("Modelo de resposta rápida salvo!");
      setShowModal(false);
      setShortcut("");
      setTitle("");
      setContent("");
    } catch (err: any) {
      error(err.message || "Erro ao salvar.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Respostas Rápidas"
        subtitle="Atalhos de texto para acelerar seus atendimentos e orçamentos no WhatsApp"
      />

      <div className={styles.content}>
        <div className={styles.topBar}>
          <p className={styles.hint}>
            💡 <strong>Como usar:</strong> Na Caixa de Entrada, digite o atalho ou clique no raio ⚡ para preencher sua mensagem em 1 clique.
          </p>
          <button onClick={() => setShowModal(true)} className={styles.addBtn}>
            <Plus size={16} />
            <span>Criar Resposta Rápida</span>
          </button>
        </div>

        <div className={styles.grid}>
          {replies.map((qr) => (
            <div key={qr.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.shortcutBadge}>{qr.shortcut}</span>
                <span className={styles.qrTitle}>{qr.title}</span>
              </div>
              <p className={styles.qrBody}>{qr.content}</p>
              <div className={styles.cardFooter}>
                <button
                  onClick={() => handleCopy(qr.content)}
                  className={styles.copyBtn}
                  title="Copiar mensagem"
                >
                  <Copy size={14} />
                  <span>Copiar</span>
                </button>
                <button
                  onClick={() => handleDelete(qr.id)}
                  className={styles.deleteBtn}
                  title="Remover"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Nova Resposta Rápida</h3>
              <button onClick={() => setShowModal(false)} className={styles.modalCloseBtn}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreate} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Atalho (ex: /pix, /ola, /frete) *</label>
                <input
                  type="text"
                  required
                  placeholder="/atalho"
                  value={shortcut}
                  onChange={(e) => setShortcut(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Título descritivo *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Dados para pagamento Pix com desconto"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Texto da Mensagem *</label>
                <textarea
                  required
                  placeholder="Escreva a mensagem completa que será enviada ao cliente..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className={styles.modalTextarea}
                  rows={4}
                />
              </div>
              <div className={styles.modalFooter}>
                <button type="button" onClick={() => setShowModal(false)} className={styles.modalCancelBtn}>
                  Cancelar
                </button>
                <button type="submit" disabled={isSaving} className={styles.modalSubmitBtn}>
                  Salvar Resposta
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}