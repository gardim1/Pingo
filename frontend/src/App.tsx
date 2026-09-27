import React, { useState, useEffect } from 'react';
import { HomeScreen } from './components/HomeScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { ConsentScreen } from './components/ConsentScreen';
import { ChatScreen } from './components/ChatScreen';
import { SupervisorSheet } from './components/SupervisorSheet';
import { FlowMap } from './components/FlowMap';
import { saveSupervisorOptIn } from './api/client';

const DESIGN_NOTES: Record<string, { title: string; items: string[] }> = {
  home: {
    title: 'Home do banco',
    items: [
      'Estrutura, espaçamentos e navegação seguem a home de referência: cabeçalho, atalhos em carrossel, cartões de conta e fatura.',
      'Pingo é um atalho flutuante discreto acima da barra, sem cobrir conteúdo.',
      'Marca do banco substituída por elementos neutros.',
    ],
  },
  loading: {
    title: 'Carregamento',
    items: [
      'Mesma composição da referência: fechar no topo, muito branco, indicador baixo e centralizado.',
      'Com movimento reduzido o anel fica parado; o texto carrega a mensagem.',
    ],
  },
  consent: {
    title: 'Consentimento',
    items: [
      'Só na primeira vez. O necessário é fixo; o opcional tem switch.',
      'O que o Pingo nunca faz vem antes do botão de aceitar.',
    ],
  },
  greet: {
    title: 'Pergunta',
    items: [
      'Layout de chat da referência: texto do assistente sem balão, balão cinza do usuário com avatar e horário.',
    ],
  },
  terms: {
    title: 'Forma de pagamento',
    items: [
      'O Pingo não responde sem saber a forma de pagamento. A resposta muda muito entre à vista e parcelado.',
    ],
  },
  facts: {
    title: 'O que observei',
    items: [
      'Só dados reais da persona: renda CLT, margem média, último mês e as 3 parcelas.',
      'Lista no estilo de extrato, não um widget.',
    ],
  },
  compare: {
    title: 'Projeção da folga',
    items: [
      'Primeira camada: uma conclusão, uma mudança-chave e uma linha do tempo simples.',
      'Linha contínua é observado; pontilhado e tracejado são simulação, com rótulo escrito.',
      'O fim das parcelas não é apresentado como "cabe". "Ver detalhes" abre a comparação agora x novembro.',
    ],
  },
  whatif: {
    title: 'E se…',
    items: [
      'Três perguntas "e se": momento, prazo e um mês como o último.',
      'Negativo aparece abaixo da linha, listrado e com sinal de menos.',
      'Gráfico com descrição completa para leitor de tela.',
    ],
  },
  plan: {
    title: 'Plano',
    items: [
      'Observado em traço sólido; simulação em tracejado.',
      'Supervisor só é oferecido depois do valor entregue.',
    ],
  },
  sheet: {
    title: 'Supervisor',
    items: [
      'Opt-in explícito, com o que faz e o que nunca faz.',
      'Recusar é tão fácil quanto aceitar.',
    ],
  },
  saved: {
    title: 'Plano salvo',
    items: [
      'Resumo deixa claro que nada foi comprado.',
      'Status do Supervisor fica no topo da conversa.',
    ],
  },
  nudge: {
    title: 'Aviso proativo',
    items: [
      'Aviso proativo sai do atalho flutuante, no momento certo: quando as parcelas terminam.',
      'Sempre dispensável.',
    ],
  },
};

export const App: React.FC = () => {
  // Check route: /demo-map or /dev/flow renders the presentation board
  const isDemoMapRoute =
    typeof window !== 'undefined' &&
    (window.location.pathname.startsWith('/demo-map') || window.location.pathname.startsWith('/dev/flow'));

  const [screen, setScreen] = useState<'home' | 'loading' | 'consent' | 'chat'>('home');
  const [consented, setConsented] = useState<boolean>(false);
  const [supervisorActive, setSupervisorActive] = useState<boolean>(false);
  const [supervisorSheetOpen, setSupervisorSheetOpen] = useState<boolean>(false);
  const [nudgeDismissed, setNudgeDismissed] = useState<boolean>(false);

  // Presentation mode helpers
  const [demoStepKey, setDemoStepKey] = useState<string>('home');
  const [textScale, setTextScale] = useState<'100%' | '115%' | '130%'>('100%');
  const [reduceMotion, setReduceMotion] = useState<boolean>(false);

  const zoomFactor = textScale === '130%' ? 1.3 : textScale === '115%' ? 1.15 : 1;
  const currentNote = DESIGN_NOTES[demoStepKey] || DESIGN_NOTES['home'];

  const handleOpenPingo = () => {
    setScreen('loading');
    setSupervisorSheetOpen(false);
    setTimeout(() => {
      setScreen(consented ? 'chat' : 'consent');
    }, 1000);
  };

  const handleAgreeConsent = (_allowIncome: boolean) => {
    setConsented(true);
    setScreen('chat');
  };

  const handleGoHome = () => {
    setScreen('home');
    setSupervisorSheetOpen(false);
  };

  const handleActivateSupervisor = (config: { alerts: boolean; remind: boolean }) => {
    setSupervisorActive(true);
    setSupervisorSheetOpen(false);
    setNudgeDismissed(false);
    saveSupervisorOptIn(true, config).catch((e: unknown) => console.warn('Supervisor opt-in failed:', e));
  };

  const handleDeactivateSupervisor = () => {
    setSupervisorActive(false);
    setSupervisorSheetOpen(false);
    saveSupervisorOptIn(false).catch((e: unknown) => console.warn('Supervisor deactivate failed:', e));
  };

  // Demo Map jumper
  const handleSelectDemoStep = (key: string) => {
    setDemoStepKey(key);
    setSupervisorSheetOpen(false);

    switch (key) {
      case 'home':
        setScreen('home');
        setSupervisorActive(false);
        setConsented(false);
        break;
      case 'loading':
        setConsented(false);
        handleOpenPingo();
        break;
      case 'consent':
        setScreen('consent');
        setConsented(false);
        break;
      case 'greet':
      case 'terms':
      case 'facts':
      case 'compare':
      case 'whatif':
      case 'plan':
        setConsented(true);
        setScreen('chat');
        break;
      case 'sheet':
        setConsented(true);
        setScreen('chat');
        setSupervisorSheetOpen(true);
        break;
      case 'saved':
        setConsented(true);
        setScreen('chat');
        setSupervisorActive(true);
        break;
      case 'nudge':
        setScreen('home');
        setSupervisorActive(true);
        setNudgeDismissed(false);
        break;
      default:
        break;
    }
  };

  // -------------------------------------------------------------
  // 1. PRIMARY ROUTE `/`: PURE BANKING PRODUCT EXPERIENCE
  // -------------------------------------------------------------
  if (!isDemoMapRoute) {
    return (
      <main
        style={{
          minHeight: '100vh',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          background: '#eceae6',
          padding: 0,
          margin: 0,
        }}
      >
        <div className="device-frame">
          <div className="device-screen">
            {screen === 'home' && (
              <HomeScreen
                onOpenPingo={handleOpenPingo}
                onOpenSupervisorSheet={() => setSupervisorSheetOpen(true)}
                supervisorActive={supervisorActive}
                showNudge={supervisorActive && !nudgeDismissed}
                onDismissNudge={() => setNudgeDismissed(true)}
              />
            )}

            {screen === 'loading' && (
              <LoadingScreen onClose={handleGoHome} reduceMotion={reduceMotion} />
            )}

            {screen === 'consent' && (
              <ConsentScreen onAgree={handleAgreeConsent} onCancel={handleGoHome} />
            )}

            {screen === 'chat' && (
              <ChatScreen
                supervisorActive={supervisorActive}
                onOpenSupervisor={() => setSupervisorSheetOpen(true)}
                onGoHome={handleGoHome}
                reduceMotion={reduceMotion}
              />
            )}

            <SupervisorSheet
              isOpen={supervisorSheetOpen}
              isActive={supervisorActive}
              onClose={() => setSupervisorSheetOpen(false)}
              onActivate={handleActivateSupervisor}
              onDeactivate={handleDeactivateSupervisor}
              lastMonthMarginFormatted="−R$ 576,85"
              installmentsEndMonth="outubro"
              installmentsCount={3}
            />
          </div>
        </div>
      </main>
    );
  }

  // -------------------------------------------------------------
  // 2. SECONDARY ROUTE `/demo-map` OR `/dev/flow`: PRESENTATION BOARD
  // -------------------------------------------------------------
  return (
    <div
      style={{
        maxWidth: 1180,
        margin: '0 auto',
        padding: '36px 24px 60px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: 28,
      }}
    >
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
        <svg width="40" height="40" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M10 3c.6 4.4 2.6 6.4 7 7-4.4.6-6.4 2.6-7 7-.6-4.4-2.6-6.4-7-7 4.4-.6 6.4-2.6 7-7z"
            fill="#0e5a5f"
          />
          <path
            d="M18.5 2c.3 1.7 1 2.4 2.5 2.7-1.5.3-2.2 1-2.5 2.6-.3-1.6-1-2.3-2.6-2.6 1.6-.3 2.3-1 2.6-2.7z"
            fill="#0e5a5f"
          />
        </svg>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ font: "700 26px/1 'Montserrat', sans-serif", letterSpacing: '-0.02em' }}>
            pingo · mapa de apresentação
          </div>
          <div style={{ fontSize: 13, color: '#4a4545', marginTop: 5 }}>
            Fluxo navegável de demonstração e notas de design · <a href="/">Ir para o produto direto</a>
          </div>
        </div>

        {/* Accessibility Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <label style={{ fontSize: 13, color: '#4a4545', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>Texto:</span>
            <select
              value={textScale}
              onChange={(e) => setTextScale(e.target.value as any)}
              style={{
                borderRadius: 6,
                border: '1px solid #cfcac7',
                padding: '4px 8px',
                fontSize: 13,
                background: '#fff',
              }}
            >
              <option value="100%">100%</option>
              <option value="115%">115%</option>
              <option value="130%">130%</option>
            </select>
          </label>
          <label style={{ fontSize: 13, color: '#4a4545', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={reduceMotion}
              onChange={(e) => setReduceMotion(e.target.checked)}
            />
            <span>Movimento reduzido</span>
          </label>
        </div>
      </header>

      {/* Flow Map Navigation */}
      <FlowMap currentKey={demoStepKey} onSelectStep={handleSelectDemoStep} />

      {/* Frame & Aside Presentation */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 40,
          alignItems: 'flex-start',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: 390,
            height: 844,
            borderRadius: 54,
            background: '#111',
            padding: 10,
            boxSizing: 'border-box',
            boxShadow: '0 30px 60px -20px rgba(28,27,27,.35)',
            flex: 'none',
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              height: '100%',
              borderRadius: 44,
              overflow: 'hidden',
              background: '#fff',
            }}
          >
            {screen === 'home' && (
              <HomeScreen
                onOpenPingo={handleOpenPingo}
                onOpenSupervisorSheet={() => setSupervisorSheetOpen(true)}
                supervisorActive={supervisorActive}
                showNudge={supervisorActive && !nudgeDismissed}
                onDismissNudge={() => setNudgeDismissed(true)}
                zoom={zoomFactor}
              />
            )}

            {screen === 'loading' && (
              <LoadingScreen onClose={handleGoHome} reduceMotion={reduceMotion} />
            )}

            {screen === 'consent' && (
              <ConsentScreen onAgree={handleAgreeConsent} onCancel={handleGoHome} zoom={zoomFactor} />
            )}

            {screen === 'chat' && (
              <ChatScreen
                supervisorActive={supervisorActive}
                onOpenSupervisor={() => setSupervisorSheetOpen(true)}
                onGoHome={handleGoHome}
                zoom={zoomFactor}
                reduceMotion={reduceMotion}
              />
            )}

            <SupervisorSheet
              isOpen={supervisorSheetOpen}
              isActive={supervisorActive}
              onClose={() => setSupervisorSheetOpen(false)}
              onActivate={handleActivateSupervisor}
              onDeactivate={handleDeactivateSupervisor}
              zoom={zoomFactor}
              lastMonthMarginFormatted="−R$ 576,85"
              installmentsEndMonth="outubro"
              installmentsCount={3}
            />
          </div>
        </div>

        {/* Aside Notes */}
        <aside
          aria-label="Notas de design"
          style={{
            width: 320,
            maxWidth: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 14,
              padding: 18,
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            <div
              style={{
                font: "600 11px/1 ui-monospace, Menlo, monospace",
                color: '#4a4545',
                letterSpacing: '.06em',
              }}
            >
              NESTA TELA
            </div>
            <div style={{ font: "600 17px/23px 'Montserrat', sans-serif" }}>{currentNote.title}</div>
            <ul
              style={{
                margin: 0,
                paddingLeft: 18,
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                fontSize: 13,
                lineHeight: '19px',
                color: '#3d3939',
              }}
            >
              {currentNote.items.map((item, i) => (
                <li key={i} style={{ textWrap: 'pretty' }}>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div
            style={{
              background: '#fff',
              borderRadius: 14,
              padding: 18,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div
              style={{
                font: "600 11px/1 ui-monospace, Menlo, monospace",
                color: '#4a4545',
                letterSpacing: '.06em',
              }}
            >
              OBSERVADO OU SIMULAÇÃO
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 13, lineHeight: '19px' }}>
              <span
                style={{
                  flex: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  border: '1px solid #e3e1e1',
                  borderRadius: 8,
                  padding: '4px 8px',
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                <img
                  src="https://unpkg.com/lucide-static@0.460.0/icons/circle-check.svg"
                  alt=""
                  width="14"
                  height="14"
                />
                Observado
              </span>
              <span>Borda sólida, ícone de check. Dado real da conta.</span>
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 13, lineHeight: '19px' }}>
              <span
                style={{
                  flex: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  border: '1.5px dashed #0e5a5f',
                  borderRadius: 8,
                  padding: '3px 8px',
                  fontSize: 12,
                  fontWeight: 700,
                  color: '#0a3f43',
                }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    width: 12,
                    height: 12,
                    border: '2px dashed #0e5a5f',
                    borderRadius: '50%',
                    boxSizing: 'border-box',
                  }}
                />
                Simulação
              </span>
              <span>Borda tracejada e rótulo escrito. Projeção, pode mudar.</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};
