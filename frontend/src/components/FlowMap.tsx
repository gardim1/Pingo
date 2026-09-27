import React from 'react';

export interface FlowStepDef {
  key: string;
  label: string;
  desc: string;
  tag?: string;
}

export const FLOW_STEPS: FlowStepDef[] = [
  { key: 'home', label: 'Home do banco', desc: 'Pingo como atalho flutuante' },
  { key: 'loading', label: 'Carregamento', desc: 'Conexão protegida' },
  { key: 'consent', label: 'Consentimento', desc: 'Só na primeira vez', tag: '1ª VEZ' },
  { key: 'greet', label: 'Pergunta', desc: 'Posso comprar um iPhone?' },
  { key: 'terms', label: 'Forma de pagamento', desc: 'Pingo pergunta antes' },
  { key: 'facts', label: 'O que observei', desc: 'Renda, margem, parcelas', tag: 'OBS.' },
  { key: 'compare', label: 'Projeção da folga', desc: 'Conclusão + detalhes', tag: 'SIM.' },
  { key: 'whatif', label: 'E se…', desc: 'Momento, prazo, mês difícil', tag: 'SIM.' },
  { key: 'plan', label: 'Plano', desc: 'Linha do tempo e etapas', tag: 'SIM.' },
  { key: 'sheet', label: 'Supervisor', desc: 'Aceitar ou recusar', tag: 'OPT-IN' },
  { key: 'saved', label: 'Plano salvo', desc: 'Resumo e status' },
  { key: 'nudge', label: 'Aviso proativo', desc: 'Com Supervisor ativo' },
];

interface FlowMapProps {
  currentKey: string;
  onSelectStep: (key: string) => void;
}

export const FlowMap: React.FC<FlowMapProps> = ({ currentKey, onSelectStep }) => {
  return (
    <section aria-label="Mapa do fluxo" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div
        style={{
          font: "600 11px/1 ui-monospace, Menlo, monospace",
          color: '#4a4545',
          letterSpacing: '.06em',
        }}
      >
        MAPA DO FLUXO · TOQUE PARA ABRIR NO PROTÓTIPO
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
          gap: 8,
        }}
      >
        {FLOW_STEPS.map((step, idx) => {
          const isCurrent = step.key === currentKey;
          const numStr = String(idx + 1).padStart(2, '0');
          return (
            <button
              key={step.key}
              onClick={() => onSelectStep(step.key)}
              aria-current={isCurrent ? 'step' : 'false'}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                minHeight: 92,
                padding: 12,
                borderRadius: 12,
                border: isCurrent ? '1px solid #0b3c49' : '1px solid #dcd8d4',
                background: isCurrent ? '#0b3c49' : '#fff',
                color: isCurrent ? '#fff' : '#1c1b1b',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.15s ease-in-out',
              }}
            >
              <span
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  width: '100%',
                  font: "600 11px/1 ui-monospace, Menlo, monospace",
                  opacity: 0.85,
                }}
              >
                <span>{numStr}</span>
                {step.tag && <span>{step.tag}</span>}
              </span>
              <span style={{ fontWeight: 600, fontSize: 14, lineHeight: '18px' }}>{step.label}</span>
              <span style={{ fontSize: 12, lineHeight: '16px', opacity: 0.85 }}>{step.desc}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
};
