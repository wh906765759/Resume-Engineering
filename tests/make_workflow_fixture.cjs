// Reproducibly convert the explicit synthetic display fixture into fact-bound data.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),box={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'skill/resume-engineering/assets/shared/demo-data.js'),'utf8'),box);
const example=JSON.parse(fs.readFileSync(path.join(root,'examples/synthetic-person/fact.json'),'utf8'));
const facts=[];
function bind(value,route){
  if(Array.isArray(value))return value.map((v,i)=>bind(v,route.concat(i)));
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,bind(v,route.concat(k))]));
  if(typeof value!=='string')return value;
  const f=JSON.parse(JSON.stringify(example));
  f.fact_id=`SYN-${String(facts.length+1).padStart(3,'0')}`;
  f.title='虚构展示字段 '+route.join('.');
  f.category=({work:'work',projects:'project',education:'education',capabilities:'capability',research:'research'})[route[0]]||'other';
  f.role=route.at(-1)==='role'?value:null;
  f.result=value;
  f.responsibility=[];f.technical_approach=[];f.method=[];f.tools=[];f.applicable_roles=[];
  f.evidence[0].supports=['result',...(f.role?['role']:[])];
  for(const use of Object.keys(f.permissions))f.permissions[use]={decision:'allow',reason:'Explicitly fictional integration test fixture',review:{review_id:'SYN-REVIEW',reviewed_at:'2026-01-01T00:00:00Z',fact_version:1,evidence_ref:'DEMO-E-001'}};
  facts.push(f);
  return {$fact:f.fact_id,field:f.role?'role':'result'};
}
const view=bind(box.window.RESUME_DEMO,[]);
const plan={schema_version:'1.0',synthetic:true,view,roles:{process:{project_order:[1,0,2,3],capability_order:[0,1,2,3]},npi:{project_order:[0,1,3,2],capability_order:[1,3,0,2]},quality:{project_order:[2,3,1,0],capability_order:[2,3,0,1]}}};
fs.writeFileSync(path.join(root,'examples/synthetic-person/workflow.json'),JSON.stringify({facts,plan},null,2)+'\n');
console.log(`Synthetic workflow fixture: ${facts.length} fact-bound fields`);
