// Round-two visual harness. Set PLAYWRIGHT_MODULE and CHROME_PATH only locally.
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const assets=path.join(root,'skill/resume-engineering/assets');
const out=path.join(root,'output');
fs.mkdirSync(path.join(out,'pdf'),{recursive:true});
const check=(condition,message)=>{if(!condition)throw Error(message);};
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
  const checks={website:[],resume:null,interactions:{},externalRequests:[]};
  try{
    const page=await browser.newPage();
    const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.route(/^https?:/,route=>{checks.externalRequests.push(route.request().url());return route.abort();});
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:1000});
      await page.goto(pathToFileURL(path.join(assets,'website-template/index.html')).href);
      await page.evaluate(()=>document.fonts.ready);
      const layout=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length}));
      check(layout.scrollWidth<=width,'Website horizontal overflow');
      check(layout.brokenImages===0,'Broken image');
      checks.website.push(layout);
      await page.screenshot({path:path.join(out,`website-${width}.png`),fullPage:true});
    }
    await page.locator('[data-project]').first().click();
    check(await page.locator('dialog').isVisible(),'Project dialog failed');
    await page.keyboard.press('Escape');
    check(!await page.locator('dialog').isVisible(),'Escape did not close dialog');
    await page.locator('[data-question="0"]').click();
    check((await page.locator('#answer').innerText()).includes('固定演示回答'),'Demo answer not labeled');
    await page.locator('summary').click();
    check(await page.locator('#education').isVisible(),'Education expansion failed');
    const href=await page.locator('.text-link').getAttribute('href');
    check(fs.existsSync(path.resolve(assets,'website-template',href)),'Resume preview link broken');
    checks.interactions={dialog:true,escape:true,demoAnswer:true,education:true,resumeLink:true};
    await page.goto(pathToFileURL(path.join(assets,'resume-template/index.html')).href);
    await page.evaluate(()=>document.fonts.ready);
    await page.emulateMedia({media:'print'});
    await page.setViewportSize({width:1000,height:1300});
    checks.resume=await page.evaluate(()=>[...document.querySelectorAll('.page')].map(p=>{const r=p.getBoundingClientRect(),f=p.querySelector('footer').getBoundingClientRect();const maxBottom=Math.max(...[...p.children].filter(c=>c.tagName!=='FOOTER').map(c=>c.getBoundingClientRect().bottom));return{width:r.width,height:r.height,contentBottom:maxBottom-r.top,footerTop:f.top-r.top,overflow:p.scrollHeight>p.clientHeight||maxBottom>=f.top,brokenImages:[...p.querySelectorAll('img')].some(i=>!i.complete||!i.naturalWidth)};}));
    check(checks.resume.length===2,'Expected two resume pages');
    check(checks.resume.every(p=>!p.overflow&&!p.brokenImages),'Resume overflow or broken image');
    await page.pdf({path:path.join(out,'pdf/resume-template-demo.pdf'),preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false,tagged:true});
    check(errors.length===0,'Browser errors: '+errors.join('; '));
    check(checks.externalRequests.length===0,'Unexpected network requests');
    fs.writeFileSync(path.join(out,'template-validation.json'),JSON.stringify(checks,null,2));
    console.log(JSON.stringify(checks));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
