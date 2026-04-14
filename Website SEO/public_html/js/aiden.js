// Persistent visitor ID
let sessionId = localStorage.getItem("aiden_session");

if (!sessionId) {
  sessionId = crypto.randomUUID();
  localStorage.setItem("aiden_session", sessionId);
}

async function sendMessage(message, email = "", phone = "", industry = "", visitorType = "", country = "", language = "") {

  const response = await fetch("https://aiden-backend-aiden.up.railway.app/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message,
      sessionId,
      email,
      phone,
      industry,
      visitorType,
      country,
      language
    })
  });

  const data = await response.json();
  return data.reply;
}