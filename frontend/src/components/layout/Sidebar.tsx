"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import styles from "./Sidebar.module.css";
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  Kanban,
  CalendarClock,
  CheckSquare,
  Zap,
  BarChart3,
  Users2,
  Settings,
  LogOut,
  Sparkles,
  ChevronRight
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string | number;
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user, company, logout } = useAuth();

  const mainNav: NavItem[] = [
    { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard size={18} /> },
    { label: "Caixa de Entrada", href: "/inbox", icon: <MessageSquare size={18} /> },
    { label: "Clientes", href: "/customers", icon: <Users size={18} /> },
    { label: "Pipeline de Vendas", href: "/pipeline", icon: <Kanban size={18} /> },
    { label: "Follow-ups", href: "/followups", icon: <CalendarClock size={18} /> },
    { label: "Tarefas", href: "/tasks", icon: <CheckSquare size={18} /> },
  ];

  const secondaryNav: NavItem[] = [
    { label: "Respostas Rápidas", href: "/quick-replies", icon: <Zap size={18} /> },
    { label: "Relatórios", href: "/reports", icon: <BarChart3 size={18} /> },
    { label: "Equipe", href: "/team", icon: <Users2 size={18} /> },
    { label: "Configurações", href: "/settings", icon: <Settings size={18} /> },
  ];

  return (
    <aside className={styles.sidebar}>
      {/* Brand Header */}
      <div className={styles.header}>
        <div className={styles.logoMark}>
          <MessageSquare size={20} className={styles.logoIcon} />
        </div>
        <div className={styles.logoTextContainer}>
          <span className={styles.logoText}>Converza</span>
          <span className={styles.logoTag}>CRM WhatsApp</span>
        </div>
      </div>

      {/* Company Box */}
      <div className={styles.companyBox}>
        <div className={styles.companyAvatar}>
          {company?.name?.charAt(0) || "C"}
        </div>
        <div className={styles.companyInfo}>
          <span className={styles.companyName}>{company?.name || "Minha Empresa"}</span>
          <span className={styles.companySegment}>{company?.segment || "Pequeno Negócio"}</span>
        </div>
      </div>

      {/* Main Navigation */}
      <div className={styles.navGroup}>
        <div className={styles.groupLabel}>PRINCIPAL</div>
        <nav className={styles.nav}>
          {mainNav.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`${styles.navItem} ${isActive ? styles.active : ""}`}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <span className={styles.navLabel}>{item.label}</span>
                {item.badge && <span className={styles.badge}>{item.badge}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Tools Navigation */}
      <div className={styles.navGroup}>
        <div className={styles.groupLabel}>GERENCIAMENTO</div>
        <nav className={styles.nav}>
          {secondaryNav.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`${styles.navItem} ${isActive ? styles.active : ""}`}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <span className={styles.navLabel}>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Quick Upgrade / Status Card */}
      <div className={styles.upgradeCard}>
        <div className={styles.upgradeHeader}>
          <Sparkles size={16} className={styles.sparkleIcon} />
          <span className={styles.upgradeTitle}>WhatsApp Conectado</span>
        </div>
        <p className={styles.upgradeDesc}>
          API Oficial Cloud ativa e operante para envio e recebimento de mensagens.
        </p>
      </div>

      {/* User Footer */}
      <div className={styles.footer}>
        <div className={styles.userProfile}>
          <div className={styles.userAvatar}>
            {user?.name?.charAt(0) || "U"}
          </div>
          <div className={styles.userInfo}>
            <span className={styles.userName}>{user?.name || "Usuário"}</span>
            <span className={styles.userRole}>
              {user?.role === "admin" ? "Administrador" : "Vendedor"}
            </span>
          </div>
        </div>
        <button
          onClick={logout}
          className={styles.logoutBtn}
          title="Sair da conta"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
}
