import { useState, useEffect, useRef } from 'react';
import { getStrategies, getData, runBacktest } from './api/client';
import Chart from './components/Chart';
import BacktestForm from './components/BacktestForm';
import TradesTable from './components/TradesTable';
import './App.css';

function App() {
  const [strategies, setStrategies] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [periodYears, setPeriodYears] = useState(5);
  const [ticker, setTicker] = useState('EURCHF=X');
  const [interval, setInterval] = useState('1h');
  const [runResults, setRunResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const prevIntervalRef = useRef('1h');

  useEffect(() => {
    getStrategies()
      .then((res) => setStrategies(res.strategies || []))
      .catch((e) => setError(e.message));
  }, []);

  // Fetch chart data whenever period, ticker, or interval changes
  useEffect(() => {
    // Check if interval changed (not period or ticker)
    const intervalChanged = prevIntervalRef.current !== interval;
    if (intervalChanged) {
      prevIntervalRef.current = interval;
    }

    setLoading(true);

    // Only clear chart if interval changed (not on initial load or period/ticker changes)
    if (intervalChanged && chartData.length > 0) {
      setChartData([]);
    }

    getData(periodYears, ticker, interval)
      .then((res) => {
        setChartData(res.data || []);
        setError(null);
      })
      .catch((e) => {
        setError(`Failed to load chart data: ${e.message}`);
        setChartData([]);
      })
      .finally(() => setLoading(false));
  }, [periodYears, ticker, interval]);

  const handleRun = async (params) => {
    setError(null);
    setLoading(true);

    try {
      // Params already match state because of lifted state, but we keep this for consistency
      // if we ever allow running with different params than selected (e.g. batch run)

      const res = await runBacktest({
        ticker: params.ticker,
        interval: params.interval,
        period_years: params.periodYears,
        strategies: params.strategies,
        initial_cash: params.initialCash,
        commission: params.commission,
        max_entries_per_week: params.maxEntriesPerWeek,
        cooldown_days: params.cooldownDays,
      });
      
      setRunResults(res);
      
      // If the run returned a different period than currently displayed (e.g. backend adjustment), update it
      if (res.period_years && res.period_years !== params.periodYears) {
        setPeriodYears(res.period_years);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Flatten markers and include strategy name for display
  const markers = runResults?.results?.flatMap((r) =>
    (r.markers || []).map(m => ({ ...m, strategy: r.strategy }))
  ) ?? [];

  // Merge indicators from all strategies
  const indicators = runResults?.results?.reduce((acc, r) => {
    if (r.indicators) {
      Object.entries(r.indicators).forEach(([key, value]) => {
        acc[`${key}_${r.strategy}`] = value;
      });
    }
    return acc;
  }, {}) ?? {};

  return (
    <div className="app">
      <header className="header">
        <h1>Kalix Multi-Symbol Backtester</h1>
        <p>Backtest trading strategies on Forex, Commodities, and Stocks across multiple timeframes.</p>
      </header>
      <main className="main">
        <aside className="sidebar">
          <BacktestForm
            strategies={strategies}
            periodYears={periodYears}
            onPeriodChange={setPeriodYears}
            ticker={ticker}
            onTickerChange={setTicker}
            interval={interval}
            onIntervalChange={setInterval}
            onRun={handleRun}
            loading={loading}
          />
        </aside>
        <section className="chart-section">
          {error && <div className="error">{error}</div>}
          {loading && !runResults && <div className="loading">Loading chart data…</div>}
          <Chart data={chartData} markers={markers} indicators={indicators} height={500} runResults={runResults} />

          {runResults?.results?.map((result) => (
            result.trades && result.trades.length > 0 && (
              <TradesTable 
                key={result.strategy}
                trades={result.trades} 
                strategyName={result.strategy}
                metrics={result.metrics}
              />
            )
          ))}
        </section>
      </main>
    </div>
  );
}

export default App;
