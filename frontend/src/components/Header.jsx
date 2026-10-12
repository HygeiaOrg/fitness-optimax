import { Link } from 'react-router-dom'
import logo from '../assets/ntb-logo-white.png'
import './Header.css'

export default function Header({ title, subtitle, backTo }) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-left">
          {backTo && (
            <Link to={backTo} className="header-back" id="back-button">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M12.5 15L7.5 10L12.5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </Link>
          )}
          <div className="header-titles">
            <div className="header-brand">
              <img className="header-logo" src={logo} alt="North Tyneside Barbells" />
              <h1 className="header-title">{title || 'Fitness OptiMax'}</h1>
            </div>
            {subtitle && <p className="header-subtitle">{subtitle}</p>}
          </div>
        </div>
        <div className="header-right">
          <div className="header-status">
            <span className="header-status-dot"></span>
            <span className="header-status-text">Live</span>
          </div>
        </div>
      </div>
    </header>
  )
}
