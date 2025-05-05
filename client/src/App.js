import { useState } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)
  const [scrapedText, setScrapedText] = useState('')

  const handleUrlSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setScrapedText('')

    try {
      const response = await fetch('http://localhost:5000/api/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to scrape URL')
      }

      setScrapedText(data.text)
      setIsInitialized(true)
      setUrl('')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuestionSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    
    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:5000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to get answer')
      }

      setAnswer(data.answer)
      setQuestion('')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Terms & Conditions Analyzer</h1>
      
      {!isInitialized ? (
        <div className="url-form">
          <h2>Enter Website URL</h2>
          <form onSubmit={handleUrlSubmit}>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter website URL"
              required
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Processing...' : 'Analyze'}
            </button>
          </form>
        </div>
      ) : (
        <div className="chat-interface">
          <div className="scraped-content">
            <h3>Scraped Content</h3>
            <div className="text-container">
              {scrapedText}
            </div>
          </div>
          
          <div className="qa-section">
            <h3>Ask Questions</h3>
            <form onSubmit={handleQuestionSubmit}>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about the terms..."
                required
              />
              <button type="submit" disabled={isLoading}>
                {isLoading ? 'Processing...' : 'Ask'}
              </button>
            </form>
            
            {answer && (
              <div className="answer">
                <h4>Answer:</h4>
                <div>
                  {answer.split(/\n/).map((line, lineIndex) => {
                    const isListItem = line.trim().startsWith('*');
                    const processedLine = isListItem ? line.trim().substring(1).trim() : line;
                    return (
                      <p key={lineIndex} style={{ marginBottom: '1rem' }}>
                        {isListItem ? (
                          <span style={{ display: 'flex', alignItems: 'flex-start' }}>
                            <span style={{ marginRight: '0.5rem' }}>•</span>
                            <span>
                              {processedLine.split(/\*\*(.+?)\*\*/g).map((part, index) => (
                                index % 2 === 0 ? part : <strong key={index}>{part}</strong>
                              ))}
                            </span>
                          </span>
                        ) : (
                          processedLine.split(/\*\*(.+?)\*\*/g).map((part, index) => (
                            index % 2 === 0 ? part : <strong key={index}>{part}</strong>
                          ))
                        )}
                      </p>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  )
}

export default App