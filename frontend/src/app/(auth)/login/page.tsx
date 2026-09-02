"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import styles from "./Auth.module.css";
import { MessageSquare, ArrowRight, Lock, Mail, Sparkles } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login, user } = useAuth();
  const { error, success } = useToast();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      error("Preencha seu e-mail e senha.");
      return;
    }

    try {
      setIsLoading(true);
      await login(email, password);
      success("Login efetuado com sucesso!");
      // Navigate after successful login
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "E-mail ou senha incorretos.";
      error(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.logoBadge}>
            <MessageSquare size={22} className={styles.logoIcon} />
          </div>
          <h1 className={styles.title}>Converza</h1>
          <p className={styles.subtitle}>O CRM de WhatsApp para o seu negócio crescer</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <label htmlFor="login-email" className={styles.label}>E-mail de acesso</label>
            <div className={styles.inputWrapper}>
              <Mail size={16} className={styles.inputIcon} />
              <input
                id="login-email"
                name="username"
                type="email"
                className={styles.input}
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <div className={styles.labelRow}>
              <label htmlFor="login-password" className={styles.label}>Sua Senha</label>
              <a href="#" className={styles.forgotPass}>Esqueceu a senha?</a>
            </div>
            <div className={styles.inputWrapper}>
              <Lock size={16} className={styles.inputIcon} />
              <input
                id="login-password"
                name="password"
                type="password"
                className={styles.input}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={styles.submitBtn}
          >
            {isLoading ? "Entrando..." : "Entrar no CRM"}
            <ArrowRight size={16} />
          </button>
        </form>

        <div className={styles.footer}>
          Não tem uma conta ainda?{" "}
          <Link href="/register" className={styles.footerLink}>
            Criar conta grátis
          </Link>
        </div>
      </div>
    </div>
  );
}