import Chat from "./components/chat";
import Form from "./components/form";
import "./App.css";
function App() {
  return (
    <div className="app">
      <div className="main-container">

        {/* LEFT: FORM */}
        <div className="form-section">
          <Form />
        </div>

        {/* RIGHT: CHAT */}
        <div className="chat-section">
          <Chat />
        </div>

      </div>
    </div>
  );
}

export default App;