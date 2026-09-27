import React, { useState } from 'react';

interface HomeScreenProps {
  onOpenPingo: () => void;
  supervisorActive: boolean;
  onOpenSupervisorSheet: () => void;
  showNudge?: boolean;
  onDismissNudge?: () => void;
  zoom?: number;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  onOpenPingo,
  supervisorActive,
  onOpenSupervisorSheet,
  showNudge: controlledShowNudge,
  onDismissNudge,
  zoom = 1,
}) => {
  const [hideBalances, setHideBalances] = useState(false);
  const [internalNudge, setInternalNudge] = useState(supervisorActive);
  const showNudge = controlledShowNudge !== undefined ? controlledShowNudge : internalNudge;
  const dismissNudge = onDismissNudge || (() => setInternalNudge(false));

  return (
    <div data-screen-label="Início" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', background: '#f0f1f3' }}>
      {/* Top Banking Header */}
      <div style={{ background: '#0b3c49', color: '#fff', flex: 'none' }}>
        {/* Status Bar */}
        <div style={{ height: 50, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 30px', font: '600 15px "Inter", sans-serif', position: 'relative' }}>
          <span>10:02</span>
          <div style={{ position: 'absolute', left: '50%', top: 10, width: 110, height: 32, marginLeft: -55, background: '#000', borderRadius: 20 }}></div>
          <div style={{ width: 26, height: 12, border: '1.5px solid #fff', borderRadius: 4, padding: 1.5, boxSizing: 'border-box' }}>
            <div style={{ width: '70%', height: '100%', background: '#fff', borderRadius: 1 }}></div>
          </div>
        </div>

        {/* User bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px 18px 22px' }}>
          <div aria-hidden="true" style={{ width: 30, height: 30, borderRadius: '50%', background: '#fff', color: '#1c1b1b', display: 'flex', alignItems: 'center', justifyContent: 'center', font: '500 13px "Inter"' }}>
            VG
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, height: 30, padding: '0 12px 0 8px', borderRadius: 15, background: 'rgba(255,255,255,0.16)', fontSize: 13, fontWeight: 600 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>
            Nível 4
          </div>
          <div style={{ flex: 1 }}></div>
          <button aria-label="Buscar" style={{ width: 44, height: 44, border: 0, background: 'none', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </button>
          <button aria-label="Notificações, 1 nova" style={{ position: 'relative', width: 44, height: 44, border: 0, background: 'none', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
            <span aria-hidden="true" style={{ position: 'absolute', top: 9, right: 10, width: 8, height: 8, borderRadius: '50%', background: '#e2483d', border: '1.5px solid #0b3c49' }}></span>
          </button>
          <button aria-label="Mensagens" style={{ width: 44, height: 44, border: 0, background: 'none', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflowY: 'auto' }} data-noscrollbar="1">
        <div style={{ padding: '24px 0 130px', display: 'flex', flexDirection: 'column', gap: 22 }}>
          {/* Section: Minha conta */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px 0 22px' }}>
            <h1 style={{ margin: 0, font: '700 17px/22px "Inter", sans-serif' }}>Minha conta</h1>
            <button
              onClick={() => setHideBalances(!hideBalances)}
              aria-label={hideBalances ? 'Mostrar valores' : 'Ocultar valores'}
              style={{ width: 44, height: 44, border: 0, background: 'none', color: '#4a4545', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
            >
              {hideBalances ? (
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
              ) : (
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
              )}
            </button>
          </div>

          {/* Quick Action Shortcuts */}
          <div
            role="list"
            aria-label="Atalhos rápidos"
            data-noscrollbar="1"
            style={{
              display: 'flex',
              gap: 18,
              overflowX: 'auto',
              padding: '0 22px',
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
              WebkitOverflowScrolling: 'touch',
            }}
          >
            {[
              { label: 'Pix e transferir', icon: 'M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5' },
              { label: 'Pagar', icon: 'M3 5v14M8 5v14M12 5v14M17 5v14M21 5v14' },
              { label: 'Cartão virtual', icon: 'M2 5h20v14H2zM2 10h20' },
              { label: 'Caixinhas', icon: 'M19 5c-1.5 0-2.8 1.4-3 2-3.5-1.5-11-.3-11 5 0 1.8 0 3 2 4.5V20h4v-2h3v2h4v-4c1-.5 1.5-1 2-2.5 1-3 0-8.5-1-8.5z' },
              { label: 'Recarga', icon: 'M5 2h14v20H5zM12 18h.01' },
              { label: 'Investir', icon: 'M22 7l-8.5 8.5-5-5L2 17' },
            ].map((q, idx) => (
              <button
                key={idx}
                role="listitem"
                style={{ flex: 'none', width: 62, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 9, border: 0, background: 'none', cursor: 'pointer', color: '#3d3a3a', fontSize: 13, lineHeight: '17px', textAlign: 'center', padding: 0 }}
              >
                <span aria-hidden="true" style={{ width: 60, height: 60, borderRadius: 16, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 6px rgba(0,0,0,0.04)' }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0e5a5f" strokeWidth="2"><path d={q.icon}/></svg>
                </span>
                {q.label}
              </button>
            ))}
          </div>

          {/* Cards: Conta Corrente & Cartão */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20, padding: '0 22px' }}>
            {/* Conta Corrente */}
            <div style={{ background: '#fff', borderRadius: 16, padding: '22px 22px 8px', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, minHeight: 44, color: '#3d3a3a', fontSize: 15 }}>
                <span aria-hidden="true" style={{ width: 22, height: 22, borderRadius: 5, background: '#0b3c49', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/></svg>
                </span>
                <span style={{ flex: 1, fontWeight: 500 }}>Conta corrente</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9a9493" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
              </div>
              <div style={{ marginTop: 22 }}>
                <div style={{ fontSize: 14, color: '#4a4545' }}>Saldo</div>
                <div style={{ font: '700 19px/26px "Inter", sans-serif', color: '#2a2727', marginTop: 2 }}>
                  {hideBalances ? 'R$ ••••' : 'R$ 4,49'}
                </div>
              </div>
              <div style={{ height: 1, background: '#dedcdc', margin: '20px 0 4px' }}></div>
              <div style={{ display: 'flex', alignItems: 'center', minHeight: 52, color: '#3d3a3a', fontSize: 15 }}>
                <span style={{ flex: 1 }}>Limite disponível para habilitar</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9a9493" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </div>

            {/* Cartão Platinum */}
            <div style={{ background: '#fff', borderRadius: 16, padding: 22, boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, minHeight: 44, color: '#3d3a3a', fontSize: 15 }}>
                <span aria-hidden="true" style={{ width: 24, height: 16, borderRadius: 4, background: '#e7e5e4', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ width: 12, height: 7, borderRadius: 2, background: '#9a9493' }}></span>
                </span>
                <span style={{ flex: 1, fontWeight: 500 }}>Cartão Platinum final 8511</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9a9493" strokeWidth="2"><path d="m9 18 6-6-6-6"/></svg>
              </div>
              <div style={{ marginTop: 22 }}>
                <div style={{ fontSize: 14, color: '#4a4545' }}>Fatura aberta</div>
                <div style={{ font: '700 19px/26px "Inter", sans-serif', color: '#2a2727', marginTop: 2 }}>
                  {hideBalances ? 'R$ ••••' : 'R$ 962,18'}
                </div>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#3d3a3a', marginTop: 12 }}>
                Melhor data de compras: 03 out
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Floating Pingo Action Area */}
      <div style={{ position: 'absolute', right: 16, bottom: 96, left: 16, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10, pointerEvents: 'none', zIndex: 10 }}>
        {/* Proactive Supervisor Nudge */}
        {showNudge && (
          <section
            aria-label="Aviso do Pingo Supervisor"
            style={{ pointerEvents: 'auto', width: '100%', boxSizing: 'border-box', background: '#fff', borderRadius: 16, padding: 16, boxShadow: '0 12px 32px -8px rgba(28,27,27,0.28)', display: 'flex', flexDirection: 'column', gap: 10 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0e5a5f" strokeWidth="2">
                <path d="M10 3c.6 4.4 2.6 6.4 7 7-4.4.6-6.4 2.6-7 7-.6-4.4-2.6-6.4-7-7 4.4-.6 6.4-2.6 7-7z" fill="#0e5a5f"/>
              </svg>
              <span style={{ flex: 1, fontSize: 12, fontWeight: 600, color: '#0a3f43' }}>Pingo Supervisor · agora</span>
              <button
                onClick={dismissNudge}
                aria-label="Dispensar aviso"
                style={{ width: 40, height: 40, margin: '-10px -10px -10px 0', border: 0, background: 'none', color: '#4a4545', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
              </button>
            </div>
            <div style={{ fontSize: 15, lineHeight: '22px', color: '#2a2727' }}>
              Suas 3 parcelas de R$ 690,78 terminam este mês. Quer rever a simulação do iPhone para novembro?
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button
                onClick={onOpenPingo}
                style={{ minHeight: 44, padding: '0 16px', borderRadius: 22, border: 0, background: '#0e5a5f', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}
              >
                Rever simulação
              </button>
              <button
                onClick={onOpenSupervisorSheet}
                style={{ minHeight: 44, padding: '0 16px', borderRadius: 22, border: '1px solid #cfcac7', background: '#fff', color: '#1c1b1b', fontSize: 14, cursor: 'pointer' }}
              >
                Ajustar avisos
              </button>
            </div>
          </section>
        )}

        {/* Pingo Floating Action Button */}
        <button
          onClick={onOpenPingo}
          aria-label={supervisorActive ? 'Abrir Pingo, assistente financeiro. Supervisor ativo' : 'Abrir Pingo, assistente financeiro'}
          style={{
            pointerEvents: 'auto',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            height: 48,
            padding: '0 18px 0 14px',
            borderRadius: 24,
            border: '1px solid #e3e0de',
            background: '#fff',
            color: '#1c1b1b',
            font: '600 15px "Inter", sans-serif',
            cursor: 'pointer',
            boxShadow: '0 8px 20px -6px rgba(11,60,73,0.35)',
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24">
            <path d="M10 3c.6 4.4 2.6 6.4 7 7-4.4.6-6.4 2.6-7 7-.6-4.4-2.6-6.4-7-7 4.4-.6 6.4-2.6 7-7z" fill="#0e5a5f"/>
            <path d="M18.5 2c.3 1.7 1 2.4 2.5 2.7-1.5.3-2.2 1-2.5 2.6-.3-1.6-1-2.3-2.6-2.6 1.6-.3 2.3-1 2.6-2.7z" fill="#0e5a5f"/>
          </svg>
          Pingo
          {supervisorActive && (
            <span
              aria-hidden="true"
              style={{ position: 'absolute', top: -2, right: -2, width: 12, height: 12, borderRadius: '50%', background: '#0e5a5f', border: '2px solid #fff' }}
            ></span>
          )}
        </button>
      </div>

      {/* Bottom Navigation */}
      <nav aria-label="Navegação principal" style={{ flex: 'none', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', background: '#fff', borderTop: '1px solid #e3e1e1', padding: '8px 6px 20px' }}>
        <button aria-current="page" aria-label="Início, página atual" style={{ minHeight: 52, border: 0, background: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
          <span style={{ width: 44, height: 44, borderRadius: 10, background: '#0b3c49', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </span>
        </button>
        <button style={{ minHeight: 52, border: 0, background: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4, fontSize: 11, color: '#3d3a3a', cursor: 'pointer' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>
          Extrato
        </button>
        <button style={{ minHeight: 52, border: 0, background: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4, fontSize: 11, color: '#3d3a3a', cursor: 'pointer' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/></svg>
          Pagamentos
        </button>
        <button style={{ minHeight: 52, border: 0, background: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4, fontSize: 11, color: '#3d3a3a', cursor: 'pointer' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 12 20 22 4 22 4 12"/><rect width="20" height="5" x="2" y="7"/><line x1="12" x2="12" y1="22" y2="7"/></svg>
          Pra você
        </button>
        <button style={{ minHeight: 52, border: 0, background: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4, fontSize: 11, color: '#3d3a3a', cursor: 'pointer' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
          Menu
        </button>
      </nav>
    </div>
  );
};
