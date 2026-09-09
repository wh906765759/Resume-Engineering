const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||undefined});
 const report={resumes:[],website:[],errors:[]};
 try {
  const page=await browser.newPage();
  page.on('pageerror',e=>report.errors.push(e.message));
  for(const role of ['process','npi','quality']) {
   await page.goto(pathToFileURL(path.join(root,`output/workflow-demo/exports/resume-${role}/index.html`)).href);
   await page.evaluate(()=>document.fonts.ready);
   const pages=await page.locator('.page').count();
   const overflow=await page.evaluate(()=>[...document.querySelectorAll('.page')].some(p=>p.scrollHeight>p.clientHeight||Math.max(...[...p.children].filter(c=>c.tagName!=='FOOTER').map(c=>c.getBoundingClientRect().bottom))>=p.querySelector('footer').getBoundingClientRect().top));
   if(pages!==2||overflow)throw Error('Resume layout failed: '+role);
   report.resumes.push({role,pages,overflow});
   await page.screenshot({path:path.join(root,`output/workflow-${role}.png`),fullPage:true});
  }
  for(const width of [1440,390]) {
   await page.setViewportSize({width,height:1000});
   await page.goto('http://127.0.0.1:8765');
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
   if(overflow)throw Error('Website overflow');
   report.website.push({width,overflow});
  }
  await page.locator('textarea').fill('工艺开发');
  await page.locator('form button').click();
  await page.waitForFunction(()=>document.querySelector('#live-answer').textContent.includes('本地检索演示'));
  report.ai=await page.locator('#live-answer').innerText();
  await page.screenshot({path:path.join(root,'output/workflow-ai.png'),fullPage:true});
  if(report.errors.length)throw Error(report.errors.join(';'));
  fs.writeFileSync(path.join(root,'output/workflow-browser-validation.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
