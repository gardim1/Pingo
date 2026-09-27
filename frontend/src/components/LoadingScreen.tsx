import React from 'react';

interface LoadingScreenProps {
  onClose: () => void;
  reduceMotion?: boolean;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ onClose, reduceMotion = false }) => {
  return (
    <div
      data-screen-label="Carregamento"
      role="status"
      aria-live="polite"
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

      {/* Top Bar with Close button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '6px 14px' }}>
        <button
          onClick={onClose}
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

      {/* Center Loader */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'flex-end',
          padding: '0 32px 118px',
          gap: 0,
          textAlign: 'center',
        }}
      >
        <div aria-hidden="true" style={{ position: 'relative', width: 60, height: 60 }}>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              border: '3px solid #e3eeee',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              border: '3px solid transparent',
              borderBottomColor: '#0e5a5f',
              borderLeftColor: '#0e5a5f',
              animation: reduceMotion ? 'none' : 'pgSpin 1.2s linear infinite',
            }}
          />
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            style={{ position: 'absolute', inset: 17 }}
          >
            <path
              d="M10 3c.6 4.4 2.6 6.4 7 7-4.4.6-6.4 2.6-7 7-.6-4.4-2.6-6.4-7-7 4.4-.6 6.4-2.6 7-7z"
              fill="#0e5a5f"
            />
            <path
              d="M18.5 2c.3 1.7 1 2.4 2.5 2.7-1.5.3-2.2 1-2.5 2.6-.3-1.6-1-2.3-2.6-2.6 1.6-.3 2.3-1 2.6-2.7z"
              fill="#0e5a5f"
            />
          </svg>
        </div>

        <div
          style={{
            font: "600 18px/24px 'Inter', sans-serif",
            color: '#3d3a3a',
            marginTop: 24,
          }}
        >
          Preparando tudo por aqui...
        </div>
        <div style={{ fontSize: 14, lineHeight: '20px', color: '#4a4545', marginTop: 6 }}>
          Conexão protegida pelo seu banco.
        </div>
      </div>
    </div>
  );
};
