/**
 * Advanced logging utility for debugging chart and data loading issues
 */

const LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug',
  TRACE: 'trace',
};

const COLORS = {
  error: '#ff6b6b',
  warn: '#ffa94d',
  info: '#4ecdc4',
  debug: '#95e1d3',
  trace: '#a8e6cf',
};

class Logger {
  constructor(prefix = 'App') {
    this.prefix = prefix;
    this.logs = [];
    this.maxLogs = 1000;
  }

  _formatMessage(level, message, data) {
    const timestamp = new Date().toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });

    const prefix = `[${timestamp}] [${this.prefix}] [${level.toUpperCase()}]`;

    if (data) {
      return { prefix, message, data };
    }
    return { prefix, message };
  }

  _log(level, message, data) {
    const formatted = this._formatMessage(level, message, data);

    // Store in memory
    this.logs.push({ ...formatted, level, timestamp: new Date().getTime() });
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output
    const color = COLORS[level] || '#000';
    const style = `color: ${color}; font-weight: bold;`;

    if (data !== undefined) {
      console.log(`%c${formatted.prefix} ${formatted.message}`, style, data);
    } else {
      console.log(`%c${formatted.prefix} ${formatted.message}`, style);
    }
  }

  error(message, data) {
    this._log(LOG_LEVELS.ERROR, message, data);
  }

  warn(message, data) {
    this._log(LOG_LEVELS.WARN, message, data);
  }

  info(message, data) {
    this._log(LOG_LEVELS.INFO, message, data);
  }

  debug(message, data) {
    this._log(LOG_LEVELS.DEBUG, message, data);
  }

  trace(message, data) {
    this._log(LOG_LEVELS.TRACE, message, data);
  }

  getLogs(level = null) {
    if (level) {
      return this.logs.filter(log => log.level === level);
    }
    return this.logs;
  }

  getLogsSince(timestamp) {
    return this.logs.filter(log => log.timestamp >= timestamp);
  }

  clearLogs() {
    this.logs = [];
  }

  exportLogs() {
    return JSON.stringify(this.logs, null, 2);
  }

  downloadLogs() {
    const logsText = this.logs
      .map(log => `${log.prefix} ${log.message}${log.data ? ' ' + JSON.stringify(log.data) : ''}`)
      .join('\n');

    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(logsText));
    element.setAttribute('download', `logs_${Date.now()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }
}

export const appLogger = new Logger('App');
export const chartLogger = new Logger('Chart');
export const apiLogger = new Logger('API');
export const strategyLogger = new Logger('Strategy');

export default { appLogger, chartLogger, apiLogger, strategyLogger };
