const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1500,height:1100}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const model=JSON.parse(fs.readFileSync(path.join(__dirname,'../R2_REPAIRED_006/source_contract.json'),'utf8'));
 const evidence=JSON.parse(fs.readFileSync(path.join(__dirname,'ALL_BLOCKS_EVIDENCE.json'),'utf8'));
 await page.goto(pathToFileURL(path.join(__dirname,'ALL_BLOCKS_GUIDE.html')).href);
 if(await page.locator('[role=tab]').count()!==15)throw Error('15 tabs missing');
 let testedGraphs=0;
 for(let b=1;b<=15;b++){
  await page.locator('#tab-B'+b).click();
  let frame=await (await page.$('#document')).contentFrame();
  await frame.waitForSelector('h1');
  if(b===1){await frame.waitForSelector('#connected-diagram svg');continue;}
  await frame.waitForSelector('#drawing svg');
  const cs=model.components.filter(c=>+c.block.match(/^B(\d+)/)[1]===b&&!c.ref.startsWith('#'));
  if(await frame.locator('#parts-table tbody tr').count()!==cs.length)throw Error('parts B'+b);
  if(await frame.locator('#pins-table tbody tr').count()!==cs.reduce((n,c)=>n+c.pins.length,0))throw Error('pins B'+b);
  const opts=await frame.locator('#diagram-choice option').count();
  for(let i=0;i<opts;i++){
   await frame.selectOption('#diagram-choice',''+i);
   const check=evidence.diagrams.find(d=>d.name===`B${b}_${i}`);
   const actual=await frame.locator('#drawing .node.component').evaluateAll(ns=>ns.map(n=>n.id.replace('part-','')).sort());
   if(JSON.stringify(actual)!==JSON.stringify(check.components.sort()))throw Error('diagram parts '+check.name);
   if(await frame.locator('#drawing .edge.wire').count()!==check.pin_edges)throw Error('edges '+check.name);
   testedGraphs++;
  }
  await frame.selectOption('#diagram-choice','0');
  await frame.locator('#circuit').scrollIntoViewIfNeeded();
  if([2,8,11,12].includes(b))await page.screenshot({path:path.join(__dirname,`qa-B${b}.png`)});
  await frame.locator('#drawing .node.net').first().dispatchEvent('click');
  if(!await frame.locator('.diagram').evaluate(e=>e.classList.contains('is-focus')))throw Error('net focus B'+b);
  await frame.locator('#zoom').click();
  if(!await frame.locator('#drawing').evaluate(e=>parseFloat(e.style.width)>=1400))throw Error('zoom');
  await frame.locator('#fit').click();
  await frame.locator('input[data-table=parts-table]').fill(cs[0].ref);
  if(!await frame.locator('#parts-table tbody tr:visible').count())throw Error('filter');
  await page.setViewportSize({width:390,height:844});
  await frame.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('outer mobile');
  if(await frame.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)){
   console.log(await frame.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,items:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth&&!e.closest('.tablewrap,.diagram')).map(e=>[e.tagName,e.className,e.textContent.slice(0,90)])})));
   throw Error('inner mobile B'+b);
  }
  await page.setViewportSize({width:1500,height:1100});
 }
 await page.locator('#search').fill('R507');
 await page.locator('#search-result button').first().click();
 if(await page.locator('#tab-B5').getAttribute('aria-selected')!=='true')throw Error('global search');
 const f=await(await page.$('#document')).contentFrame();await f.waitForSelector('#reasoning');
 if(!await f.locator('#reasoning').innerText().then(t=>t.includes('R525·R526')))throw Error('conflict missing');
 await page.locator('#search').fill('');
 await page.setViewportSize({width:390,height:844});
 await f.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:path.join(__dirname,'qa-mobile.png')});
 if(errors.length)throw Error(errors.join('\n'));
 const result={tabs:15,integrated_and_detail_graphs:testedGraphs,checks:'part/pin rows, actual SVG components/edges, net focus, zoom, filters, global search, mobile overflow, offline load',js_errors:errors};
 fs.writeFileSync(path.join(__dirname,'ALL_BLOCKS_QA.json'),JSON.stringify(result,null,2));
 console.log(result);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
