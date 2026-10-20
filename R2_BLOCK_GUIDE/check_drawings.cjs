const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1600,height:1200}});
 const report=JSON.parse(fs.readFileSync(path.join(__dirname,'SCHEMATIC_DRAWING_AUDIT.json'),'utf8'));
 const issues=[];fs.mkdirSync(path.join(__dirname,'screenshots'),{recursive:true});
 for(const item of report.diagrams.filter(x=>!x.name.endsWith('_0'))){
  const source=fs.readFileSync(path.join(__dirname,'schematics',item.name+'.svg'),'utf8');
  await page.setContent('<style>body{margin:0}svg{width:1600px;height:auto}</style>'+source);
  const bad=await page.evaluate(()=>{
   const svg=document.querySelector('svg'),bounds=svg.getBoundingClientRect(),texts=[...svg.querySelectorAll('text')];
   let clipped=texts.filter(t=>{const r=t.getBoundingClientRect();return r.left<bounds.left-1||r.right>bounds.right+1||r.top<bounds.top-1||r.bottom>bounds.bottom+1}).map(t=>t.textContent);
   let overlaps=[];
   for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){
    const a=texts[i].getBoundingClientRect(),b=texts[j].getBoundingClientRect();
    const w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
    if(w>5&&h>5)overlaps.push([texts[i].textContent,texts[j].textContent]);
   }
   return {clipped,overlaps};
  });
  if(bad.clipped.length||bad.overlaps.length)issues.push({name:item.name,...bad});
  await page.screenshot({path:path.join(__dirname,'screenshots',item.name+'.png'),fullPage:true});
 }
 fs.writeFileSync(path.join(__dirname,'DRAWING_LAYOUT_QA.json'),JSON.stringify(issues,null,2));
 console.log(JSON.stringify(issues,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
