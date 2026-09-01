"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { apiFetch } from "@/lib/api";
import { Notification } from "@/types";
import styles from "./Header.module.css";
import {
  Bell,
  Sun,
  Moon,
  Laptop,
  CheckCircle2,
  ExternalLink,
  Search,
  Plus,
  MessageSquare
} from "lucide-react";
import Link from "next/link";

interface HeaderProps {
  title?: string;
  subtitle?: string;
  onQuickNewLead?: () => void;
}

export default function Header({ title, subtitle, onQuickNewLead }: HeaderProps) {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const data = await apiFetch<Notification[]>("/notifications");
      setNotifications(data);
    } catch {
      // ignore
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markAllAsRead = async () => {
    try {
      await apiFetch("/notifications/read-all", { method: "POST" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // ignore
    }
  };

  return (
    <header className={styles.header}>
      <div className={styles.titleSection}>
        {title && <h1 className={styles.title}>{title}</h1>}
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>

      <div className={styles.actions}>
        {/* Quick New Customer Button */}
        <Link href="/customers?new=true" className={styles.quickActionBtn}>
          <Plus size={16} />
          <span>Novo Cliente</span>
        </Link>

        {/* Theme Selector */}
        <div className={styles.dropdownContainer}>
          <button
            className={styles.iconBtn}
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            title="Alterar tema"
          >
            {theme === "light" && <Sun size={18} />}
            {theme === "dark" && <Moon size={18} />}
            {theme === "system" && <Laptop size={18} />}
          </button>

          {showThemeMenu && (
            <div className={styles.themeMenu} onClick={() => setShowThemeMenu(false)}>
              <button
                className={`${styles.themeOption} ${theme === "light" ? styles.active : ""}`}
                onClick={() => setTheme("light")}
              >
                <Sun size={15} />
                <span>Claro</span>
              </button>
              <button
                className={`${styles.themeOption} ${theme === "dark" ? styles.active : ""}`}
                onClick={() => setTheme("dark")}
              >
                <Moon size={15} />
                <span>Escuro</span>
              </button>
              <button
                className={`${styles.themeOption} ${theme === "system" ? styles.active : ""}`}
                onClick={() => setTheme("system")}
              >
                <Laptop size={15} />
                <span>Sistema</span>
              </button>
            </div>
          )}
        </div>

        {/* Notification Bell */}
        <div className={styles.dropdownContainer}>
          <button
            className={styles.iconBtn}
            onClick={() => setShowNotifs(!showNotifs)}
            title="Notificações"
          >
            <Bell size={18} />
            {unreadCount > 0 && <span className={styles.notifBadge}>{unreadCount}</span>}
          </button>

          {showNotifs && (
            <div className={styles.notifDropdown}>
              <div className={styles.notifHeader}>
                <span className={styles.notifTitle}>Notificações</span>
                {unreadCount > 0 && (
                  <button onClick={markAllAsRead} className={styles.markAllReadBtn}>
                    Marcar todas lidas
                  </button>
                )}
              </div>
              <div className={styles.notifList}>
                {notifications.length === 0 ? (
                  <div className={styles.emptyNotifs}>Nenhuma notificação no momento</div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`${styles.notifItem} ${!notif.is_read ? styles.unread : ""}`}
                    >
                      <div className={styles.notifItemContent}>
                        <span className={styles.notifItemTitle}>{notif.title}</span>
                        <span className={styles.notifItemMsg}>{notif.message}</span>
                      </div>
                      {notif.link && (
                        <Link href={notif.link} className={styles.notifLink}>
                          <ExternalLink size={14} />
                        </Link>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
