export async function request(path, options = {}) {
  const { headers: requestHeaders, ...requestOptions } = options;
  const response = await fetch(`/api${path}`, {
    ...requestOptions,
    headers: {
      "Content-Type": "application/json",
      ...(requestHeaders || {}),
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    throw new Error(data?.error || "The request could not be completed.");
  }

  return data;
}
