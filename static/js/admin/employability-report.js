(function () {
  'use strict';
  const quarterly = document.getElementById('employability-quarters');
  const groups = document.getElementById('employability-groups');
  if (!quarterly || !groups || typeof window.Chart === 'undefined') return;
  const totals = JSON.parse(quarterly.textContent);
  const rows = JSON.parse(groups.textContent);
  const common = {responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{precision:0}}}};
  const quarterCanvas = document.getElementById('employabilityQuarterChart');
  if (quarterCanvas) new window.Chart(quarterCanvas,{
    type:'bar',data:{labels:['Q1','Q2','Q3','Q4'],datasets:[{label:'Recorded hires',data:totals,backgroundColor:['#172541','#36547e','#a58454','#c39b5e'],borderRadius:5}]},options:common
  });
  const groupCanvas = document.getElementById('employabilityGroupChart');
  if (groupCanvas) new window.Chart(groupCanvas,{
    type:'bar',data:{labels:rows.map(r=>r.name),datasets:[{label:'Recorded hires',data:rows.map(r=>r.total_hired),backgroundColor:'#b18a50',borderRadius:4}]},
    options:{...common,indexAxis:'y',scales:{x:{beginAtZero:true,ticks:{precision:0}},y:{ticks:{autoSkip:false}}}}
  });
})();
