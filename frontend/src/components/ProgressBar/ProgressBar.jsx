export default function ProgressBar({ answered, total, correct }) {
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0

  return (
    <div style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '10px 20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, fontSize: 13, color: '#64748b' }}>
        <span>Question <strong style={{ color: '#1e293b' }}>{answered + 1}</strong> of <strong style={{ color: '#1e293b' }}>{total}</strong></span>
        <span><strong style={{ color: '#16a34a' }}>{correct}</strong> correct</span>
      </div>
      <div style={{ background: '#f1f5f9', borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          background: 'linear-gradient(90deg, #7c3aed, #a78bfa)',
          transition: 'width 0.4s ease',
          borderRadius: 4,
        }} />
      </div>
    </div>
  )
}
