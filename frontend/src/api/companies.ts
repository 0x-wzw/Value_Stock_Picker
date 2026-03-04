import client from "./client";

export const searchCompanies = (q: string) =>
  client.get("/companies/search", { params: { q } }).then((r) => r.data);

export const getQuote = (ticker: string) =>
  client.get(`/companies/${ticker}/quote`).then((r) => r.data);

export const getCompanyFull = (ticker: string) =>
  client.get(`/companies/${ticker}`).then((r) => r.data);

export const getOverview = (ticker: string) =>
  client.get(`/companies/${ticker}/overview`).then((r) => r.data);

export const getFinancials = (ticker: string) =>
  client.get(`/companies/${ticker}/financials`).then((r) => r.data);

export const getKeyMetrics = (ticker: string) =>
  client.get(`/companies/${ticker}/metrics`).then((r) => r.data);

export const getValueSignals = (ticker: string) =>
  client.get(`/companies/${ticker}/signals`).then((r) => r.data);

export const getPriceHistory = (
  ticker: string,
  period = "5y",
  interval = "1d"
) =>
  client
    .get(`/companies/${ticker}/history`, { params: { period, interval } })
    .then((r) => r.data);

export const getFilings = (ticker: string, forms?: string) =>
  client
    .get(`/companies/${ticker}/filings`, { params: { forms } })
    .then((r) => r.data);

export const getSecFacts = (ticker: string) =>
  client.get(`/companies/${ticker}/sec-facts`).then((r) => r.data);

export const getNews = (ticker: string, limit = 10) =>
  client
    .get(`/companies/${ticker}/news`, { params: { limit } })
    .then((r) => r.data);

export const getAnalysts = (ticker: string) =>
  client.get(`/companies/${ticker}/analysts`).then((r) => r.data);

export const getInsiders = (ticker: string) =>
  client.get(`/companies/${ticker}/insiders`).then((r) => r.data);
