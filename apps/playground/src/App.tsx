import { useState } from 'react'

interface PipelineResult {
  ticket_text: string;
  classification: string;
  redacted_ticket: string;
  final_reply: string;
}

function App() {
  const [ticket, setTicket] = useState(
    "Hi, my name is Jane Doe (SSN: 000-12-3456, email: jane.doe@example.com). I was charged $120.00 twice on invoice #98765 on my credit card 4532-1234-5678-9012. Please issue a refund immediately!"
  );
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async () => {
    setIsLoading(true);
    setResult(null);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8001/api/process_ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticket_text: ticket }),
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setResult(data.data);
      } else {
        setError(data.message || "An unknown error occurred.");
      }
    } catch (err) {
      setError("Failed to connect to the backend. Is the API running on port 8001?");
    } finally {
      setIsLoading(false);
    }
  };

  const getBadgeClass = (classification: string) => {
    if (!classification) return 'badge-none';
    const c = classification.toLowerCase();
    if (c.includes('billing')) return 'badge-billing';
    if (c.includes('technical')) return 'badge-technical';
    if (c.includes('general')) return 'badge-general';
    return 'badge-none';
  };

  return (
    <>
      <div className="glass-panel" style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>AI Micro-Agent Assembly Line</h1>
        <p style={{ color: '#94a3b8', fontSize: '1.1em' }}>
          Triage, Redact, and Synthesize Responses with a unified Multi-LoRA vLLM Engine.
        </p>
      </div>

      <div className="layout-grid">
        <div className="glass-panel">
          <h2>1. Input Customer Ticket</h2>
          <textarea 
            value={ticket}
            onChange={(e) => setTicket(e.target.value)}
            placeholder="Type a customer support ticket here..."
          />
          <button onClick={handleProcess} disabled={isLoading || !ticket.trim()}>
            {isLoading ? 'Processing Pipeline...' : 'Run Agent Pipeline'}
          </button>
          
          {error && (
            <div style={{ marginTop: '1rem', color: '#ef4444', background: 'rgba(239,68,68,0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.2)' }}>
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        <div className="glass-panel">
          <h2>2. Pipeline Output</h2>
          
          {isLoading ? (
            <div style={{ textAlign: 'center' }}>
              <div className="loader"></div>
              <p style={{ color: '#94a3b8' }}>Coordinating Agents & LLM...</p>
            </div>
          ) : result ? (
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9em', color: '#94a3b8' }}>Triage Classification</h3>
              <div className={`badge ${getBadgeClass(result.classification)}`}>
                {result.classification}
              </div>

              <h3 style={{ margin: '1rem 0 0.5rem 0', fontSize: '0.9em', color: '#94a3b8' }}>Redacted Ticket (PII Safe)</h3>
              <div className="output-box redacted-text">
                {result.redacted_ticket}
              </div>

              <h3 style={{ margin: '1rem 0 0.5rem 0', fontSize: '0.9em', color: '#94a3b8' }}>Synthesized Reply</h3>
              <div className="output-box final-reply">
                {result.final_reply}
              </div>
            </div>
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
              Run the pipeline to see the output.
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default App
