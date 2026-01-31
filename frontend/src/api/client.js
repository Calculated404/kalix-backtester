import { apiLogger } from '../utils/logger';

const API_BASE = '/api';

export async function getHealth() {
  apiLogger.trace('Health check');
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}

export async function getStrategies() {
  apiLogger.info('Fetching strategies list');
  const r = await fetch(`${API_BASE}/strategies`);
  if (!r.ok) {
    throw new Error(`Failed to fetch strategies: ${r.status}`);
  }
  const result = await r.json();
  apiLogger.info('Strategies fetched', { count: result.strategies?.length || 0 });
  return result;
}

export async function getData(periodYears = 5, ticker = 'EURCHF=X', interval = '1d') {
  // Add timestamp to prevent caching
  const url = `${API_BASE}/data?period_years=${periodYears}&ticker=${encodeURIComponent(ticker)}&interval=${interval}&_t=${Date.now()}`;
  apiLogger.info('Fetching chart data', { periodYears, ticker, interval, url });

  const r = await fetch(url);

  if (!r.ok) {
    const errorText = await r.text();
    apiLogger.error('Chart data fetch failed', { status: r.status, error: errorText });
    throw new Error(`Failed to fetch chart data: ${r.status} ${errorText}`);
  }

  const result = await r.json();
  apiLogger.info('Chart data received', {
    dataPoints: result.data?.length || 0,
    ticker,
    interval,
    period: periodYears
  });
  return result;
}


export async function runBacktest(params) {
  apiLogger.info('Starting backtest', {
    ticker: params.ticker,
    interval: params.interval,
    strategies: params.strategies,
    periodYears: params.period_years
  });

  const r = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!r.ok) {
    const errorText = await r.text();
    apiLogger.error('Backtest request failed', { status: r.status, error: errorText });
    throw new Error(errorText);
  }

  const result = await r.json();
  const totalTrades = result.results?.reduce((sum, r) => sum + (r.trades?.length || 0), 0) || 0;

  apiLogger.info('Backtest completed', {
    strategies: result.results?.length || 0,
    totalTrades,
    results: result.results?.map(r => ({
      strategy: r.strategy,
      trades: r.trades?.length || 0
    }))
  });

  return result;
}

export async function reportSignal(strategy, data) {
  apiLogger.debug('Reporting signal', { strategy, dataPoints: data?.length || 0 });

  const r = await fetch(`${API_BASE}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ strategy, data }),
  });

  if (!r.ok) {
    const errorText = await r.text();
    apiLogger.error('Report signal failed', { status: r.status, error: errorText });
    throw new Error(errorText);
  }

  const result = await r.json();
  apiLogger.debug('Signal reported', { signal: result.signal });
  return result;
}
