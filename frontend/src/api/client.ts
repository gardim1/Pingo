import { ChatResponse, DecisionTerms, AccompanimentResponse } from '../types/pingo';

export async function sendChat(message: string, draft?: DecisionTerms | null): Promise<ChatResponse> {
  const res = await fetch('/api/pingo/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      decision: draft || null,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData?.message || errorData?.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function savePlan(decision: DecisionTerms, consentEnabled: boolean = true): Promise<any> {
  const res = await fetch('/api/pingo/plan', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: 'Guardar plano na sessão',
      consent_enabled: consentEnabled,
      decision,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData?.message || errorData?.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function reviewSupervisor(
  consentEnabled: boolean,
  planSnapshot?: any,
  event?: any
): Promise<AccompanimentResponse> {
  const res = await fetch('/api/pingo/supervisor', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      consent_enabled: consentEnabled,
      plan_snapshot: planSnapshot || null,
      event: event || null,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData?.message || errorData?.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function sendChatMessage(
  message: string,
  sessionId?: string,
  consentEnabled: boolean = true,
  draft?: DecisionTerms | null
): Promise<ChatResponse> {
  const res = await fetch('/api/pingo/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      consent_enabled: consentEnabled,
      decision: draft || null,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData?.message || errorData?.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function saveSupervisorOptIn(
  enabled: boolean,
  config?: { alerts: boolean; remind: boolean }
): Promise<AccompanimentResponse> {
  return reviewSupervisor(enabled, config);
}

export async function checkBackendHealth(): Promise<{ status: string }> {
  const res = await fetch('/api/pingo/health');
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}
