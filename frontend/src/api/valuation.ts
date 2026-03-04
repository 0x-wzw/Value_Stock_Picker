import client from "./client";

export const runDCF = (ticker: string, inputs: Record<string, number>) =>
  client.post(`/valuation/${ticker}/dcf`, inputs).then((r) => r.data);

export const runOwnerEarnings = (
  ticker: string,
  inputs: Record<string, number>
) =>
  client
    .post(`/valuation/${ticker}/owner-earnings`, inputs)
    .then((r) => r.data);

export const getQuickValuation = (ticker: string) =>
  client.get(`/valuation/${ticker}/quick`).then((r) => r.data);
