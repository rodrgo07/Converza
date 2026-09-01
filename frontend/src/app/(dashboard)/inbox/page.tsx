"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatCurrency, formatPhone } from "@/lib/api";
import { Conversation, Message, Customer, QuickReply, User } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Inbox.module.css";
import {
  Send,
  Zap,
  Phone,
  Mail,
  ShoppingBag,
  Clock,
  Search,
  CheckCheck,
  Plus,
  MessageSquare,
  Users,
  UserCheck,
  ArrowRightLeft,
  CheckCircle,
  Inbox as InboxIcon,
  Filter,
  ShieldCheck,
  AlertCircle
} from "lucide-react";
import Link from "next/link";

export default function InboxPage() {
  const { user } = useAuth();
  const { success, error } = useToast();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<number | null>(null);
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>([]);
  const [teamMembers, setTeamMembers] = useState<User[]>([]);

  // Queue filter
  const [selectedQueue, setSelectedQueue] = useState<"all" | "mine" | "unassigned" | "waiting" | "resolved">("all");
  
  const [messageText, setMessageText] = useState("");
  const [searchFilter, setSearchFilter] = useState("");
  const [showQuickMenu, setShowQuickMenu] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferTargetUserId, setTransferTargetUserId] = useState<number | null>(null);
  const [transferNotes, setTransferNotes] = useState("");
  const [isSending, setIsSending] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchConversations();
    fetchQuickReplies();
    fetchTeamMembers();
  }, [selectedQueue]);

  // Realtime WebSocket Connection with multi-tenant company isolation
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("converza_token") : null;
    if (!token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname;
    // Backend default port 8000
    const wsUrl = `${protocol}//${host}:8000/ws?token=${token}`;

    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      // Ping interval to maintain connection alive
      const interval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "PING" }));
        }
      }, 30000);
      (ws as any).pingInterval = interval;
    };

    ws.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        const { type, data } = payload;

        if (type === "NEW_MESSAGE") {
          const newMsg: Message = data.message;
          const convUpdate: Conversation = data.conversation;

          // Se a mensagem pertence à conversa atualmente aberta
          if (newMsg.conversation_id === selectedConvId) {
            setMessages((prev) => {
              if (prev.some((m) => m.id === newMsg.id || (m.external_id && m.external_id === newMsg.external_id))) {
                return prev;
              }
              return [...prev, newMsg];
            });
          }

          // Atualiza lista de conversas
          setConversations((prev) => {
            const exists = prev.some((c) => c.id === convUpdate.id);
            if (exists) {
              return prev.map((c) => (c.id === convUpdate.id ? { ...c, ...convUpdate } : c));
            } else {
              return [convUpdate, ...prev];
            }
          });
        } else if (type === "MESSAGE_STATUS_UPDATE") {
          const { message_id, status } = data;
          setMessages((prev) =>
            prev.map((m) => (m.id === message_id ? { ...m, status } : m))
          );
        } else if (type === "CONVERSATION_ASSIGNED" || type === "CONVERSATION_TRANSFERRED") {
          const { conversation_id, assigned_user_id, version } = data;
          setConversations((prev) =>
            prev.map((c) =>
              c.id === conversation_id ? { ...c, assigned_user_id, version } : c
            )
          );
          if (selectedConvId === conversation_id) {
            loadConversationDetails(conversation_id);
          }
        }
      } catch (err) {
        // ignore parse error
      }
    };

    ws.onerror = () => {
      // fallback
    };

    return () => {
      if ((ws as any).pingInterval) clearInterval((ws as any).pingInterval);
      ws.close();
    };
  }, [selectedConvId]);

  useEffect(() => {
    if (selectedConvId) {
      loadConversationDetails(selectedConvId);
    }
  }, [selectedConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const qParam = selectedQueue !== "all" ? `?queue=${selectedQueue}` : "";
      const list = await apiFetch<Conversation[]>(`/conversations${qParam}`);
      setConversations(list);
      if (list.length > 0 && !selectedConvId) {
        setSelectedConvId(list[0].id);
      }
    } catch {
      // ignore
    }
  };

  const fetchQuickReplies = async () => {
    try {
      const qrs = await apiFetch<QuickReply[]>("/quick-replies");
      setQuickReplies(qrs);
    } catch {
      // ignore
    }
  };

  const fetchTeamMembers = async () => {
    try {
      const team = await apiFetch<User[]>("/team");
      setTeamMembers(team);
    } catch {
      // ignore
    }
  };

  const loadConversationDetails = async (id: number) => {
    try {
      const data = await apiFetch<Conversation & { messages: Message[] }>(`/conversations/${id}`);
      setActiveConv(data);
      setMessages(data.messages || []);
      
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, unread_count: 0 } : c))
      );
    } catch (err: any) {
      error("Erro ao carregar conversa.");
    }
  };

  const handleAssignToMe = async () => {
    if (!selectedConvId || !activeConv) return;
    try {
      const updated = await apiFetch<Conversation>(`/conversations/${selectedConvId}/assign`, {
        method: "POST",
        body: JSON.stringify({
          assigned_user_id: user?.id,
          expected_version: activeConv.version
        }),
      });
      setActiveConv(updated);
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      success("Você assumiu esta conversa com sucesso!");
    } catch (err: any) {
      error(err.message || "Erro ao assumir conversa.");
    }
  };

  const handleTransfer = async () => {
    if (!selectedConvId || !transferTargetUserId || !activeConv) return;
    try {
      const updated = await apiFetch<Conversation>(`/conversations/${selectedConvId}/transfer`, {
        method: "POST",
        body: JSON.stringify({
          target_user_id: transferTargetUserId,
          notes: transferNotes.trim() || undefined,
          expected_version: activeConv.version
        }),
      });
      setActiveConv(updated);
      setShowTransferModal(false);
      setTransferNotes("");
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      success("Conversa transferida com sucesso!");
    } catch (err: any) {
      error(err.message || "Erro ao transferir conversa.");
    }
  };

  const handleResolveConversation = async () => {
    if (!selectedConvId) return;
    try {
      const updated = await apiFetch<Conversation>(`/conversations/${selectedConvId}/resolve`, {
        method: "POST",
      });
      setActiveConv(updated);
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      success("Atendimento finalizado!");
    } catch (err: any) {
      error(err.message || "Erro ao finalizar atendimento.");
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!messageText.trim() || !selectedConvId) return;

    const content = messageText.trim();
    setMessageText("");
    setShowQuickMenu(false);

    try {
      setIsSending(true);
      const sentMsg = await apiFetch<Message>(`/conversations/${selectedConvId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content, message_type: "text" }),
      });

      setMessages((prev) => [...prev, sentMsg]);
      
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedConvId
            ? { ...c, last_message_text: content, last_message_time: new Date().toISOString() }
            : c
        )
      );
    } catch (err: any) {
      error(err.message || "Falha ao enviar mensagem.");
    } finally {
      setIsSending(false);
    }
  };

  const handleApplyQuickReply = (qr: QuickReply) => {
    setMessageText(qr.content);
    setShowQuickMenu(false);
  };

  const filteredConversations = conversations.filter((c) => {
    const term = searchFilter.toLowerCase();
    return (
      c.customer?.name?.toLowerCase().includes(term) ||
      c.customer?.phone?.includes(term) ||
      c.last_message_text?.toLowerCase().includes(term)
    );
  });

  return (
    <div className={styles.inboxPage}>
      <Header
        title="Caixa de Entrada Compartilhada"
        subtitle="Atendimento oficial WhatsApp com múltiplos atendentes simultâneos"
      />

      <div className={styles.inboxLayout}>
        {/* COLUNA 1: Lista de Conversas e Filas */}
        <div className={styles.colConversations}>
          {/* Filas / Queues */}
          <div className={styles.queueTabs}>
            <button
              className={`${styles.queueTab} ${selectedQueue === "all" ? styles.queueActive : ""}`}
              onClick={() => setSelectedQueue("all")}
            >
              Todas
            </button>
            <button
              className={`${styles.queueTab} ${selectedQueue === "unassigned" ? styles.queueActive : ""}`}
              onClick={() => setSelectedQueue("unassigned")}
            >
              Não Atribuídas
            </button>
            <button
              className={`${styles.queueTab} ${selectedQueue === "mine" ? styles.queueActive : ""}`}
              onClick={() => setSelectedQueue("mine")}
            >
              Minhas
            </button>
            <button
              className={`${styles.queueTab} ${selectedQueue === "resolved" ? styles.queueActive : ""}`}
              onClick={() => setSelectedQueue("resolved")}
            >
              Resolvidas
            </button>
          </div>

          <div className={styles.colHeader}>
            <div className={styles.searchBox}>
              <Search size={15} className={styles.searchIcon} />
              <input
                type="text"
                placeholder="Buscar conversa ou telefone..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className={styles.searchInput}
              />
            </div>
          </div>

          <div className={styles.convList}>
            {filteredConversations.map((conv) => {
              const isSelected = conv.id === selectedConvId;
              const isAssignedToMe = conv.assigned_user_id === user?.id;

              return (
                <div
                  key={conv.id}
                  className={`${styles.convItem} ${isSelected ? styles.selected : ""}`}
                  onClick={() => setSelectedConvId(conv.id)}
                >
                  <div className={styles.avatarWrapper}>
                    <div className={styles.convAvatar}>
                      {conv.customer?.name?.charAt(0) || "C"}
                    </div>
                    {conv.unread_count > 0 && (
                      <span className={styles.onlineDot} />
                    )}
                  </div>

                  <div className={styles.convInfo}>
                    <div className={styles.convTopRow}>
                      <span className={styles.convName}>{conv.customer?.name}</span>
                      <span className={styles.convTime}>
                        {new Date(conv.last_message_time).toLocaleTimeString("pt-BR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>

                    <div className={styles.convBottomRow}>
                      <span className={styles.convLastMsg}>
                        {conv.last_message_text || "Sem mensagens anteriores..."}
                      </span>
                      {conv.unread_count > 0 && (
                        <span className={styles.unreadCountBadge}>
                          {conv.unread_count}
                        </span>
                      )}
                    </div>

                    {/* Attendant Assignment Tag */}
                    <div className={styles.attendantTagRow}>
                      {conv.assigned_user ? (
                        <span className={isAssignedToMe ? styles.assignedToMeTag : styles.assignedOtherTag}>
                          <UserCheck size={11} />
                          {isAssignedToMe ? "Você está atendendo" : conv.assigned_user.name}
                        </span>
                      ) : (
                        <span className={styles.unassignedTag}>
                          Não atribuída
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredConversations.length === 0 && (
              <div className={styles.emptyListNotice}>
                <MessageSquare size={32} style={{ color: "var(--text-muted)", marginBottom: 8 }} />
                <span>Nenhuma conversa nesta fila.</span>
              </div>
            )}
          </div>
        </div>

        {/* COLUNA 2: Chat Atual */}
        <div className={styles.colChat}>
          {activeConv ? (
            <>
              {/* Chat Header com Status de Atribuição e Ações Multiatendente */}
              <div className={styles.chatHeader}>
                <div className={styles.chatHeaderUser}>
                  <div className={styles.chatAvatar}>
                    {activeConv.customer?.name?.charAt(0) || "C"}
                  </div>
                  <div>
                    <h3 className={styles.chatCustomerName}>{activeConv.customer?.name}</h3>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 2 }}>
                      <span className={styles.chatStatus}>
                        {formatPhone(activeConv.customer?.phone || "")}
                      </span>
                      {activeConv.assigned_user ? (
                        <span className={activeConv.assigned_user_id === user?.id ? styles.assignedBadgeMe : styles.assignedBadgeOther}>
                          Responsável: <strong>{activeConv.assigned_user.name}</strong>
                        </span>
                      ) : (
                        <span className={styles.assignedBadgeNone}>
                          Nenhum atendente responsável
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className={styles.chatHeaderActions}>
                  {activeConv.assigned_user_id !== user?.id && (
                    <button
                      onClick={handleAssignToMe}
                      className={styles.assignBtn}
                      title="Assumir o atendimento desta conversa"
                    >
                      <UserCheck size={14} />
                      <span>Assumir Atendimento</span>
                    </button>
                  )}

                  <button
                    onClick={() => setShowTransferModal(true)}
                    className={styles.transferBtn}
                    title="Transferir para outro atendente"
                  >
                    <ArrowRightLeft size={14} />
                    <span>Transferir</span>
                  </button>

                  <button
                    onClick={handleResolveConversation}
                    className={styles.resolveBtn}
                    title="Finalizar e resolver atendimento"
                  >
                    <CheckCircle size={14} />
                    <span>Resolver</span>
                  </button>
                </div>
              </div>

              {/* Chat Message Stream */}
              <div className={styles.messagesContainer}>
                <div className={styles.encryptionNotice}>
                  🔒 Caixa compartilhada oficial conectada ao WhatsApp Cloud API
                </div>

                {messages.length === 0 && (
                  <div className={styles.emptyMessagesBox}>
                    <MessageSquare size={32} style={{ color: "var(--text-muted)", marginBottom: 6 }} />
                    <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>Esta conversa ainda não possui mensagens.</p>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Envie uma mensagem abaixo para iniciar o contato com o cliente.</span>
                  </div>
                )}

                {messages.map((msg) => {
                  const isOutbound = msg.direction === "outbound";
                  return (
                    <div
                      key={msg.id}
                      className={`${styles.msgBubbleWrapper} ${
                        isOutbound ? styles.outbound : styles.inbound
                      }`}
                    >
                      <div className={styles.msgBubble}>
                        {isOutbound && msg.sender && (
                          <div className={styles.msgSenderLabel}>
                            Enviado por: {msg.sender.name}
                          </div>
                        )}
                        <p className={styles.msgContent}>{msg.content}</p>
                        <div className={styles.msgMeta}>
                          <span className={styles.msgTimestamp}>
                            {new Date(msg.created_at).toLocaleTimeString("pt-BR", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          {isOutbound && (
                            <span className={styles.msgCheck}>
                              <CheckCheck
                                size={14}
                                className={
                                  msg.status === "read"
                                    ? styles.checkRead
                                    : msg.status === "failed"
                                    ? styles.checkFailed
                                    : styles.doubleCheck
                                }
                              />
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Replies Floater */}
              {showQuickMenu && (
                <div className={styles.quickRepliesMenu}>
                  <div className={styles.qrHeader}>
                    <span>Respostas Rápidas</span>
                    <button onClick={() => setShowQuickMenu(false)}>✕</button>
                  </div>
                  <div className={styles.qrList}>
                    {quickReplies.map((qr) => (
                      <button
                        key={qr.id}
                        className={styles.qrItem}
                        onClick={() => handleApplyQuickReply(qr)}
                      >
                        <span className={styles.qrShortcut}>{qr.shortcut}</span>
                        <span className={styles.qrTitle}>{qr.title}</span>
                      </button>
                    ))}
                    {quickReplies.length === 0 && (
                      <div style={{ padding: 12, fontSize: 12, color: "var(--text-muted)" }}>
                        Nenhuma resposta rápida cadastrada. Cadastre em Respostas Rápidas.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Chat Input Bar */}
              <form onSubmit={handleSendMessage} className={styles.inputBar}>
                <button
                  type="button"
                  onClick={() => setShowQuickMenu(!showQuickMenu)}
                  className={`${styles.toolBtn} ${showQuickMenu ? styles.toolBtnActive : ""}`}
                  title="Respostas Rápidas"
                >
                  <Zap size={18} />
                </button>

                <textarea
                  className={styles.chatInput}
                  placeholder="Escreva uma resposta oficial..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  rows={1}
                />

                <button
                  type="submit"
                  disabled={!messageText.trim() || isSending}
                  className={styles.sendBtn}
                >
                  <Send size={16} />
                </button>
              </form>
            </>
          ) : (
            <div className={styles.emptyChat}>
              <InboxIcon size={48} className={styles.emptyChatIcon} />
              <h3>Nenhuma conversa selecionada</h3>
              <p>Selecione uma conversa na lista lateral ou aguarde novas mensagens reais de clientes.</p>
            </div>
          )}
        </div>

        {/* COLUNA 3: Informações do Cliente */}
        {activeConv && activeConv.customer && (
          <div className={styles.colCustomer}>
            <div className={styles.customerHeader}>
              <div className={styles.customerBigAvatar}>
                {activeConv.customer.name.charAt(0)}
              </div>
              <h3 className={styles.customerName}>{activeConv.customer.name}</h3>
              <span className={styles.customerCompany}>
                {activeConv.customer.company_name || "Pessoa Física"}
              </span>
            </div>

            <div className={styles.customerBody}>
              {/* Tags */}
              <div className={styles.detailSection}>
                <label className={styles.detailLabel}>Etiquetas</label>
                <div className={styles.tagChips}>
                  {activeConv.customer.customer_tags && activeConv.customer.customer_tags.length > 0 ? (
                    activeConv.customer.customer_tags.map((ct) => (
                      <span
                        key={ct.id}
                        className={styles.tagChip}
                        style={{ backgroundColor: `${ct.tag.color}20`, color: ct.tag.color }}
                      >
                        {ct.tag.name}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Nenhuma tag vinculada</span>
                  )}
                </div>
              </div>

              {/* Contact Info */}
              <div className={styles.detailSection}>
                <label className={styles.detailLabel}>Contato</label>
                <div className={styles.infoRow}>
                  <Phone size={14} className={styles.infoIcon} />
                  <span>{formatPhone(activeConv.customer.phone)}</span>
                </div>
                {activeConv.customer.email && (
                  <div className={styles.infoRow}>
                    <Mail size={14} className={styles.infoIcon} />
                    <span>{activeConv.customer.email}</span>
                  </div>
                )}
              </div>

              {/* Commercial Metrics */}
              <div className={styles.detailSection}>
                <label className={styles.detailLabel}>Métricas do Cliente</label>
                <div className={styles.metricsGrid}>
                  <div className={styles.metricBox}>
                    <span className={styles.metricVal}>
                      {formatCurrency(activeConv.customer.total_spent)}
                    </span>
                    <span className={styles.metricSub}>Total Comprado</span>
                  </div>
                  <div className={styles.metricBox}>
                    <span className={styles.metricVal}>
                      {activeConv.customer.orders_count}
                    </span>
                    <span className={styles.metricSub}>Pedidos Fechados</span>
                  </div>
                </div>
              </div>

              {/* Notes */}
              <div className={styles.detailSection}>
                <label className={styles.detailLabel}>Observações Internas</label>
                <p className={styles.notesBox}>
                  {activeConv.customer.notes || "Nenhuma observação cadastrada."}
                </p>
              </div>

              {/* Quick Actions */}
              <div className={styles.sideActions}>
                <Link
                  href={`/pipeline`}
                  className={styles.sideActionBtn}
                >
                  <ShoppingBag size={14} />
                  <span>Criar Oportunidade</span>
                </Link>
                <Link
                  href={`/followups`}
                  className={styles.sideActionBtn}
                >
                  <Clock size={14} />
                  <span>Agendar Follow-up</span>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal de Transferência de Conversa */}
      {showTransferModal && (
        <div className={styles.modalBackdrop}>
          <div className={styles.modalContent}>
            <h3 className={styles.modalTitle}>Transferir Atendimento</h3>
            <p className={styles.modalDesc}>
              Selecione o atendente que continuará o atendimento através do mesmo número oficial de WhatsApp.
            </p>

            <div className={styles.modalFormGroup}>
              <label>Selecione o Atendente</label>
              <select
                className={styles.modalSelect}
                value={transferTargetUserId || ""}
                onChange={(e) => setTransferTargetUserId(Number(e.target.value))}
              >
                <option value="">Selecione um colega...</option>
                {teamMembers
                  .filter((m) => m.id !== user?.id)
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.role})
                    </option>
                  ))}
              </select>
            </div>

            <div className={styles.modalFormGroup}>
              <label>Motivo / Observação da Transferência (Opcional)</label>
              <textarea
                className={styles.modalTextarea}
                placeholder="Ex: Cliente tem dúvidas financeiras sobre emissão de nota..."
                value={transferNotes}
                onChange={(e) => setTransferNotes(e.target.value)}
                rows={3}
              />
            </div>

            <div className={styles.modalActions}>
              <button
                type="button"
                className={styles.modalCancelBtn}
                onClick={() => setShowTransferModal(false)}
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={!transferTargetUserId}
                className={styles.modalConfirmBtn}
                onClick={handleTransfer}
              >
                Confirmar Transferência
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}