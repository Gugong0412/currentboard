const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path=require('path');
const {pathToFileURL}=require('url');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(__dirname,'B1_GUIDE.html')).href);
 if(await page.locator('#pin-body tr').count()!==17)throw Error('pin count');
 if(await page.locator('#parts tbody tr').count()!==13)throw Error('part count');
 if(await page.locator('#connected-diagram svg').count()!==1)throw Error('integrated diagram');
 await page.locator('#diagram-zoom').click();
 if(await page.locator('#diagram-width').evaluate(e=>e.style.width)!=='1600px')throw Error('diagram zoom');
 await page.locator('#diagram-fit').click();
 for(const href of await page.locator('nav a').evaluateAll(xs=>xs.map(x=>x.getAttribute('href')))){
  if(await page.locator(href).count()!==1)throw Error('anchor '+href);
 }
 await page.screenshot({path:path.join(__dirname,'b1-desktop.png')});
 await page.locator('#pin-search').fill('PC15');
 if(await page.locator('#pin-body tr:visible').count()!==1)throw Error('search');
 await page.locator('#pin-search').fill('');
 await page.locator('#threshold').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(__dirname,'b1-calculations.png')});
 await page.setViewportSize({width:390,height:844});
 await page.evaluate(()=>window.scrollTo(0,0));
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('mobile overflow');
 await page.screenshot({path:path.join(__dirname,'b1-mobile.png')});
 await page.evaluate(()=>{window.print=()=>window.didPrint=true});
 await page.locator('#print').click();
 if(!await page.evaluate(()=>window.didPrint && [...document.querySelectorAll('details')].every(x=>x.open)))throw Error('print');
 if(errors.length)throw Error(errors.join('\n'));
 console.log('PASS: 13 parts, 17 pins, navigation, pin search, mobile width, print action, no JS errors');
 await browser.close();
})();
