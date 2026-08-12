import ChatWidget from "./ChatWidget.jsx";

export default function App() {
  return (
    <div className="page">
      <header className="page-header">
        <h1>Acme Support</h1>
        <p>This page embeds the chat widget the way a real product page would.</p>
      </header>
      <ChatWidget />
    </div>
  );
}
