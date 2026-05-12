/*
 * AI-NIDS chart helpers
 * Compatibility layer for dashboard templates that reference charts.js.
 */

function updateCharts() {
    // Dashboard pages define their own chart update handlers.
    // This no-op keeps older cached templates from failing when this file is loaded.
}

window.updateCharts = window.updateCharts || updateCharts;
