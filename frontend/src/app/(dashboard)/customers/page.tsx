"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatCurrency, formatPhone } from "@/lib/api";
import { Customer, Tag } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Customers.module.css";
import {
  Users,
  Search,
  Plus,
  Filter,
  Phone,
  Mail,
  Building,
  Calendar,
  DollarSign,
  MessageSquare,
  ChevronRight,
  X
} from "lucide-react";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [search, setSearch] = useState("");
  const [selectedTag, setSelectedTag] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Modal Create Customer
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
  const [isCreating, setIsCreating] = useState(false);

  const { success, error } = useToast();

  useEffect(() => {
    fetchCustomers();
    fetchTags();
  }, [selectedTag]);

  const fetchCustomers = async () => {
    try {
      setIsLoading(true);
      let url = "/customers";
      if (selectedTag) url += `?tag_id=${selectedTag}`;
      const data = await apiFetch<Customer[]>(url);
      setCustomers(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const data = await apiFetch<Tag[]>("/tags");
      setTags(data);
    } catch {
      // ignore
    }
  };

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newPhone.trim()) {
      error("Nome e telefone são obrigatórios.");
      return;
    }

    try {
      setIsCreating(true);
      const created = await apiFetch<Customer>("/customers", {
        method: "POST",
        body: JSON.stringify({
          name: newName.trim(),
          phone: newPhone.trim(),
          email: newEmail.trim() || undefined,
          company_name: newCompany.trim() || undefined,
          notes: newNotes.trim() || undefined,
          tag_ids: selectedTagIds,
        }),
      });

      setCustomers([created, ...customers]);
      success(`Cliente ${created.name} cadastrado com sucesso no banco de dados!`);
      setShowModal(false);
      setNewName("");
      setNewPhone("");
      setNewEmail("");
      setNewCompany("");
      setNewNotes("");
      setSelectedTagIds([]);
    } catch (err: any) {
      error(err.message || "Erro ao salvar cliente.");
    } finally {
      setIsCreating(false);
    }
  };

  const filtered = customers.filter((c) => {
    const s = search.toLowerCase();
    return (
      c.name.toLowerCase().includes(s) ||
      c.phone.includes(s) ||
      c.company_name?.toLowerCase().includes(s)
    );
  });

  return (
    <div className={styles.page}>
      <Header
        title="Clientes"
        subtitle="Sua base de contatos reais cadastrados no PostgreSQL"
      />

      <div className={styles.content}>
        {/* Controls Toolbar */}
        <div className={styles.toolbar}>
          <div className={styles.searchBox}>
            <Search size={16} className={styles.searchIcon} />
            <input
              type="text"
              placeholder="Pesquisar por nome, telefone ou empresa..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={styles.searchInput}
            />
          </div>

          <div className={styles.tagFilters}>
            <button
              className={`${styles.tagFilterBtn} ${selectedTag === null ? styles.active : ""}`}
              onClick={() => setSelectedTag(null)}
            >
              Todos ({customers.length})
            </button>
            {tags.map((t) => (
              <button
                key={t.id}
                className={`${styles.tagFilterBtn} ${selectedTag === t.id ? styles.active : ""}`}
                onClick={() => setSelectedTag(selectedTag === t.id ? null : t.id)}
              >
                <span className={styles.tagDot} style={{ backgroundColor: t.color }} />
                <span>{t.name}</span>
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowModal(true)}
            className={styles.addCustomerBtn}
          >
            <Plus size={16} />
            <span>Novo Cliente</span>
          </button>
        </div>

        {/* Customers Table */}
        <div className={styles.tableCard}>
          {filtered.length > 0 ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Telefone</th>
                  <th>Tags</th>
                  <th>Responsável</th>
                  <th>Total Comprado</th>
                  <th>Data de Cadastro</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((cust) => (
                  <tr key={cust.id}>
                    <td>
                      <div className={styles.nameCell}>
                        <div className={styles.avatar}>
                          {cust.name.charAt(0)}
                        </div>
                        <div>
                          <span className={styles.customerName}>{cust.name}</span>
                          <span className={styles.companySub}>{cust.company_name || "Pessoa Física"}</span>
                        </div>
                      </div>
                    </td>
                    <td className={styles.phoneText}>{formatPhone(cust.phone)}</td>
                    <td>
                      <div className={styles.tagList}>
                        {cust.customer_tags && cust.customer_tags.length > 0 ? (
                          cust.customer_tags.map((ct) => (
                            <span
                              key={ct.id}
                              className={styles.tagBadge}
                              style={{ backgroundColor: `${ct.tag.color}20`, color: ct.tag.color }}
                            >
                              {ct.tag.name}
                            </span>
                          ))
                        ) : (
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>-</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className={styles.assignedBadge}>
                        {cust.assigned_user?.name || "Não atribuído"}
                      </span>
                    </td>
                    <td className={styles.spentText}>{formatCurrency(cust.total_spent)}</td>
                    <td className={styles.dateText}>
                      {new Date(cust.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td>
                      <div className={styles.rowActions}>
                        <Link
                          href={`/inbox?customer_id=${cust.id}`}
                          className={styles.actionIconBtn}
                          title="Abrir Conversa"
                        >
                          <MessageSquare size={15} />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className={styles.emptyState}>
              <Users size={40} className={styles.emptyIcon} />
              <h3>Nenhum cliente cadastrado</h3>
              <p>Adicione seu primeiro contato para começar a registrar conversas e oportunidades.</p>
              <button
                onClick={() => setShowModal(true)}
                className={styles.addCustomerBtn}
                style={{ marginTop: 12 }}
              >
                <Plus size={16} />
                <span>Cadastrar Primeiro Cliente</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Modal Criar Cliente */}
      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Cadastrar Novo Cliente</h3>
              <button
                onClick={() => setShowModal(false)}
                className={styles.modalCloseBtn}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className={styles.modalForm}>
              <div className={styles.modalGrid}>
                <div className={styles.formGroup}>
                  <label className={styles.label}>Nome Completo *</label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: João da Silva"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className={styles.modalInput}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>WhatsApp / Telefone *</label>
                  <input
                    type="text"
                    required
                    placeholder="(11) 98765-4321"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    className={styles.modalInput}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>E-mail</label>
                  <input
                    type="email"
                    placeholder="joao@empresa.com"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className={styles.modalInput}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Empresa / Negócio</label>
                  <input
                    type="text"
                    placeholder="Ex: Silva Advocacia"
                    value={newCompany}
                    onChange={(e) => setNewCompany(e.target.value)}
                    className={styles.modalInput}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>Observações Iniciais</label>
                <textarea
                  placeholder="Informações sobre preferências, produtos de interesse..."
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
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
                  disabled={isCreating}
                  className={styles.modalSubmitBtn}
                >
                  {isCreating ? "Salvando no Banco..." : "Salvar Cliente"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}