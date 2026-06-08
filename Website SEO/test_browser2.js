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
  
  // Wait 11 seconds to see if it pops up automatically
  console.log("Waiting 11 seconds for auto popup...");
  await page.waitForTimeout(11000);
  
  let isActive = await page.evaluate(() => {
     return document.getElementById('aiden-ui').classList.contains('active');
  });
  console.log("Auto popup active? " + isActive);
  
  if (!isActive) {
      console.log("Auto popup failed! Clicking manually...");
      await page.click('button[onclick="toggleChat()"]');
      isActive = await page.evaluate(() => {
         return document.getElementById('aiden-ui').classList.contains('active');
      });
      console.log("Manual popup active? " + isActive);
  }
  
  await browser.close();
})();
