export default function Footer({ disclaimer }) {
  return (
    <footer className="app-footer">
      {disclaimer && <p className="disclaimer">{disclaimer}</p>}
    </footer>
  )
}
