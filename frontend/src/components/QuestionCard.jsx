import { useEffect, useRef, useState } from 'react'
import { postEvent } from '../api'

function prettify(slug) {
  if (slug === 'greater_manchester') return 'Not sure / all of Greater Manchester'
  return slug
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export default function QuestionCard({ question, sessionId, onAnswer }) {
  const [exiting, setExiting] = useState(false)
  const [selected, setSelected] = useState([])
  const viewedRef = useRef(false)

  useEffect(() => {
    setExiting(false)
    setSelected([])
    // Guard against React StrictMode's dev-only double effect invocation,
    // which would otherwise double-count every question view in analytics.
    if (!viewedRef.current) {
      viewedRef.current = true
      postEvent(sessionId, 'question_viewed', { question_id: question.id })
    }
  }, [question.id])

  function submit(answer) {
    postEvent(sessionId, 'question_answered', { question_id: question.id, answer })
    setExiting(true)
    setTimeout(() => onAnswer(question.id, answer), 220)
  }

  function toggleMulti(option) {
    setSelected((prev) =>
      prev.includes(option) ? prev.filter((item) => item !== option) : [...prev, option]
    )
  }

  return (
    <div className={`question-card${exiting ? ' exiting' : ''}`}>
      <h2>{question.prompt}</h2>

      {question.type === 'single' && (
        <div className="options">
          {question.options.map((option) => (
            <button key={option} className="option-button" onClick={() => submit(option)}>
              {prettify(option)}
            </button>
          ))}
        </div>
      )}

      {question.type === 'boolean' && (
        <div className="options">
          <button className="option-button" onClick={() => submit(true)}>
            Yes
          </button>
          <button className="option-button" onClick={() => submit(false)}>
            No
          </button>
        </div>
      )}

      {question.type === 'multi' && (
        <div className="options">
          {question.options.map((option) => (
            <button
              key={option}
              className={`option-button${selected.includes(option) ? ' selected' : ''}`}
              onClick={() => toggleMulti(option)}
            >
              {prettify(option)}
            </button>
          ))}
          <button
            className="continue-button"
            disabled={selected.length === 0}
            onClick={() => submit(selected)}
          >
            Continue
          </button>
        </div>
      )}
    </div>
  )
}
