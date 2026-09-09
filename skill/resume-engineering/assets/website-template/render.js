(() => {
  'use strict';
  const d=window.RESUME_DATA||window.RESUME_DEMO;
  if(!d || (!d.approved_view && d.synthetic!==true)) throw Error('Approved projection or synthetic fixture required.');
  const e=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  document.getElementById('name').textContent=d.name;
  const positioning=d.positioning.split('｜');
  document.getElementById('positioning').innerHTML=`<span style="display:block">${e(positioning[0])}</span><span style="display:block">${e(positioning.slice(1).join('｜'))}</span>`;
  const indices=[1,0,2];
  document.getElementById('pillars').innerHTML=indices.map((n,i)=>{const p=d.projects[n];return `<article class="pillar"><div class="topline"><span>0${i+1} / ENGINEERING</span><span>↗</span></div><div class="pillar-title"><h3>${e(p.tag.replaceAll(' ','\n'))}</h3><p>${e(p.title)}</p></div><p class="muted">${e(p.background)}</p><div class="deliverable"><strong>${['工艺验证','制造准备','问题闭环'][i]}</strong><span>PROJECT EVIDENCE / 虚构项目</span></div><ul class="tags"><li>背景与角色</li><li>工程行动</li><li>成果与边界</li></ul><button class="project-link" data-project="${n}">查看项目详情 <span>→</span></button></article>`;}).join('');
  document.getElementById('timeline').innerHTML=d.work.map(w=>`<article class="timeline-entry"><time>${e(w.period)}</time><div><h3>${e(w.company)}</h3><p class="role">${e(w.role)}</p><p class="muted">${e(w.bullets[0])}</p></div></article>`).join('');
  document.getElementById('education').innerHTML=d.education.map(x=>`<p>${e(x.school)} · ${e(x.degree)} · ${e(x.period)}</p>`).join('');
  const dialog=document.getElementById('project-dialog');
  document.querySelectorAll('[data-project]').forEach(button=>button.addEventListener('click',()=>{const p=d.projects[Number(button.dataset.project)];document.getElementById('dialog-title').textContent=p.title;document.getElementById('dialog-body').innerHTML=[['项目背景',p.background],['我的职责',p.role],['工程行动',p.action],['项目成果',p.result]].map(([k,v])=>`<h3>${e(k)}</h3><p>${e(v)}</p>`).join('');dialog.showModal();}));
  document.getElementById('close-dialog').addEventListener('click',()=>dialog.close());
  const answers=['演示资料中的装配单元导入项目，覆盖工序验证、准备事项核对与现场问题跟踪。个人承担所辖工序任务，未声明负责整线交付。','演示资料通过测量条件复核、工装状态比较和对照验证分析尺寸波动；结论保留适用条件与未验证假设。','页面顶部“预览两页演示简历”可打开相同风格的HTML简历。PDF由本地打印生成；当前页面没有连接真实下载服务。'];
  document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>{
    if(d.approved_view){const q=document.getElementById('ai-question');q.value=b.textContent.trim();q.focus();}
    else document.getElementById('answer').textContent='【固定演示回答】'+answers[Number(b.dataset.question)];
  }));
  if(d.approved_view){
    document.querySelector('h1').innerHTML=d.english.map(e).join('<br>');
    document.querySelector('.summary').textContent='通过项目、职责与工程行动了解职业经历。';
    document.querySelector('.english').textContent='PROFESSIONAL EXPERIENCE';
    document.querySelector('.text-link').removeAttribute('href');
    document.querySelector('.text-link').textContent='简历附件需单独审核后发布';
    document.querySelector('.assistant .demo-label').textContent=d.synthetic?'虚构资料 · 已连接本地问答接口':'基于获准公开的职业资料';
    if(!d.synthetic){
      document.querySelectorAll('.demo-label').forEach(n=>{if(!n.closest('.assistant'))n.textContent='职业资料';});
      document.querySelector('.eyebrow span:last-child').textContent='CAREER PORTFOLIO';
      document.querySelector('.site-footer span:last-child').textContent='基于本人获准公开的资料';
      document.querySelectorAll('.deliverable span').forEach(n=>n.textContent='PROJECT EVIDENCE');
      document.querySelector('#project-dialog .kicker').textContent='PROJECT DETAILS';
    }
    const panel=document.querySelector('.assistant-panel');
    panel.innerHTML='<form id="ai-form"><label for="ai-question">你的问题</label><textarea id="ai-question" maxlength="1600" rows="4" required placeholder="例如：有哪些装配工艺验证经验？"></textarea><button type="submit">发送问题</button></form><div class="answer" role="status" aria-live="polite" id="live-answer">输入问题，查询获准公开的职业资料。</div>';
    const form=document.getElementById('ai-form'),question=document.getElementById('ai-question'),button=form.querySelector('button'),answer=document.getElementById('live-answer');
    form.addEventListener('submit',async event=>{
      event.preventDefault();if(button.disabled||!question.value.trim())return;
      button.disabled=true;answer.textContent='正在查询…';
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),35000);
      try{
        const response=await fetch('/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:question.value.trim()}),signal:controller.signal});
        const value=await response.json();
        if(response.status===403)throw Error('当前网站来源未获授权，请检查服务来源配置。');
        if(response.status===429)throw Error('请求较频繁，请稍后重试。');
        if(!response.ok)throw Error('问答服务暂时不可用，请稍后重试。');
        answer.textContent=(value.mode==='mock'?'【本地检索演示】':'')+value.answer;
      }catch(error){answer.textContent=error.name==='AbortError'?'请求超时，请稍后重试。':error.message;}
      finally{clearTimeout(timer);button.disabled=false;}
    });
  }
})();
