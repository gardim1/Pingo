import React, { useState } from 'react';

interface ConsentScreenProps {
  onAgree: (allowIncome: boolean) => void;
  onCancel: () => void;
  zoom?: number;
}

export const ConsentScreen: React.FC<ConsentScreenProps> = ({ onAgree, onCancel, zoom = 1 }) => {
  const [allowIncome, setAllowIncome] = useState(true);

  return (
    <div
      data-screen-label="Consentimento"
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        background: '#fff',
        zIndex: 10,
      }}
    >
      {/* iOS Status Bar */}
      <div
        style={{
          height: 50,
          flex: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 30px',
          font: "600 15px 'Inter', sans-serif",
          position: 'relative',
        }}
      >
        <span>10:02</span>
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

      {/* Close button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '6px 14px', flex: 'none' }}>
        <button
          onClick={onCancel}
          aria-label="Fechar Pingo"
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
            src="https://unpkg.com/lucide-static@0.460.0/icons/x.svg"
            alt=""
            width="26"
            height="26"
          />
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto' }} data-noscrollbar="1">
        <div
          style={{
            zoom,
            padding: '4px 22px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          <svg width="30" height="30" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M10 3c.6 4.4 2.6 6.4 7 7-4.4.6-6.4 2.6-7 7-.6-4.4-2.6-6.4-7-7 4.4-.6 6.4-2.6 7-7z"
              fill="#0e5a5f"
            />
            <path
              d="M18.5 2c.3 1.7 1 2.4 2.5 2.7-1.5.3-2.2 1-2.5 2.6-.3-1.6-1-2.3-2.6-2.6 1.6-.3 2.3-1 2.6-2.7z"
              fill="#0e5a5f"
            />
          </svg>

          <div>
            <h1 style={{ margin: 0, font: "700 22px/28px 'Inter', sans-serif", color: '#2a2727' }}>
              Oi, eu sou o Pingo
            </h1>
            <p
              style={{
                margin: '8px 0 0',
                fontSize: 16,
                lineHeight: '24px',
                color: '#3d3a3a',
                textWrap: 'pretty',
              }}
            >
              Mostro o impacto de uma decisão no seu mês antes de você decidir. Para isso, preciso ler
              alguns dados da sua conta.
            </p>
          </div>

          <div style={{ border: '1px solid #e3e1e1', borderRadius: 16 }}>
            {/* Required item: Account, card & installments */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                minHeight: 60,
                padding: '0 16px',
                borderBottom: '1px solid #eeecec',
                fontSize: 15,
                color: '#2a2727',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/wallet.svg"
                alt=""
                width="20"
                height="20"
              />
              <span style={{ flex: 1 }}>
                Conta, cartão e parcelas
                <span style={{ display: 'block', fontSize: 12, color: '#4a4545' }}>
                  Necessário para simular
                </span>
              </span>
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/lock.svg"
                alt="Fixo"
                width="16"
                height="16"
              />
            </div>

            {/* Optional item: Income & Salary */}
            <button
              role="switch"
              aria-checked={allowIncome}
              onClick={() => setAllowIncome(!allowIncome)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                minHeight: 60,
                padding: '0 16px',
                border: 0,
                background: 'none',
                textAlign: 'left',
                fontSize: 15,
                color: '#2a2727',
                cursor: 'pointer',
              }}
            >
              <img
                src="https://unpkg.com/lucide-static@0.460.0/icons/briefcase.svg"
                alt=""
                width="20"
                height="20"
              />
              <span style={{ flex: 1 }}>
                Renda e salário
                <span style={{ display: 'block', fontSize: 12, color: '#4a4545' }}>
                  {allowIncome ? 'Permitido' : 'Não permitido'}
                </span>
              </span>
              <span
                aria-hidden="true"
                style={{
                  flex: 'none',
                  width: 48,
                  height: 28,
                  borderRadius: 14,
                  background: allowIncome ? '#0e5a5f' : '#fff',
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
                    left: allowIncome ? 23 : 3,
                    width: 19,
                    height: 19,
                    borderRadius: '50%',
                    background: allowIncome ? '#fff' : '#0e5a5f',
                    transition: 'left 0.2s',
                  }}
                />
              </span>
            </button>
          </div>

          {/* Privacy & Security Guarantee */}
          <div
            style={{
              display: 'flex',
              gap: 12,
              background: '#f3f4f5',
              borderRadius: 14,
              padding: '14px 16px',
            }}
          >
            <img
              src="https://unpkg.com/lucide-static@0.460.0/icons/shield-check.svg"
              alt=""
              width="20"
              height="20"
              style={{ flex: 'none', marginTop: 1 }}
            />
            <div style={{ fontSize: 14, lineHeight: '20px', color: '#3d3a3a' }}>
              <strong style={{ color: '#1c1b1b' }}>O Pingo nunca</strong> faz pagamentos,
              transferências ou contrata crédito. Seus dados não saem do banco.
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div
        style={{
          flex: 'none',
          padding: '12px 22px 28px',
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        <button
          onClick={() => onAgree(allowIncome)}
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
          Concordar e começar
        </button>
        <button
          onClick={onCancel}
          style={{
            minHeight: 44,
            border: 0,
            background: 'none',
            color: '#1c1b1b',
            fontSize: 15,
            textDecoration: 'underline',
            cursor: 'pointer',
          }}
        >
          Agora não
        </button>
      </div>
    </div>
  );
};
