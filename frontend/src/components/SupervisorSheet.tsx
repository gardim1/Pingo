import React, { useState } from 'react';

interface SupervisorSheetProps {
  isOpen: boolean;
  isActive: boolean;
  onClose: () => void;
  onActivate: (config: { alerts: boolean; remind: boolean }) => void;
  onDeactivate: () => void;
  zoom?: number;
  lastMonthMarginFormatted?: string;
  installmentsEndMonth?: string;
  installmentsCount?: number;
}

export const SupervisorSheet: React.FC<SupervisorSheetProps> = ({
  isOpen,
  isActive,
  onClose,
  onActivate,
  onDeactivate,
  zoom = 1,
  lastMonthMarginFormatted = '−R$ 576,85',
  installmentsEndMonth = 'outubro',
  installmentsCount = 3,
}) => {
  const [alerts, setAlerts] = useState(true);
  const [remind, setRemind] = useState(true);

  if (!isOpen) return null;

  return (
    <div
      data-screen-label="Supervisor"
      style={{
        position: 'absolute',
        inset: 0,
        background: 'rgba(28,27,27,.45)',
        display: 'flex',
        alignItems: 'flex-end',
        zIndex: 50,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Pingo Supervisor"
        data-noscrollbar="1"
        style={{
          width: '100%',
          maxHeight: '92%',
          overflowY: 'auto',
          background: '#fff',
          borderRadius: '24px 24px 0 0',
        }}
      >
        <div
          style={{
            zoom,
            padding: '10px 22px 30px',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {/* Handle */}
          <div
            aria-hidden="true"
            style={{
              width: 40,
              height: 5,
              borderRadius: 3,
              background: '#d9d4d1',
              alignSelf: 'center',
            }}
          />

          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#0a3f43',
                  letterSpacing: '.04em',
                }}
              >
                OPCIONAL · DESLIGUE QUANDO QUISER
              </div>
              <h2 style={{ margin: '6px 0 0', font: "700 22px/28px 'Inter', sans-serif" }}>
                Pingo Supervisor
              </h2>
            </div>
            <button
              onClick={onClose}
              aria-label="Fechar"
              style={{
                width: 44,
                height: 44,
                border: 0,
                background: '#f0f1f3',
                borderRadius: '50%',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/x.svg"
                alt=""
                width="20"
                height="20"
              />
            </button>
          </div>

          {/* Core Guarantees & Functions */}
          <ul
            style={{
              listStyle: 'none',
              margin: 0,
              padding: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            <li
              style={{
                display: 'flex',
                gap: 12,
                fontSize: 15,
                lineHeight: '22px',
                color: '#2a2727',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/calendar-check.svg"
                alt=""
                width="22"
                height="22"
                style={{ flex: 'none' }}
              />
              Aviso quando suas {installmentsCount} parcelas terminarem em {installmentsEndMonth}.
            </li>
            <li
              style={{
                display: 'flex',
                gap: 12,
                fontSize: 15,
                lineHeight: '22px',
                color: '#2a2727',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/triangle-alert.svg"
                alt=""
                width="22"
                height="22"
                style={{ flex: 'none' }}
              />
              Alerta se um mês começar parecido com o último ({lastMonthMarginFormatted}).
            </li>
            <li
              style={{
                display: 'flex',
                gap: 12,
                fontSize: 15,
                lineHeight: '22px',
                color: '#2a2727',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/hand.svg"
                alt=""
                width="22"
                height="22"
                style={{ flex: 'none' }}
              />
              Nunca movimento dinheiro. Toda ação continua com você.
            </li>
          </ul>

          {/* Toggle Switches */}
          <div style={{ border: '1px solid #e3e1e1', borderRadius: 14 }}>
            <button
              role="switch"
              aria-checked={alerts}
              onClick={() => setAlerts(!alerts)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12,
                minHeight: 60,
                padding: '0 16px',
                border: 0,
                borderBottom: '1px solid #eeecec',
                background: 'none',
                textAlign: 'left',
                fontSize: 15,
                color: '#1c1b1b',
                cursor: 'pointer',
              }}
            >
              <span>
                Alertas de risco
                <span style={{ display: 'block', fontSize: 12, color: '#4a4545' }}>
                  {alerts ? 'Ligado' : 'Desligado'}
                </span>
              </span>
              <span
                aria-hidden="true"
                style={{
                  flex: 'none',
                  width: 48,
                  height: 28,
                  borderRadius: 14,
                  background: alerts ? '#0e5a5f' : '#fff',
                  position: 'relative',
                  border: '1.5px solid #0e5a5f',
                  boxSizing: 'border-box',
                  transition: 'background 0.2s',
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    top: 3,
                    left: alerts ? 23 : 3,
                    width: 19,
                    height: 19,
                    borderRadius: '50%',
                    background: alerts ? '#fff' : '#0e5a5f',
                    transition: 'left 0.2s',
                  }}
                />
              </span>
            </button>

            <button
              role="switch"
              aria-checked={remind}
              onClick={() => setRemind(!remind)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12,
                minHeight: 60,
                padding: '0 16px',
                border: 0,
                background: 'none',
                textAlign: 'left',
                fontSize: 15,
                color: '#1c1b1b',
                cursor: 'pointer',
              }}
            >
              <span>
                Lembrete em novembro
                <span style={{ display: 'block', fontSize: 12, color: '#4a4545' }}>
                  {remind ? 'Ligado, no início de novembro' : 'Desligado'}
                </span>
              </span>
              <span
                aria-hidden="true"
                style={{
                  flex: 'none',
                  width: 48,
                  height: 28,
                  borderRadius: 14,
                  background: remind ? '#0e5a5f' : '#fff',
                  position: 'relative',
                  border: '1.5px solid #0e5a5f',
                  boxSizing: 'border-box',
                  transition: 'background 0.2s',
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    top: 3,
                    left: remind ? 23 : 3,
                    width: 19,
                    height: 19,
                    borderRadius: '50%',
                    background: remind ? '#fff' : '#0e5a5f',
                    transition: 'left 0.2s',
                  }}
                />
              </span>
            </button>
          </div>

          {/* Action Buttons */}
          {!isActive ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                onClick={() => onActivate({ alerts, remind })}
                style={{
                  minHeight: 52,
                  borderRadius: 26,
                  border: 0,
                  background: '#0e5a5f',
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Ativar Supervisor
              </button>
              <button
                onClick={onClose}
                style={{
                  minHeight: 48,
                  borderRadius: 24,
                  border: 0,
                  background: 'none',
                  color: '#1c1b1b',
                  fontSize: 15,
                  fontWeight: 500,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Agora não
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                onClick={() => onActivate({ alerts, remind })}
                style={{
                  minHeight: 52,
                  borderRadius: 26,
                  border: 0,
                  background: '#0e5a5f',
                  color: '#fff',
                  fontSize: 16,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Salvar ajustes
              </button>
              <button
                onClick={onDeactivate}
                style={{
                  minHeight: 48,
                  borderRadius: 24,
                  border: '1px solid #8f1114',
                  background: '#fff',
                  color: '#8f1114',
                  fontSize: 15,
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                Desligar Supervisor
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
