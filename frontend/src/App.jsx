import { useEffect, useState } from 'react'
import Header from './components/Header'
import Footer from './components/Footer'
import QuestionCard from './components/QuestionCard'
import OverviewReport from './components/OverviewReport'
import SummaryReport from './components/SummaryReport'
import { fetchQuestions, postOverview, postRecommendations } from './api'
import './App.css'

function makeSessionId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export default function App() {
  const [sessionId] = useState(makeSessionId)
  const [questions, setQuestions] = useState(null)
  const [disclaimer, setDisclaimer] = useState('')
  const [questionIndex, setQuestionIndex] = useState(0)
  const [profile, setProfile] = useState({})
  // loading | question | loading-overview | overview | loading-recommendations | recommendations | error
  const [stage, setStage] = useState('loading')
  const [overview, setOverview] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [note, setNote] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchQuestions()
      .then((data) => {
        setQuestions(data.questions)
        setDisclaimer(data.disclaimer)
        setStage('question')
      })
      .catch(() => {
        setError('Could not reach the Cycle Compass backend. Is it running?')
        setStage('error')
      })
  }, [])

  async function handleAnswer(questionId, answer) {
    const value = questionId === 'borough' && answer === 'greater_manchester' ? null : answer
    const nextProfile = { ...profile, [questionId]: value }
    setProfile(nextProfile)

    const current = questions[questionIndex]
    const next = questions[questionIndex + 1]
    const isLastOfStage1 = current.stage === 1 && (!next || next.stage !== 1)
    const isLastQuestion = !next

    if (isLastOfStage1) {
      setStage('loading-overview')
      try {
        const result = await postOverview(nextProfile)
        setOverview(result.overview)
        setStage('overview')
      } catch {
        setError('Something went wrong generating your overview. Please try again.')
        setStage('error')
      }
    } else if (isLastQuestion) {
      setStage('loading-recommendations')
      try {
        const result = await postRecommendations(nextProfile)
        setRecommendations(result.recommendations)
        setNote(result.note)
        setStage('recommendations')
      } catch {
        setError('Something went wrong generating your recommendations. Please try again.')
        setStage('error')
      }
    } else {
      setQuestionIndex((i) => i + 1)
    }
  }

  function handleContinue() {
    setQuestionIndex((i) => i + 1)
    setStage('question')
  }

  return (
    <div className="app">
      <Header />
      <main className="app-main">
        {stage === 'loading' && <p className="status-text">Loading...</p>}
        {stage === 'error' && <p className="status-text status-error">{error}</p>}

        {stage === 'question' && questions && (
          <QuestionCard
            key={questions[questionIndex].id}
            question={questions[questionIndex]}
            sessionId={sessionId}
            onAnswer={handleAnswer}
          />
        )}

        {stage === 'loading-overview' && (
          <p className="status-text">Generating your overview...</p>
        )}
        {stage === 'overview' && (
          <OverviewReport overview={overview} sessionId={sessionId} onContinue={handleContinue} />
        )}

        {stage === 'loading-recommendations' && (
          <p className="status-text">Generating your recommendations...</p>
        )}
        {stage === 'recommendations' && (
          <SummaryReport
            overview={overview}
            recommendations={recommendations}
            note={note}
            sessionId={sessionId}
          />
        )}
      </main>
      <Footer disclaimer={disclaimer} />
    </div>
  )
}
