import React, { useState, useEffect, useRef } from 'react';
import { FolgaChart } from './FolgaChart';
import { GoldenAnalysis, DecisionResponse, DecisionTerms } from '../types/pingo';
import { sendChatMessage } from '../api/client';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'pingo';
  text: string;
  timestamp: string;
  draft?: DecisionTerms | null;
  decision?: DecisionResponse | null;
  goldenAnalysis?: GoldenAnalysis | null;
  showDetails?: boolean;
  isWhatIf?: boolean;
  isPlan?: boolean;
  isSaved?: boolean;
}

interface ChatScreenProps {
  supervisorActive: boolean;
  onOpenSupervisor: () => void;
  onGoHome: () => void;
  zoom?: number;
  reduceMotion?: boolean;
}

export const ChatScreen: React.FC<ChatScreenProps> = ({
  supervisorActive,
  onOpenSupervisor,
  onGoHome,
  zoom = 1,
  reduceMotion = false,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      sender: 'pingo',
      text: 'Oi, Vinicius! Eu sou o Pingo. Te ajudo a ver o impacto de uma decisão no seu mês antes de você decidir.\n\nMe conte o que você está pensando em fazer.',
      timestamp: '10:02',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [thinking, setThinking] = useState(false);
  const [currentDraft, setCurrentDraft] = useState<DecisionTerms | null>(null);
  const [sessionId] = useState<string>(`session-${Date.now()}`);
  const scrollRef = useRef<HTMLDivElement>(null);

  // What-If state for simulator
  const [whatIfWait, setWhatIfWait] = useState(true);
  const [whatIfCount, setWhatIfCount] = useState<number>(10);
  const [whatIfStress, setWhatIfStress] = useState(false);

  // Helper formatting functions
  const formatBrl = (val: number, withSign = false) => {
    const absStr = Math.abs(val).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    const prefix = val < 0 ? '−' : withSign ? '+' : '';
    return `${prefix}R$ ${absStr}`;
  };

  const formatCents = (cents: number | null | undefined, withSign = false) => {
    if (cents === null || cents === undefined) return 'R$ 0,00';
    return formatBrl(cents / 100, withSign);
  };

  const getNowTime = () => {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  };

  // Auto scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: reduceMotion ? 'auto' : 'smooth',
      });
    }
  }, [messages, thinking]);

  // Send a message to backend
  const handleSendMessage = async (text: string, overrideDraft?: DecisionTerms | null) => {
    const trimmed = text.trim();
    if (!trimmed || thinking) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: trimmed,
      timestamp: getNowTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setThinking(true);

    try {
      const activeDraft = overrideDraft !== undefined ? overrideDraft : currentDraft;
      const res = await sendChatMessage(trimmed, sessionId, true, activeDraft);

      if (res.draft) {
        setCurrentDraft(res.draft);
      }

      // Check if what-if or plan requested
      const lower = trimmed.toLowerCase();
      const isWhatIf = lower.includes('e se');
      const isPlan = lower.includes('plano') || lower.includes('montar');

      const pingoMsg: ChatMessage = {
        id: `pingo-${Date.now()}`,
        sender: 'pingo',
        text: res.message,
        timestamp: getNowTime(),
        draft: res.draft,
        decision: res.decision,
        goldenAnalysis: res.golden_analysis,
        showDetails: false,
        isWhatIf,
        isPlan,
      };

      setMessages((prev) => [...prev, pingoMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `pingo-err-${Date.now()}`,
        sender: 'pingo',
        text: 'Não consegui consultar as informações agora. Por favor, tente novamente.',
        timestamp: getNowTime(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setThinking(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage(inputText);
    }
  };

  const toggleDetails = (msgId: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, showDetails: !m.showDetails } : m))
    );
  };

  // Term button clicked
  const handleSelectTerm = (termText: string, installmentCount?: number, isInterestFree = true) => {
    let updatedDraft = currentDraft ? { ...currentDraft } : null;
    if (updatedDraft && installmentCount) {
      updatedDraft.installment_count = installmentCount;
      updatedDraft.interest_free = isInterestFree;
    }
    handleSendMessage(termText, updatedDraft);
  };

  // Find latest golden analysis for global metrics if available
  const latestAnalysisMsg = [...messages].reverse().find((m) => m.goldenAnalysis);
  const analysis = latestAnalysisMsg?.goldenAnalysis || null;

  const salaryObserved = analysis?.salary_observed_cents ?? 675499;
  const recentAvgMargin = analysis?.recent_average_margin_cents ?? 20377;
  const lastMonthMargin = analysis?.last_month_margin_cents ?? -57685;
  const installmentsTotal = analysis?.observed_installments_total_cents ?? 69078;
  const installmentsList = analysis?.installments_cents ?? [24401, 41109, 3568];

  const baseMarginFloat = recentAvgMargin / 100;
  const freedMarginFloat = (recentAvgMargin + installmentsTotal) / 100;

  // Render what-if simulator data
  const months = ['out', 'nov', 'dez', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set'];
  const baseMarginWf = whatIfStress ? lastMonthMargin / 100 : baseMarginFloat;
  const itemPrice = currentDraft?.total_price_cents ? currentDraft.total_price_cents / 100 : 10000;
  const wfInstallment = itemPrice / whatIfCount;
  const wfStartMonthIdx = whatIfWait ? 1 : 0;

  const wfValues: number[] = [];
  for (let i = 0; i < 12; i++) {
    const freed = i >= 1 ? installmentsTotal / 100 : 0;
    const expense = i >= wfStartMonthIdx && i < wfStartMonthIdx + whatIfCount ? wfInstallment : 0;
    wfValues.push(baseMarginWf + freed - expense);
  }

  const maxPos = Math.max(100, ...wfValues.map((v) => Math.max(0, v)));
  const maxNeg = Math.max(100, ...wfValues.map((v) => Math.max(0, -v)));
  const totalH = maxPos + maxNeg;
  const chartHeightPx = 140;
  const zeroLineTop = (maxPos / totalH) * chartHeightPx;
  const negCount = wfValues.filter((v) => v < 0).length;
  const novAfterFloat = wfValues[1];

  let wfAssessment = {
    icon: 'circle-check',
    title: 'Sem meses no negativo',
    text: 'Nesta simulação sobra dinheiro todo mês.',
    bg: '#e6f3ec',
    fg: '#0f5230',
  };
  if (negCount > 0) {
    wfAssessment = {
      icon: 'triangle-alert',
      title: `${negCount} ${negCount > 1 ? 'meses' : 'mês'} no negativo em 12`,
      text: whatIfStress
        ? 'Se os meses forem como o último, a compra não cabe em nenhum dos cenários.'
        : 'Vale rever o prazo ou o momento da compra.',
      bg: '#fbf1e1',
      fg: '#5e3300',
    };
  } else if (novAfterFloat < 300) {
    wfAssessment = {
      icon: 'info',
      title: 'Sem meses no negativo, mas com pouca folga',
      text: `Sobram ${formatBrl(novAfterFloat)}/mês. Um imprevisto pequeno já muda o resultado.`,
      bg: '#fbf1e1',
      fg: '#5e3300',
    };
  }

  return (
    <div
      data-screen-label="Conversa"
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(180deg, #ffffff 50%, #dcecea 100%)',
        zIndex: 10,
      }}
    >
      {/* Top Bar with Supervisor status & Close */}
      <div style={{ flex: 'none' }}>
        {/* iOS Status Bar */}
        <div
          style={{
            height: 50,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 30px',
            font: "600 15px 'Inter', sans-serif",
            position: 'relative',
          }}
        >
          <span>10:03</span>
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: 10,
              width: 110,
              height: 32,
              marginLeft: -55,
              background: '#000',
              borderRadius: 20,
            }}
          />
          <div
            style={{
              width: 26,
              height: 12,
              border: '1.5px solid #1c1b1b',
              borderRadius: 4,
              padding: 1.5,
              boxSizing: 'border-box',
            }}
          >
            <div style={{ width: '70%', height: '100%', background: '#1c1b1b', borderRadius: 1 }} />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px 0 16px' }}>
          {supervisorActive ? (
            <button
              onClick={onOpenSupervisor}
              aria-label="Pingo Supervisor ativo. Abrir ajustes"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                minHeight: 44,
                padding: '0 12px',
                borderRadius: 22,
                border: 0,
                background: '#e3eeee',
                color: '#0a3f43',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/shield-check.svg"
                alt=""
                width="16"
                height="16"
              />
              Supervisor ativo
            </button>
          ) : (
            <button
              onClick={onOpenSupervisor}
              aria-label="Pingo Supervisor desligado. Saiba mais"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                minHeight: 44,
                padding: '0 12px',
                borderRadius: 22,
                border: '1px solid #dedcdc',
                background: '#fff',
                color: '#3d3a3a',
                fontSize: 12,
                fontWeight: 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/shield-off.svg"
                alt=""
                width="16"
                height="16"
                style={{ opacity: 0.75 }}
              />
              Supervisor desligado
            </button>
          )}

          <div style={{ flex: 1 }} />

          <button
            onClick={onGoHome}
            aria-label="Fechar Pingo e voltar ao início"
            style={{
              width: 44,
              height: 44,
              border: 0,
              background: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flex: 'none',
            }}
          >
            <img
              src="https://unpkg.com/lucide-static@0.460.0/icons/x.svg"
              alt=""
              width="26"
              height="26"
            />
          </button>
        </div>
      </div>

      {/* Message Log */}
      <div data-pg-scroll="1" data-noscrollbar="1" ref={scrollRef} style={{ flex: 1, overflowY: 'auto' }}>
        <div
          role="log"
          aria-live="polite"
          aria-label="Conversa com o Pingo"
          style={{
            zoom,
            padding: '6px 22px 28px',
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
          }}
        >
          {/* Day Label */}
          <div style={{ textAlign: 'center', fontSize: 13, color: '#4a4545' }}>Hoje</div>

          {/* Render All Messages in Order */}
          {messages.map((msg, idx) => {
            if (msg.sender === 'user') {
              return (
                <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', justifyContent: 'flex-end' }}>
                    <div
                      style={{
                        maxWidth: 260,
                        background: '#f0f1f3',
                        color: '#1c1b1b',
                        borderRadius: 14,
                        padding: '14px 16px',
                        fontSize: 15,
                        lineHeight: '22px',
                        wordBreak: 'break-word',
                      }}
                    >
                      <span style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>
                        Você:{' '}
                      </span>
                      {msg.text}
                    </div>
                    <div
                      aria-hidden="true"
                      style={{
                        width: 30,
                        height: 30,
                        borderRadius: '50%',
                        background: '#333',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        font: "500 12px 'Inter'",
                        flex: 'none',
                      }}
                    >
                      VG
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: '#4a4545', marginRight: 42 }}>
                    {msg.timestamp}
                    <img
                      src="https://unpkg.com/lucide-static@0.460.0/icons/check-check.svg"
                      alt="lida"
                      width="16"
                      height="16"
                      style={{ opacity: 0.7 }}
                    />
                  </div>
                </div>
              );
            }

            // Pingo message
            const hasAnalysis = !!msg.goldenAnalysis && msg.goldenAnalysis.installments_cents.length > 0;
            const installmentAmount = hasAnalysis ? (msg.goldenAnalysis!.installments_cents[0] ?? 100000) / 100 : 0;
            const installmentCount = hasAnalysis ? msg.goldenAnalysis!.installments_cents.length : 10;
            const itemLabel = msg.draft?.label || 'Item';

            return (
              <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Pingo Avatar Sparkle */}
                <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M10 3c.6 4.4 2.6 6.4 7 7-4.4.6-6.4 2.6-7 7-.6-4.4-2.6-6.4-7-7 4.4-.6 6.4-2.6 7-7z"
                    fill="#0e5a5f"
                  />
                  <path
                    d="M18.5 2c.3 1.7 1 2.4 2.5 2.7-1.5.3-2.2 1-2.5 2.6-.3-1.6-1-2.3-2.6-2.6 1.6-.3 2.3-1 2.6-2.7z"
                    fill="#0e5a5f"
                  />
                </svg>

                {/* Natural Response Text */}
                <div style={{ fontSize: 16, lineHeight: '24px', color: '#3d3a3a', textWrap: 'pretty' }}>
                  {msg.text}
                </div>

                {/* Starter Suggestions (only on initial turn) */}
                {idx === 0 && messages.length === 1 && !thinking && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 4 }}>
                    <div style={{ fontSize: 13, color: '#4a4545', fontWeight: 500 }}>
                      Sugestões para começar:
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-start' }}>
                      <button
                        onClick={() => handleSendMessage('Posso comprar um iPhone de R$ 10.000?')}
                        style={{
                          minHeight: 44,
                          padding: '10px 16px',
                          borderRadius: 22,
                          border: '1px solid #0e5a5f',
                          background: '#fff',
                          color: '#0a3f43',
                          fontSize: 15,
                          fontWeight: 500,
                          cursor: 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        Posso comprar um iPhone de R$ 10.000?
                      </button>
                      <button
                        onClick={() => handleSendMessage('Posso comprar um AirPods de R$ 2.000?')}
                        style={{
                          minHeight: 44,
                          padding: '10px 16px',
                          borderRadius: 22,
                          border: '1px solid #0e5a5f',
                          background: '#fff',
                          color: '#0a3f43',
                          fontSize: 15,
                          fontWeight: 500,
                          cursor: 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        Posso comprar um AirPods de R$ 2.000?
                      </button>
                      <button
                        onClick={() => handleSendMessage('Quero comprar um notebook de R$ 8.000 em 8x sem juros.')}
                        style={{
                          minHeight: 44,
                          padding: '10px 16px',
                          borderRadius: 22,
                          border: '1px solid #0e5a5f',
                          background: '#fff',
                          color: '#0a3f43',
                          fontSize: 15,
                          fontWeight: 500,
                          cursor: 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        Quero comprar um notebook de R$ 8.000 em 8x sem juros
                      </button>
                      <button
                        onClick={() => handleSendMessage('Quero viajar em dezembro e preciso de R$ 6.000.')}
                        style={{
                          minHeight: 44,
                          padding: '10px 16px',
                          borderRadius: 22,
                          border: '1px solid #cfcac7',
                          background: '#fff',
                          color: '#1c1b1b',
                          fontSize: 15,
                          cursor: 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        Quero viajar em dezembro e preciso de R$ 6.000
                      </button>
                      <button
                        onClick={() => handleSendMessage('Quero comprar uma casa.')}
                        style={{
                          minHeight: 44,
                          padding: '10px 16px',
                          borderRadius: 22,
                          border: '1px solid #cfcac7',
                          background: '#fff',
                          color: '#1c1b1b',
                          fontSize: 15,
                          cursor: 'pointer',
                          textAlign: 'left',
                        }}
                      >
                        Quero comprar uma casa
                      </button>
                    </div>
                    <div style={{ fontSize: 12, color: '#4a4545', marginTop: 2, fontStyle: 'italic' }}>
                      Ou pergunte do seu jeito no campo abaixo.
                    </div>
                  </div>
                )}

                {/* Question Payment Term Chips */}
                {msg.decision?.question?.field === 'installment_count' && idx === messages.length - 1 && !thinking && (
                  <div role="group" aria-label="Forma de pagamento" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    <button
                      onClick={() => handleSelectTerm('À vista')}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      À vista
                    </button>
                    <button
                      onClick={() => handleSelectTerm('10x sem juros no cartão', 10, true)}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      10x sem juros
                    </button>
                    <button
                      onClick={() => handleSelectTerm('12x sem juros no cartão', 12, true)}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      12x sem juros
                    </button>
                  </div>
                )}

                {/* Question Upfront Chips */}
                {msg.decision?.question?.field === 'upfront_cents' && idx === messages.length - 1 && !thinking && (
                  <div role="group" aria-label="Condição de entrada" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    <button
                      onClick={() => handleSendMessage('Sem entrada')}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      Sem entrada
                    </button>
                    <button
                      onClick={() => handleSendMessage('Consigo pagar R$ 2.000 agora de entrada')}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      R$ 2.000 de entrada
                    </button>
                  </div>
                )}

                {/* Observed Facts Card (Attached when financial facts are present) */}
                {hasAnalysis && (
                  <section
                    aria-label="Observado na sua conta"
                    style={{
                      background: '#fff',
                      border: '1px solid #e3e1e1',
                      borderRadius: 16,
                      padding: '4px 16px 8px',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        minHeight: 44,
                        borderBottom: '1px solid #eeecec',
                      }}
                    >
                      <img
                        src="https://unpkg.com/lucide-static@0.460.0/icons/circle-check.svg"
                        alt=""
                        width="18"
                        height="18"
                      />
                      <span
                        style={{
                          flex: 1,
                          fontSize: 13,
                          fontWeight: 700,
                          color: '#1c1b1b',
                          letterSpacing: '.02em',
                        }}
                      >
                        Observado
                      </span>
                      <span style={{ fontSize: 12, color: '#4a4545' }}>dados da sua conta</span>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'baseline',
                        gap: 12,
                        padding: '14px 0',
                        borderBottom: '1px solid #eeecec',
                      }}
                    >
                      <span style={{ fontSize: 14, color: '#4a4545' }}>Renda CLT</span>
                      <span style={{ fontSize: 15, fontWeight: 600, color: '#1c1b1b', whiteSpace: 'nowrap' }}>
                        {formatCents(salaryObserved)}/mês
                      </span>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'baseline',
                        gap: 12,
                        padding: '14px 0',
                        borderBottom: '1px solid #eeecec',
                      }}
                    >
                      <span style={{ fontSize: 14, color: '#4a4545' }}>
                        Margem média recente
                        <span style={{ display: 'block', fontSize: 12, color: '#4a4545' }}>
                          o que sobra depois das despesas
                        </span>
                      </span>
                      <span style={{ fontSize: 15, fontWeight: 600, color: '#1c1b1b', whiteSpace: 'nowrap' }}>
                        {formatCents(recentAvgMargin, true)}/mês
                      </span>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'baseline',
                        gap: 12,
                        padding: '14px 0',
                        borderBottom: '1px solid #eeecec',
                      }}
                    >
                      <span style={{ fontSize: 14, color: '#4a4545' }}>Último mês</span>
                      <span style={{ fontSize: 15, fontWeight: 600, color: '#8f1114', whiteSpace: 'nowrap' }}>
                        {formatCents(lastMonthMargin)}
                      </span>
                    </div>

                    <div style={{ padding: '14px 0 6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
                        <span style={{ fontSize: 14, color: '#4a4545' }}>
                          {installmentsList.length} parcelas ativas
                        </span>
                        <span style={{ fontSize: 15, fontWeight: 600, color: '#1c1b1b', whiteSpace: 'nowrap' }}>
                          {formatCents(installmentsTotal)}/mês
                        </span>
                      </div>
                      <ul
                        style={{
                          listStyle: 'none',
                          margin: '10px 0 0',
                          padding: '0 0 0 12px',
                          borderLeft: '2px solid #e3e1e1',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 6,
                          fontSize: 13,
                          color: '#3d3a3a',
                        }}
                      >
                        {installmentsList.map((instCents, i) => (
                          <li key={i} style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Parcela {i + 1}</span>
                            <span>{formatCents(instCents)}</span>
                          </li>
                        ))}
                      </ul>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          marginTop: 10,
                          fontSize: 13,
                          fontWeight: 600,
                          color: '#0a3f43',
                        }}
                      >
                        <img
                          src="https://unpkg.com/lucide-static@0.460.0/icons/calendar-check.svg"
                          alt=""
                          width="16"
                          height="16"
                        />
                        Previsão de término: outubro de 2025
                      </div>
                    </div>
                  </section>
                )}

                {/* Folga Projection Card (Only when calculated installments exist) */}
                {hasAnalysis && (
                  <section
                    aria-label="Projeção da sua folga no mês"
                    style={{
                      background: '#fff',
                      borderRadius: 28,
                      padding: '24px 0 10px',
                      boxShadow: '0 18px 40px -22px rgba(11,60,73,.35)',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <div style={{ padding: '0 22px' }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: '#3d3a3a' }}>Sua folga no mês</div>
                      <h3
                        style={{
                          margin: '6px 0 0',
                          font: "700 24px/30px 'Montserrat', sans-serif",
                          letterSpacing: '-0.02em',
                          color: '#1c1b1b',
                          textWrap: 'balance',
                        }}
                      >
                        Esperar até novembro melhora bastante o cenário.
                      </h3>
                      <p style={{ margin: '8px 0 0', fontSize: 14, lineHeight: '21px', color: '#3d3a3a' }}>
                        3 parcelas terminam em outubro e liberam {formatCents(installmentsTotal)}/mês.
                      </p>
                    </div>

                    <div style={{ margin: '20px 0 6px' }}>
                      <FolgaChart
                        freedMargin={freedMarginFloat}
                        recentAvgMargin={baseMarginFloat}
                        lastMonthMargin={lastMonthMargin / 100}
                        installments={installmentsList.map((c) => c / 100)}
                        reduceMotion={reduceMotion}
                      />
                    </div>

                    <div style={{ padding: '0 22px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <p style={{ margin: 0, fontSize: 14, lineHeight: '21px', color: '#2a2727' }}>
                        {freedMarginFloat - installmentAmount < 0
                          ? `Mesmo esperando, ${installmentCount}x de ${formatBrl(installmentAmount)} ainda deixariam cerca de ${formatBrl(-(freedMarginFloat - installmentAmount))} negativos por mês.`
                          : `Mesmo esperando, ${installmentCount}x de ${formatBrl(installmentAmount)} deixariam só cerca de ${formatBrl(freedMarginFloat - installmentAmount, true)} por mês de folga.`}
                      </p>
                      <button
                        onClick={() => toggleDetails(msg.id)}
                        aria-expanded={msg.showDetails}
                        style={{
                          alignSelf: 'flex-start',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          minHeight: 44,
                          padding: 0,
                          border: 0,
                          background: 'none',
                          color: '#0a3f43',
                          fontSize: 15,
                          fontWeight: 600,
                          cursor: 'pointer',
                          textDecoration: 'underline',
                          textUnderlineOffset: 3,
                        }}
                      >
                        <span>{msg.showDetails ? 'Ocultar detalhes' : 'Ver detalhes'}</span>
                        <img
                          src={`https://unpkg.com/lucide-static@0.460.0/icons/${msg.showDetails ? 'chevron-up' : 'chevron-down'}.svg`}
                          alt=""
                          width="18"
                          height="18"
                        />
                      </button>
                    </div>
                  </section>
                )}

                {/* Expanded Comparison Details */}
                {hasAnalysis && msg.showDetails && (
                  <section
                    aria-label="Detalhes: comprar agora ou esperar até novembro"
                    style={{
                      background: '#fff',
                      border: '1.5px dashed #0e5a5f',
                      borderRadius: 16,
                      padding: '4px 14px 14px',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        minHeight: 44,
                        borderBottom: '1px solid #eeecec',
                        flexWrap: 'wrap',
                      }}
                    >
                      <span
                        aria-hidden="true"
                        style={{
                          width: 16,
                          height: 16,
                          border: '2px dashed #0e5a5f',
                          borderRadius: '50%',
                          boxSizing: 'border-box',
                        }}
                      />
                      <span
                        style={{
                          flex: 1,
                          fontSize: 13,
                          fontWeight: 700,
                          color: '#0a3f43',
                          letterSpacing: '.02em',
                        }}
                      >
                        Simulação
                      </span>
                      <span style={{ fontSize: 12, color: '#0a3f43' }}>
                        {itemLabel} · {installmentCount}x de {formatBrl(installmentAmount)}
                      </span>
                    </div>

                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                        gap: 10,
                        marginTop: 12,
                      }}
                    >
                      {/* COMPRAR AGORA */}
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 10,
                          padding: 12,
                          borderRadius: 12,
                          background: '#fff',
                          border: '1px solid #e3e1e1',
                        }}
                      >
                        <div style={{ font: "700 13px/17px 'Inter'", letterSpacing: '.03em', color: '#1c1b1b' }}>
                          COMPRAR AGORA
                        </div>
                        <dl style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                          <div>
                            <dt style={{ fontSize: 12, lineHeight: '16px', color: '#4a4545' }}>Parcelas em outubro</dt>
                            <dd style={{ margin: 0, font: "600 14px/20px 'Inter'", color: '#1c1b1b' }}>
                              {formatBrl(installmentsTotal / 100 + installmentAmount)}
                            </dd>
                          </div>
                          <div>
                            <dt style={{ fontSize: 12, lineHeight: '16px', color: '#4a4545' }}>Folga em outubro</dt>
                            <dd style={{ margin: 0, font: "600 14px/20px 'Inter'", color: '#8f1114' }}>
                              {formatBrl(baseMarginFloat - installmentAmount, true)}
                            </dd>
                          </div>
                          <div>
                            <dt style={{ fontSize: 12, lineHeight: '16px', color: '#4a4545' }}>A partir de novembro</dt>
                            <dd
                              style={{
                                margin: 0,
                                font: "600 14px/20px 'Inter'",
                                color: freedMarginFloat - installmentAmount < 0 ? '#8f1114' : '#1c1b1b',
                              }}
                            >
                              {formatBrl(freedMarginFloat - installmentAmount, true)}/mês
                            </dd>
                          </div>
                        </dl>
                      </div>

                      {/* ESPERAR ATÉ NOVEMBRO */}
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 10,
                          padding: 12,
                          borderRadius: 12,
                          background: '#f3f8f8',
                          border: '1px solid #b9d3d3',
                        }}
                      >
                        <div style={{ font: "700 13px/17px 'Inter'", letterSpacing: '.03em', color: '#1c1b1b' }}>
                          ESPERAR ATÉ NOVEMBRO
                        </div>
                        <dl style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                          <div>
                            <dt style={{ fontSize: 12, lineHeight: '16px', color: '#4a4545' }}>Parcelas em outubro</dt>
                            <dd style={{ margin: 0, font: "600 14px/20px 'Inter'", color: '#1c1b1b' }}>
                              {formatCents(installmentsTotal)}
                            </dd>
                          </div>
                          <div>
                            <dt style={{ fontSize: 12, lineHeight: '16px', color: '#4a4545' }}>Folga em outubro</dt>
                            <dd style={{ margin: 0, font: "600 14px/20px 'Inter'", color: baseMarginFloat < 0 ? '#8f1114' : '#1c1b1b' }}>
                              {formatBrl(baseMarginFloat, true)}
                            </dd>
                          </div>
                          <div>
                            <dt style={{ fontSize: 12, lineHeight: '16px', color: '#4a4545' }}>A partir de novembro</dt>
                            <dd
                              style={{
                                margin: 0,
                                font: "600 14px/20px 'Inter'",
                                color: freedMarginFloat - installmentAmount < 0 ? '#8f1114' : '#1c1b1b',
                              }}
                            >
                              {formatBrl(freedMarginFloat - installmentAmount, true)}/mês
                            </dd>
                          </div>
                        </dl>
                      </div>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        gap: 10,
                        alignItems: 'flex-start',
                        marginTop: 14,
                        padding: 12,
                        borderRadius: 12,
                        background: '#fbf1e1',
                        color: '#5e3300',
                        fontSize: 14,
                        lineHeight: '20px',
                      }}
                    >
                      <img
                        src="https://unpkg.com/lucide-static@0.460.0/icons/triangle-alert.svg"
                        alt="Atenção"
                        width="20"
                        height="20"
                        style={{ flex: 'none', marginTop: 1 }}
                      />
                      <span>
                        Esperar evita somar parcelas em outubro, mas não torna a compra segura por si só. Um mês como o
                        último ({formatCents(lastMonthMargin)}) ainda exigiria cautela.
                      </span>
                    </div>
                  </section>
                )}

                {/* Follow-up Action Chips (Only after analysis and at latest turn) */}
                {hasAnalysis && idx === messages.length - 1 && !thinking && (
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button
                      onClick={() => handleSendMessage('E se…')}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      E se…
                    </button>
                    <button
                      onClick={() => handleSendMessage('Montar um plano')}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #cfcac7',
                        background: '#fff',
                        color: '#1c1b1b',
                        fontSize: 15,
                        cursor: 'pointer',
                      }}
                    >
                      Montar um plano
                    </button>
                  </div>
                )}

                {/* Interactive What-If Simulator Card (When user asks E se...) */}
                {msg.isWhatIf && (
                  <section
                    aria-label="Simulação: e se"
                    style={{
                      background: '#fff',
                      border: '1.5px dashed #0e5a5f',
                      borderRadius: 16,
                      padding: '4px 14px 14px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 14,
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        minHeight: 44,
                        borderBottom: '1px solid #eeecec',
                      }}
                    >
                      <span
                        aria-hidden="true"
                        style={{
                          width: 16,
                          height: 16,
                          border: '2px dashed #0e5a5f',
                          borderRadius: '50%',
                          boxSizing: 'border-box',
                        }}
                      />
                      <span
                        style={{
                          flex: 1,
                          fontSize: 13,
                          fontWeight: 700,
                          color: '#0a3f43',
                          letterSpacing: '.02em',
                        }}
                      >
                        Simulação · e se…
                      </span>
                    </div>

                    {/* Options */}
                    <div role="radiogroup" aria-label="Quando comprar" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <span style={{ fontSize: 13, color: '#3d3a3a' }}>Quando comprar</span>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, padding: 4, background: '#f0f1f3', borderRadius: 12 }}>
                        <button
                          role="radio"
                          aria-checked={!whatIfWait}
                          onClick={() => setWhatIfWait(false)}
                          style={{
                            minHeight: 44,
                            borderRadius: 9,
                            border: !whatIfWait ? '1.5px solid #0e5a5f' : '1.5px solid transparent',
                            background: !whatIfWait ? '#fff' : 'transparent',
                            color: '#1c1b1b',
                            fontSize: 14,
                            fontWeight: !whatIfWait ? 600 : 400,
                            cursor: 'pointer',
                          }}
                        >
                          Agora
                        </button>
                        <button
                          role="radio"
                          aria-checked={whatIfWait}
                          onClick={() => setWhatIfWait(true)}
                          style={{
                            minHeight: 44,
                            borderRadius: 9,
                            border: whatIfWait ? '1.5px solid #0e5a5f' : '1.5px solid transparent',
                            background: whatIfWait ? '#fff' : 'transparent',
                            color: '#1c1b1b',
                            fontSize: 14,
                            fontWeight: whatIfWait ? 600 : 400,
                            cursor: 'pointer',
                          }}
                        >
                          Novembro
                        </button>
                      </div>
                    </div>

                    <div role="radiogroup" aria-label="Parcelas" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <span style={{ fontSize: 13, color: '#3d3a3a' }}>Parcelas sem juros</span>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, padding: 4, background: '#f0f1f3', borderRadius: 12 }}>
                        <button
                          role="radio"
                          aria-checked={whatIfCount === 10}
                          onClick={() => setWhatIfCount(10)}
                          style={{
                            minHeight: 44,
                            borderRadius: 9,
                            border: whatIfCount === 10 ? '1.5px solid #0e5a5f' : '1.5px solid transparent',
                            background: whatIfCount === 10 ? '#fff' : 'transparent',
                            color: '#1c1b1b',
                            fontSize: 14,
                            fontWeight: whatIfCount === 10 ? 600 : 400,
                            cursor: 'pointer',
                          }}
                        >
                          10x
                        </button>
                        <button
                          role="radio"
                          aria-checked={whatIfCount === 12}
                          onClick={() => setWhatIfCount(12)}
                          style={{
                            minHeight: 44,
                            borderRadius: 9,
                            border: whatIfCount === 12 ? '1.5px solid #0e5a5f' : '1.5px solid transparent',
                            background: whatIfCount === 12 ? '#fff' : 'transparent',
                            color: '#1c1b1b',
                            fontSize: 14,
                            fontWeight: whatIfCount === 12 ? 600 : 400,
                            cursor: 'pointer',
                          }}
                        >
                          12x
                        </button>
                      </div>
                    </div>

                    <div role="radiogroup" aria-label="Cenário" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <span style={{ fontSize: 13, color: '#3d3a3a' }}>Como serão os próximos meses</span>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, padding: 4, background: '#f0f1f3', borderRadius: 12 }}>
                        <button
                          role="radio"
                          aria-checked={!whatIfStress}
                          onClick={() => setWhatIfStress(false)}
                          style={{
                            minHeight: 44,
                            borderRadius: 9,
                            border: !whatIfStress ? '1.5px solid #0e5a5f' : '1.5px solid transparent',
                            background: !whatIfStress ? '#fff' : 'transparent',
                            color: '#1c1b1b',
                            fontSize: 14,
                            fontWeight: !whatIfStress ? 600 : 400,
                            cursor: 'pointer',
                          }}
                        >
                          Como a média
                        </button>
                        <button
                          role="radio"
                          aria-checked={whatIfStress}
                          onClick={() => setWhatIfStress(true)}
                          style={{
                            minHeight: 44,
                            borderRadius: 9,
                            border: whatIfStress ? '1.5px solid #0e5a5f' : '1.5px solid transparent',
                            background: whatIfStress ? '#fff' : 'transparent',
                            color: '#1c1b1b',
                            fontSize: 14,
                            fontWeight: whatIfStress ? 600 : 400,
                            cursor: 'pointer',
                          }}
                        >
                          Como o último
                        </button>
                      </div>
                    </div>

                    {/* Result */}
                    <div>
                      <div style={{ fontSize: 13, color: '#3d3a3a' }}>Folga projetada a partir de nov/25</div>
                      <div
                        style={{
                          font: "700 24px/30px 'Inter', sans-serif",
                          color: novAfterFloat < 0 ? '#8f1114' : '#1c1b1b',
                        }}
                      >
                        {formatBrl(novAfterFloat, true)}/mês
                      </div>
                      <div style={{ fontSize: 13, lineHeight: '19px', color: '#3d3a3a' }}>
                        {whatIfWait ? 'Comprando em novembro' : 'Comprando agora'}, {whatIfCount}x de{' '}
                        {formatBrl(wfInstallment)}. Outubro: {formatBrl(wfValues[0], true)}.
                      </div>
                    </div>

                    {/* 12-Month Bar Chart */}
                    <div>
                      <div style={{ fontSize: 12, color: '#4a4545', marginBottom: 8 }}>
                        Folga por mês, próximos 12 meses
                      </div>
                      <div
                        role="img"
                        aria-label="Folga por mês nos próximos 12 meses"
                        style={{
                          position: 'relative',
                          height: chartHeightPx,
                          display: 'grid',
                          gridTemplateColumns: 'repeat(12, minmax(0, 1fr))',
                          gap: 4,
                        }}
                      >
                        <div
                          aria-hidden="true"
                          style={{
                            position: 'absolute',
                            left: 0,
                            right: 0,
                            top: `${zeroLineTop}px`,
                            borderTop: '1.5px solid #1c1b1b',
                            zIndex: 2,
                          }}
                        />
                        {wfValues.map((val, bIdx) => {
                          const posH = (Math.max(0, val) / totalH) * chartHeightPx;
                          const negH = (Math.max(0, -val) / totalH) * chartHeightPx;
                          return (
                            <div key={bIdx} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                              <div
                                style={{
                                  height: `${zeroLineTop}px`,
                                  display: 'flex',
                                  flexDirection: 'column',
                                  justifyContent: 'flex-end',
                                }}
                              >
                                <div style={{ height: `${posH}px`, background: '#0e5a5f', borderRadius: '3px 3px 0 0' }} />
                              </div>
                              <div style={{ flex: 1 }}>
                                <div
                                  style={{
                                    height: `${negH}px`,
                                    background:
                                      'repeating-linear-gradient(135deg, #8f1114 0 3px, #c9797b 3px 6px)',
                                    borderRadius: '0 0 3px 3px',
                                  }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      <div aria-hidden="true" style={{ display: 'grid', gridTemplateColumns: 'repeat(12, minmax(0, 1fr))', gap: 4, marginTop: 4 }}>
                        {months.map((m, mIdx) => (
                          <div key={mIdx} style={{ fontSize: 9, textAlign: 'center', color: '#4a4545' }}>
                            {m}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Assessment */}
                    <div
                      style={{
                        display: 'flex',
                        gap: 10,
                        alignItems: 'flex-start',
                        padding: 12,
                        borderRadius: 12,
                        background: wfAssessment.bg,
                        color: wfAssessment.fg,
                        fontSize: 14,
                        lineHeight: '20px',
                      }}
                    >
                      <img
                        src={`https://unpkg.com/lucide-static@0.460.0/icons/${wfAssessment.icon}.svg`}
                        alt=""
                        width="20"
                        height="20"
                        style={{ flex: 'none', marginTop: 1 }}
                      />
                      <span>
                        <strong>{wfAssessment.title}</strong>
                        <span style={{ display: 'block' }}>{wfAssessment.text}</span>
                      </span>
                    </div>

                    <button
                      onClick={() => handleSendMessage('Montar um plano')}
                      style={{
                        minHeight: 44,
                        padding: '0 16px',
                        borderRadius: 22,
                        border: '1px solid #0e5a5f',
                        background: '#fff',
                        color: '#0a3f43',
                        fontSize: 15,
                        fontWeight: 500,
                        cursor: 'pointer',
                        alignSelf: 'flex-start',
                      }}
                    >
                      Montar um plano
                    </button>
                  </section>
                )}

                {/* Milestones Plan Card (When user asks Montar um plano) */}
                {msg.isPlan && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <section
                      aria-label="Plano de etapas"
                      style={{
                        background: '#fff',
                        border: '1px solid #e3e1e1',
                        borderRadius: 16,
                        padding: 16,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 14,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                        <div style={{ font: "700 16px/22px 'Inter', sans-serif", color: '#1c1b1b' }}>
                          Esperar até novembro
                        </div>
                        <div style={{ fontSize: 13, color: '#3d3a3a' }}>Etapa 1 de 3</div>
                      </div>

                      <div
                        role="img"
                        aria-label="Etapa 1 de 3 em andamento"
                        style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4 }}
                      >
                        <div style={{ height: 6, borderRadius: 3, background: '#0e5a5f' }} />
                        <div
                          style={{
                            height: 6,
                            borderRadius: 3,
                            background: 'repeating-linear-gradient(90deg, #0e5a5f 0 4px, transparent 4px 8px)',
                            opacity: 0.6,
                          }}
                        />
                        <div
                          style={{
                            height: 6,
                            borderRadius: 3,
                            background: 'repeating-linear-gradient(90deg, #0e5a5f 0 4px, transparent 4px 8px)',
                            opacity: 0.6,
                          }}
                        />
                      </div>

                      <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column' }}>
                        <li style={{ display: 'flex', gap: 12 }}>
                          <div aria-hidden="true" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 14 }}>
                            <span style={{ width: 12, height: 12, marginTop: 4, borderRadius: '50%', background: '#1c1b1b' }} />
                            <span style={{ flex: 1, width: 0, borderLeft: '2px solid #1c1b1b', minHeight: 16 }} />
                          </div>
                          <div style={{ paddingBottom: 14, flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#1c1b1b', fontWeight: 600 }}>
                              <span>Hoje</span>
                              <span>set/25</span>
                            </div>
                            <div style={{ fontSize: 12, color: '#4a4545', marginTop: 2 }}>
                              Observado · 3 parcelas ativas, {formatCents(installmentsTotal)}/mês
                            </div>
                          </div>
                        </li>

                        <li style={{ display: 'flex', gap: 12 }}>
                          <div aria-hidden="true" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 14 }}>
                            <span style={{ width: 12, height: 12, marginTop: 4, borderRadius: '50%', background: '#1c1b1b' }} />
                            <span style={{ flex: 1, width: 0, borderLeft: '2px dashed #0e5a5f', minHeight: 16 }} />
                          </div>
                          <div style={{ paddingBottom: 14, flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#1c1b1b', fontWeight: 600 }}>
                              <span>Últimas parcelas atuais</span>
                              <span>out/25</span>
                            </div>
                            <div style={{ fontSize: 12, color: '#4a4545', marginTop: 2 }}>
                              Observado · previsão de término
                            </div>
                          </div>
                        </li>

                        <li style={{ display: 'flex', gap: 12 }}>
                          <div aria-hidden="true" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 14 }}>
                            <span style={{ width: 12, height: 12, marginTop: 4, borderRadius: '50%', border: '2px dashed #0e5a5f', background: '#fff' }} />
                            <span style={{ flex: 1, width: 0, borderLeft: '2px dashed #0e5a5f', minHeight: 16 }} />
                          </div>
                          <div style={{ paddingBottom: 14, flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#1c1b1b', fontWeight: 600 }}>
                              <span>Folga projetada sobe</span>
                              <span>nov/25</span>
                            </div>
                            <div style={{ fontSize: 12, color: '#4a4545', marginTop: 2 }}>
                              Simulação · para {formatBrl(freedMarginFloat, true)}/mês
                            </div>
                          </div>
                        </li>

                        <li style={{ display: 'flex', gap: 12 }}>
                          <div aria-hidden="true" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 14 }}>
                            <span style={{ width: 12, height: 12, marginTop: 4, borderRadius: '50%', border: '2px dashed #0e5a5f', background: '#fff' }} />
                            <span style={{ flex: 1, width: 0, borderLeft: 0, minHeight: 16 }} />
                          </div>
                          <div style={{ paddingBottom: 14, flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#1c1b1b', fontWeight: 600 }}>
                              <span>1ª parcela</span>
                              <span>nov/25</span>
                            </div>
                            <div style={{ fontSize: 12, color: '#4a4545', marginTop: 2 }}>
                              Simulação · {formatBrl(wfInstallment)}/mês
                            </div>
                          </div>
                        </li>
                      </ol>
                    </section>

                    {/* Supervisor Promotion */}
                    <section
                      aria-label="Pingo Supervisor"
                      style={{
                        background: '#fff',
                        border: '1px solid #e3e1e1',
                        borderRadius: 16,
                        padding: 16,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 12,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <img
                          src="https://unpkg.com/lucide-static@0.460.0/icons/shield-check.svg"
                          alt=""
                          width="20"
                          height="20"
                        />
                        <span style={{ flex: 1, fontSize: 15, fontWeight: 700, color: '#1c1b1b' }}>Pingo Supervisor</span>
                        <span style={{ fontSize: 12, fontWeight: 600, color: '#3d3a3a', border: '1px solid #cfcac7', borderRadius: 6, padding: '3px 6px' }}>
                          Opcional
                        </span>
                      </div>
                      <div style={{ fontSize: 14, lineHeight: '21px', color: '#3d3a3a' }}>
                        Aviso quando suas parcelas terminarem e se um mês começar parecido com o último. Só com a sua permissão.
                      </div>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button
                          onClick={onOpenSupervisor}
                          style={{
                            minHeight: 44,
                            padding: '0 16px',
                            borderRadius: 22,
                            border: 0,
                            background: '#0e5a5f',
                            color: '#fff',
                            fontSize: 14,
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Conhecer o Supervisor
                        </button>
                        <button
                          onClick={() => {
                            const savedMsg: ChatMessage = {
                              id: `saved-${Date.now()}`,
                              sender: 'pingo',
                              text: 'Combinado. Salvei o plano sem acompanhamento. Se mudar de ideia, o Supervisor fica no topo da conversa.',
                              timestamp: getNowTime(),
                              isSaved: true,
                            };
                            setMessages((p) => [...p, savedMsg]);
                          }}
                          style={{
                            minHeight: 44,
                            padding: '0 16px',
                            borderRadius: 22,
                            border: '1px solid #cfcac7',
                            background: '#fff',
                            color: '#1c1b1b',
                            fontSize: 14,
                            cursor: 'pointer',
                          }}
                        >
                          Salvar sem acompanhar
                        </button>
                      </div>
                    </section>
                  </div>
                )}

                {/* Plan Saved Card */}
                {msg.isSaved && (
                  <section
                    aria-label="Plano salvo"
                    style={{
                      background: '#fff',
                      border: '1px solid #e3e1e1',
                      borderRadius: 16,
                      padding: 16,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 12,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span
                        aria-hidden="true"
                        style={{
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          background: '#1a7f4b',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <img
                          src="https://unpkg.com/lucide-static@0.460.0/icons/check.svg"
                          alt=""
                          width="16"
                          height="16"
                          style={{ filter: 'invert(1)' }}
                        />
                      </span>
                      <div style={{ font: "700 16px/22px 'Inter', sans-serif" }}>Plano salvo</div>
                    </div>

                    <dl style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: 10, fontSize: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                        <dt style={{ color: '#4a4545' }}>Compra</dt>
                        <dd style={{ margin: 0, fontWeight: 600, textAlign: 'right' }}>
                          {itemLabel}
                        </dd>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                        <dt style={{ color: '#4a4545' }}>Folga projetada</dt>
                        <dd style={{ margin: 0, fontWeight: 600, textAlign: 'right' }}>
                          {formatBrl(novAfterFloat, true)}/mês
                        </dd>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                        <dt style={{ color: '#4a4545' }}>Supervisor</dt>
                        <dd style={{ margin: 0, fontWeight: 600, textAlign: 'right' }}>
                          {supervisorActive ? 'Ativo' : 'Desligado'}
                        </dd>
                      </div>
                    </dl>

                    <div style={{ fontSize: 12, lineHeight: '17px', color: '#4a4545' }}>
                      Nenhuma compra foi feita. Simulações não são recomendação financeira.
                    </div>

                    <button
                      onClick={onGoHome}
                      style={{
                        minHeight: 48,
                        borderRadius: 24,
                        border: 0,
                        background: '#0e5a5f',
                        color: '#fff',
                        fontSize: 15,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Voltar ao início
                    </button>
                  </section>
                )}
              </div>
            );
          })}

          {/* Pulsing Thinking indicator */}
          {thinking && (
            <div
              role="status"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                fontSize: 14,
                color: '#3d3a3a',
              }}
            >
              <span aria-hidden="true" style={{ display: 'flex', gap: 4 }}>
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      background: '#0e5a5f',
                      animation: reduceMotion ? 'none' : `pgPulse 1.2s ${i * 0.2}s ease-in-out infinite`,
                    }}
                  />
                ))}
              </span>
              <span>Analisando seus dados</span>
            </div>
          )}
        </div>
      </div>

      {/* Input Bar (Always active and visible) */}
      <div style={{ flex: 'none', padding: '6px 22px 28px', display: 'flex', gap: 8, alignItems: 'center' }}>
        <label
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            minHeight: 52,
            borderRadius: 26,
            background: '#fff',
            padding: '0 6px 0 20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
        >
          <span style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>
            Mensagem para o Pingo
          </span>
          <input
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Digite aqui (ex: Posso comprar...)"
            style={{
              flex: 1,
              minWidth: 0,
              border: 0,
              background: 'transparent',
              font: "400 16px 'Inter', sans-serif",
              color: '#1c1b1b',
              outline: 'none',
              height: 48,
            }}
          />
          <button
            aria-label="Falar com o Pingo"
            style={{
              width: 44,
              height: 44,
              border: 0,
              background: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <img
              src="https://unpkg.com/lucide-static@0.460.0/icons/mic.svg"
              alt=""
              width="22"
              height="22"
            />
          </button>
        </label>

        {inputText.trim().length > 0 && (
          <button
            onClick={() => handleSendMessage(inputText)}
            aria-label="Enviar mensagem"
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              border: 0,
              background: '#0e5a5f',
              cursor: 'pointer',
              flex: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <img
              src="https://unpkg.com/lucide-static@0.460.0/icons/arrow-up.svg"
              alt=""
              width="22"
              height="22"
              style={{ filter: 'invert(1)' }}
            />
          </button>
        )}
      </div>
    </div>
  );
};
