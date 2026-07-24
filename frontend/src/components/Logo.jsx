export default function Logo({ size = 56 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
      role="img"
      className="logo-mark"
    >
      {/* wheel rim */}
      <circle cx="24" cy="24" r="19" fill="none" stroke="currentColor" strokeWidth="2.5" />

      {/* spokes */}
      <g stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.55">
        <line x1="24" y1="7" x2="24" y2="15" />
        <line x1="24" y1="33" x2="24" y2="41" />
        <line x1="7" y1="24" x2="15" y2="24" />
        <line x1="33" y1="24" x2="41" y2="24" />
        <line x1="12.4" y1="12.4" x2="18" y2="18" />
        <line x1="30" y1="30" x2="35.6" y2="35.6" />
        <line x1="35.6" y1="12.4" x2="30" y2="18" />
        <line x1="18" y1="30" x2="12.4" y2="35.6" />
      </g>

      {/* compass needle - solid north half, faint south half */}
      <polygon points="24,11 29,24 24,24" fill="currentColor" />
      <polygon points="24,37 19,24 24,24" fill="currentColor" opacity="0.4" />

      {/* hub */}
      <circle cx="24" cy="24" r="3.2" fill="var(--card-bg)" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}
