import Header from '../components/Header'
import './Privacy.css'

// TODO: swap for the club's real contact address before this reaches real athletes.
const PRIVACY_CONTACT = '[club contact email]'

export default function Privacy() {
  return (
    <div className="privacy-page animate-fade-in">
      <Header title="Privacy Notice" backTo="/" subtitle="How North Tyneside Barbells uses your data" />
      <main className="privacy-main">
        <section>
          <h2>Who runs this</h2>
          <p>Fitness OptiMax is run by North Tyneside Barbells for its athletes.</p>
        </section>
        <section>
          <h2>What we collect</h2>
          <p>
            Your name, email address, sex category, age category and weight
            category, and the lifts, sets, loads, RPE and session notes you
            log while training.
          </p>
        </section>
        <section>
          <h2>Why we collect it</h2>
          <p>
            To calculate your training targets, track your progress over
            time, and — only if you opt in — let other club members see your
            lift logs.
          </p>
        </section>
        <section>
          <h2>Who can see it</h2>
          <p>
            Only you and your coach, unless you've opted in to share your
            lift logs with other club members. You can withdraw that sharing
            at any time from your profile.
          </p>
        </section>
        <section>
          <h2>How long we keep it</h2>
          <p>Until you withdraw consent or ask us to delete your data.</p>
        </section>
        <section>
          <h2>Questions, or want your data deleted?</h2>
          <p>Email {PRIVACY_CONTACT}.</p>
        </section>
      </main>
    </div>
  )
}
