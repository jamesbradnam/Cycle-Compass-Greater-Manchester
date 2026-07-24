import { useEffect, useRef } from 'react'
import { postEvent } from '../api'

export default function OverviewReport({ overview, sessionId, onContinue }) {
  const viewedRef = useRef(false)

  useEffect(() => {
    // Guard against React StrictMode's dev-only double effect invocation.
    if (!viewedRef.current) {
      viewedRef.current = true
      postEvent(sessionId, 'overview_viewed')
    }
  }, [sessionId])

  function handleContinue() {
    postEvent(sessionId, 'continue_clicked')
    onContinue()
  }

  return (
    <div className="report fade-in">
      <h2>Your overview</h2>
      <p className="report-text">{overview}</p>
      <button className="continue-button" onClick={handleContinue}>
        Continue to your recommendations
      </button>
    </div>
  )
}
