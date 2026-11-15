import { useState } from "react";

export default function Avatar({ user }) {
  const [failed, setFailed] = useState(false);
  return user.picture && !failed ? (
    <img src={user.picture} alt="" onError={() => setFailed(true)} />
  ) : (
    <span className="account-initial">{user.name?.[0] || "U"}</span>
  );
}
