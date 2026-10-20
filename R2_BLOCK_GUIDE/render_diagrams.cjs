const fs=require('fs'),path=require('path');
let Viz;try{Viz=require('@viz-js/viz')}catch{Viz=require('./vendor/viz-standalone.js')}
(async()=>{
 const v=await Viz.instance(),dir=path.join(__dirname,'diagrams');
 for(const name of fs.readdirSync(dir).filter(n=>n.endsWith('.dot'))){
  const dot=fs.readFileSync(path.join(dir,name),'utf8');
  const svg=v.renderString(dot,{format:'svg',engine:'dot'});
  fs.writeFileSync(path.join(dir,name.replace(/\.dot$/,'.svg')),svg);
 }
 console.log('Rendered all native pin/net graphs as SVG');
})();
