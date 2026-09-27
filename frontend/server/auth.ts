import { execSync } from 'child_process';

const TARGET_AUDIENCE = process.env.BACKEND_URL || 'https://pingo-backend-uahbqqbh3a-uc.a.run.app';

let cachedToken: string | null = null;
let tokenExpiresAt = 0;

export async function getBackendHeaders(): Promise<Record<string, string>> {
  const now = Date.now();
  if (cachedToken && now < tokenExpiresAt - 60000) {
    return {
      'Authorization': `Bearer ${cachedToken}`,
      'Content-Type': 'application/json',
    };
  }

  // 1. If in Cloud Run (or GCP workload environment), fetch from Metadata Server
  try {
    const metadataUrl = `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=${encodeURIComponent(TARGET_AUDIENCE)}`;
    const response = await fetch(metadataUrl, {
      headers: { 'Metadata-Flavor': 'Google' },
      signal: AbortSignal.timeout(2000),
    });
    if (response.ok) {
      const token = (await response.text()).trim();
      if (token) {
        cachedToken = token;
        tokenExpiresAt = now + 50 * 60 * 1000; // cache for 50 mins
        return {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        };
      }
    }
  } catch {
    // Not running on Cloud Run metadata server, proceed to local development fallback
  }

  // 2. Local development fallback: use gcloud CLI to print identity token
  try {
    const cmd = process.platform === 'win32' ? 'gcloud.cmd' : 'gcloud';
    const token = execSync(`${cmd} auth print-identity-token --project=batalha-time-08-g7ha`, {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    if (token) {
      cachedToken = token;
      tokenExpiresAt = now + 40 * 60 * 1000;
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    }
  } catch (err: any) {
    console.error('Local fallback gcloud token failed:', err?.message || err);
  }

  return { 'Content-Type': 'application/json' };
}

export function getBackendUrl(): string {
  return TARGET_AUDIENCE.replace(/\/+$/, '');
}
