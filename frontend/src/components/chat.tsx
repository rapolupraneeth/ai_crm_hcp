import { useDispatch } from "react-redux";
import { updateForm } from "../store/formSlice";
import { useState,useEffect } from "react";
function Chat() {
  const dispatch = useDispatch();
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState(() => Date.now().toString());
  const [loading, setLoading] = useState(false);
  type Message = {
  role: "user" | "ai";
  text: string;
};
  const [messages, setMessages] = useState<Message[]>(() => {
  const saved = localStorage.getItem("chat_messages");
  return saved ? JSON.parse(saved) : [];
});
useEffect(() => {
  localStorage.setItem("chat_messages", JSON.stringify(messages));
}, [messages]);
  

const handleSend = async () => {
  if (!message) return;

  setLoading(true);

  // ✅ add user message
  setMessages(prev => [...prev, { role: "user", text: message }]);

  try {
    const response = await fetch("http://127.0.0.1:8000/api/v1/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
      }),
    });

    const data = await response.json();
    console.log("Response from backend:", data);

    dispatch(updateForm(data.data));

    setMessages(prev => [...prev, { role: "ai", text: data.message }]);

    setMessage("");

  } catch (error) {
    console.error("Error:", error);
  }

  setLoading(false);
};
const handleNewChat = async () => {
  try {
    await fetch("http://127.0.0.1:8000/api/v1/chat/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    // ✅ THIS is the correct use of setSessionId
    setSessionId(Date.now().toString());
    setMessages([]);
    localStorage.removeItem("chat_messages");

    // optional but recommended
    dispatch(updateForm({
      hcp: {},
      interaction: {},
      follow_up: {},
      compliance_flags: [],
    }));

  } catch (error) {
    console.error("Reset failed:", error);
  }
};



  return (
  <div>
    <div className="chat-title">AI Assistant</div>

    {/* ✅ Chat messages */}
    <div className="chat-box">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-bubble ${
              msg.role === "user" ? "user" : "assistant"
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>
    </div>

    {/* ✅ Input + Buttons */}
    <div className="chat-input-container">
      <input
        className="chat-input"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Describe interaction..."
      />

      <button
        className="chat-button"
        onClick={handleSend}
        disabled={loading}
      >
        {loading ? "Thinking..." : "Log"}
      </button>

      <button
        className="chat-button secondary"
        onClick={handleNewChat}
      >
        New
      </button>
    </div>
  </div>
);
}

export default Chat;