export const money = (amount) => `$${Number(amount).toFixed(2)}`;

export const releaseDateLabel = (d) =>
  new Date(d + "T12:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

function localClock(date, timeZone) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: timeZone || "America/Chicago",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  return Object.fromEntries(parts.map(({ type, value }) => [type, value]));
}

export function isDatePast(showDate, timeZone, now = new Date()) {
  const local = localClock(now, timeZone);
  const today = `${local.year}-${local.month}-${local.day}`;
  return showDate < today;
}

export function isShowtimePast(showDate, showTime, timeZone, now = new Date()) {
  const local = localClock(now, timeZone);
  const today = `${local.year}-${local.month}-${local.day}`;
  if (showDate < today) return true;
  if (showDate > today) return false;

  const match = /^(\d{1,2}):(\d{2}) (AM|PM)$/.exec(showTime || "");
  if (!match) return false;
  let hour = Number(match[1]) % 12;
  if (match[3] === "PM") hour += 12;
  const showMinutes = hour * 60 + Number(match[2]);
  const currentMinutes = Number(local.hour) * 60 + Number(local.minute);
  return showMinutes <= currentMinutes;
}
