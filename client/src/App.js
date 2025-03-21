import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [scrapedText, setScrapedText] = useState("");
  const [chatHistory, setChatHistory] = useState([]);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const response = await fetch("http://localhost:5000/chat_history");
      const data = await response.json();
      setChatHistory(data);
    } catch (err) {
      console.error("Failed to fetch chat history:", err);
    }
  };

  const formatText = (text) => {
    // Format bold text
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Format bullet points (both - and * prefixes)
    formattedText = formattedText
      .split("\n")
      .map((line) => {
        if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
          return `<li>${line.trim().substring(2)}</li>`;
        }
        return line;
      })
      .join("\n");

    return formattedText;
  };

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setScrapedText("");

    try {
      const response = await fetch("http://localhost:5000/api/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to scrape URL");
      }

      setScrapedText(data.text);
      setIsInitialized(true);
      setUrl("");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:5000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to get answer");
      }

      setAnswer(data.answer);
      setQuestion("");
      fetchChatHistory(); // Refresh chat history after new question
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <center>
        {" "}
        <h1>LegallyAsk AI</h1>
        <h5>Know what you are agreeing to !!!</h5>
      </center>

      {!isInitialized ? (
        <div className="url-form">
          <form onSubmit={handleUrlSubmit}>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter website URL"
              required
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Processing..." : "Analyze"}
            </button>
          </form>
        </div>
      ) : (
        <div className="chat-interface">
          <div className="scraped-content">
            <h3>Scraped Content</h3>
            <div className="text-container">{scrapedText}</div>
          </div>

          <div className="chat-section">
            <form onSubmit={handleQuestionSubmit}>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about the terms..."
                required
              />
              <button type="submit" disabled={isLoading}>
                {isLoading ? "Processing..." : "Ask"}
              </button>
            </form>

            {error && <div className="error">{error}</div>}

            {answer && (
              <div className="answer">
                <h3>Answer:</h3>
                <div dangerouslySetInnerHTML={{ __html: formatText(answer) }} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
