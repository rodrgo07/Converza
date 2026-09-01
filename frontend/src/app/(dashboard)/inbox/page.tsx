"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch, formatCurrency, formatPhone } from "@/lib/api";
import { Conversation, Message, Customer, QuickReply } from "@/types";
import Header from "@/components/layout/Header";
import styles from "./Inbox.module.css";
import {
  Send,
  Paperclip,
  Smile,
  Zap,
  Phone,
  Mail,
  Building,
  User,
  ShoppingBag,
  Clock,
  Search,
  Check,
  CheckCheck,
  Plus,
  MessageSquare,
  Sparkles,
  Bot,
  ExternalLink
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
  
  const [messageText, setMessageText] = useState("");
  const [searchFilter, setSearchFilter] = useState("");
  const [showQuickMenu, setShowQuickMenu] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConversations();
    fetchQuickReplies();
  }, []);

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
      const list = await apiFetch<Conversation[]>("/conversations");
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

  const loadConversationDetails = async (id: number) => {
    try {
      const data = await apiFetch<Conversation & { messages: Message[] }>(`/conversations/${id}`);
      setActiveConv(data);
      setMessages(data.messages || []);
      
      // Update local unread counter
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, unread_count: 0 } : c))
      );
    } catch (err: any) {
      error("Erro ao carregar mensagens");
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
      
      // Update conversation in sidebar
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedConvId
            ? { ...c, last_message_text: content, last_message_time: new Date().toISOString() }
            : c
        )
      );
      success("Mensagem enviada via WhatsApp!");
    } catch (err: any) {
      error(err.message || "Falha ao enviar mensagem.");
    } finally {
      setIsSending(false);
    }
  };

  const handleSimulateReply = async () => {
    if (!selectedConvId) return;
    try {
      setIsSimulating(true);
      const replies = [
        "Perfeito! Me manda a chave Pix que já vou fazer o pagamento agora.",
        "Gostei muito do modelo, tem como reservar pra mim até amanhã?",
        "Qual é o prazo de entrega se eu fechar hoje?",
        "Consegue dar mais 5% de desconto no Pix à vista?",
        "Recebi as fotos aqui, ficaram ótimas! Vou querer esse mesmo."
      ];
      const randomReply = replies[Math.floor(Math.random() * replies.length)];

      const receivedMsg = await apiFetch<Message>(`/conversations/${selectedConvId}/simulate-receive`, {
        method: "POST",
        body: JSON.stringify({ content: randomReply, message_type: "text" }),
      });

      setMessages((prev) => [...prev, receivedMsg]);
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedConvId
            ? { ...c, last_message_text: randomReply, last_message_time: new Date().toISOString() }
            : c
        )
      );
      success("Simulação: O cliente acabou de responder!");
    } catch (err: any) {
      error("Erro na simulação.");
    } finally {
      setIsSimulating(false);
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
        title="Caixa de Entrada"
        subtitle="Atendimento e vendas do WhatsApp em tempo real"
      />

      <div className={styles.inboxLayout}>
        {/* COLUNA 1: Lista de Conversas */}
        <div className={styles.colConversations}>
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
                        {conv.last_message_text || "Iniciar atendimento..."}
                      </span>
                      {conv.unread_count > 0 && (
                        <span className={styles.unreadCountBadge}>
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* COLUNA 2: Chat Atual */}
        <div className={styles.colChat}>
          {activeConv ? (
            <>
              {/* Chat Header */}
              <div className={styles.chatHeader}>
                <div className={styles.chatHeaderUser}>
                  <div className={styles.chatAvatar}>
                    {activeConv.customer?.name?.charAt(0) || "C"}
                  </div>
                  <div>
                    <h3 className={styles.chatCustomerName}>{activeConv.customer?.name}</h3>
                    <span className={styles.chatStatus}>
                      WhatsApp Oficial • {formatPhone(activeConv.customer?.phone || "")}
                    </span>
                  </div>
                </div>

                <div className={styles.chatHeaderActions}>
                  <button
                    onClick={handleSimulateReply}
                    disabled={isSimulating}
                    className={styles.simReplyBtn}
                    title="Simular cliente respondendo"
                  >
                    <Bot size={14} />
                    <span>{isSimulating ? "Recebendo..." : "Simular Resposta"}</span>
                  </button>
                  <Link
                    href={`/customers/${activeConv.customer_id}`}
                    className={styles.profileBtn}
                  >
                    Ver Perfil
                  </Link>
                </div>
              </div>

              {/* Chat Message Stream */}
              <div className={styles.messagesContainer}>
                <div className={styles.encryptionNotice}>
                  🔒 Conversa integrada com a API Oficial do WhatsApp Business
                </div>

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
                              <CheckCheck size={14} className={styles.doubleCheck} />
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
                  placeholder="Escreva uma mensagem ou use respostas rápidas..."
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
              <MessageSquare size={48} className={styles.emptyChatIcon} />
              <h3>Nenhuma conversa selecionada</h3>
              <p>Escolha um cliente à esquerda para visualizar as mensagens.</p>
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
                {activeConv.customer.company_name || "Cliente Final"}
              </span>
            </div>

            <div className={styles.customerBody}>
              {/* Tags */}
              <div className={styles.detailSection}>
                <label className={styles.detailLabel}>Etiquetas</label>
                <div className={styles.tagChips}>
                  {activeConv.customer.customer_tags?.map((ct) => (
                    <span
                      key={ct.id}
                      className={styles.tagChip}
                      style={{ backgroundColor: `${ct.tag.color}20`, color: ct.tag.color }}
                    >
                      {ct.tag.name}
                    </span>
                  ))}
                  <button className={styles.addTagBtn}>+ Tag</button>
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
                  {activeConv.customer.notes || "Nenhuma anotação cadastrada."}
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
    </div>
  );
}