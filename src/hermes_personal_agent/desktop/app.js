const paths = {
  grid:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  tasks:'m4 6 2 2 4-4 M13 6h7 M4 13l2 2 4-4 M13 13h7 M4 20h16',
  calendar:'M5 5h14a2 2 0 0 1 2 2v13H3V7a2 2 0 0 1 2-2Z M7 3v4 M17 3v4 M3 11h18 M7 15h2 M13 15h2 M7 18h2',
  memory:'M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H3V4Z M13 7a3 3 0 0 1 3-3h5v15h-4a4 4 0 0 0-4 2',
  phone:'M7 3H4a1 1 0 0 0-1 1c0 9 8 17 17 17a1 1 0 0 0 1-1v-3l-5-2-2 2a15 15 0 0 1-7-7l2-2Z',
  settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z M9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1Z',
  log:'M5 3h10l4 4v14H5Z M15 3v5h4 M8 12h8 M8 16h8',
  laptop:'M4 4h16v12H4Z M2 20h20l-2-4H4Z',
  server:'M4 3h16v7H4Z M4 14h16v7H4Z M7 6h1 M7 17h1 M15 6h2 M15 17h2',
  play:'m8 4 12 8-12 8Z', stop:'M6 6h12v12H6Z', plus:'M12 5v14 M5 12h14',
  refresh:'M20 10a8 8 0 0 0-14-5L3 8 M3 3v5h5 M4 14a8 8 0 0 0 14 5l3-3 M21 21v-5h-5',
  chevron:'m9 5 7 7-7 7', left:'m15 5-7 7 7 7', down:'m6 9 6 6 6-6',
  check:'m5 12 4 4L19 6', close:'m6 6 12 12 M6 18 18 6',
  clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M12 7v5l3 2',
  search:'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Z m5 12 6 6',
  info:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M12 11v6 M12 7h.01',
  trash:'M3 6h18 M8 6V3h8v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7',
  file:'M5 3h9l5 5v13H5Z M14 3v6h5 M8 13h8 M8 17h6',
  upload:'M12 16V3 m-5 5 5-5 5 5 M4 15v6h16v-6',
  pause:'M7 4h3v16H7Z M14 4h3v16h-3Z',
  message:'M3 4h18v13H9l-6 4Z M7 8h10 M7 12h7',
  arrow:'M5 12h14 m-6-6 6 6-6 6', globe:'M3 12h18 M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z M12 3c5 5 5 13 0 18-5-5-5-13 0-18',
  shield:'m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z m-4 9 3 3 5-6',
};
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.info}"/></svg>`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $ = selector => document.querySelector(selector);
const markupCache = new WeakMap();
function setMarkup(node, html) {
  if(markupCache.get(node)===html)return;
  const active=document.activeElement;
  const focused=node.contains(active)?{id:active.id,tag:active.tagName,attrs:[...active.attributes].filter(a=>a.name.startsWith('data-')||['href','name','type'].includes(a.name)).map(a=>[a.name,a.value])}:null;
  node.innerHTML=html;markupCache.set(node,html);
  if(focused){
    const candidates=focused.id?[...node.querySelectorAll('[id]')].filter(n=>n.id===focused.id):[...node.querySelectorAll(focused.tag)].filter(n=>focused.attrs.every(([k,v])=>n.getAttribute(k)===v));
    const next=candidates.find(n=>!n.disabled);
    next?.focus({preventScroll:true});
  }
}
const nowKey = () => new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Tashkent',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const dateKey = value => value ? new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Tashkent',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value)) : '';
const formatDate = (value, options={day:'numeric',month:'short'}) => value ? new Intl.DateTimeFormat('uz-UZ',{timeZone:'Asia/Tashkent',...options}).format(new Date(value)) : '—';
const formatTime = value => formatDate(value,{hour:'2-digit',minute:'2-digit'});
let today = nowKey();
const nextPlan = () => {const date=new Date(Date.now()+3600000);return dateKey(date)+'T'+new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Tashkent',hour:'2-digit',minute:'2-digit',hour12:false}).format(date);};
const state = {page:'overview',env:'local',environments:{},operation:null,hiddenOperation:0,busy:false,
  taskFilter:'active',taskForm:false,job:null,memoryTab:'sources',sources:null,source:null,facts:null,wikiPages:[],wikiPage:null,
  search:'',file:null,drafts:{},calendar:new Date(today+'T12:00:00'),selectedDay:today,logFilter:'all'};
const pages = {
  overview:['Boshqaruv stoli','Yordamchingiz, rejalaringiz va xotirangiz — bir joyda.','grid'],
  tasks:['Vazifalar','Topshiriqlarni bering, rejalashtiring va natijasini kuzating.','tasks'],
  calendar:['Kalendar','Rejalashtirilgan ishlar va qo‘ng‘iroqlar kunlar bo‘yicha.','calendar'],
  memory:['Xotira','Yordamchi biladigan ma’lumotlarni ko‘ring va boyiting.','memory'],
  calls:['Qo‘ng‘iroqlar','Suhbat, ovoz modeli va audio oqimini boshqaring.','phone'],
  settings:['Sozlamalar','Yordamchingizning ishlash tartibini o‘zingizga moslang.','settings'],
  logs:['Faoliyat jurnali','Xizmat holati va xatoliklarning haqiqiy qaydlari.','log'],
};
const labels = {scheduled:'Rejalangan',running:'Bajarilmoqda',done:'Bajarildi',failed:'Xatolik',missed:'O‘tkazib yuborilgan',cancelled:'Bekor qilingan',interrupted:'To‘xtab qolgan',active:'Faol',stopped:'To‘xtatilgan',replaced:'Almashtirilgan',starting:'Ishga tushmoqda',error:'Ulanmadi'};
const kindLabel = {task:'Topshiriq',call:'Qo‘ng‘iroq',message:'Eslatma'};
const kindIcon = {task:'tasks',call:'phone',message:'message'};
const snap = () => state.environments[state.env]?.data || null;
const jobs = () => [...(snap()?.jobs || [])].sort((a,b)=>new Date(a.at)-new Date(b.at));
const runtime = () => snap()?.runtime || {};
const activeOperation = () => state.operation && !['done','error'].includes(state.operation.phase);
const badge = (status,label=null) => `<span class="status-pill ${esc(status)}"><i class="dot"></i>${esc(label || labels[status] || status)}</span>`;
const button = (text,action,options={}) => `<button type="button" class="button ${options.class || ''}" data-act="${action}" ${options.extra || ''} ${options.disabled?'disabled':''}>${options.icon?icon(options.icon):''}${text}</button>`;
const empty = (title,text,action,label,symbol='tasks',compact=false) => `<div class="empty ${compact?'compact':''}"><span class="empty-symbol">${icon(symbol)}</span><h3>${title}</h3><p>${text}</p>${action?button(label,action,{class:'primary',icon:'plus'}):''}</div>`;

async function rpc(action,args={}) {
  if (!window.pywebview?.api) throw new Error('Desktop ko‘prigi hali tayyor emas. Bir oz kuting.');
  const response = await window.pywebview.api.invoke(action,{environment:state.env,...args});
  if (!response?.ok) throw new Error(response?.error || 'Amal bajarilmadi. Qayta urinib ko‘ring.');
  return response.result ?? response;
}
function toast(text,error=false) {
  const node=$('#toast');node.textContent=text;node.className='visible'+(error?' error':'');
  clearTimeout(toast.timer);toast.timer=setTimeout(()=>node.className='',error?7000:4000);
}
async function mutate(action,args,message='Saqlandi') {
  if(state.busy)return;
  state.busy=true;renderShell();
  markupCache.delete($('#page'));
  document.querySelectorAll('#page button[type="submit"],#page [data-act="import-file"]').forEach(b=>{b.disabled=true;b.setAttribute('aria-busy','true');b.textContent='Bajarilmoqda…';});
  try {const result=await rpc(action,args);toast(message);await poll();return result;}
  catch(error){toast(error.message,true);return null;}
  finally{state.busy=false;render();}
}
async function confirmAction(title,text) {
  const dialog=$('#confirm-dialog');$('#confirm-title').textContent=title;$('#confirm-text').textContent=text;
  $('#confirm-symbol').innerHTML=icon('trash');dialog.returnValue='cancel';dialog.showModal();
  return new Promise(resolve=>dialog.addEventListener('close',()=>resolve(dialog.returnValue==='confirm'),{once:true}));
}
function navigate(page){state.page=page;location.hash=page;render();$('#content-scroll').scrollTop=0;}
function renderShell() {
  const [title,description]=pages[state.page];
  $('#page-title').textContent=title;$('#breadcrumb').textContent=title;$('#page-description').textContent=description;
  $('#today-label').textContent=formatDate(new Date(),{day:'numeric',month:'long',year:'numeric'});
  $('#refresh-button').innerHTML=icon('refresh');
  const nav=Object.entries(pages).map(([key,[label,,symbol]],index)=>`${index===5?'<div class="nav-divider"></div>':''}<a href="#${key}" class="nav-item ${state.page===key?'active':''}" ${state.page===key?'aria-current="page"':''} title="${label}">${icon(symbol)}<span>${label}</span></a>`).join('');
  setMarkup($('#navigation'),nav);
  document.querySelectorAll('[data-act="select-env"]').forEach(b=>{b.classList.toggle('selected',b.dataset.env===state.env);b.setAttribute('aria-pressed',String(b.dataset.env===state.env));});
  const runtimeHtml=['local','server'].map(env=>{
    const record=state.environments[env],data=record?.data,rt=data?.runtime,known=!!rt&&!record?.error;
    let phase=known?rt.phase:'starting',label=record?.error?'Ulanmadi':!known?'Tekshirilmoqda':rt.ready?'Ishlayapti':rt.running?'Ishga tushmoqda':'To‘xtatilgan';
    if(record?.error)phase='error';
    const busy=state.busy||activeOperation();
    return `<article class="runtime ${env===state.env?'selected':''}"><div class="runtime-main"><span class="device-symbol">${icon(env==='local'?'laptop':'server')}</span><div class="runtime-title"><h3>${env==='local'?'Shu kompyuter':'VPS server'}</h3><p>${env==='local'?'Windows · local nusxa':'Ubuntu · masofaviy nusxa'}</p></div><div class="runtime-controls">${badge(rt?.ready&&known?'running':phase,label)}${button(rt?.running?'To‘xtatish':'Ishga tushirish',rt?.running?'stop-runtime':'start-runtime',{icon:rt?.running?'stop':'play',class:rt?.running?'':'primary',disabled:busy||!known,extra:`data-env="${env}"`})}</div></div><div class="runtime-foot"><span>${icon(rt?.ready?'check':'clock')}${known&&rt?.ready?(rt.paused?'Avtomatik ishlar pauzada':rt.model || 'Xizmat tayyor'):known?'Ishga tushirishga tayyor':'Holat aniqlanmoqda'}</span><span>${env===state.env?'Tanlangan muhit':button('Ko‘rish','select-env',{class:'subtle small',extra:`data-env="${env}"`})}</span></div></article>`;
  }).join('');
  setMarkup($('#runtimes'),runtimeHtml);
  const running=Object.entries(state.environments).filter(([,v])=>v.data?.runtime?.ready&&!v.error);
  $('#connection-note').textContent=running.length?`${running[0][0]==='local'?'Local':'VPS'} yordamchi ishlayapti`:'Yordamchi holatini kuzatish';
  const record=state.environments[state.env];
  $('#environment-error').innerHTML=record?.error?`<div class="alert">${icon('info')}<div><strong>${state.env==='server'?'VPS bilan bog‘lanib bo‘lmadi':'Local ma’lumot olinmadi'}</strong><p>${esc(record.error)}</p><small>${record.data?'Oxirgi olingan ma’lumot ko‘rsatilmoqda.':'Internet va SSH ulanishini tekshirib, yangilashni bosing.'}</small></div></div>`:'';
  $('#last-update').textContent=record?.time?`Oxirgi yangilanish: ${formatTime(new Date(record.time*1000))} · ${state.env==='local'?'shu kompyuter':'VPS server'}`:'Haqiqiy holat olinmoqda…';
  renderOperation();
}
function renderOperation(){
  const op=state.operation;
  if(!op||state.hiddenOperation===op.updated_at){setMarkup($('#operation'),'');return;}
  const phases=['checking','stopping_other','starting','waiting'];
  setMarkup($('#operation'),`<div class="operation ${op.phase==='error'?'error':''}">${icon(op.phase==='done'?'check':op.phase==='error'?'info':'clock')}<div><strong>${op.phase==='done'?'Boshqaruv amali yakunlandi':op.phase==='error'?'Amalni yakunlab bo‘lmadi':'Muhit almashtirilmoqda'}</strong><p>${esc(op.text)}</p>${!['done','error','stopping'].includes(op.phase)?`<div class="steps">${['Tekshirish','To‘xtatish','Ishga tushirish','Ulanish'].map((t,i)=>`<span class="${phases[i]===op.phase?'current':''}">${icon(i<phases.indexOf(op.phase)?'check':'clock')}${t}</span>`).join('')}</div>`:''}</div>${['done','error'].includes(op.phase)?`<button class="icon-button" data-act="dismiss-operation" aria-label="Bildirishnomani yopish">${icon('close')}</button>`:''}</div>`);
}
function taskRows(list,compact=false){
  if(!list.length)return empty('Hozircha reja yo‘q','Yangi topshiriq yoki eslatma qo‘shing. Yordamchi vaqtida bajaradi.','new-task','Vazifa qo‘shish','tasks',compact);
  return list.map(job=>`<div class="task-row"><span class="task-symbol">${icon(kindIcon[job.kind])}</span><div class="task-content"><a href="#tasks" data-act="job-detail" data-id="${esc(job.id)}"><strong>${esc(job.text||'Sizga qo‘ng‘iroq qilish')}</strong></a><p><span>${kindLabel[job.kind]||job.kind}</span>${badge(job.status)}${job.repeat!=='once'?`<span>${job.repeat==='daily'?'Har kuni':'Har hafta'}</span>`:''}</p></div><div class="task-time">${formatTime(job.at)}<small>${formatDate(job.at)}</small></div>${job.status==='scheduled'?`<button class="icon-button destructive" data-act="cancel-job" data-id="${esc(job.id)}" aria-label="Vazifani bekor qilish" title="Bekor qilish">${icon('close')}</button>`:''}</div>`).join('');
}
function miniCalendar(){return calendarMarkup(true);}
function overview(){
  const data=snap(),rt=runtime(),pending=jobs().filter(j=>['scheduled','running'].includes(j.status));
  return `<div class="page-grid"><div><section class="panel"><div class="panel-head"><div><div class="section-title"><h2>Navbatdagi ishlar</h2><span class="count">${pending.length}</span></div><p>Tanlangan muhitdagi topshiriq va eslatmalar</p></div>${button('Yangi vazifa','new-task',{class:'primary',icon:'plus'})}</div><div class="tabs"><button class="${state.taskFilter==='active'?'active':''}" data-act="task-filter" data-filter="active">Rejalangan</button><button class="${state.taskFilter==='finished'?'active':''}" data-act="task-filter" data-filter="finished">Yakunlangan</button></div>${taskRows((state.taskFilter==='active'?pending:jobs().filter(j=>!['scheduled','running'].includes(j.status))).slice(0,6))}<div class="panel-body" style="padding-top:14px;padding-bottom:14px">${button('Barcha vazifalar','nav-tasks',{class:'subtle small',icon:'arrow'})}</div></section><section class="panel"><div class="panel-head"><div><h2>Xotiraga yangi ma’lumot</h2><p>Yordamchi keyingi suhbatlarda foydalanadigan bilimlar</p></div>${button('Ma’lumot qo‘shish','new-memory',{icon:'plus'})}</div><div class="panel-body"><dl class="info-list"><div><dt>Saqlangan manbalar</dt><dd>${data.memory.sources}</dd></div><div><dt>Tasdiqlangan faktlar</dt><dd>${data.memory.facts}</dd></div><div><dt>O‘rganish navbatida</dt><dd>${data.memory.learning_pending}</dd></div></dl>${(data.sources||[]).slice(0,3).map(source=>`<div class="mini-source"><a href="#memory" data-act="source-detail" data-id="${esc(source.id)}"><strong>${esc(source.title)}</strong></a><span>${formatDate(source.created_at)} · ${sourceKind(source.kind)}</span></div>`).join('')||'<p class="subtle-note" style="padding-top:16px">Matn yoki hujjat qo‘shib, shaxsiy bilimlar bazasini yarating.</p>'}</div></section></div><aside><section class="panel"><div class="panel-head"><h2>Bugun</h2>${button('Kalendar','nav-calendar',{class:'subtle small'})}</div>${miniCalendar()}</section><section class="panel"><div class="panel-head"><h2>Yordamchi holati</h2></div><div class="panel-body"><dl class="info-list"><div><dt>Telegram akkaunt</dt><dd>@${esc(data.agent)}</dd></div><div><dt>Jonli ovoz</dt><dd>${esc(rt.model||data.settings.voice_provider)}</dd></div><div><dt>Vazifalar modeli</dt><dd>${esc(rt.task_model||data.settings.hermes_model)}</dd></div><div><dt>Suhbat</dt><dd>${callLabel(rt.call)}</dd></div><div><dt>Navbat</dt><dd>${rt.owner_queue||0} ta vazifa</dd></div></dl><div class="actions" style="justify-content:stretch">${button(data.paused?'Davom ettirish':'Avtomatik ishlarni pauzalash','toggle-pause',{icon:data.paused?'play':'pause',disabled:!rt.ready})}</div></div></section></aside></div>`;
}
function sourceKind(kind){return ({note:'Ma’lumot',conversation:'Suhbat',file:'Hujjat',research:'Tadqiqot'})[kind]||kind;}
function callLabel(status){return ({idle:'Faol emas',connecting:'Ulanmoqda',connected:'Suhbat davom etmoqda'})[status]||'Faol emas';}
function draft(name,defaults){return state.drafts[state.env+':'+name] ||= {...defaults};}
function value(d,key){return esc(d[key]??'');}
function jobForm(){
  const d=draft('task',{kind:'task',text:'',when:'later',at:nextPlan(),repeat:'once'});
  return `<section class="panel"><div class="panel-head"><div><h2>Vazifa qo‘shish</h2><p>${state.env==='local'?'Shu kompyuterda':'VPS serverda'} bajariladi</p></div></div><form id="task-form" class="panel-body" data-form="task"><div class="field"><label for="task-kind">Vazifa turi</label><select id="task-kind" name="kind">${Object.entries(kindLabel).map(([k,v])=>`<option value="${k}" ${d.kind===k?'selected':''}>${v}</option>`).join('')}</select></div><div class="field"><label for="task-text">Nima qilish kerak?</label><textarea id="task-text" name="text" placeholder="Masalan: ertangi uchrashuvga tayyorgarlik rejasini tuz" ${d.kind!=='call'?'required':''}>${value(d,'text')}</textarea>${d.kind==='call'?'<small>Rejalashtirilgan qo‘ng‘iroq sizning akkauntingizga qilinadi.</small>':''}</div><div class="field"><label for="task-when">Qachon bajarilsin?</label><select id="task-when" name="when"><option value="later" ${d.when==='later'?'selected':''}>Vaqtni belgilash</option><option value="now" ${d.when==='now'?'selected':''}>Hozir</option></select></div>${d.when!=='now'?`<div class="field"><label for="task-at">Sana va vaqt · Toshkent</label><input id="task-at" name="at" type="datetime-local" value="${value(d,'at')}" required></div>`:''}<div class="field"><label for="task-repeat">Takrorlash</label><select id="task-repeat" name="repeat"><option value="once">Bir marta</option><option value="daily" ${d.repeat==='daily'?'selected':''}>Har kuni</option><option value="weekly" ${d.repeat==='weekly'?'selected':''}>Har hafta</option></select></div><p class="subtle-note">Vazifa tanlangan muhit ishlab turganida bajariladi. Hozir ishlamasa, avval yordamchini ishga tushiring.</p><div class="actions"><button class="button primary" type="submit" ${!runtime().ready||state.busy?'disabled':''}>${icon('plus')}Vazifani saqlash</button></div></form></section>`;
}
function tasksPage(){
  const list=jobs().filter(j=>state.taskFilter==='all'||(state.taskFilter==='active'?['scheduled','running'].includes(j.status):!['scheduled','running'].includes(j.status)));
  const selected=jobs().find(j=>j.id===state.job);
  const missions=(snap().missions||[]).filter(m=>m.status==='active');
  return `<div class="page-grid"><div><section class="panel"><div class="panel-head"><div class="section-title"><h2>Barcha vazifalar</h2><span class="count">${jobs().length}</span></div></div><div class="tabs">${[['active','Rejalangan'],['finished','Yakunlangan'],['all','Barchasi']].map(([k,v])=>`<button class="${state.taskFilter===k?'active':''}" data-act="task-filter" data-filter="${k}">${v}</button>`).join('')}</div>${selected?`<div class="job-detail"><div style="display:flex;justify-content:space-between;gap:15px"><strong>${esc(selected.text||'Qo‘ng‘iroq')}</strong><button class="icon-button" data-act="close-job" aria-label="Tafsilotlarni yopish">${icon('close')}</button></div>${selected.result?`<p style="white-space:pre-wrap;margin-top:12px">${esc(selected.result)}</p>`:selected.error?`<p class="error-inline">${esc(selected.error)}</p>`:'<p class="subtle-note">Natija vazifa bajarilgach shu yerda ko‘rinadi.</p>'}<small>ID: ${esc(selected.id)} · ${formatDate(selected.at)} ${formatTime(selected.at)}</small></div>`:''}${taskRows(list)}</section><section class="panel"><div class="panel-head"><div><h2>Davomiy topshiriqlar</h2><p>Sizning topshirig‘ingiz bilan kuzatilayotgan suhbatlar</p></div><span class="count">${missions.length}</span></div>${missions.length?missions.map(m=>`<div class="mission"><h3>${esc(m.goal)}</h3><p>Chat ${esc(m.chat_id)} · ${formatDate(m.until)} ${formatTime(m.until)} gacha</p><div class="mission-foot">${badge('active')}${button('Kuzatishni to‘xtatish','stop-mission',{class:'small',extra:`data-id="${esc(m.id)}"`})}</div></div>`).join(''):empty('Faol kuzatuv yo‘q','Telegram’da yordamchiga qaysi suhbatni va qanday maqsadda kuzatishni ayting.',null,null,'message',true)}</section></div><aside>${jobForm()}</aside></div>`;
}
function calendarMarkup(mini=false){
  const base=mini?new Date(today+'T12:00:00'):state.calendar;
  const year=base.getFullYear(),month=base.getMonth();
  const first=new Date(year,month,1);const offset=(first.getDay()+6)%7;
  const start=new Date(year,month,1-offset);
  const days=Array.from({length:42},(_,i)=>{const date=new Date(start);date.setDate(start.getDate()+i);return date;});
  return `<div class="${mini?'mini-calendar':''}">${!mini?`<div class="panel-head"><div class="calendar-head"><button class="icon-button" data-act="month-prev" aria-label="Oldingi oy">${icon('left')}</button><h2>${formatDate(base,{month:'long',year:'numeric'})}</h2><button class="icon-button" data-act="month-next" aria-label="Keyingi oy">${icon('chevron')}</button></div>${button('Bugun','calendar-today',{class:'small'})}</div>`:''}<div class="month-grid">${['Du','Se','Ch','Pa','Ju','Sh','Ya'].map(d=>`<span class="weekday">${d}</span>`).join('')}${days.map(date=>{const key=`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;const list=jobs().filter(j=>dateKey(j.at)===key&&j.status!=='cancelled');return `<button class="day ${date.getMonth()!==month?'dimmed':''} ${key===today?'today':''} ${key===state.selectedDay?'selected':''} ${list.length?'has-job':''}" data-act="select-day" data-date="${key}" aria-label="${formatDate(date,{day:'numeric',month:'long'})}: ${list.length} ta vazifa"><span class="day-number">${date.getDate()}</span>${!mini?list.slice(0,2).map(j=>`<span class="calendar-job ${j.kind}">${formatTime(j.at)} ${esc(j.text||'Qo‘ng‘iroq')}</span>`).join('')+(list.length>2?`<small>+${list.length-2} ta</small>`:''):''}</button>`;}).join('')}</div></div>`;
}
function calendarPage(){const list=jobs().filter(j=>dateKey(j.at)===state.selectedDay&&j.status!=='cancelled');return `<div class="page-grid"><section class="panel">${calendarMarkup()}<div class="calendar-legend"><span><i class="dot" style="background:#5e889a"></i>Topshiriq</span><span><i class="dot" style="background:#a88b46"></i>Qo‘ng‘iroq</span><span><i class="dot" style="background:#8879ad"></i>Eslatma</span></div></section><aside><section class="panel"><div class="panel-head"><h2>${formatDate(state.selectedDay+'T12:00:00',{day:'numeric',month:'long'})}</h2><span class="count">${list.length}</span></div>${taskRows(list,true)}<div class="panel-body" style="padding-top:18px">${button('Shu kunga vazifa','new-day-task',{class:'primary',icon:'plus'})}</div></section><div class="inline-note" style="margin-top:20px">${icon('info')}<span>Barcha sanalar Toshkent vaqti bilan. Kalendar tanlangan muhit vazifalarini ko‘rsatadi.</span></div></aside></div>`;}
function memoryForm(){
  const d=draft('memory',{title:'',text:''});
  return `<section class="panel"><div class="panel-head"><div><h2>Bilim qo‘shish</h2><p>Matn yozing yoki hujjat tanlang</p></div></div><form id="memory-form" class="panel-body" data-form="memory"><div class="field"><label for="memory-title">Sarlavha</label><input id="memory-title" name="title" placeholder="Masalan: mening ish tartibim" value="${value(d,'title')}" required></div><div class="field"><label for="memory-text">Yordamchi nimani bilishi kerak?</label><textarea id="memory-text" name="text" rows="7" placeholder="Shaxsiy ma’lumotlar, afzalliklar yoki loyiha haqida yozing…" required>${value(d,'text')}</textarea></div><button class="button primary" type="submit" ${state.busy?'disabled':''}>${icon('plus')}Xotiraga saqlash</button><div style="border-top:1px solid var(--line);margin:24px 0 18px"></div><h3>Hujjatdan o‘rganish</h3><p class="subtle-note" style="margin:8px 0 15px">PDF, DOCX, XLSX, matn yoki kod. Fayl tanlangan muhitga qo‘shiladi.</p>${state.file?`<div class="file-choice">${icon('file')}<span>${esc(state.file.name)}<small style="display:block;margin-top:3px">${(state.file.size/1024).toFixed(0)} KB</small></span></div>`:''}<div style="display:flex;gap:8px;flex-wrap:wrap">${button(state.file?'Boshqa fayl':'Fayl tanlash','pick-file',{icon:'upload',disabled:state.busy})}${state.file?button('Qo‘shish','import-file',{class:'primary',disabled:state.busy}):''}</div></form></section>`;
}
function memoryPage(){
  const sources=state.sources||snap().sources||[];
  const selected=state.source;
  let body;
  if(state.memoryTab==='wiki'){
    body=state.wikiPages.length ? `<div class="panel-body">${state.wikiPages.map(p=>`<div class="mini-source"><button class="text-link cell-title" data-act="wiki-page" data-name="${esc(p.name)}">${esc(p.title)}</button><span>${esc(p.name)}</span></div>`).join('')}</div>` : empty('Wiki bo‘sh','Manbalar o‘rganilganda sahifalar yaratiladi.',null,null,'memory');
  } else if(state.memoryTab==='facts'){
    const facts=state.facts||[];
    body=!state.facts?empty('Faktlar yuklanmoqda','Bilimlar bazasi tekshirilmoqda.',null,null,'memory',true):facts.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Mavzu</th><th>Bilim</th><th>Holat</th><th></th></tr></thead><tbody>${facts.map(f=>`<tr><td>${esc(f.entity)}<span class="cell-note">${esc(f.attribute)}</span></td><td>${esc(f.value)}</td><td>${badge(f.status,f.status==='conflict'?'Qarama-qarshi':f.status==='active'?'Tasdiqlangan':f.status)}</td><td>${f.status==='conflict'?button('To‘g‘ri deb belgilash','resolve-fact',{class:'small',extra:`data-id="${esc(f.id)}"` }):''}</td></tr>`).join('')}</tbody></table></div>`:empty('Hozircha faktlar ajratilmagan','Ma’lumot qo‘shing va sozlamalarda o‘rganishni yoqing.',null,null,'memory');
  }else{
    body=sources.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Manba</th><th>Turi</th><th>Qo‘shilgan</th><th></th></tr></thead><tbody>${sources.map(s=>`<tr data-act="source-detail" data-id="${esc(s.id||s.source_id)}" ><td><button class="text-link cell-title" data-act="source-detail" data-id="${esc(s.id||s.source_id)}">${esc(s.title)}</button><span class="cell-note">${esc(s.trust==='owner'?'Siz qo‘shgansiz':s.trust==='assistant'?'Yordamchi javobi':'Tashqi ma’lumot')}</span></td><td><span class="badge-label">${sourceKind(s.kind||'note')}</span></td><td>${formatDate(s.created_at)}</td><td>${icon('chevron')}</td></tr>`).join('')}</tbody></table></div>`:empty('Manba topilmadi',state.search?'Boshqa so‘z bilan qidirib ko‘ring.':'Birinchi ma’lumotingizni o‘ng tomondagi shakl orqali qo‘shing.',null,null,'memory');
  }
  return `<div class="two-columns"><section class="panel"><div class="panel-head"><div><div class="section-title"><h2>Bilimlar bazasi</h2><span class="count">${snap().memory.sources} manba</span></div><p>${snap().memory.facts} fakt · ${snap().memory.conflicts} qarama-qarshilik</p></div></div><div class="tabs"><button class="${state.memoryTab==='sources'?'active':''}" data-act="memory-tab" data-tab="sources">Manbalar</button><button class="${state.memoryTab==='facts'?'active':''}" data-act="memory-tab" data-tab="facts">Faktlar</button><button class="${state.memoryTab==='wiki'?'active':''}" data-act="memory-tab" data-tab="wiki">Wiki</button></div><form id="search-form" class="toolbar"><label class="search-wrap"><span class="screenreader">Xotiradan qidirish</span>${icon('search')}<input class="search-input" name="query" id="memory-search" value="${esc(state.search)}" placeholder="Xotiradan qidirish…"></label><button type="submit" class="button small">Qidirish</button>${state.search?button('Tozalash','clear-search',{class:'subtle small'}):''}</form>${body}</section><aside>${state.wikiPage?`<section class="panel"><div class="panel-head"><h2>Wiki sahifasi</h2><button class="icon-button" data-act="close-wiki" aria-label="Sahifani yopish">${icon('close')}</button></div><div class="panel-body"><h3>${esc(state.wikiPage.name)}</h3><div class="source-text">${esc(state.wikiPage.content)}</div></div></section>`:selected?`<section class="panel"><div class="panel-head"><h2>Manba mazmuni</h2><button class="icon-button" data-act="close-source" aria-label="Manbani yopish">${icon('close')}</button></div><div class="panel-body"><h3>${esc(selected.title)}</h3><div class="source-meta"><span>${sourceKind(selected.kind)}</span><span>${formatDate(selected.created_at)}</span></div><div class="source-text">${esc(selected.content)}</div>${selected.next_offset?`<div style="margin-top:12px">${button('Davomini yuklash','source-more',{class:'small'})}</div>`:''}<div class="actions">${button('Qidiruvdan chiqarish','forget-source',{class:'small',icon:'trash',extra:`data-id="${esc(selected.id)}"`})}</div><p class="subtle-note" style="margin-top:12px">Chiqarilgan manba javoblarda ishlatilmaydi. Audit va oldingi zaxiralar alohida saqlanadi.</p></div></section>`:memoryForm()}</aside></div>`;
}
function callsPage(){
  const rt=runtime(),data=snap(),d=draft('call',{chat:'',purpose:''});
  return `<div class="page-grid"><div><section class="panel"><div class="panel-head"><h2>Ovozli suhbat</h2><span class="badge-label">${esc(rt.model||data.settings.voice_provider)}</span></div><div class="call-stage"><div class="call-orb" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div><h2>${callLabel(rt.call)}</h2><p>${rt.call==='connected'?'Yordamchi hozir suhbatlashmoqda.':'Qo‘ng‘iroqni shu yerdan boshlang yoki Telegram orqali qo‘ng‘iroq qiling.'}</p>${badge(rt.call==='connected'?'running':rt.call==='connecting'?'starting':'stopped',rt.call==='connected'?'Audio ulangan':rt.call==='connecting'?'Ulanmoqda':'Kutish holatida')}</div><form id="call-form" class="panel-body" data-form="call"><div class="form-grid"><div class="field"><label for="call-chat">Kimga qo‘ng‘iroq?</label><input id="call-chat" name="chat" value="${value(d,'chat')}" placeholder="Sizga yoki @username"><small>Bo‘sh qoldirsangiz, sizning akkauntingizga.</small></div><div class="field"><label for="call-purpose">Suhbat maqsadi</label><input id="call-purpose" name="purpose" value="${value(d,'purpose')}" placeholder="Masalan: uchrashuv vaqtini so‘rash"></div></div><div class="actions">${rt.call!=='idle'?button('Qo‘ng‘iroqni yakunlash','hangup',{class:'danger',icon:'phone',disabled:state.busy}):`<button class="button primary" type="submit" ${!rt.ready||state.busy?'disabled':''}>${icon('phone')}Qo‘ng‘iroq qilish</button>`}</div></form></section><section class="panel"><div class="panel-head"><h2>Audio diagnostikasi</h2></div><div class="panel-body"><dl class="info-list"><div><dt>Qabul qilingan kadrlar</dt><dd>${rt.frames_in||0}</dd></div><div><dt>Ijro qilingan kadrlar</dt><dd>${rt.frames_out||0}</dd></div><div><dt>Bufer yetishmasligi</dt><dd>${rt.playback_underruns||0}</dd></div><div><dt>Eng katta kechikish</dt><dd>${rt.native_max_gap_ms||rt.playback_max_lag_ms||0} ms</dd></div><div><dt>Oxirgi xato</dt><dd>${esc(rt.last_error||'Xato yo‘q')}</dd></div></dl></div></section></div><aside><section class="panel"><div class="panel-head"><h2>Ovoz sozlamalari</h2></div><div class="panel-body"><dl class="info-list"><div><dt>Jonli model</dt><dd>${esc(rt.model||'—')}</dd></div><div><dt>Ovoz</dt><dd>${esc(rt.voice||data.settings.voice)}</dd></div><div><dt>Vazifalar modeli</dt><dd>${esc(rt.task_model||data.settings.hermes_model)}</dd></div></dl><div style="margin-top:18px">${button('Sozlamalarni ochish','nav-settings',{icon:'settings'})}</div></div></section><div class="inline-note" style="margin-top:20px">${icon('shield')}<span>Boshqa suhbatdoshlar sizning huquqlaringizga ega emas. Ular faqat sizga xabar yetkazishni so‘rashi mumkin.</span></div></aside></div>`;
}
function settingsPage(){
  const settings=snap().settings,d=draft('settings',settings);
  return `<div class="page-grid"><section class="panel"><div class="panel-head"><div><h2>Muloqot va modellar</h2><p>O‘zgarishlar tanlangan muhitda saqlanadi</p></div></div><form class="panel-body" id="settings-form" data-form="settings"><div class="form-grid"><div class="field"><label for="settings-provider">Jonli ovoz provayderi</label><select id="settings-provider" name="voice_provider"><option value="gemini" ${d.voice_provider==='gemini'?'selected':''}>Gemini 3.8 Live</option><option value="openai" ${d.voice_provider==='openai'?'selected':''}>GPT-Live 1</option></select><small>API kaliti shu muhitda oldindan sozlangan bo‘lishi kerak.</small></div><div class="field"><label for="settings-voice">Gemini ovozi</label><select id="settings-voice" name="voice">${[...new Set([d.voice,'Rasalgethi','Puck','Charon','Kore'])].map(v=>`<option ${v===d.voice?'selected':''}>${esc(v)}</option>`).join('')}</select></div><div class="field"><label for="settings-model">Vazifalar modeli</label><input id="settings-model" name="hermes_model" value="${value(d,'hermes_model')}" required><small>Mavjud OpenAI obuna marshrutidan foydalanadi.</small></div><div class="field"><label for="settings-max">Qo‘ng‘iroq limiti (daqiqa)</label><input type="number" min="1" max="60" id="settings-max" name="max_call_minutes" value="${value(d,'max_call_minutes')}" required></div><div class="field"><label for="settings-openai-max">GPT-Live sinov limiti (daqiqa)</label><input type="number" min="1" max="60" id="settings-openai-max" name="openai_live_max_minutes" value="${value(d,'openai_live_max_minutes')}" required></div><div class="field"><label for="settings-language">Asosiy til</label><select id="settings-language" name="language">${[['uz','O‘zbekcha'],['ru','Ruscha'],['en','Inglizcha']].map(([k,v])=>`<option value="${k}" ${d.language===k?'selected':''}>${v}</option>`).join('')}</select></div><div class="field full"><label for="settings-style">Siz bilan muomala uslubi</label><textarea id="settings-style" name="owner_style" rows="3">${value(d,'owner_style')}</textarea><small>Tanishtirish: “Men Ownerning shaxsiy AI yordamchisiman.”</small></div></div><div class="switch-row"><div><strong>Ma’lumotlardan avtomatik o‘rganish</strong><p>Manbalardan faktlarni ajratadi; obuna limitlaridan foydalanadi.</p></div><input type="checkbox" name="learning_enabled" id="settings-learning" aria-label="Avtomatik o‘rganish" ${d.learning_enabled?'checked':''}></div><div class="actions"><button class="button primary" type="submit" ${state.busy||runtime().call!=='idle'?'disabled':''}>${icon('check')}O‘zgarishlarni saqlash</button></div></form></section><aside><section class="panel"><div class="panel-head"><h2>Muhit haqida</h2></div><div class="panel-body"><dl class="info-list"><div><dt>Tanlangan muhit</dt><dd>${state.env==='local'?'Shu kompyuter':'VPS server'}</dd></div><div><dt>Ega</dt><dd>@${esc(snap().owner)}</dd></div><div><dt>Agent</dt><dd>@${esc(snap().agent)}</dd></div><div><dt>Vaqt zonasi</dt><dd>Asia/Tashkent</dd></div></dl><p class="subtle-note" style="margin-top:18px">Har muhitning xotira va vazifalari alohida. Muhitni almashtirish ma’lumotlarni avtomatik ko‘chirmaydi.</p></div></section><div class="inline-note" style="margin-top:20px">${icon('info')}<span>Ovoz provayderini almashtirishdan oldin faol qo‘ng‘iroqni tugating. Kalitlar bu oynada ko‘rsatilmaydi.</span></div></aside></div>`;
}
function logsPage(){const logs=(snap().logs||[]).filter(line=>state.logFilter!=='errors'||/ERROR|WARNING/.test(line));return `<section class="panel"><div class="panel-head"><div><h2>Xizmat qaydlari</h2><p>Oxirgi 80 ta qayd · ${state.env==='local'?'shu kompyuter':'VPS server'}</p></div><div><label class="screenreader" for="log-filter">Jurnal filtri</label><select class="search-input" style="padding:8px 12px" id="log-filter"><option value="all">Barcha qaydlar</option><option value="errors" ${state.logFilter==='errors'?'selected':''}>Xato va ogohlantirishlar</option></select></div></div><div class="panel-body">${logs.length?`<div class="log-view">${esc(logs.join('\n'))}</div>`:empty('Bu filtrda qayd yo‘q','Xizmat ishlaganida uning qaydlari shu yerda ko‘rinadi.',null,null,'log',true)}</div></section>`;}
function render(){
  renderShell();
  const data=snap();
  if(!data){$('#page').innerHTML=state.environments[state.env]?.error?empty('Ulanish mavjud emas','Muhit holatini yangilang yoki ikkinchi muhitni tanlang.',null,null,'globe'):'<div class="loading-surface"><div></div><div></div><div></div></div>';return;}
  if(document.activeElement?.closest('form')&&document.activeElement.id!=='log-filter')return;
  const scroll=$('#content-scroll').scrollTop;
  const html=({overview,tasks:tasksPage,calendar:calendarPage,memory:memoryPage,calls:callsPage,settings:settingsPage,logs:logsPage})[state.page]();
  setMarkup($('#page'),html);
  $('#content-scroll').scrollTop=scroll;
}
async function poll(){
  try{
    const day=nowKey();if(day!==today){if(state.selectedDay===today)state.selectedDay=day;today=day;}
    const result=await rpc('poll');state.environments=result.environments;state.operation=result.operation;
    render();
  }catch(error){$('#environment-error').innerHTML=`<div class="alert">${icon('info')}<span>${esc(error.message)}</span></div>`;}
}
document.addEventListener('input',event=>{
  const form=event.target.closest('[data-form]');if(!form||!event.target.name)return;
  const key=state.env+':'+form.dataset.form;state.drafts[key] ||= {};
  state.drafts[key][event.target.name]=event.target.type==='checkbox'?event.target.checked:event.target.value;
});
document.addEventListener('change',event=>{
  if(['task-when','task-kind'].includes(event.target.id)){event.target.blur();render();}
  if(event.target.id==='log-filter'){state.logFilter=event.target.value;event.target.blur();render();}
});
document.addEventListener('keydown',event=>{if(event.key==='Enter'&&event.target.matches('tr[data-act]'))event.target.click();});
document.addEventListener('click',async event=>{
  const node=event.target.closest('[data-act]');if(!node||node.disabled)return;
  event.preventDefault();const action=node.dataset.act;
  try{
    if(action.startsWith('nav-'))return navigate(action.slice(4));
    if(action==='select-env'){state.env=node.dataset.env;state.sources=state.source=state.facts=null;state.file=null;render();return;}
    if(action==='refresh'){await rpc('refresh');toast('Ma’lumotlar yangilanmoqda');return;}
    if(action==='start-runtime'||action==='stop-runtime'){
      if(action==='start-runtime'){state.env=node.dataset.env;state.sources=state.source=state.facts=null;state.file=null;render();}
      const result=await rpc(action==='start-runtime'?'runtime-start':'runtime-stop',{environment:node.dataset.env});
      await poll();return;
    }
    if(action==='dismiss-operation'){state.hiddenOperation=state.operation.updated_at;renderOperation();return;}
    if(action==='task-filter'){state.taskFilter=node.dataset.filter;render();return;}
    if(action==='new-task'||action==='new-day-task'){
      if(action==='new-day-task'){const d=draft('task',{});d.at=state.selectedDay+'T09:00';d.when='later';}
      navigate('tasks');setTimeout(()=>$('#task-text')?.focus(),0);return;
    }
    if(action==='job-detail'){state.job=node.dataset.id;navigate('tasks');return;}
    if(action==='close-job'){state.job=null;render();return;}
    if(action==='cancel-job'){await mutate('agent',{op:'cancel',id:node.dataset.id},'Vazifa bekor qilindi');return;}
    if(action==='stop-mission'){await mutate('agent',{op:'unwatch',id:node.dataset.id},'Kuzatish to‘xtatildi');return;}
    if(action==='toggle-pause'){await mutate('agent',{op:snap().paused?'resume':'pause'},snap().paused?'Avtomatik ishlar davom etmoqda':'Yangi avtomatik ishlar pauzaga qo‘yildi');return;}
    if(action==='select-day'){state.selectedDay=node.dataset.date;if(state.page!=='calendar')navigate('calendar');else render();return;}
    if(action==='month-prev'||action==='month-next'){state.calendar=new Date(state.calendar.getFullYear(),state.calendar.getMonth()+(action==='month-prev'?-1:1),1,12);render();return;}
    if(action==='calendar-today'){state.calendar=new Date(today+'T12:00:00');state.selectedDay=today;render();return;}
    if(action==='new-memory'){state.source=null;navigate('memory');setTimeout(()=>$('#memory-title')?.focus(),0);return;}
    if(action==='source-detail'){state.source=await rpc('memory-source',{id:node.dataset.id});navigate('memory');return;}
    if(action==='source-more'){const more=await rpc('memory-source',{id:state.source.id,offset:state.source.next_offset});state.source.content+=more.content;state.source.next_offset=more.next_offset;render();return;}
    if(action==='close-source'){state.source=null;render();return;}
    if(action==='memory-tab'){state.memoryTab=node.dataset.tab;state.wikiPage=null;if(state.memoryTab==='facts')state.facts=(await rpc('memory-facts',{query:state.search})).facts;if(state.memoryTab==='wiki')state.wikiPages=(await rpc('memory-wiki-pages')).pages;render();return;}
    if(action==='wiki-page'){state.wikiPage=await rpc('memory-wiki-page',{name:node.dataset.name});state.source=null;render();return;}
    if(action==='close-wiki'){state.wikiPage=null;render();return;}
    if(action==='clear-search'){state.search='';state.sources=null;if(state.memoryTab==='facts')state.facts=(await rpc('memory-facts')).facts;if(state.memoryTab==='wiki')state.wikiPages=(await rpc('memory-wiki-pages')).pages;render();return;}
    if(action==='pick-file'){const result=await rpc('pick-file');if(!result.cancelled)state.file=result;document.activeElement?.blur();render();return;}
    if(action==='import-file'){const result=await mutate('import-file',{token:state.file.token},'Hujjat xotiraga qo‘shildi');if(result)state.file=null;document.activeElement?.blur();render();return;}
    if(action==='forget-source'){
      if(await confirmAction('Manba qidiruvdan chiqarilsinmi?','Yordamchi bu ma’lumotni javoblarida ishlatmaydi. Audit va avvalgi zaxiralar saqlanadi.')){
        if(await mutate('memory-forget',{id:node.dataset.id},'Manba qidiruvdan chiqarildi')){state.source=null;state.sources=null;render();}}
      return;
    }
    if(action==='resolve-fact'){
      if(await confirmAction('Shu faktni to‘g‘ri deb belgilaysizmi?','Ushbu qiymat joriy deb olinadi. Boshqa qarama-qarshi qiymatlar avvalgi ma’lumot sifatida saqlanadi.'))await mutate('memory-resolve',{id:node.dataset.id},'Fakt tasdiqlandi');
      state.facts=(await rpc('memory-facts',{query:state.search})).facts;render();return;
    }
    if(action==='hangup'){await mutate('hangup',{},'Qo‘ng‘iroq yakunlanmoqda');return;}
  }catch(error){toast(error.message,true);}
});
document.addEventListener('submit',async event=>{
  const form=event.target;if(!['task-form','memory-form','search-form','call-form','settings-form'].includes(form.id))return;
  event.preventDefault();if(!form.reportValidity())return;
  const data=Object.fromEntries(new FormData(form));
  document.activeElement?.blur();
  if(form.id==='task-form'){
    const at=data.when==='now'?new Date(Date.now()+5000).toISOString():data.at+':00+05:00';
    if(!Number.isFinite(new Date(at).getTime())||new Date(at)<=new Date()){toast('Kelajakdagi sana va vaqtni tanlang.',true);return;}
    if(await mutate('agent',{op:'schedule',kind:data.kind,at,text:data.text,repeat:data.repeat},'Vazifa rejalashtirildi')){delete state.drafts[state.env+':task'];render();}
  }else if(form.id==='memory-form'){
    if(await mutate('memory-text',data,'Ma’lumot xotiraga saqlandi')){delete state.drafts[state.env+':memory'];render();}
  }else if(form.id==='search-form'){
    state.search=data.query.trim();
    try{if(state.memoryTab==='wiki'){state.wikiPages=(await rpc('memory-wiki-pages')).pages.filter(p=>p.title.toLowerCase().includes(state.search.toLowerCase()));}else if(state.memoryTab==='facts')state.facts=(await rpc('memory-facts',{query:state.search})).facts;else state.sources=state.search?(await rpc('memory-search',{query:state.search})).results:null;render();}catch(error){toast(error.message,true);}
  }else if(form.id==='call-form'){
    await mutate('call',{chat:data.chat.trim()||snap().owner,purpose:data.purpose},'Qo‘ng‘iroq boshlandi; ulanish holatini kuzating');
  }else if(form.id==='settings-form'){
    data.max_call_minutes=Number(data.max_call_minutes);data.openai_live_max_minutes=Number(data.openai_live_max_minutes);
    data.learning_enabled=form.elements.learning_enabled.checked;
    if(await mutate('settings-save',data,'Sozlamalar saqlandi')){state.environments[state.env].data.settings={...snap().settings,...data};delete state.drafts[state.env+':settings'];render();}
  }
});
window.addEventListener('hashchange',()=>{const page=location.hash.slice(1);if(pages[page]){state.page=page;render();}});
let started=false;
function start(){if(started)return;started=true;renderShell();poll();setInterval(poll,2000);}
window.addEventListener('pywebviewready',start);
if(window.pywebview?.api)start();
