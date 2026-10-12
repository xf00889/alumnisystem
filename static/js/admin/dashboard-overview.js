/* Custom admin dashboard analytics. Chart.js 4.4.1 is loaded once by base.html. */
(function () {
  'use strict';
  const root = document.getElementById('adminDashboard');
  if (!root) return;
  const analyticsUrl = root.dataset.analyticsUrl;
  const collegeUrl = root.dataset.collegeUrl;
  const charts = new Map();
  const specs = {
    userRegistration: { label: 'New users', columns: ['Date', 'New users'] },
    donation: { label: 'Completed donations (₱)', columns: ['Date', 'Verified donations (₱)'] },
    alumniYear: { label: 'Alumni records', columns: ['Graduation year', 'Alumni'] },
    activity: { label: 'Engagement', columns: ['Date', 'Event RSVPs', 'Job applications'] },
    college: { label: 'Alumni records', columns: ['College', 'Alumni'] }
  };
  let currentPeriod = 30;
  let analyticsRequest = null;
  let collegeRequest = null;
  let requestId = 0;
  const palette = { primary:'#2b3c6b', accent:'#5775ab', second:'#ae8a57', text:'#64748b', grid:'#edf1f6' };
  // Restrained, distinguishable bar colors. Values and labels remain available in the data tables.
  const barColors = ['#2B3C6B', '#437E91', '#B18447', '#6D62A4', '#BF695B', '#398569', '#9B5B83', '#647F9A'];
  if (typeof window.Chart === 'function') {
    window.Chart.defaults.font.family = "'Poppins', -apple-system, BlinkMacSystemFont, sans-serif";
  }
  function el(id) { return document.getElementById(id); }
  function safeList(value) { return Array.isArray(value) ? value : []; }
  function number(value) { const n=Number(value);return Number.isFinite(n)?n:0; }
  function money(value) { return '₱' + number(value).toLocaleString('en-PH',{maximumFractionDigits:2}); }
  function dateLabel(value) {
    if (typeof value !== 'string') return String(value ?? '');
    const parts=value.split('-');
    if (parts.length===3) {
      const d=new Date(Date.UTC(Number(parts[0]),Number(parts[1])-1,Number(parts[2])));
      if (!isNaN(d.getTime())) return d.toLocaleDateString('en-US',{timeZone:'UTC',month:'short',day:'numeric'});
    }
    return value;
  }
  function showStatus(prefix, type, message) {
    const loading=el(prefix+'Loading'),empty=el(prefix+'NoData');
    if (loading) loading.hidden=type!=='loading';
    if (empty) { empty.hidden=type!=='empty';if(message) empty.textContent=message; }
    const canvas=el(prefix+'Chart');
    if (canvas) canvas.hidden=type!=='ready';
  }
  function showError(message) {
    const node=el('dashboardError');
    if(node){node.textContent=message;node.hidden=false;}
  }
  function clearError(){ const node=el('dashboardError');if(node) node.hidden=true; }
  function gridOptions(isCurrency=false, horizontal=false) {
    const axis={ticks:{color:palette.text,font:{size:11},maxTicksLimit:7},border:{display:false},grid:{color:palette.grid}};
    return {
      responsive:true, maintainAspectRatio:false, animation:{duration:200},
      interaction:{intersect:false,mode:'index'},
      plugins:{legend:{display:false},tooltip:{backgroundColor:'#203158',padding:11,cornerRadius:8,callbacks:{label(ctx){ const value=horizontal?ctx.parsed.x:ctx.parsed.y;return `${ctx.dataset.label}: ${isCurrency?money(value):number(value).toLocaleString()}`;}}}},
      scales:{x:{...axis,grid:{display:false}},y:{...axis,beginAtZero:!horizontal,ticks:{...axis.ticks,precision:horizontal?undefined:0}}}
    };
  }
  function renderTable(prefix, rows, columns) {
    const head=el(prefix+'TableHead'),body=el(prefix+'TableBody');
    if(!head||!body)return;
    head.replaceChildren();body.replaceChildren();
    const tr=document.createElement('tr');
    columns.forEach(c=>{const th=document.createElement('th');th.scope='col';th.textContent=c;tr.appendChild(th);});head.appendChild(tr);
    rows.forEach(row=>{const line=document.createElement('tr');row.forEach((cell,i)=>{const td=document.createElement('td');td.textContent=String(cell??'');line.appendChild(td);});body.appendChild(line);});
  }
  function draw(prefix,type,labels,datasets,rows,opts={}) {
    const canvas=el(prefix+'Chart');if(!canvas)return;
    renderTable(prefix,rows,specs[prefix].columns);
    if(charts.has(prefix)){charts.get(prefix).destroy();charts.delete(prefix);}
    if(!labels.length){showStatus(prefix,'empty','No records for this period.');return;}
    if(typeof window.Chart!=='function'){
      showStatus(prefix,'empty','Chart.js could not load. Use the data table below.');
      showError('The chart library is unavailable. The data tables are still accessible.');return;
    }
    showStatus(prefix,'ready');
    const options=gridOptions(Boolean(opts.currency),Boolean(opts.horizontal));
    if(opts.horizontal){options.indexAxis='y';options.scales.x.beginAtZero=true;options.scales.x.grid={color:palette.grid};options.scales.y.grid={display:false};options.scales.y.ticks={...options.scales.y.ticks,callback:function(value){const label=String(this.getLabelForValue(value));return label.length>24?label.slice(0,23)+'…':label;}};}
    if(type==='line') {options.elements={line:{tension:.28,borderWidth:2.5},point:{radius:0,hoverRadius:4,hitRadius:10}};}
    if(prefix==='activity')options.plugins.legend={display:true,position:'bottom',labels:{color:palette.text,usePointStyle:true,boxWidth:10,font:{size:11}}};
    if(prefix==='alumniYear')options.scales.x.ticks.maxRotation=45;
    charts.set(prefix,new window.Chart(canvas.getContext('2d'),{type,data:{labels,datasets},options}));
  }
  function series(label,values,color,fill=false){return {label,data:values,borderColor:color,backgroundColor:fill?color+'20':color,fill,borderRadius:4,maxBarThickness:32};}
  function coloredBars(label,values){
    const colors=values.map((_,index)=>barColors[index % barColors.length]);
    return {label,data:values,backgroundColor:colors,borderColor:colors,borderRadius:4,maxBarThickness:32};
  }
  function updateAnalytics(payload) {
    const registrations=safeList(payload.user_registrations),donations=safeList(payload.donations);
    const years=safeList(payload.alumni_by_year).filter(r=>r.graduation_year!=null).sort((a,b)=>number(a.graduation_year)-number(b.graduation_year));
    const rsvps=safeList(payload.event_rsvps),applications=safeList(payload.job_applications);
    draw('userRegistration','line',registrations.map(x=>dateLabel(x.date)),[series('New users',registrations.map(x=>number(x.count)),palette.primary,true)],registrations.map(x=>[x.date,number(x.count)]));
    draw('donation','line',donations.map(x=>dateLabel(x.date)),[series('Completed donations',donations.map(x=>number(x.amount)),palette.accent,true)],donations.map(x=>[x.date,money(x.amount)]),{currency:true});
    draw('alumniYear','bar',years.map(x=>String(x.graduation_year)),[coloredBars('Alumni',years.map(x=>number(x.count)))],years.map(x=>[x.graduation_year,number(x.count)]));
    const byDate=new Map();
    for(const r of rsvps){byDate.set(String(r.date),{rsvp:number(r.count),jobs:0});}
    for(const r of applications){const date=String(r.date);const curr=byDate.get(date)||{rsvp:0,jobs:0};curr.jobs=number(r.count);byDate.set(date,curr);}
    const points=[...byDate.entries()].sort((a,b)=>a[0].localeCompare(b[0]));
    draw('activity','line',points.map(x=>dateLabel(x[0])),[
      series('Event RSVPs',points.map(x=>x[1].rsvp),palette.primary),
      series('Job applications',points.map(x=>x[1].jobs),palette.second)
    ],points.map(x=>[x[0],x[1].rsvp,x[1].jobs]));
  }
  async function loadAnalytics(days) {
    if(analyticsRequest)analyticsRequest.abort();
    const controller=new AbortController();analyticsRequest=controller;
    const token=++requestId;
    ['userRegistration','donation','alumniYear','activity'].forEach(p=>showStatus(p,'loading'));
    clearError();
    try {
      const url=new URL(analyticsUrl,window.location.href);url.searchParams.set('days',String(days));
      const resp=await fetch(url.toString(),{credentials:'same-origin',signal:controller.signal,headers:{Accept:'application/json'}});
      if(!resp.ok)throw new Error(`HTTP ${resp.status}`);
      const data=await resp.json();
      if(token!==requestId)return;
      updateAnalytics(data);
    }catch(err){if(err.name==='AbortError')return;
      ['userRegistration','donation','alumniYear','activity'].forEach(p=>showStatus(p,'empty','Could not load chart data. Retry using the period selector.'));
      showError('Dashboard trends could not be loaded. Try again or check your connection.');
      console.error('Dashboard analytics request failed',err);
    }
  }
  async function loadColleges() {
    if(collegeRequest)collegeRequest.abort();
    const controller=new AbortController();collegeRequest=controller;
    showStatus('college','loading');
    try {
      const resp=await fetch(collegeUrl,{credentials:'same-origin',signal:controller.signal,headers:{Accept:'application/json'}});
      if(!resp.ok)throw new Error(`HTTP ${resp.status}`);
      const result=await resp.json();if(!result.success)throw new Error('Unexpected college response');
      const data=safeList(result.data);
      draw('college','bar',data.map(x=>String(x.college_name??'Unspecified')),[coloredBars('Alumni',data.map(x=>number(x.count)))],data.map(x=>[x.college_name??'Unspecified',number(x.count)]),{horizontal:true});
      if(el('totalColleges'))el('totalColleges').textContent=String(data.length);
      if(el('largestCollege'))el('largestCollege').textContent=data.length?`${number(data[0].count).toLocaleString()} alumni`:'—';
      if(el('averagePerCollege'))el('averagePerCollege').textContent=data.length?`${Math.round(number(result.total_alumni)/data.length).toLocaleString()} alumni`:'—';
    }catch(err){if(err.name==='AbortError')return;
      showStatus('college','empty','College information is unavailable.');console.error('College data request failed',err);
    }
  }
  document.querySelectorAll('.admin-overview .time-btn').forEach(button=>button.addEventListener('click',()=>{
    const requested=Number(button.dataset.period);if(![7,30,90].includes(requested))return;
    currentPeriod=requested;
    root.querySelectorAll('.time-btn').forEach(b=>{const active=b===button;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
    loadAnalytics(currentPeriod);
  }));
  window.showBulkExportModal=function(){const url=root.dataset.bulkExportUrl;if(url)window.location.assign(url);};
  window.handleSingleExport=function(url,modelName,format){
    // Browser download is requested via the existing export endpoint. Never claim success before completion.
    if(typeof url!=='string'||!url.startsWith('/'))return;
    const a=document.createElement('a');a.href=url;a.rel='noopener';document.body.appendChild(a);a.click();a.remove();
  };
  if(typeof window.Chart!=='function'){
    showError('Chart.js is not available. Check the shared Chart.js 4.4.1 script in base.html.');
  }
  loadAnalytics(currentPeriod);loadColleges();
  // Refresh analytics only when the tab is visible. Export and API routes are unchanged.
  const timer=window.setInterval(()=>{if(!document.hidden)loadAnalytics(currentPeriod);},300000);
  window.addEventListener('pagehide',()=>{window.clearInterval(timer);if(analyticsRequest)analyticsRequest.abort();if(collegeRequest)collegeRequest.abort();charts.forEach(c=>c.destroy());charts.clear();},{once:true});
})();
