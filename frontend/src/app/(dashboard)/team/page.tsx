"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatPhone } from "@/lib/api";
import { User as UserType, UserRole } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Team.module.css";
import { Users2, Plus, Shield, User as UserIcon, X } from "lucide-react";

export default function TeamPage() {
  const [members, setMembers] = useState<UserType[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("sales");
  const [isSaving, setIsSaving] = useState(false);

  const { user } = useAuth();
  const { success, error } = useToast();

  useEffect(() => {
    loadMembers();
  }, []);

  const loadMembers = async () => {
    try {
      setIsLoading(true);
      const data = await apiFetch<UserType[]>("/team");
      setMembers(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) return;

    try {
      setIsSaving(true);
      const created = await apiFetch<UserType>("/team", {
        method: "POST",
        body: JSON.stringify({ name, email, phone: phone || undefined, password, role }),
      });
      setMembers([...members, created]);
      success(`Membro ${created.name} adicionado à equipe!`);
      setShowModal(false);
      setName("");
      setEmail("");
      setPhone("");
      setPassword("");
    } catch (err: any) {
      error(err.message || "Erro ao adicionar.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Gestão de Equipe"
        subtitle="Controle de atendentes, vendedores e permissões de acesso"
      />

      <div className={styles.content}>
        <div className={styles.topBar}>
          <div className={styles.rolesLegend}>
            <span className={styles.roleTag}>👑 Administrador: Acesso Total</span>
            <span className={styles.roleTag}>💼 Gerente: Relatórios e Atribuições</span>
            <span className={styles.roleTag}>💬 Vendedor: Caixa de entrada e Pipeline</span>
          </div>

          {user?.role === "admin" && (
            <button onClick={() => setShowModal(true)} className={styles.addBtn}>
              <Plus size={16} />
              <span>Convidar Membro</span>
            </button>
          )}
        </div>

        <div className={styles.grid}>
          {members.map((m) => (
            <div key={m.id} className={styles.card}>
              <div className={styles.avatar}>
                {m.name.charAt(0)}
              </div>
              <div className={styles.info}>
                <h4 className={styles.name}>{m.name}</h4>
                <span className={styles.email}>{m.email}</span>
                {m.phone && <span className={styles.phone}>{formatPhone(m.phone)}</span>}
              </div>
              <div className={styles.badgeWrapper}>
                <span className={`${styles.roleBadge} ${styles[m.role]}`}>
                  {m.role === "admin" && "Administrador"}
                  {m.role === "manager" && "Gerente"}
                  {m.role === "sales" && "Vendedor"}
                  {m.role === "support" && "Atendente"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Novo Membro da Equipe</h3>
              <button onClick={() => setShowModal(false)} className={styles.modalCloseBtn}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleAddMember} className={styles.modalForm}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Nome Completo *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Juliana Silva"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>E-mail de acesso *</label>
                <input
                  type="email"
                  required
                  placeholder="juliana@suaempresa.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>WhatsApp do Vendedor</label>
                <input
                  type="tel"
                  placeholder="(11) 97777-6666"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Nível de Permissão *</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className={styles.modalInput}
                >
                  <option value="sales">Vendedor (Atende clientes e fecha vendas)</option>
                  <option value="manager">Gerente (Acompanha métricas e equipe)</option>
                  <option value="admin">Administrador (Controle total da conta)</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Senha Inicial *</label>
                <input
                  type="password"
                  required
                  placeholder="Mínimo 6 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={styles.modalInput}
                />
              </div>
              <div className={styles.modalFooter}>
                <button type="button" onClick={() => setShowModal(false)} className={styles.modalCancelBtn}>
                  Cancelar
                </button>
                <button type="submit" disabled={isSaving} className={styles.modalSubmitBtn}>
                  Criar Acesso
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}