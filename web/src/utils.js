export const money = (amount) => `$${Number(amount).toFixed(2)}`;

export const releaseDateLabel = (d) =>
  new Date(d + "T12:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
