"use client";

import { useI18n } from "@/lib/i18n";

type Section = { heading: string; points: string[] };

const CONTENT: Record<"en" | "fr", { intro: string; sections: Section[]; contact: string }> = {
  en: {
    intro: "Credential Navigator is built so that applicants can use it without an account and without leaving personal information behind. This page explains exactly what happens to what you enter.",
    sections: [
      { heading: "Your answers", points: [
        "Your answers are sent to our server only to build your roadmap, and the roadmap is sent straight back to you. They are not written to a database or kept after the reply.",
        "There are no accounts, no sign-in and no names, email addresses or ID numbers asked for.",
      ] },
      { heading: "Documents you upload", points: [
        "A transcript or course description you upload is read on our server to find your courses. Scans are read with OCR software running on the same server; nothing is sent to an outside service or an AI provider.",
        "While a file is read, it and the page images made for OCR may sit briefly in temporary files. They are deleted as soon as the comparison is done; the document is never saved.",
        "Use course descriptions or a transcript only. Remove anything you don't need, such as your student number, before uploading.",
      ] },
      { heading: "What stays in your browser", points: [
        "If you tick “Save my answers on this browser”, your answers are kept in this browser's local storage so they come back when you return. It is off by default, never includes uploaded files, and “Delete saved draft” removes it.",
        "Your language choice is remembered in the same way.",
        "On a shared or public computer, leave draft saving off.",
      ] },
      { heading: "What we don't do", points: [
        "No cookies, no analytics, no advertising and no tracking of any kind.",
        "No sharing with regulators, employers or anyone else. Links to regulator websites open their sites, which have their own privacy policies.",
      ] },
      { heading: "Server logs", points: [
        "Like most websites, the server's technical logs record when a request arrived, the page or service asked for and the network address it came from. They don't contain your answers or documents.",
      ] },
      { heading: "Advice, not a decision", points: [
        "The roadmap is advisory. Only the regulator (APEGA, the CRNA or the ACP) or CIPS decides on registration or certification. Always check the linked source pages before you pay or apply.",
      ] },
    ],
    contact: "Organizations piloting the tool can ask for the full technical description of how data is handled.",
  },
  fr: {
    intro: "Credential Navigator est conçu pour être utilisé sans compte et sans laisser de renseignements personnels derrière soi. Cette page explique exactement ce qu'il advient de ce que vous saisissez.",
    sections: [
      { heading: "Vos réponses", points: [
        "Vos réponses sont envoyées à notre serveur uniquement pour préparer votre feuille de route, qui vous est renvoyée aussitôt. Elles ne sont pas inscrites dans une base de données ni conservées après la réponse.",
        "Il n'y a pas de compte ni de connexion, et nous ne demandons ni nom, ni adresse courriel, ni numéro d'identification.",
      ] },
      { heading: "Documents téléversés", points: [
        "Le relevé de notes ou les descriptions de cours que vous téléversez sont lus sur notre serveur pour y trouver vos cours. Les documents numérisés sont lus par un logiciel de ROC sur le même serveur; rien n'est envoyé à un service externe ni à un fournisseur d'IA.",
        "Pendant la lecture, le fichier et les images des pages créées pour la ROC peuvent se trouver brièvement dans des fichiers temporaires. Ils sont supprimés dès la fin de la comparaison; le document n'est jamais conservé.",
        "Utilisez seulement des descriptions de cours ou un relevé de notes. Retirez ce qui n'est pas nécessaire, comme votre numéro d'étudiant, avant de téléverser.",
      ] },
      { heading: "Ce qui reste dans votre navigateur", points: [
        "Si vous cochez « Enregistrer mes réponses dans ce navigateur », vos réponses sont gardées dans le stockage local de ce navigateur pour les retrouver plus tard. Cette option est désactivée par défaut, n'inclut jamais les fichiers téléversés, et « Supprimer le brouillon enregistré » l'efface.",
        "Votre choix de langue est conservé de la même façon.",
        "Sur un ordinateur partagé ou public, laissez l'enregistrement désactivé.",
      ] },
      { heading: "Ce que nous ne faisons pas", points: [
        "Aucun témoin (cookie), aucune mesure d'audience, aucune publicité et aucun suivi de quelque nature que ce soit.",
        "Aucun partage avec les organismes de réglementation, les employeurs ou qui que ce soit. Les liens vers les sites des organismes ouvrent leurs sites, qui ont leurs propres politiques de confidentialité.",
      ] },
      { heading: "Journaux du serveur", points: [
        "Comme la plupart des sites Web, les journaux techniques du serveur enregistrent l'heure d'une requête, la page ou le service demandé et l'adresse réseau d'origine. Ils ne contiennent ni vos réponses ni vos documents.",
      ] },
      { heading: "Un conseil, pas une décision", points: [
        "La feuille de route est fournie à titre indicatif. Seul l'organisme de réglementation (APEGA, CRNA ou ACP) ou CIPS décide de l'inscription ou de la certification. Vérifiez toujours les pages sources en lien avant de payer ou de présenter une demande.",
      ] },
    ],
    contact: "Les organismes qui mettent l'outil à l'essai peuvent demander la description technique complète du traitement des données.",
  },
};

export default function Privacy() {
  const { lang, t } = useI18n();
  const page = CONTENT[lang];
  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold">{t("privacy.title")}</h1>
      <p className="text-lg text-slate-700">{page.intro}</p>
      {page.sections.map((s) => (
        <section key={s.heading} className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold">{s.heading}</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-700">{s.points.map((p) => <li key={p}>{p}</li>)}</ul>
        </section>
      ))}
      <p className="text-sm text-slate-600">{page.contact}</p>
    </div>
  );
}
