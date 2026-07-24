import { useEffect, useRef, useState } from 'react'
import { postEvent } from '../api'

export default function SummaryReport({ overview, recommendations, note, sessionId }) {
  const viewedRef = useRef(false)
  const [feedback, setFeedback] = useState(null)

  useEffect(() => {
    // Guard against React StrictMode's dev-only double effect invocation.
    if (!viewedRef.current) {
      viewedRef.current = true
      postEvent(sessionId, 'recommendations_viewed')
    }
  }, [sessionId])

  function handleLinkClick(rec) {
    postEvent(sessionId, 'recommendation_link_clicked', { url: rec.url, name: rec.name })
  }

  function handleFeedback(helpful) {
    setFeedback(helpful)
    postEvent(sessionId, 'feedback_given', { helpful })
  }

  return (
    <div className="report fade-in summary-report">
      <section>
        <h2>Your overview</h2>
        <p className="report-text">{overview}</p>
      </section>

      <section>
        <h2>Your recommendations</h2>

        {recommendations.length === 0 && note && <p className="report-note">{note}</p>}

        <ol className="recommendations-list">
          {recommendations.map((rec) => (
            <li key={rec.url}>
              <a href={rec.url} target="_blank" rel="noreferrer" onClick={() => handleLinkClick(rec)}>
                {rec.name}
              </a>
              <p>{rec.reason}</p>
            </li>
          ))}
        </ol>

        {recommendations.length > 0 && note && <p className="report-note">{note}</p>}
      </section>

      <section className="thank-you">
        <p className="thank-you-text">
          Thanks for trying Cycle Compass! We hope this made it a little easier to get moving in
          Greater Manchester.
        </p>

        {feedback === null ? (
          <div className="feedback-prompt">
            <span>Did you find this helpful?</span>
            <div className="options">
              <button className="option-button" onClick={() => handleFeedback(true)}>
                Yes
              </button>
              <button className="option-button" onClick={() => handleFeedback(false)}>
                No
              </button>
            </div>
          </div>
        ) : (
          <p className="feedback-thanks">Thanks for letting us know!</p>
        )}
      </section>
    </div>
  )
}
