import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);

  const handleSubmit = async () => {
    try {
      const res = await axios.post("http://localhost:5000/api/process", {
        query,
      });
      setResponse(res.data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="container">
      <h1>Type your request</h1>
      <textarea
        className="textarea"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your query here..."
      />
      <button className="button" onClick={handleSubmit}>
        Send
      </button>
      {response && <div className="result">Response: {response}</div>}
    </div>
  );
}

export default App;
