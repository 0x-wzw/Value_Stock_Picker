import client from "./client";

export const getMarketOverview = () =>
  client.get("/screener/market").then((r) => r.data);

export const getSectorPerformance = (period = "1y") =>
  client.get("/screener/sectors", { params: { period } }).then((r) => r.data);

export const filterStocks = (filters: Record<string, unknown>) =>
  client.post("/screener/filter", filters).then((r) => r.data);

export const getBulkQuotes = (tickers: string[]) =>
  client
    .get("/screener/quotes", { params: { tickers: tickers.join(",") } })
    .then((r) => r.data);

export const getScreenerUniverse = () =>
  client.get("/screener/universe").then((r) => r.data);
