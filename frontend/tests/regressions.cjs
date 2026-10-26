// Synthetic local regression scenarios. No user profiles or documents are retained.
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const AxeBuilder = require(process.env.AXE_MODULE || '@axe-core/playwright').default;
const BASE = process.env.PORTAL_URL || 'http://127.0.0.1:3010';
const OUT = process.env.TEST_OUTPUT || path.resolve(__dirname, '../test-artifacts/regressions');
const FIX = path.resolve(__dirname, '../../backend/tests/fixtures');
const results = [];
function expect(value, message) { if (!value) throw new Error(message); }
async function check(name, fn) { try { await fn(); results.push({ name, status: 'PASS' }); } catch (e) { results.push({ name, status: 'FAIL', error: e.stack }); } }
async function yes(page, name, text) { await page.getByRole('group', { name }).getByText(text, { exact: true }).click(); }
async function submit(page) { await page.getByRole('button', { name: 'Show my roadmap', exact: true }).click(); await page.getByRole('heading', { name: 'Your roadmap', exact: true }).waitFor(); }
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: process.env.HEADLESS !== '0' });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage(); page.setDefaultTimeout(12000);
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  const english = { test: 'IELTS Academic', taken_on: '2025-03-01', scores: { listening: 8, writing: 7, reading: 7, speaking: 7, overall: 7 } };
  const request = body => context.request.post(`${BASE}/api/roadmap/crna`, { data: body });

  await check('API rejects future dates and invalid test-specific score values', async () => {
    for (const change of [{ taken_on: '2099-01-01' }, { scores: { writing: 12 } }, { scores: { writing: 6.25 } }, { test: 'CELBAN', scores: { writing: 7.5 } }]) {
      const res = await request({ english: { ...english, ...change } }); expect(res.status() === 422, `${JSON.stringify(change)} returned ${res.status()}`);
    }
    expect((await request({ english, english_exemption: true })).status() === 422, 'conflicting evidence was accepted');
  });
  await check('Leap-day date returns a roadmap instead of HTTP 500', async () => {
    expect((await request({ english: { ...english, taken_on: '2024-02-29' } })).status() === 200, 'leap day crashed');
  });
  await check('Every route fits 320, 375 and 768 px and marks current navigation', async () => {
    for (const route of ['/', '/engineering', '/nursing', '/pharmacy', '/computing']) {
      await page.goto(BASE + route); await page.getByRole('heading', { level: 1 }).waitFor();
      expect(await page.locator(`nav[aria-label="Main"] a[aria-current="page"]`).count() === 1, `no current nav on ${route}`);
      for (const width of [320, 375, 768]) {
        await page.setViewportSize({ width, height: 800 });
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow on ${route} at ${width}`);
      }
      await page.setViewportSize({ width: 1280, height: 900 });
    }
  });
  await check('Nursing clears inactive exemption and uses the visible test scores', async () => {
    await page.goto(BASE + '/nursing');
    await yes(page, 'Does an English exemption apply to you?', 'Yes');
    await page.getByLabel('Test', { exact: true }).selectOption('IELTS Academic');
    await page.getByLabel('Date taken').fill('2025-03-01');
    for (const part of Object.keys(english.scores)) await page.getByLabel(part, { exact: true }).fill('1');
    const pending = page.waitForRequest(r => r.url().endsWith('/api/roadmap/crna') && r.method() === 'POST');
    await submit(page); const body = (await pending).postDataJSON();
    expect(body.english_exemption !== true, 'hidden exemption was sent');
    await page.getByText(/Below the minimum/).first().waitFor();
    expect(await page.locator('#roadmap-title').evaluate(e => e === document.activeElement), 'result heading not focused');
  });
  await check('Missing date cannot silently discard test scores', async () => {
    await page.goto(BASE + '/nursing'); await page.getByLabel('Test', { exact: true }).selectOption('IELTS Academic');
    await page.getByLabel('writing', { exact: true }).fill('7');
    expect(await page.getByLabel('Date taken').evaluate(e => e.required && e.validity.valueMissing), 'date not required');
    await page.getByText('Date required for test results. Future dates cannot be used.').waitFor();
    expect(await page.getByLabel('writing', { exact: true }).getAttribute('max') === '9', 'IELTS bound incorrect');
  });
  await check('Editing answers immediately clears old roadmap', async () => {
    await page.goto(BASE + '/engineering'); await page.getByLabel(/How many months/).fill('72');
    await yes(page, 'Are you a Canadian citizen or permanent resident?', 'No'); await submit(page);
    await yes(page, 'Are you a Canadian citizen or permanent resident?', 'Yes');
    expect(await page.getByRole('heading', { name: 'Your roadmap', exact: true }).count() === 0, 'old roadmap retained');
  });
  await check('Older late success cannot overwrite a newer request after input edits', async () => {
    await page.goto(BASE + '/engineering');
    const licensee = await (await context.request.post(BASE + '/api/roadmap/apega', { data: { experience_months: 72, canadian_citizen_or_pr: false } })).json();
    const member = await (await context.request.post(BASE + '/api/roadmap/apega', { data: { experience_months: 72, canadian_citizen_or_pr: true } })).json();
    let first; let count = 0;
    await page.route('**/api/roadmap/apega', async route => { if (++count === 1) first = route; else await route.fulfill({ json: member }); });
    try {
      await page.getByLabel(/How many months/).fill('72'); await yes(page, 'Are you a Canadian citizen or permanent resident?', 'No');
      await page.getByRole('button', { name: 'Show my roadmap', exact: true }).click();
      await page.getByRole('button', { name: 'Building your roadmap…', exact: true }).waitFor();
      expect(await page.getByRole('button', { name: 'Building your roadmap…', exact: true }).isDisabled(), 'pending submit enabled');
      await yes(page, 'Are you a Canadian citizen or permanent resident?', 'Yes'); await submit(page);
      if (first) await first.fulfill({ json: licensee }).catch(() => {});
      await page.waitForTimeout(150);
      expect((await page.getByText(/^Route:/).textContent()).includes(member.pathway.name), 'older response won');
    } finally { await page.unroute('**/api/roadmap/apega'); }
  });
  await check('Drafts save only with opt-in, restore on reload, and can be deleted', async () => {
    await page.goto(BASE + '/engineering'); await page.getByLabel(/How many months/).fill('72');
    expect(await page.evaluate(() => localStorage.getItem('navigator-engineering-v1')) === null, 'saved without opt-in');
    await page.getByLabel('Save my answers on this browser').check(); await page.reload();
    await page.getByText('Saved answers restored on this browser.').waitFor();
    expect(await page.getByLabel(/How many months/).inputValue() === '72', 'draft not restored');
    await page.getByRole('button', { name: 'Delete saved draft' }).click(); await page.reload();
    expect(await page.getByLabel(/How many months/).inputValue() === '', 'deleted draft restored');
  });
  await check('Corrupt saved drafts do not crash the questionnaire', async () => {
    await page.evaluate(() => localStorage.setItem('navigator-nursing-v1', JSON.stringify({ answers: 'bad' })));
    await page.goto(BASE + '/nursing'); await page.getByText(/incompatible saved draft/).waitFor();
    expect(await page.getByRole('button', { name: 'Show my roadmap' }).isEnabled(), 'form unusable');
  });
  await check('Upload shows document identity and reasons; editing inputs clears results', async () => {
    await page.goto(BASE + '/engineering');
    await page.getByLabel('Your discipline').selectOption('mechanical-engineering');
    await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIX, 'mechanical_course_descriptions.pdf'));
    await page.getByRole('button', { name: 'Compare', exact: true }).click();
    await page.getByText(/We found 21 courses/).waitFor({ timeout: 30000 });
    await page.getByText('mechanical_course_descriptions.pdf', { exact: true }).waitFor();
    await page.getByText('Why this match?', { exact: true }).first().click();
    await page.getByText(/Shared terms:/).first().waitFor();
    expect(await page.locator('#gap-results-title').evaluate(e => e === document.activeElement) || await page.getByText('Why this match?', { exact: true }).first().evaluate(e => e === document.activeElement), 'result not keyboard reachable');
    const download = page.waitForEvent('download'); await page.getByRole('button', { name: 'Download report (JSON)' }).click();
    expect((await download).suggestedFilename().includes('course-comparison'), 'wrong report export');
    await page.getByLabel('Your discipline').selectOption('chemical-engineering');
    expect(await page.getByText(/We found 21 courses/).count() === 0, 'stale upload result retained');
    await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIX, 'mechanical_transcript.pdf'));
    expect(await page.getByRole('heading', { name: 'Course comparison results' }).count() === 0, 'old file result retained');
  });
  await check('Axe audit on all routes and nursing result; mobile nursing scores fit', async () => {
    for (const route of ['/', '/engineering', '/pharmacy', '/computing', '/privacy', '/nursing']) {
      await page.goto(BASE + route); const axe = await new AxeBuilder({ page }).analyze();
      expect(axe.violations.length === 0, `${route}: ${axe.violations.map(v => v.id).join(', ')}`);
    }
    await page.getByLabel('Test', { exact: true }).selectOption('IELTS Academic'); await page.getByLabel('Date taken').fill('2025-03-01');
    for (const part of Object.keys(english.scores)) await page.getByLabel(part, { exact: true }).fill(String(english.scores[part]));
    await submit(page);
    expect(await page.getByRole('link', { name: /Timeline source/ }).count() > 0, 'timeline sources missing');
    const axe = await new AxeBuilder({ page }).analyze(); expect(axe.violations.length === 0, axe.violations.map(v => v.id).join(', '));
    for (const width of [320, 375]) { await page.setViewportSize({ width, height: 800 }); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `results overflow ${width}`); }
    await page.screenshot({ path: path.join(OUT, 'nursing-mobile-after.png'), fullPage: true });
  });
  await check('Malformed JSON drafts are removed without breaking the form', async () => {
    await page.evaluate(() => localStorage.setItem('navigator-engineering-v1', '{broken'));
    await page.goto(BASE + '/engineering'); await page.getByText(/unreadable saved draft was removed/).waitFor();
    expect(await page.evaluate(() => localStorage.getItem('navigator-engineering-v1')) === null, 'corrupt JSON was retained');
  });
  await check('Storage denial leaves the form usable without claiming a saved draft', async () => {
    const isolated = await browser.newContext();
    await isolated.addInitScript(() => { Storage.prototype.setItem = function () { throw new DOMException('blocked', 'SecurityError'); }; });
    const q = await isolated.newPage();
    try {
      await q.goto(BASE + '/engineering'); await q.getByLabel('Save my answers on this browser').click();
      await q.getByText('Browser storage could not be updated. Check your browser settings.').waitFor();
      expect(!await q.getByLabel('Save my answers on this browser').isChecked(), 'claims saving succeeded');
      await q.getByLabel(/How many months/).fill('72'); await submit(q);
    } finally { await isolated.close(); }
  });
  await check('Changing files cancels an in-flight comparison and ignores its late response', async () => {
    await page.goto(BASE + '/engineering');
    let pending, capture; const captured = new Promise(resolve => { capture = resolve; });
    await page.route('**/api/apega/analysis', async route => { pending = route; capture(); });
    try {
      await page.getByLabel('Your discipline').selectOption('mechanical-engineering');
      await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIX, 'mechanical_course_descriptions.pdf'));
      await page.getByRole('button', { name: 'Compare', exact: true }).click();
      await page.getByRole('button', { name: 'Reading your document…', exact: true }).waitFor();
      await captured;
      await page.getByLabel(/Course descriptions or transcript/).setInputFiles(path.join(FIX, 'mechanical_transcript.pdf'));
      if (pending) await pending.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({detail:'Old request failed'}) }).catch(() => {});
      await page.waitForTimeout(150);
      expect(await page.getByText('Old request failed', {exact:true}).count() === 0, 'old error became visible');
      expect(await page.getByRole('heading', { name: 'Course comparison results' }).count() === 0, 'stale comparison appeared');
      expect(await page.getByRole('button', { name: 'Compare', exact:true }).isEnabled(), 'new file cannot be submitted');
    } finally { await page.unroute('**/api/apega/analysis'); }
  });
  await check('No browser JavaScript exceptions', async () => expect(errors.length === 0, errors.join('; ')));
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(results, null, 2));
  for (const r of results) console.log(`${r.status} ${r.name}${r.error ? '\n' + r.error : ''}`);
  const failures = results.filter(r => r.status === 'FAIL').length;
  console.log(`\n${results.length - failures}/${results.length} passed`); process.exitCode = failures ? 1 : 0;
})().catch(e => { console.error(e); process.exitCode = 1; });
