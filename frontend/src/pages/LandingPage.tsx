import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BarChart2,
  CheckCircle,
  ChevronRight,
  FileText,
  Menu,
  Mic,
  X,
  Zap,
} from "lucide-react";
import { NudgeMark } from "../components/NudgeMark";
import "./LandingPage.css";

const HERO_TAGS = [
  "AI transcription",
  "Structured debriefs",
  "Offline-capable",
  "Manager dashboards",
];

const STATS = [
  { value: "10K+", label: "Field visits tracked" },
  { value: "3×", label: "Faster debrief creation" },
  { value: "98%", label: "Transcription accuracy" },
  { value: "40+", label: "Programs monitored" },
];

const FEATURES = [
  {
    icon: FileText,
    title: "Structured",
    subtitle: "Visit metadata + free-form notes",
    body: "Log every field visit with rich metadata — site, date, program, participants — plus open-ended notes captured the way your team naturally thinks.",
  },
  {
    icon: Mic,
    title: "AI-powered",
    subtitle: "Transcription & debrief summaries",
    body: "Voice recordings are automatically transcribed and transformed into structured debriefs with key findings, observations, and next steps — no manual write-ups.",
  },
  {
    icon: BarChart2,
    title: "Actionable",
    subtitle: "Findings, blockers & follow-ups",
    body: "Surface blockers and follow-up actions across every visit. Managers get a clear picture of what is working and what needs attention — without reading every report.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Log the visit",
    body: "Field officers open the app, select the site and program, and start a visit. Add photos, quick notes, or a voice memo — even offline.",
  },
  {
    n: "02",
    title: "AI generates the debrief",
    body: "Audio is transcribed and an AI debrief is created automatically, extracting findings, blockers, and follow-up actions in a structured format.",
  },
  {
    n: "03",
    title: "Managers see the patterns",
    body: "Program managers get a live dashboard of all visits, can filter by site or date, and spot issues across the portfolio without chasing updates.",
  },
];

const BENEFITS = [
  "No more manual report compilation",
  "Works offline in low-connectivity areas",
  "Voice-to-text in local languages",
  "Export to CSV or share instantly",
  "Role-based access for large teams",
  "Audit trail for every visit",
];

const TESTIMONIALS = [
  {
    quote:
      "FIT cut our debrief time from 2 hours to 20 minutes. Our field officers actually look forward to logging visits now.",
    name: "Priya Menon",
    role: "Program Manager, Livelihood Initiative",
    initials: "PM",
  },
  {
    quote:
      "For the first time I can see what is happening across 30 sites without scheduling a single status call. The pattern view is a game-changer.",
    name: "Arjun Sharma",
    role: "Director of Operations",
    initials: "AS",
  },
];

function BrandMark({ size = 18 }: { size?: number }) {
  return (
    <div className="landing-nav__logo" aria-hidden>
      <NudgeMark size={size} color="#fff" />
    </div>
  );
}

function LandingNav() {
  const [open, setOpen] = useState(false);

  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "How it works", href: "#how-it-works" },
    { label: "About", href: "#about" },
  ];

  return (
    <nav className="landing-nav">
      <div className="landing-nav__inner">
        <a href="#" className="landing-nav__brand" onClick={(e) => e.preventDefault()}>
          <BrandMark />
          <span className="landing-nav__title">
            The/Nudge <span className="landing-nav__title-accent">FIT</span>
          </span>
        </a>

        <div className="landing-nav__links">
          {navLinks.map(({ label, href }) => (
            <a key={label} href={href} className="landing-nav__link">
              {label}
            </a>
          ))}
        </div>

        <div className="landing-nav__actions">
          <Link to="/login" className="landing-nav__signin">
            Sign in
          </Link>
          <Link to="/signup" className="landing-nav__cta">
            Get started
          </Link>
          <button
            type="button"
            className="landing-nav__menu-btn"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((prev) => !prev)}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {open ? (
        <div className="landing-nav__mobile">
          {navLinks.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              className="landing-nav__mobile-link"
              onClick={() => setOpen(false)}
            >
              {label}
            </a>
          ))}
          <Link to="/login" className="landing-nav__mobile-link" onClick={() => setOpen(false)}>
            Sign in
          </Link>
        </div>
      ) : null}
    </nav>
  );
}

export function LandingPage() {
  return (
    <div className="landing animate-in">
      <LandingNav />

      <header className="landing-hero">
        <div className="landing-hero__ring landing-hero__ring--lg" aria-hidden />
        <div className="landing-hero__ring landing-hero__ring--sm" aria-hidden />
        <div className="landing-hero__inner">
          <p className="landing-hero__eyebrow">The/Nudge Institute</p>
          <h1 className="landing-hero__title">
            Field Intelligence
            <span className="landing-hero__title-accent">Tool</span>
          </h1>
          <p className="landing-hero__desc">
            Capture field visits, transcribe notes, and produce structured debriefs — so managers can
            see patterns across programs without reading every report.
          </p>
          <div className="landing-hero__actions">
            <Link to="/signup" className="landing-btn landing-btn--primary">
              Get started <ArrowRight size={16} />
            </Link>
            <Link to="/login" className="landing-btn landing-btn--ghost">
              Sign in
            </Link>
          </div>
          <div className="landing-hero__tags">
            {HERO_TAGS.map((tag) => (
              <span key={tag} className="landing-hero__tag">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </header>

      <section className="landing-stats" aria-label="Impact statistics">
        <div className="landing-stats__grid">
          {STATS.map(({ value, label }) => (
            <div key={label}>
              <p className="landing-stats__value">{value}</p>
              <p className="landing-stats__label">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="features" className="landing-features">
        <div className="landing-features__inner">
          <div className="landing-section__header">
            <p className="landing-section__eyebrow landing-features__eyebrow">Core capabilities</p>
            <h2 className="landing-section__title landing-features__title">
              Everything your field team needs
            </h2>
          </div>
          <div className="landing-features__grid">
            {FEATURES.map(({ icon: Icon, title, subtitle, body }) => (
              <article key={title} className="landing-feature-card">
                <div className="landing-feature-card__icon">
                  <Icon size={22} />
                </div>
                <h3 className="landing-feature-card__title">{title}</h3>
                <p className="landing-feature-card__subtitle">{subtitle}</p>
                <p className="landing-feature-card__body">{body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="landing-steps">
        <div className="landing-steps__inner">
          <div className="landing-section__header">
            <p className="landing-section__eyebrow landing-steps__eyebrow">How it works</p>
            <h2 className="landing-section__title landing-steps__title">
              From field to insight — in minutes
            </h2>
          </div>
          <div className="landing-steps__grid">
            {STEPS.map(({ n, title, body }) => (
              <article key={n} className="landing-step-card">
                <span className="landing-step-card__num">{n}</span>
                <h3 className="landing-step-card__title">{title}</h3>
                <p className="landing-step-card__body">{body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="about" className="landing-why">
        <div className="landing-why__inner">
          <div>
            <p className="landing-section__eyebrow landing-why__eyebrow">Built for the field</p>
            <h2 className="landing-section__title landing-why__title">
              Designed for the realities of on-the-ground work
            </h2>
            <p className="landing-why__desc">
              Field work is messy. Connectivity is unreliable. Reports pile up. FIT is built to make
              capturing and sharing field intelligence effortless — so teams can focus on impact, not
              paperwork.
            </p>
            <a
              href="https://www.thenudge.org/"
              target="_blank"
              rel="noreferrer"
              className="landing-why__link"
            >
              Learn more about our approach <ChevronRight size={15} />
            </a>
          </div>
          <div className="landing-why__benefits">
            {BENEFITS.map((benefit) => (
              <div key={benefit} className="landing-benefit">
                <CheckCircle size={18} className="landing-benefit__icon" />
                <span className="landing-benefit__text">{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-testimonials">
        <div className="landing-testimonials__inner">
          <div className="landing-section__header">
            <p className="landing-section__eyebrow landing-testimonials__eyebrow">From the field</p>
            <h2 className="landing-section__title landing-testimonials__title">
              Trusted by program teams
            </h2>
          </div>
          <div className="landing-testimonials__grid">
            {TESTIMONIALS.map(({ quote, name, role, initials }) => (
              <blockquote key={name} className="landing-quote">
                <p className="landing-quote__text">&ldquo;{quote}&rdquo;</p>
                <footer className="landing-quote__author">
                  <div className="landing-quote__avatar">{initials}</div>
                  <div>
                    <p className="landing-quote__name">{name}</p>
                    <p className="landing-quote__role">{role}</p>
                  </div>
                </footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-cta">
        <div className="landing-cta__card">
          <div className="landing-cta__icon">
            <Zap size={24} />
          </div>
          <h2 className="landing-cta__title">Ready to bring intelligence to your field work?</h2>
          <p className="landing-cta__desc">
            Join program teams across India using FIT to capture, understand, and act on field
            insights — faster than ever before.
          </p>
          <div className="landing-cta__actions">
            <Link to="/signup" className="landing-btn landing-btn--primary">
              Get started — it&apos;s free <ArrowRight size={16} />
            </Link>
            <Link to="/login" className="landing-btn landing-btn--outline">
              Sign in
            </Link>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-footer__inner">
          <div className="landing-footer__top">
            <div>
              <div className="landing-footer__brand-row">
                <div className="landing-footer__logo" aria-hidden>
                  <NudgeMark size={16} color="#fff" />
                </div>
                <span className="landing-footer__brand">
                  The/Nudge <span className="landing-nav__title-accent">FIT</span>
                </span>
              </div>
              <p className="landing-footer__tagline">
                Field Intelligence Tool — an initiative of The/Nudge Institute.
              </p>
            </div>
            <div className="landing-footer__cols">
              <div>
                <p className="landing-footer__col-heading">Product</p>
                <div className="landing-footer__col-links">
                  <a href="#features" className="landing-footer__col-link">
                    Features
                  </a>
                  <a href="#how-it-works" className="landing-footer__col-link">
                    How it works
                  </a>
                  <Link to="/signup" className="landing-footer__col-link">
                    Get started
                  </Link>
                </div>
              </div>
              <div>
                <p className="landing-footer__col-heading">Company</p>
                <div className="landing-footer__col-links">
                  <a href="#about" className="landing-footer__col-link">
                    About
                  </a>
                  <a
                    href="https://www.thenudge.org/"
                    target="_blank"
                    rel="noreferrer"
                    className="landing-footer__col-link"
                  >
                    The/Nudge Institute
                  </a>
                  <Link to="/login" className="landing-footer__col-link">
                    Sign in
                  </Link>
                </div>
              </div>
            </div>
          </div>
          <div className="landing-footer__bottom">
            <p className="landing-footer__copy">
              An extension of{" "}
              <a href="https://www.thenudge.org/" target="_blank" rel="noreferrer">
                The/Nudge Institute
              </a>
            </p>
            <div className="landing-footer__legal">
              <span className="landing-footer__legal-link">Privacy</span>
              <span className="landing-footer__legal-link">Terms</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
