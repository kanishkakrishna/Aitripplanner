import { useState } from 'react'
import { MapPin, CloudSun, Route, Sparkles, LoaderCircle } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'https://aitripplanner-api.onrender.com'

function App() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [trip, setTrip] = useState(null)
  const [error, setError] = useState('')

  async function generatePlan() {
    if (!prompt.trim()) return
    setLoading(true)
    setError('')
    setTrip(null)

    try {
      const response = await fetch(`${API_URL}/api/plan-trip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim() }),
      })

      if (!response.ok) throw new Error(`Request failed with ${response.status}`)
      const data = await response.json()
      setTrip(data)
    } catch (err) {
      setError('The planner could not generate a trip. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      generatePlan()
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="eyebrow"><Sparkles size={16} /> KhojIndia data + Gemini</div>
        <h1>Discover India beyond the obvious.</h1>
        <p className="subtitle">Describe the trip you want. The planner searches uploaded hidden gems in MongoDB first, then builds a grounded itinerary of up to four days.</p>

        <div className="planner-box">
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Example: Plan a peaceful weekend trip from Jamshedpur near a waterfall"
            rows={4}
          />
          <button onClick={generatePlan} disabled={loading || !prompt.trim()}>
            {loading ? <><LoaderCircle className="spin" size={18} /> Planning...</> : <><Sparkles size={18} /> Generate itinerary</>}
          </button>
        </div>
      </section>

      {error && <div className="error-card">{error}</div>}

      {trip && (
        <section className="result-card">
          <div className="result-header">
            <div>
              <span className="label">Your grounded trip</span>
              <h2>{trip.title}</h2>
            </div>
            <div className="destination"><MapPin size={18} /> {trip.destination}</div>
          </div>

          <div className="info-grid">
            <article><CloudSun size={22} /><div><strong>Weather</strong><p>{trip.weather}</p></div></article>
            <article><Route size={22} /><div><strong>Route</strong><p>{trip.route}</p></div></article>
          </div>

          <div className="section-block">
            <h3>Itinerary</h3>
            <div className="timeline">
              {(trip.itinerary || []).map((item) => (
                <div className="day-row" key={`${item.day}-${item.activity}`}>
                  <span className="day-number">Day {item.day}</span>
                  <p>{item.activity}</p>
                </div>
              ))}
              {!trip.itinerary?.length && <p className="muted">No itinerary was returned.</p>}
            </div>
          </div>

          <div className="section-block">
            <h3>Travel tips</h3>
            <ul>{(trip.tips || []).map((tip) => <li key={tip}>{tip}</li>)}</ul>
          </div>
        </section>
      )}

      <footer>AI suggestions are grounded in the KhojIndia MongoDB dataset. Always verify local conditions before travel.</footer>
    </main>
  )
}

export default App
