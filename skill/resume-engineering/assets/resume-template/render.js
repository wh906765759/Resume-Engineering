(() => {
  'use strict';
  const d = window.RESUME_DATA || window.RESUME_DEMO;
  if (!d || (!d.approved_view && d.synthetic !== true)) throw Error('Approved projection or synthetic fixture required.');
  const e = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const section = (title, css, body) => `<section class="section ${css}"><h2>${e(title)}</h2>${body}</section>`;
  const heading = (title, period, cls='entry-heading') => `<header class="${cls}"><h3>${e(title)}</h3><time>${e(period)}</time></header>`;
  const footer = n => `<footer class="page-footer"><span>${d.synthetic?'Resume Engineering · 虚构演示 / 不用于投递':e(d.name)+' · 职业简历'}</span><span>${n} / 2</span></footer>`;
  const identity = `<header class="identity"><div class="identity-main"><p class="eyebrow">ADVANCED MANUFACTURING · SYNTHETIC DEMO</p><h1>${e(d.name)}</h1><p class="position">${e(d.positioning)}</p><p class="ats-line">${e(d.englishPositioning)}</p><p class="contact">${e(d.contact)}</p></div><figure class="avatar-frame"><img src="../shared/portrait-placeholder.svg" alt="抽象头像占位图，非真实人物"></figure></header><p class="privacy-note">SYNTHETIC DEMO｜所有经历均为虚构测试资料</p>`;
  const capabilities = d.capabilities.map((c,i)=>`<article class="capability ${i<2?'capability-primary':''}"><h3>${e(c.title)} <span>${e(c.en)}</span></h3>${c.lines.map(p=>`<p>${e(p)}</p>`).join('')}</article>`).join('');
  const work=d.work.map((w,i)=>`<article class="experience ${i?'experience-secondary':''}">${heading(w.company+'｜'+w.role,w.period)}<ul>${w.bullets.map(b=>`<li>${e(b)}</li>`).join('')}</ul></article>`).join('');
  const projects=d.projects.map((p,i)=>`<article class="project ${i<2?'project-featured':'project-secondary'}">${heading(p.title,p.period,'project-heading')}<p><strong>背景：</strong>${e(p.background)} <strong>职责：</strong>${e(p.role)} <strong>行动：</strong>${e(p.action)} <strong>成果：</strong>${e(p.result)}</p></article>`).join('');
  const education=d.education.map(w=>`<article class="education-entry">${heading(w.school+'｜'+w.degree,w.period)}${w.description?`<p>${e(w.description)}</p>`:''}</article>`).join('')+`<article class="education-entry"><h3>材料分析与实验基础</h3><p>${e(d.research)}</p></article>`;
  document.getElementById('resume').innerHTML=`<article class="page page-one">${identity}${section('个人简介','summary-section',`<p>${e(d.summary)}</p>`)}${section('核心能力','capability-section',`<div class="capability-grid">${capabilities}</div>`)}${section('工作经历','experience-section',work)}${footer(1)}</article><article class="page page-two"><header class="continuation-header"><span>${e(d.name)} · 虚构演示</span><span>工艺开发 / 产品导入</span></header>${section('代表性工程项目与制造成果','projects-section',projects)}${section('自我评价','self-evaluation-section',`<p>${e(d.evaluation)}</p>`)}${section('专业技能','skills-section',`<dl class="skills-list">${d.skills.map(s=>`<div><dt>${e(s[0])}</dt><dd>${e(s[1])}</dd></div>`).join('')}</dl>`)}${section('教育经历','education-section',education)}${footer(2)}</article>`;
  if(!d.synthetic){
    document.querySelector('.eyebrow').textContent='PROFESSIONAL PROFILE';
    document.querySelector('.privacy-note').textContent='定向投递简历';
    document.querySelector('.continuation-header span').textContent=d.name;
    document.querySelector('.continuation-header span:last-child').textContent=d.positioning;
  }
})();
