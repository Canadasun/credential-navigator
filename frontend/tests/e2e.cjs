// Browser test of the portal against the running API (docker compose up -d api) and
// `npm run start`. Opens a visible Chromium window; set HEADLESS=1 to hide it.
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const AxeBuilder = require(process.env.AXE_MODULE || "@axe-core/playwright").default;

const BASE = process.env.PORTAL_URL || "http://127.0.0.1:3010";
const FIXTURES = path.resolve(__dirname, "../../backend/tests/fixtures");
const OUT = process.env.TEST_OUTPUT || path.resolve(__dirname, "../test-artifacts");
const results = [];

async function check(name, fn) {
  try { await fn(); results.push(["PASS", name]); }
  catch (e) { results.push(["FAIL", name, e.message.split("\n")[0]]); }
}
function expect(cond, message) { if (!cond) throw new Error(message); }

async function yes(page, question, answer) {
  await page.getByRole("group", { name: question }).getByText(answer, { exact: true }).click();
}

async function audit(page, name) {
  const { violations } = await new AxeBuilder({ page }).analyze();
  const serious = violations.filter((v) => ["serious", "critical"].includes(v.impact));
  expect(serious.length === 0, `${name}: ${serious.map((v) => `${v.id} on ${v.nodes.slice(0, 3)
    .map((n) => `${n.target.join(" ")} (${(n.any[0] || {}).message || ""})`).join("; ")}`).join(" / ")}`);
}

(async () => {
  require("fs").mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: process.env.HEADLESS === "1", slowMo: process.env.HEADLESS === "1" ? 0 : 150 });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  await check("Home page links to both professions and shows the advisory note", async () => {
    await page.goto(BASE);
    await page.getByRole("note").getByText("Advisory tool").waitFor();
    await audit(page, "home");
    await page.getByRole("link", { name: /Engineering.*Start/s }).click();
    await page.waitForURL(/engineering/);
  });

  await check("Engineer: 6 years, no PR, non-accredited degree → Licensee roadmap with $750 expected", async () => {
    await page.goto(`${BASE}/engineering`);
    await page.getByLabel("How many months of engineering work experience do you have?").fill("72");
    await yes(page, "Are you a Canadian citizen or permanent resident?", "No");
    await yes(page, /CEAB-accredited/, "No");
    await page.getByRole("button", { name: "Show my roadmap" }).click();
    await page.getByRole("heading", { name: "Your roadmap" }).waitFor();
    await page.getByText("Route: Licensee.").waitFor();
    await page.getByText("CAD 750.00", { exact: false }).first().waitFor();
    const mayApply = await page.getByText("May apply", { exact: true }).count();
    expect(mayApply >= 1, "assigned exams should be 'May apply'");
    await audit(page, "engineering roadmap");
    await page.screenshot({ path: path.join(OUT, "engineering-roadmap.png"), fullPage: true });
  });

  await check("Engineer: course descriptions upload shows the complementary studies gap", async () => {
    await page.getByLabel("Your discipline").selectOption("mechanical-engineering");
    await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIXTURES, "mechanical_course_descriptions.pdf"));
    await page.getByRole("button", { name: "Compare" }).click();
    await page.getByText(/We found 21 courses/).waitFor({ timeout: 30000 });
    const heading = page.getByRole("heading", { name: /Complementary Studies/ });
    await heading.getByText("3 may be needed").waitFor();
    await page.screenshot({ path: path.join(OUT, "engineering-gap-analysis.png"), fullPage: true });
  });

  await check("Engineer: a scanned transcript is read with OCR and says so", async () => {
    await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIXTURES, "mechanical_transcript_scanned.pdf"));
    await page.getByRole("button", { name: "Compare" }).click();
    await page.getByText(/read with OCR/).waitFor({ timeout: 60000 });
    await page.getByText(/We found 6 courses/).waitFor();
  });

  await check("Engineer: a blank scan gives a clear error", async () => {
    await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIXTURES, "scanned_like.pdf"));
    await page.getByRole("button", { name: "Compare" }).click();
    await page.getByRole("alert").filter({ hasText: /No readable text|scanned/ }).waitFor({ timeout: 60000 });
  });

  await check("Nurse: IELTS writing 6.0 is flagged; 500 hours meets currency", async () => {
    await page.goto(`${BASE}/nursing`);
    await yes(page, "Have you passed the NCLEX-RN?", "No");
    await page.getByLabel("Which report assesses your nursing education?").selectOption("nnas");
    await page.getByLabel("How did NNAS rate your education?").selectOption("comparable");
    await page.getByLabel("Nursing practice hours in the last 2 years").fill("500");
    await page.getByLabel("Test", { exact: true }).selectOption("IELTS Academic");
    await page.getByLabel("Date taken").fill("2026-03-01");
    for (const [part, score] of [["listening", "8"], ["reading", "7"], ["writing", "6"], ["speaking", "7"], ["overall", "7"]]) {
      await page.getByLabel(part, { exact: true }).fill(score);
    }
    await page.getByRole("button", { name: "Show my roadmap" }).click();
    await page.getByText(/writing 6\.0 \(needs 6\.5\)/).first().waitFor();
    await page.getByText(/500 practice hours/).first().waitFor();
    await page.getByText("Route: Equivalent education or credential recognition.").waitFor();
    await audit(page, "nursing roadmap");
    await page.screenshot({ path: path.join(OUT, "nursing-roadmap.png"), fullPage: true });
  });

  await check("Phone width: no horizontal scrolling", async () => {
    await page.setViewportSize({ width: 375, height: 800 });
    const overflow = await page.evaluate(() => {
      const extra = document.documentElement.scrollWidth - window.innerWidth;
      const wide = [...document.querySelectorAll("body *")]
        .filter((el) => el.getBoundingClientRect().right > window.innerWidth + 1)
        .slice(0, 3).map((el) => `${el.tagName.toLowerCase()}.${String(el.className).slice(0, 40)}`);
      return { extra, wide };
    });
    expect(overflow.extra <= 0, `page is ${overflow.extra}px wider than the screen: ${overflow.wide.join(" | ")}`);
  });

  await browser.close();
  for (const r of results) console.log(r.join("  "));
  const failed = results.filter((r) => r[0] === "FAIL").length;
  console.log(`\n${results.length - failed}/${results.length} passed`);
  process.exit(failed ? 1 : 0);
})();
