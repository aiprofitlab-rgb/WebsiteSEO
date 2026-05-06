
/* ─── Data ─── */
const CHANNELS = [
  {name:'إعلانات جوجل',  icon:'G',  cpc:2.5,  reach:15000, color:'#4b9cf7'},
  {name:'إعلانات ميتا',    icon:'M',  cpc:1.8,  reach:22000, color:'#7c6fff'},
  {name:'لينكد إن',    icon:'Li', cpc:6.0,  reach:5000,  color:'#2dd4bf'},
  {name:'البريد الإلكتروني',       icon:'@',  cpc:0.3,  reach:12000, color:'#1ecc8b'},
  {name:'تحسين محركات البحث', icon:'S',  cpc:0.5,  reach:8000,  color:'#f5a623'},
  {name:'المؤثرون',  icon:'I',  cpc:4.0,  reach:18000, color:'#d45fa0'},
  {name:'يوتيوب',     icon:'▶',  cpc:3.2,  reach:10000, color:'#f05c5c'},
  {name:'الرسائل النصية',         icon:'~',  cpc:0.8,  reach:6000,  color:'#a78bfa'},
];

const SEGMENTS = [
  {name:'المتبنون الأوائل',  color:'#7c6fff', pct:22},
  {name:'الباحثون عن القيمة',   color:'#1ecc8b', pct:35},
  {name:'المخلصون للعلامة', color:'#f5a623', pct:18},
  {name:'المشترون الاندفاعيون',  color:'#d45fa0', pct:15},
  {name:'الباحثون',     color:'#4b9cf7', pct:10},
];

const PAGE_META = {
  setup:    {title:'إعداد الحملة',    sub:'ضبط معاملات الحملة'},
  channels: {title:'اختيار القنوات', sub:'اختر وخصص قنوات التسويق'},
  audience: {title:'استهداف الجمهور',sub:'تحديد حجم جمهورك المستهدف'},
  funnel:   {title:'مسار التحويل', sub:'نمذجة أداء مسار التحويل بالكامل'},
  ab:       {title:'اختبار أ/ب',       sub:'محاكاة ومقارنة النسخ الإبداعية'},
  results:  {title:'نتائج الحملة',  sub:'مراجعة الأداء المتوقع والتوصيات'},
};

let selectedChannels = new Set([0,1,3]);
let channelChart = null, resultsChart = null, contribChart = null;

/* ─── Tab switching ─── */
function switchTab(t, navEl) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('tab-'+t).classList.add('active');
  if(navEl) navEl.classList.add('active');
  document.getElementById('page-title').textContent = PAGE_META[t].title;
  document.getElementById('page-sub').textContent   = PAGE_META[t].sub;
  if(t==='channels') initChannels();
  if(t==='funnel')   updateFunnel();
  if(t==='results')  initResults();
  if(t==='ab')       updateAB();
  if(t==='audience') updateAudience();
}

/* ─── Helpers ─── */
const getBudget   = () => parseInt(document.getElementById('budget').value)   || 10000;
const getDuration = () => parseInt(document.getElementById('duration').value) || 30;
const getDealSize = () => parseInt(document.getElementById('dealsize').value) || 200;
const fmt = n => n.toLocaleString();

/* ─── Setup ─── */
function updateSetup() {
  const b = getBudget(), d = getDuration(), deal = getDealSize();
  document.getElementById('budget-val').textContent = '$'+fmt(b);
  document.getElementById('dur-val').textContent    = d+' أيام';
  document.getElementById('deal-val').textContent   = '$'+deal;

  const leads = Math.round(b / 8);
  const conv  = Math.round(leads * 0.15);
  const rev   = conv * deal;
  const roi   = Math.round((rev - b) / b * 100);

  document.getElementById('m-budget').textContent   = '$'+fmt(b);
  document.getElementById('m-duration').textContent = d+'d';
  document.getElementById('m-leads').textContent    = fmt(leads);
  document.getElementById('m-rev').textContent      = '$'+fmt(rev);
  document.getElementById('m-roi').textContent      = roi+'%';

  const bPct = Math.min(95, Math.round(b / 100000 * 100));
  document.getElementById('ph-budget').style.width  = bPct+'%';
  document.getElementById('ph-budget-lbl').textContent = b > 5000 ? 'مناسبة للمدة المختارة' : 'فكر في زيادة الميزانية';

  const tPct = Math.min(95, Math.round(d / 90 * 100));
  document.getElementById('ph-time').style.width  = tPct+'%';
  document.getElementById('ph-time-lbl').textContent = d > 21 ? 'مدة مناسبة for results' : 'قصيرة — فكر في التمديد';

  const rPct = Math.min(95, Math.max(5, Math.round(roi / 4)));
  document.getElementById('ph-roi').style.width  = rPct+'%';
  document.getElementById('ph-roi-lbl').textContent = roi > 150 ? 'إمكانية ممتازة' : roi > 50 ? 'إمكانية قوية' : roi > 0 ? 'هامشي — راجع المدخلات' : 'في خطر — عدّل الاستراتيجية';
}

/* ─── Channels ─── */
function initChannels() {
  const grid = document.getElementById('channel-grid');
  grid.innerHTML = '';
  CHANNELS.forEach((ch, i) => {
    const d = document.createElement('div');
    d.className = 'channel-card' + (selectedChannels.has(i) ? ' selected' : '');
    d.innerHTML = `<div class="channel-icon" style="color:${ch.color}">${ch.icon}</div>
      <div class="channel-name">${ch.name}</div>
      <div class="channel-meta">CPC $${ch.cpc.toFixed(2)} · Reach ${fmt(ch.reach)}</div>
      <div class="ch-check">✓</div>`;
    d.onclick = () => {
      selectedChannels.has(i) ? selectedChannels.delete(i) : selectedChannels.add(i);
      initChannels();
    };
    grid.appendChild(d);
  });
  document.getElementById('ch-count').textContent = selectedChannels.size + ' مختارة';
  updateChannelAlloc();
  drawChannelChart();
}

function updateChannelAlloc() {
  const b = getBudget();
  const sel = [...selectedChannels];
  const alloc = document.getElementById('channel-alloc');
  if (!sel.length) { alloc.innerHTML = '<div style="color:var(--text3);font-size:13px">No channels مختارة.</div>'; return; }
  const share = Math.round(b / sel.length);
  alloc.innerHTML = sel.map(i => {
    const ch = CHANNELS[i];
    const pct = Math.round(100 / sel.length);
    return `<div class="alloc-row">
      <div class="alloc-name">${ch.name}</div>
      <div class="alloc-bar-wrap"><div class="alloc-bar" style="width:${pct}%;background:${ch.color}"></div></div>
      <div class="alloc-amt">$${fmt(share)}</div>
    </div>`;
  }).join('');
}

function drawChannelChart() {
  const ctx = document.getElementById('channel-chart');
  if (!ctx) return;
  if (channelChart) { channelChart.destroy(); channelChart = null; }
  const sel = [...selectedChannels];
  if (!sel.length) return;
  const b = getBudget(), share = b / sel.length;
  const labels = sel.map(i => CHANNELS[i].name);
  const data   = sel.map(i => Math.round(share / CHANNELS[i].cpc));
  const colors = sel.map(i => CHANNELS[i].color);
  // legend
  document.getElementById('ch-legend').innerHTML = sel.map(i =>
    `<div class="legend-item"><div class="legend-swatch" style="background:${CHANNELS[i].color}"></div>${CHANNELS[i].name}</div>`
  ).join('');
  channelChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Est. reach', data, backgroundColor: colors, borderRadius: 6 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#9999b0', font: { family: 'DM Sans' } }, grid: { color: 'rgba(255,255,255,.04)' } },
        y: { beginAtZero: true, ticks: { color: '#9999b0', font: { family: 'DM Sans' }, callback: v => fmt(v) }, grid: { color: 'rgba(255,255,255,.04)' } }
      }
    }
  });
}

/* ─── Audience ─── */
function updateAudience() {
  const amin = parseInt(document.getElementById('age-min').value) || 25;
  const amax = Math.max(amin + 1, parseInt(document.getElementById('age-max').value) || 44);
  document.getElementById('age-val').textContent = amin + ' – ' + amax;
  const geoM   = { Global: 10, National: 3, Regional: 0.8, 'Local (city)': 0.2 };
  const incM   = { All: 1, 'Under $50k': 0.8, '$50k–$100k': 0.7, '$100k–$200k': 0.4, '$200k+': 0.15 };
  const indM   = { 'All industries': 1, Technology: 0.4, Healthcare: 0.35, Finance: 0.3, Retail: 0.6, Education: 0.25 };
  const geo    = document.getElementById('geo').value;
  const inc    = document.getElementById('income').value;
  const ind    = document.getElementById('industry').value;
  const ageR   = amax - amin;
  const size   = Math.round((geoM[geo] || 3) * (ageR / 10) * (incM[inc] || 0.7) * (indM[ind] || 1) * 100000) * 10;
  const reach  = Math.round(getBudget() / 4);
  const pct    = Math.round(reach / size * 1000) / 10;
  const daily  = Math.round(reach / getDuration());
  document.getElementById('aud-size').textContent  = (size / 1000000).toFixed(1) + 'M';
  document.getElementById('aud-reach').textContent = fmt(reach);
  document.getElementById('aud-pct').textContent   = pct + '% من الجمهور';
  document.getElementById('aud-daily').textContent = fmt(daily);

  document.getElementById('segments-wrap').innerHTML =
    SEGMENTS.map(s => `<span class="seg-pill" style="background:${s.color}22;border-color:${s.color};color:${s.color}">${s.name} · ${s.pct}%</span>`).join('');
  document.getElementById('seg-stats').innerHTML =
    SEGMENTS.slice(0, 3).map(s => `
      <div class="stat-block">
        <div style="font-size:11px;color:${s.color};font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.06em">${s.name}</div>
        <div class="stat-num" style="color:var(--text)">${fmt(Math.round(reach * s.pct / 100))}</div>
        <div class="stat-lbl">وصول متوقع</div>
      </div>`).join('');
}

/* ─── Funnel ─── */
function updateFunnel() {
  const lpQ    = parseInt(document.getElementById('lp-q').value)    || 3;
  const emSeq  = parseInt(document.getElementById('em-seq').value)  || 3;
  const offerS = parseInt(document.getElementById('offer-s').value) || 3;
  const ret    = parseInt(document.getElementById('retarget').value)|| 0;
  const lpL    = ['ضعيف','مقبول','جيد','ممتاز','رائع'];
  const ofL    = ['ضعيف','دون المتوسط','متوسط','قوي','مقنع'];
  document.getElementById('lp-val').textContent    = lpL[lpQ - 1];
  document.getElementById('em-val').textContent    = emSeq + ' email' + (emSeq > 1 ? 's' : '');
  document.getElementById('offer-val').textContent = ofL[offerS - 1];
  document.getElementById('ret-val').textContent   = ret ? 'مفعّل' : 'معطّل';

  const reach     = Math.round(getBudget() / 4);
  const ctr       = 0.02 + lpQ * 0.008;
  const clicks    = Math.round(reach * ctr);
  const lpConv    = 0.1 + lpQ * 0.04 + offerS * 0.02;
  const leads     = Math.round(clicks * lpConv);
  const nurtureR  = Math.min(0.75, 0.2 + emSeq * 0.05);
  const nurtured  = Math.round(leads * nurtureR);
  const retBonus  = ret ? 1.25 : 1;
  const conv      = Math.round(nurtured * 0.2 * retBonus);

  const steps = [
    {label:'الجمهور الوصول', count:reach,   color:'#7c6fff'},
    {label:'النقرات',           count:clicks,  color:'#4b9cf7'},
    {label:'العملاء المحتملون',   count:leads,   color:'#1ecc8b'},
    {label:'المرعيون',         count:nurtured,color:'#f5a623'},
    {label:'التحويلات',      count:conv,    color:'#f05c5c'},
  ];
  const maxC = steps[0].count || 1;
  document.getElementById('funnel-steps').innerHTML = steps.map((s, idx) => {
    const prev = idx === 0 ? maxC : steps[idx - 1].count || 1;
    const drop = idx === 0 ? 100 : Math.round(s.count / prev * 100);
    return `<div class="funnel-step">
      <div class="funnel-label">${s.label}</div>
      <div class="funnel-bar-wrap">
        <div class="funnel-bar" style="width:${Math.max(2, Math.round(s.count / maxC * 100))}%;background:${s.color}">
          ${Math.round(s.count / maxC * 100) > 15 ? Math.round(s.count / maxC * 100) + '%' : ''}
        </div>
      </div>
      <div class="funnel-count">${fmt(s.count)}</div>
      <div class="funnel-pct">${idx === 0 ? '' : drop + '%'}</div>
    </div>`;
  }).join('');

  const rates = [
    {label:'معدل النقر',     val:(ctr * 100).toFixed(1) + '%'},
    {label:'معدل استحواذ العملاء',      val:(lpConv * 100).toFixed(1) + '%'},
    {label:'معدل الرعاية',           val:(nurtureR * 100).toFixed(0) + '%'},
    {label:'معدل إغلاق المبيعات',       val:((0.2 * retBonus) * 100).toFixed(0) + '%'},
    {label:'معدل التحويل الإجمالي',     val:reach > 0 ? (conv / reach * 100).toFixed(2) + '%' : '0%'},
  ];
  document.getElementById('conv-rates').innerHTML = rates.map(r =>
    `<div class="rate-row"><span style="color:var(--text2)">${r.label}</span><span style="font-weight:600">${r.val}</span></div>`
  ).join('');

  const d = getDuration();
  const tl = [
    {day:0,                       event:'إطلاق الحملة — تبدأ الإعلانات على جميع القنوات',          color:'#7c6fff'},
    {day:Math.round(d * 0.15),    event:'أول عملاء محتملين، تبدأ سلسلة البريد الإلكتروني',           color:'#1ecc8b'},
    {day:Math.round(d * 0.30),    event:'نتائج اختبار أ/ب متاحة — تفعيل النسخة الفائزة',           color:'#f5a623'},
    {day:Math.round(d * 0.50),    event:'مراجعة منتصف الحملة — إعادة توزيع الميزانية',       color:'#4b9cf7'},
    {day:Math.round(d * 0.75),    event:'تفعيل موجة إعادة الاستهداف للزوار غير المحولين',           color:'#d45fa0'},
    {day:d,                       event:'إغلاق الحملة — حساب وتقرير التحويلات النهائية',       color:'#f05c5c'},
  ];
  document.getElementById('timeline').innerHTML = tl.map((t, idx) => `
    <div class="tl-item">
      <div class="tl-left">
        <div class="tl-dot" style="background:${t.color}"></div>
        ${idx < tl.length - 1 ? '<div class="tl-line"></div>' : ''}
      </div>
      <div>
        <div class="tl-date">Day ${t.day}</div>
        <div class="tl-event">${t.event}</div>
      </div>
    </div>`).join('');
}

/* ─── A/B Testing ─── */
function updateAB() {
  const v      = document.getElementById('ab-var').value;
  const split  = parseInt(document.getElementById('ab-split').value) || 50;
  const dur    = parseInt(document.getElementById('ab-dur-in').value) || 14;
  document.getElementById('ab-split-val').textContent = split + ' / ' + (100 - split);
  document.getElementById('ab-dur-val').textContent   = dur + ' أيام';

  const sample  = Math.round(getBudget() / 3 * dur / 14);
  const conf    = Math.min(99, Math.round(68 + dur * 1.5 + split * 0.2));
  const uplift  = Math.round(10 + split * 0.3 + dur * 0.4);

  document.getElementById('ab-conf').textContent   = conf + '%';
  document.getElementById('ab-sample').textContent = fmt(sample);
  document.getElementById('ab-dur').textContent    = dur + 'd';
  document.getElementById('ab-uplift').textContent = '+' + uplift + '%';

  const aM = {CTR:'2.1%', CVR:'3.4%', CPL:'$12.40', ROAS:'2.1x'};
  const bM = {
    CTR:  (2.1 * (1 + uplift / 200)).toFixed(1) + '%',
    CVR:  (3.4 * (1 + uplift / 200)).toFixed(1) + '%',
    CPL:  '$' + (12.4 / (1 + uplift / 200)).toFixed(2),
    ROAS: (2.1 * (1 + uplift / 200)).toFixed(1) + 'x',
  };
  const renderStats = m => Object.entries(m).map(([k, v]) => `
    <div style="margin-bottom:10px">
      <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.06em">${k}</div>
      <div style="font-size:20px;font-weight:600">${v}</div>
      <div class="score-bar"><div class="score-fill" style="width:${Math.min(95, Math.round(parseFloat(v) * 20))}%"></div></div>
    </div>`).join('');
  document.getElementById('ab-a-stats').innerHTML = renderStats(aM);
  document.getElementById('ab-b-stats').innerHTML = renderStats(bM);

  const entries = [
    `[اليوم 01]  بدء الاختبار — المتغير: ${v}`,
    `[اليوم 03]  النسخة ب تُظهر تحسناً +${Math.round(uplift * 0.4)}% في معدل النقر`,
    `[اليوم 07]  الثقة الإحصائية وصلت ${Math.round(conf * 0.7)}%`,
    `[Day ${String(dur).padStart(2,'0')}]  انتهى الاختبار — النسخة ب فائزة بثقة ${conf}%`,
    `[تلقائي]  تم تطبيق النسخة ب على 100% من الزيارات`,
  ];
  document.getElementById('ab-log').innerHTML = entries.map(e => `<div class="log-line">${e}</div>`).join('');
}

/* ─── Results ─── */
function initResults() {
  const b = getBudget(), d = getDuration(), deal = getDealSize();
  const leads = Math.round(b / 8);
  const conv  = Math.round(leads * 0.15);
  const rev   = conv * deal;
  const roi   = Math.round((rev - b) / b * 100);
  const cpl   = (b / leads).toFixed(2);
  const reach = Math.round(b / 4);

  document.getElementById('r-reach').textContent    = fmt(reach);
  document.getElementById('r-leads').textContent    = fmt(leads);
  document.getElementById('r-conv').textContent     = fmt(conv);
  document.getElementById('r-conv-rate').textContent= Math.round(conv/leads*100) + '% معدل تحويل';
  document.getElementById('r-rev').textContent      = '$' + fmt(rev);
  document.getElementById('r-roi').textContent      = roi + '%';
  document.getElementById('r-cpl').textContent      = '$' + cpl;

  // Weekly chart
  const weeks     = Math.ceil(d / 7);
  const wLabels   = Array.from({length: weeks}, (_, i) => 'W' + (i + 1));
  const wLeads    = wLabels.map((_, i) => Math.round(leads / weeks * (0.5 + i * 0.15)));
  const wConv     = wLeads.map(v => Math.round(v * 0.15));
  const rc = document.getElementById('results-chart');
  if (resultsChart) { resultsChart.destroy(); resultsChart = null; }
  resultsChart = new Chart(rc, {
    type: 'line',
    data: { labels: wLabels, datasets: [
      {label:'عملاء محتملون', data:wLeads, borderColor:'#7c6fff', backgroundColor:'rgba(124,111,255,.12)', fill:true, tension:0.4, borderWidth:2, pointBackgroundColor:'#7c6fff'},
      {label:'التحويلات', data:wConv, borderColor:'#1ecc8b', backgroundColor:'rgba(30,204,139,.10)', fill:true, tension:0.4, borderWidth:2, borderDash:[5,4], pointBackgroundColor:'#1ecc8b'},
    ]},
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks:{color:'#9999b0', font:{family:'DM Sans'}}, grid:{color:'rgba(255,255,255,.04)'} },
        y: { beginAtZero:true, ticks:{color:'#9999b0', font:{family:'DM Sans'}}, grid:{color:'rgba(255,255,255,.04)'} }
      }
    }
  });

  // Contrib donut
  const sel = [...selectedChannels];
  const cc = document.getElementById('contrib-chart');
  if (contribChart) { contribChart.destroy(); contribChart = null; }
  if (sel.length) {
    const cLabels = sel.map(i => CHANNELS[i].name);
    const rawData = sel.map(i => Math.round(100 / sel.length + (Math.sin(i * 7) * 8)));
    const cColors = sel.map(i => CHANNELS[i].color);
    contribChart = new Chart(cc, {
      type: 'doughnut',
      data: { labels: cLabels, datasets: [{ data: rawData, backgroundColor: cColors, borderWidth: 0, hoverOffset: 8 }] },
      options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false} }, cutout:'62%' }
    });
    document.getElementById('contrib-legend').innerHTML = sel.map(i =>
      `<div class="legend-item"><div class="legend-swatch" style="background:${CHANNELS[i].color}"></div>${CHANNELS[i].name}</div>`
    ).join('');
  }

  // Recommendations
  const recs = [
    roi > 150 ? {type:'green', icon:'↑', text:'عائد قوي — فكر في زيادة الميزانية بنسبة 20-30% في دورة الحملة القادمة.'} :
                {type:'amber', icon:'!', text:'العائد أقل من المستهدف — راجع مزيج القنوات وقوة العرض وافتراضات حجم الصفقة.'},
    leads > 200 ? {type:'green', icon:'✓', text:'حجم العملاء المحتملين في المسار الصحيح. حافظ على الاستراتيجية الحالية.'} :
                  {type:'blue',  icon:'→', text:'حجم العملاء المحتملين محدود — وسّع شرائح الجمهور أو أضف قنوات أعلى وصولاً.'},
    {type:'blue',  icon:'→', text:'طبّق النسخة الفائزة من اختبار أ/ب كإعلان افتراضي للحملة القادمة.'},
    d < 21 ? {type:'amber', icon:'!', text:'تم اكتشاف مدة قصيرة للحملة — الحملات التي تزيد عن 30 يومًا تتفوق بنسبة 40% في المتوسط.'} :
             {type:'green', icon:'✓', text:'مدة الحملة مناسبة لنتائج موثوقة إحصائيًا وتحسين مستمر.'},
  ];
  document.getElementById('recommendations').innerHTML = recs.map(r =>
    `<div class="rec rec-${r.type}"><strong style="flex-shrink:0">${r.icon}</strong><span>${r.text}</span></div>`
  ).join('');
}

/* ─── Reset ─── */
function resetSim() {
  document.getElementById('budget').value   = 10000;
  document.getElementById('duration').value = 30;
  document.getElementById('dealsize').value = 200;
  selectedChannels = new Set([0, 1, 3]);
  updateSetup();
  const firstNav = document.querySelector('.nav-item');
  switchTab('setup', firstNav);
}

/* ─── Init ─── */
updateSetup();
setTimeout(() => {
  updateAB();
  updateAudience();
  updateFunnel();
}, 80);
