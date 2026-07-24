import Logo from './Logo'

export default function Header() {
  return (
    <header className="app-header">
      <Logo />
      <h1 className="app-title">Cycle Compass</h1>
      <p className="app-description">
        Cycle Compass uses AI to help you find personalised, practical ways to start (or keep)
        cycling in Greater Manchester. Answer a few quick questions to get your own overview and
        recommendations.
      </p>
    </header>
  )
}
