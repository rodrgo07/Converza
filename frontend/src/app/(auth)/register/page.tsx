"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import styles from "../login/Auth.module.css";
import { MessageSquare, ArrowRight, Lock, Mail, User, Building, Phone } from "lucide-react";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { register } = useAuth();
  const { error, success } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) {
      error("Preencha os campos obrigatórios.");
      return;
    }

    try {
      setIsLoading(true);
      await register(name, email, password, phone, companyName);
      success("Conta criada com sucesso! Configure seu negócio a seguir.");
    } catch (err: any) {
      error(err.message || "Erro ao cadastrar.");
    } finally {
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
          <h1 className={styles.title}>Criar sua Conta</h1>
          <p className={styles.subtitle}>Comece a organizar suas vendas de WhatsApp em minutos</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Seu Nome Completo</label>
            <div className={styles.inputWrapper}>
              <User size={16} className={styles.inputIcon} />
              <input
                type="text"
                className={styles.input}
                placeholder="Ex: João Silva"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Nome da sua Empresa ou Negócio</label>
            <div className={styles.inputWrapper}>
              <Building size={16} className={styles.inputIcon} />
              <input
                type="text"
                className={styles.input}
                placeholder="Ex: Barbearia do João / Loja Elegance"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>WhatsApp / Telefone</label>
            <div className={styles.inputWrapper}>
              <Phone size={16} className={styles.inputIcon} />
              <input
                type="tel"
                className={styles.input}
                placeholder="(11) 98765-4321"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>E-mail</label>
            <div className={styles.inputWrapper}>
              <Mail size={16} className={styles.inputIcon} />
              <input
                type="email"
                className={styles.input}
                placeholder="joao@seuemail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Crie uma Senha Segura</label>
            <div className={styles.inputWrapper}>
              <Lock size={16} className={styles.inputIcon} />
              <input
                type="password"
                className={styles.input}
                placeholder="Mínimo 6 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={styles.submitBtn}
          >
            {isLoading ? "Criando sua conta..." : "Começar Gratuitamente"}
            <ArrowRight size={16} />
          </button>
        </form>

        <div className={styles.footer}>
          Já possui cadastro?{" "}
          <Link href="/login" className={styles.footerLink}>
            Fazer login
          </Link>
        </div>
      </div>
    </div>
  );
}