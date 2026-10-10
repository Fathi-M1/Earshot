import type { ReactNode } from "react";
import { useState } from "react";
import { Link } from "react-router-dom";
import logo from "../../../design/logo.svg";
import { brand, contactEmail } from "@/lib/brand";
import { licenses } from "@/lib/licenses";
import { PageMeta } from "@/components/page-meta";

function Doc({
  title,
  description,
  label,
  children,
}: {
  title: string;
  description: string;
  label: string;
  children: ReactNode;
}) {
  return (
    <article className="doc">
      <PageMeta title={title} description={description} />
      <p className="mono">{label}</p>
      <h1>{title}</h1>
      <p className="updated">Last updated 10 Oct 2026</p>
      {children}
    </article>
  );
}

export function HowPage() {
  return (
    <>
      <Doc
        title="How it works"
        label="Product"
        description="Speech is heard, transcribed, and shown on your phone and watch. The models stay on the laptop."
      >
        {null}
      </Doc>
      <ol className="steps">
        <li>
          <h2>1 Hear</h2>
          <p>The laptop microphone takes the room, with automatic gain and noise suppression.</p>
          <div className="diagram" aria-hidden="true">
            <span>Mic</span>
            <i />
            <span>Laptop</span>
          </div>
        </li>
        <li>
          <h2>2 Transcribe locally</h2>
          <p>Whisper on the laptop turns speech into caption lines. The audio is not written to disk.</p>
          <div className="diagram" aria-hidden="true">
            <span>Speech</span>
            <i />
            <span>Whisper</span>
          </div>
        </li>
        <li>
          <h2>3 Notice moments</h2>
          <p>Your name, keywords, and dates. A small local model decides what is meant for you.</p>
          <div className="diagram" aria-hidden="true">
            <span>Line</span>
            <i />
            <span>Alert</span>
          </div>
        </li>
        <li>
          <h2>4 Show it</h2>
          <p>The phone, the lock screen, and a Garmin show the line over your local Wi-Fi.</p>
          <div className="diagram" aria-hidden="true">
            <span>Laptop</span>
            <i />
            <span>Phone</span>
            <i />
            <span>Watch</span>
          </div>
        </li>
      </ol>
      <article className="doc how-rest">
        <h2>What runs where</h2>
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Where</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Speech recognition</td>
              <td>Laptop</td>
            </tr>
            <tr>
              <td>Alerts and summaries</td>
              <td>Laptop</td>
            </tr>
            <tr>
              <td>Lock screen and watch</td>
              <td>Now Playing, on your Wi-Fi</td>
            </tr>
          </tbody>
        </table>
        <p>Works with the Wi-Fi off, once the models are already on the laptop. The watch and phone need the local network to mirror the line.</p>
      </article>
    </>
  );
}

export function PrivacyPage() {
  return (
    <Doc
      title="Privacy policy"
      label="Legal"
      description="Transcripts stay on your laptop. Audio is not saved. Nothing is sent to the internet."
    >
      <h2>What Earshot hears</h2>
      <p>Earshot listens through your laptop's microphone while a session is on. It turns speech into text on your laptop, and that's all it keeps.</p>
      <h2>What is never kept</h2>
      <p>Audio is never saved. Sound is turned into text in memory and then discarded. Earshot doesn't read your contacts, location, or accounts, and it doesn't filter or report anything. If someone says a phone number or an address out loud, it only exists as text on your own device.</p>
      <h2>Where it lives</h2>
      <p>On your laptop only. Nothing is uploaded.</p>
      <h2>Retention</h2>
      <p>Session text expires on the schedule you choose in the app.</p>
      <h2>Sharing</h2>
      <p>None. The app does not make network calls for captions, alerts, or summaries.</p>
      <h2>Your controls</h2>
      <p>Mute closes the microphone. You can delete everything, and you can export a session.</p>
      <h2>Changes</h2>
      <p>This page is updated when the product’s handling of text changes. The date above is the latest.</p>
      <h2>Developer contact</h2>
      <p>
        <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
      </p>
    </Doc>
  );
}

export function TermsPage() {
  return (
    <Doc
      title="Terms of use"
      label="Legal"
      description="Personal use. Tell people you are captioning. Captions are not a legal record."
    >
      <h2>Personal use</h2>
      <p>Use {brand.displayName} for yourself, on a computer you control.</p>
      <h2>Consent</h2>
      <p>Tell people you are captioning. Follow the recording laws where you are.</p>
      <h2>Accuracy</h2>
      <p>Captions and summaries can be wrong. They are not guaranteed.</p>
      <h2>Not for emergencies or legal records</h2>
      <p>Do not rely on {brand.displayName} in an emergency, or as an official transcript.</p>
      <h2>License</h2>
      <p>The code is open source. Models keep their own licenses, listed on the licenses page.</p>
      <h2>No warranty</h2>
      <p>The software is provided as it is, without a warranty.</p>
      <h2>Contact</h2>
      <p>
        <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
      </p>
    </Doc>
  );
}

const faqs = [
  {
    q: "Does it need internet?",
    a: "No, after the models are on the laptop. Captions, alerts, and summaries keep working with the network cut.",
  },
  {
    q: "Does it record audio?",
    a: "No. Audio stays in memory and is not written to disk. The text of a session can be kept until it expires.",
  },
  {
    q: "Which languages?",
    a: "English, Tagalog, and Arabic.",
  },
  {
    q: "How far away can it hear?",
    a: "There is no measured range. It depends on the room and the laptop microphone.",
  },
  {
    q: "How much RAM and battery?",
    a: "The stated requirement is 8 GB of RAM or more, and no GPU. Battery use on a laptop is not a published measurement.",
  },
  {
    q: "Which watches?",
    a: "A Garmin that shows the phone’s Now Playing title.",
  },
  {
    q: "How do I delete everything?",
    a: "Use the delete control in the app. That removes the session text stored on the laptop.",
  },
  {
    q: "Is it free?",
    a: "The code is open source. You run it on your own laptop. There is no subscription.",
  },
];

export function FaqPage() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <Doc title="FAQ" label="Help" description="Internet, audio, languages, range, memory, watches, deletion, and price.">
      <div className="faq">
        {faqs.map((item, index) => {
          const on = open === index;
          return (
            <div key={item.q} className={on ? "faq-item is-open" : "faq-item"}>
              <button type="button" aria-expanded={on} onClick={() => setOpen(on ? null : index)}>
                {item.q}
                <span aria-hidden="true">+</span>
              </button>
              <div className="faq-panel">
                <p>{item.a}</p>
              </div>
            </div>
          );
        })}
      </div>
    </Doc>
  );
}

export function LicensesPage() {
  return (
    <Doc
      title="Licenses"
      label="Legal"
      description="Licenses read from package metadata and model cards. Nothing here is guessed."
    >
      <p>Each row is the license field or classifier that the registry returned. Model rows use the Hugging Face model card.</p>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Version</th>
            <th>License</th>
            <th>Where read</th>
          </tr>
        </thead>
        <tbody>
          {licenses.map((row) => (
            <tr key={row.name}>
              <td>{row.name}</td>
              <td>{row.version}</td>
              <td>{row.license}</td>
              <td>{row.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Doc>
  );
}

export function AccessibilityPage() {
  return (
    <Doc
      title="Accessibility"
      label="Product"
      description="Built with Deaf and hard-of-hearing readers in mind. Text, contrast, labels, and Arabic direction."
    >
      <p>Built with Deaf and hard-of-hearing users in mind. The product is captions you can read, not a sound you have to catch.</p>
      <h2>Text size</h2>
      <p>Caption lines use the reading type, and the page follows your browser’s text size.</p>
      <h2>Contrast</h2>
      <p>Forest text on paper, and beige text on forest, are the two reading pairs.</p>
      <h2>Screen readers</h2>
      <p>Links and buttons have names. Decorative marks are hidden from assistive technology.</p>
      <h2>Arabic</h2>
      <p>Arabic lines are marked right to left.</p>
    </Doc>
  );
}

export function NotFound() {
  return (
    <article className="doc missing">
      <PageMeta title="Not found" description="That page is not on this site." />
      <img src={logo} alt="" width={40} height={64} />
      <h1>Nothing to hear here.</h1>
      <Link className="text-link" to="/">
        Back home →
      </Link>
    </article>
  );
}
