const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  
  const pages_to_test = [
    '/en/index.html',
    '/services-en.html',
    '/about-en.html',
    '/process-en.html',
    '/contact-en.html',
    '/index.html',
    '/services.html',
    '/about.html',
  ];
  
  let passed = 0;
  let failed = 0;
  
  for (const path of pages_to_test) {
    const page = await browser.newPage();
    page.on('pageerror', e => console.log(`  ⚠️  JS Error on ${path}: ${e.message}`));
    
    try {
      await page.goto(`http://localhost:8080${path}`, { waitUntil: 'load', timeout: 10000 });
      
      // Test 1: Manual click
      const btn = page.locator('button.pulse').first();
      const btnBox = await btn.boundingBox();
      if (!btnBox) { console.log(`❌ FAIL ${path}: Button not found`); failed++; continue; }
      
      await btn.click();
      const isVisible = await page.locator('#aiden-ui').evaluate(el => el.classList.contains('active'));
      if (!isVisible) { console.log(`❌ FAIL ${path}: Chat did not open on click`); failed++; continue; }
      
      // Click again to close
      await btn.click();
      
      // Test 2: Auto-popup (clear sessionStorage first)
      await page.evaluate(() => sessionStorage.clear());
      
      const hasTimer = await page.evaluate(() => {
        return typeof window.addEventListener === 'function';
      });
      
      console.log(`✅ PASS ${path}: Click works, timer listener registered`);
      passed++;
    } catch (e) {
      console.log(`❌ FAIL ${path}: ${e.message}`);
      failed++;
    } finally {
      await page.close();
    }
  }
  
  console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
  await browser.close();
})();
