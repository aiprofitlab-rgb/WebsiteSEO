const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('pageerror', error => {
    console.log(`Page Error: ${error.message}`);
  });
  
  page.on('console', msg => {
    console.log(`Console [${msg.type()}]: ${msg.text()}`);
  });

  await page.goto('http://localhost:8080/en/index.html');
  
  console.log("Evaluating toggleChat()");
  try {
    await page.evaluate(() => toggleChat());
    console.log("toggleChat executed");
  } catch (e) {
    console.error("Evaluation Error:", e);
  }
  
  await browser.close();
})();
