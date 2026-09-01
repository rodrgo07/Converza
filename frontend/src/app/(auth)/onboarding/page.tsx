"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { apiFetch } from "@/lib/api";
import confetti from "canvas-confetti";
import styles from "./Onboarding.module.css";
import {
  Store,
  Briefcase,
  Home,
  Sparkles,
  Utensils,
  ShoppingBag,
  HelpCircle,
  User,
  Users,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  MessageSquare
} from "lucide-react";

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [segment, setSegment] = useState("Loja de Varejo");
  const [teamSize, setTeamSize] = useState("Só eu");
  const [whatsappUsage, setWhatsappUsage] = useState("Tudo isso");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { updateUser, refreshCompany } = useAuth();
  const { success, error } = useToast();
  const router = useRouter();

  const businessSegments = [
    { label: "Loja física / Roupas", icon: <Store size={20} /> },
    { label: "Prestação de Serviços", icon: <Briefcase size={20} /> },
    { label: "Imobiliária / Corretores", icon: <Home size={20} /> },
    { label: "Saúde / Estética / Salão", icon: <Sparkles size={20} /> },
    { label: "Alimentação / Delivery", icon: <Utensils size={20} /> },
    { label: "E-commerce Online", icon: <ShoppingBag size={20} /> },
    { label: "Outro segmento", icon: <HelpCircle size={20} /> },
  ];

  const teamSizes = [
    { label: "Só eu", desc: "Trabalho sozinho(a)" },
    { label: "2 a 3 pessoas", desc: "Pequena equipe" },
    { label: "4 a 10 pessoas", desc: "Time em crescimento" },
    { label: "Mais de 10", desc: "Equipe estruturada" },
  ];

  const usages = [
    { label: "Vendas diretas", desc: "Fechar orçamentos e pedidos" },
    { label: "Atendimento ao cliente", desc: "Tirar dúvidas e suporte" },
    { label: "Agendamentos", desc: "Marcar horários e serviços" },
    { label: "Tudo isso", desc: "Uso completo para o dia a dia" },
  ];

  const handleFinish = async () => {
    try {
      setIsSubmitting(true);
      await apiFetch("/auth/onboarding", {
        method: "POST",
        body: JSON.stringify({
          segment,
          team_size: teamSize,
          whatsapp_usage: whatsappUsage,
        }),
      });

      updateUser({ onboarding_completed: true });
      await refreshCompany();

      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
      });

      success("Tudo pronto! Seu CRM está configurado.");
      setTimeout(() => {
        router.push("/dashboard");
      }, 1200);
    } catch (err: any) {
      error(err.message || "Erro ao salvar preferências.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.wizardCard}>
        {/* Progress header */}
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        <div className={styles.header}>
          <div className={styles.stepIndicator}>Etapa {step} de 3</div>
          {step === 1 && (
            <>
              <h1 className={styles.title}>Qual é o seu tipo de negócio?</h1>
              <p className={styles.subtitle}>
                Vamos personalizar seus funis e modelos para o seu nicho.
              </p>
            </>
          )}
          {step === 2 && (
            <>
              <h1 className={styles.title}>Quantas pessoas atendem seus clientes?</h1>
              <p className={styles.subtitle}>
                Você poderá convidar vendedores e gerentes a qualquer momento.
              </p>
            </>
          )}
          {step === 3 && (
            <>
              <h1 className={styles.title}>Como você utiliza o WhatsApp hoje?</h1>
              <p className={styles.subtitle}>
                Defina o foco principal para otimizarmos seus atalhos.
              </p>
            </>
          )}
        </div>

        {/* Step 1: Segment */}
        {step === 1 && (
          <div className={styles.optionsGrid}>
            {businessSegments.map((item) => (
              <button
                key={item.label}
                type="button"
                className={`${styles.optionCard} ${
                  segment === item.label ? styles.selected : ""
                }`}
                onClick={() => setSegment(item.label)}
              >
                <div className={styles.optionIcon}>{item.icon}</div>
                <span className={styles.optionLabel}>{item.label}</span>
                {segment === item.label && (
                  <CheckCircle2 size={16} className={styles.checkIcon} />
                )}
              </button>
            ))}
          </div>
        )}

        {/* Step 2: Team Size */}
        {step === 2 && (
          <div className={styles.verticalOptions}>
            {teamSizes.map((item) => (
              <button
                key={item.label}
                type="button"
                className={`${styles.verticalOptionCard} ${
                  teamSize === item.label ? styles.selected : ""
                }`}
                onClick={() => setTeamSize(item.label)}
              >
                <div className={styles.optionContent}>
                  <span className={styles.verticalOptionTitle}>{item.label}</span>
                  <span className={styles.verticalOptionDesc}>{item.desc}</span>
                </div>
                {teamSize === item.label && (
                  <CheckCircle2 size={18} className={styles.checkIcon} />
                )}
              </button>
            ))}
          </div>
        )}

        {/* Step 3: Usage */}
        {step === 3 && (
          <div className={styles.verticalOptions}>
            {usages.map((item) => (
              <button
                key={item.label}
                type="button"
                className={`${styles.verticalOptionCard} ${
                  whatsappUsage === item.label ? styles.selected : ""
                }`}
                onClick={() => setWhatsappUsage(item.label)}
              >
                <div className={styles.optionContent}>
                  <span className={styles.verticalOptionTitle}>{item.label}</span>
                  <span className={styles.verticalOptionDesc}>{item.desc}</span>
                </div>
                {whatsappUsage === item.label && (
                  <CheckCircle2 size={18} className={styles.checkIcon} />
                )}
              </button>
            ))}
          </div>
        )}

        {/* Navigation Buttons */}
        <div className={styles.footerNav}>
          {step > 1 ? (
            <button
              type="button"
              className={styles.backBtn}
              onClick={() => setStep(step - 1)}
            >
              <ArrowLeft size={16} />
              <span>Voltar</span>
            </button>
          ) : (
            <div />
          )}

          {step < 3 ? (
            <button
              type="button"
              className={styles.nextBtn}
              onClick={() => setStep(step + 1)}
            >
              <span>Continuar</span>
              <ArrowRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              disabled={isSubmitting}
              className={styles.finishBtn}
              onClick={handleFinish}
            >
              <span>{isSubmitting ? "Finalizando..." : "Seu CRM está pronto 🚀"}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}