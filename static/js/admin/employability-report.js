(function () {
  'use strict';
  const quarterly = document.getElementById('employability-period-totals');
  const groups = document.getElementById('employability-groups');
  if (!quarterly || !groups || typeof window.Chart === 'undefined') return;
  const totals = JSON.parse(quarterly.textContent);
  const rows = JSON.parse(groups.textContent);
  const periodLabels = document.getElementById('employability-period-labels');
  if (!periodLabels) return;
  const labels = JSON.parse(periodLabels.textContent);
  const common = {responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{precision:0}}}};
  const quarterCanvas = document.getElementById('employabilityQuarterChart');
  if (quarterCanvas) new window.Chart(quarterCanvas,{
    type:'bar',data:{labels,datasets:[{label:'Dated current-job starts',data:totals,backgroundColor:['#172541','#36547e','#a58454','#c39b5e'],borderRadius:5}]},options:common
  });
  const groupCanvas = document.getElementById('employabilityGroupChart');
  if (groupCanvas) new window.Chart(groupCanvas,{
    type:'bar',data:{labels:rows.map(r=>r.name),datasets:[{label:'Dated starts in selected period',data:rows.map(r=>r.total_hired),backgroundColor:'#2b3c6b',borderRadius:4}]},
    options:{...common,indexAxis:'y',scales:{x:{beginAtZero:true,ticks:{precision:0}},y:{ticks:{autoSkip:false}}}}
  });
})();
