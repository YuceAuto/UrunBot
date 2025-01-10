// Pseudocode for a React component

function Chat() {
  const [userInput, setUserInput] = useState("");
  const [response, setResponse] = useState("");

  async function sendMessage() {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: userInput }),
    });
    const data = await res.json();
    setResponse(data.combined_answer);
  }

  return (
    <div>
      <textarea 
        value={userInput}
        onChange={e => setUserInput(e.target.value)}
        placeholder="Type your question..."
      />
      <button onClick={sendMessage}>Send</button>

      <div>
        <p>Answer:</p>
        <p>{response}</p>
      </div>
    </div>
  );
}

export default Chat;