import React from 'react'
import styles from './DomainBadge.module.css'

const CONFIG = {
  trusted:   { icon: '⊛', label: 'Trusted Source',   cls: 'trusted' },
  untrusted: { icon: '⊘', label: 'Low Credibility',   cls: 'untrusted' },
  unknown:   { icon: '⊙', label: 'Unknown Source',    cls: 'unknown' },
}

export default function DomainBadge({ info }) {
  if (!info) return null
  const { domain, credibility, note } = info
  const cfg = CONFIG[credibility] ?? CONFIG.unknown

  return (
    <div className={`${styles.badge} ${styles[cfg.cls]}`} title={note ?? ''}>
      <span className={styles.icon} aria-hidden="true">{cfg.icon}</span>
      <div className={styles.text}>
        <span className={styles.label}>{cfg.label}</span>
        <span className={styles.domain}>{domain}</span>
      </div>
    </div>
  )
}
