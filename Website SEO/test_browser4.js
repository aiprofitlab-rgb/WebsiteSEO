const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8080/en/index.html');
  
  const btn = page.locator('button.pulse');
  const btnBox = await btn.boundingBox();
  console.log("Button bounding box:", btnBox);
  
  await btn.click();
  
  const chat = page.locator('#aiden-ui');
  const isVisible = await chat.isVisible();
  const chatBox = await chat.boundingBox();
  console.log("Chat visible?", isVisible);
  console.log("Chat bounding box:", chatBox);
  
  const visibility = await chat.evaluate(el => window.getComputedStyle(el).visibility);
  console.log("Chat computed visibility:", visibility);
  
  await browser.close();
})();
