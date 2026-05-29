import { chromium } from 'playwright';
const URL = 'http://119.29.128.18';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  await page.goto(URL, { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(3000);

  const info = await page.evaluate(() => {
    const app = document.getElementById('app');
    const cs = app ? window.getComputedStyle(app) : null;
    const inlineVis = app ? app.style.visibility : '';
    const inlineStyleAttr = app ? app.getAttribute('style') || '' : '';

    // Find all style rules that match #app
    const allStyles = [];
    for (let si = 0; si < document.styleSheets.length; si++) {
      try {
        const ss = document.styleSheets[si];
        for (let ri = 0; ri < ss.cssRules.length; ri++) {
          const rule = ss.cssRules[ri];
          if (rule.selectorText && rule.selectorText.includes('#app')) {
            allStyles.push({
              sheetHref: ss.href || '(inline)',
              selector: rule.selectorText,
              cssText: rule.cssText,
            });
          }
        }
      } catch(e) {}
    }

    return {
      computedVisibility: cs?.visibility,
      computedOpacity: cs?.opacity,
      computedDisplay: cs?.display,
      inlineVisibility: inlineVis,
      inlineStyleAttr: inlineStyleAttr,
      styleSheetRules: allStyles,
    };
  });

  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();
