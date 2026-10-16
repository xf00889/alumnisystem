/* Scoped Chart.js workspaces. All input is DOM JSON-script data, never executable interpolation. */
(() => {
  if (typeof Chart === 'undefined') return;
  const palette = { navy:'#2b3e70', gold:'#c9a66a', teal:'#13a5af', ink:'#1b2b48' };
  const getData = id => {const node=document.getElementById(id); if(!node)return null; try{return JSON.parse(node.textContent)}catch{return null}};
  const config = (kind, data) => ({type:kind,data:{labels:data.labels,datasets:[{data:data.values,label:'Total',backgroundColor:kind==='line'?palette.gold:[palette.navy,palette.gold,palette.teal],borderColor:palette.navy,borderWidth:kind==='line'?2:0,fill:kind==='line',tension:.3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:kind==='doughnut'}},scales:kind==='doughnut'?{}:{y:{beginAtZero:true,ticks:{precision:0}}}}});
  [['hrApplicationChart','hr-applications-data','line'],['hrJobSourcesChart','hr-sources-data','doughnut'],['coordinatorCampusChart','coordinator-campus-data','bar'],['coordinatorActivityChart','coordinator-activity-data','doughnut']].forEach(([canvasId,dataId,type]) => {const canvas=document.getElementById(canvasId), data=getData(dataId); if(canvas&&data) new Chart(canvas,config(type,data));});
})();
