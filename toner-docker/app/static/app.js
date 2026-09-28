(() => {
'use strict';
function plural(n, one, few, many) {
  n = Math.abs(n); const a = n % 10, b = n % 100;
  if (a === 1 && b !== 11) return one;
  if (a >= 2 && a <= 4 && (b < 10 || b >= 20)) return few;
  return many;
}
const pl = (n, arr) => plural(n, arr[0], arr[1], arr[2]);
const fmtInt = n => Number(n).toLocaleString('ru-RU');
const fmtCompact = n => { try { return new Intl.NumberFormat('ru-RU', { notation: 'compact', maximumFractionDigits: 1 }).format(n); } catch (e) { return fmtInt(n); } };

const T = {
  org: 'ГБПОУ МО «Физтех-колледж»', orgShort: 'Физтех-колледж', app: 'Управление принтерами',
  title: 'Расходники принтеров',
  nav: { menu: 'Меню', admin: 'Администрирование', dev: 'Разработчикам', dashboard: 'Дашборд', printers: 'Принтеры', supplies: 'Расходники', manage: 'Управление', settings: 'Настройки', log: 'Журнал', account: 'Безопасность', api: 'REST API' },
  home: 'Главная',
  printers: n => `${n} ${plural(n, 'принтер', 'принтера', 'принтеров')}`,
  demo: 'Демо-режим',
  updated: 'Обновлено',
  polling: 'Опрашиваю принтеры…',
  lost: 'Нет связи с сервером',
  refresh: 'Опросить все принтеры',
  themeToDark: 'Тёмная тема', themeToLight: 'Светлая тема',
  loading: 'Загружаю данные…',
  firstPoll: 'Идёт первый опрос принтеров',
  pScan: (d, t, f) => `Сканирую сеть: ${fmtInt(d)} из ${fmtInt(t)} адресов, найдено принтеров: ${f}`,
  pScanShort: (d, t) => `Сканирую сеть: ${Math.round(d / Math.max(1, t) * 100)}%`,
  pQueues: 'Читаю очереди принт-сервера…',
  pPoll: (d, t, c) => `Опрашиваю принтеры: ${d} из ${t}` + (c ? `, сейчас ${c}` : ''),
  pPollShort: (d, t) => `Опрашиваю: ${d} из ${t}`,
  banner: 'Сервер дашборда не отвечает. Показаны последние полученные данные.',
  search: 'Поиск: принтер, модель, IP, картридж…',
  sort: { problem: 'Сначала проблемные', name: 'По имени', ip: 'По IP', pages: 'По пробегу' },
  group: { none: 'Без группировки', location: 'По корпусам', vendor: 'По производителям', subnet: 'По подсетям', model: 'По моделям' },
  allVendors: 'Все производители', unknownVendor: 'Не определён',
  noLocation: 'Расположение не указано', noIp: 'Без IP', noModel: 'Модель неизвестна',
  f: { all: 'Все', crit: 'Менять', warn: 'Скоро', off: 'Нет данных', ok: 'В норме' },
  pill: { crit: 'Менять', warn: 'Мало', ok: 'В норме', offline: 'Не отвечает', noip: 'Без IP', nodata: 'Нет данных' },
  pillStale: 'Не в сети', pillNoCart: 'Нет картриджа', errPill: 'Ошибка', hiddenPill: 'Скрыт',
  mReplace: 'Нужно заменить', mReplaceSub: n => n ? `и ещё ${n} на подходе` : 'остальное в норме',
  mOnline: 'Принтеров на связи', mOnlineSub: n => n ? `${n} не ${plural(n, 'отвечает', 'отвечают', 'отвечают')}` : 'все отвечают',
  mAvg: 'Средний остаток тонера', mAvgSub: n => `по ${n} ${plural(n, 'картриджу', 'картриджам', 'картриджам')}`,
  mLow: 'Меньше всего тонера', mNone: '—', mNoneSub: 'нет данных об уровне',
  mDays: d => `${d}<small> ${plural(d, 'день', 'дня', 'дней')}</small>`,
  noCartShort: 'нет картриджа',
  replaceTitle: 'Нужно заменить', replaceSub: 'Расходники ниже порога и принтеры без картриджа',
  replaceEmpty: 'Сейчас менять ничего не нужно.',
  fleet: 'Состояние парка', fleetSub: 'Принтеры по статусу и производителю',
  legend: { ok: 'В норме', warn: 'Скоро', crit: 'Менять', off: 'Нет данных' },
  cardsTitle: 'Все принтеры',
  col: { supply: 'Расходник', printer: 'Принтер', where: 'Где стоит', left: 'Осталось', days: 'Хватит на', status: 'Статус', vendor: 'Производитель', ip: 'IP', location: 'Расположение', toner: 'Расходники', pages: 'Страниц', seen: 'Данные', actions: '', kind: 'Тип', name: 'Имя', source: 'Источник' },
  daysShort: d => d === 0 ? 'сегодня' : `≈ ${d} ${plural(d, 'день', 'дня', 'дней')}`,
  pages: 'стр.',
  enough: d => d === 0 ? 'кончится сегодня' : `хватит ≈ на ${d} ${plural(d, 'день', 'дня', 'дней')}`,
  inQueue: n => `в очереди ${n}`,
  offMsg: 'Принтер не отвечает ни по SNMP, ни по веб-интерфейсу. Проверьте, что он включён и в сети.',
  offDown: 'Адрес не отвечает совсем: принтер выключен, отключён от сети или сменил IP.',
  offUp: 'Устройство в сети, но принтерные порты закрыты и SNMP молчит. Возможно, по этому адресу теперь другое устройство.',
  offPort: port => `Принтер в сети (открыт порт ${port}), но не отдаёт данные по SNMP. Включите SNMP v1/v2c с community «public» в его веб-интерфейсе.`,
  downTitle: 'Нет связи', downSub: 'Не отвечают на опрос. Показаны в конце списка.',
  reach: { port: p => `в сети, порт ${p}`, up: 'в сети, порты закрыты', down: 'не в сети' },
  noipMsg: 'У очереди нет IP-адреса (WSD или USB). Переведите её на порт Standard TCP/IP.',
  noSup: 'Принтер отвечает, но уровень расходников не отдаёт. Проверьте его в разделе «Управление».',
  noCartMsg: 'Принтер сообщает, что картридж не установлен.',
  offSince: w => `Не в сети с <b>${w}</b>. Показаны последние известные данные.`,
  dataFrom: a => `данные ${a}`, offShort: 'не в сети',
  some: 'есть', na: 'н/д', free: 'свободно',
  empty: 'Под фильтр ничего не попало.',
  color: { k: 'Чёрный', c: 'Голубой', m: 'Пурпурный', y: 'Жёлтый' },
  colorLow: { k: 'чёрный', c: 'голубой', m: 'пурпурный', y: 'жёлтый' },
  kindShort: { toner: 'Тонер', ink: 'Чернила', drum: 'Барабан', dev: 'Девелопер', waste: 'Отработка', fuser: 'Печка', belt: 'Ремень', roller: 'Ролик', kit: 'Рем. комплект', staple: 'Скобы', other: 'Расходник' },
  kindFull: { toner: 'Тонер', ink: 'Чернила', drum: 'Фотобарабан', dev: 'Девелопер', waste: 'Контейнер отработки', fuser: 'Фьюзер (печка)', belt: 'Ремень переноса', roller: 'Ролик переноса', kit: 'Ремкомплект', staple: 'Скобы', other: 'Расходник' },
  alerts: { lowPaper: ['Мало бумаги', 'warn'], noPaper: ['Нет бумаги', 'err'], lowToner: ['Мало тонера', 'warn'], noToner: ['Нет тонера', 'err'], doorOpen: ['Открыта крышка', 'err'],
    jammed: ['Замятие бумаги', 'err'], offline: ['Офлайн', ''], service: ['Нужно обслуживание', 'warn'], trayMissing: ['Нет лотка', 'warn'], outTrayMissing: ['Нет выходного лотка', 'warn'],
    supplyMissing: ['Нет картриджа', 'err'], outNearFull: ['Выходной лоток почти полон', 'warn'], outFull: ['Выходной лоток полон', 'err'], trayEmpty: ['Лоток пуст', 'warn'], maintenance: ['Просрочено ТО', 'warn'] },
  kv: { via: 'Данные получены', status: 'Состояние', model: 'Модель', vendor: 'Производитель', ip: 'IP-адрес', serial: 'Серийный номер', sysName: 'Сетевое имя', location: 'Расположение', pages: 'Всего страниц', source: 'Откуда взят' },
  via: { snmp: 'по SNMP', web: 'с веб-страницы' },
  src: { queue: 'Принт-сервер', scan: 'Сканирование', 'queue+scan': 'Принт-сервер и сканирование', manual: 'Добавлен вручную', probe: 'Разовый запрос' },
  dev: { 1: 'неизвестно', 2: 'работает', 3: 'есть предупреждения', 4: 'тестирование', 5: 'не работает' },
  prn: { 1: 'другое', 2: 'неизвестно', 3: 'ожидает', 4: 'печатает', 5: 'прогревается' },
  display: 'Экран принтера', supplies: 'Расходники', queues: 'Очереди печати',
  jobs: n => n ? `${n} ${plural(n, 'задание', 'задания', 'заданий')}` : 'пусто',
  openWeb: 'Веб-интерфейс', pollNow: 'Опросить', pollQueued: 'Опрос запущен',
  edit: 'Изменить', hide: 'Скрыть', show: 'Показать', remove: 'Убрать из мониторинга', close: 'Закрыть',
  noHistory: 'история копится',
  perDay: v => `расход ${v.toLocaleString('ru-RU', { maximumFractionDigits: 1 })} % в день`,
  justNow: 'только что', minAgo: n => `${n} мин назад`, hAgo: n => `${n} ч назад`, dAgo: n => `${n} ${plural(n, 'день', 'дня', 'дней')} назад`,
  kinds: 'Все типы', states: 'Все состояния', showHidden: 'Показывать скрытые',
  csv: 'Выгрузить CSV',
  admin: 'Администратор', logout: 'Выйти', sessionTill: t => `Сессия до ${t}`,
  gate: { title: 'Вход', sub: 'Учётная запись администратора', user: 'Логин', password: 'Пароль', enter: 'Войти', entering: 'Проверяю…',
    remember: h => `Вход запомнится на этом устройстве на ${h} ${plural(h, 'час', 'часа', 'часов')}.`,
    wrong: n => n > 0 ? `Неверный логин или пароль. Осталось попыток: ${n}.` : 'Неверный логин или пароль.',
    locked: s => `Слишком много попыток. Вход заблокирован на ${Math.max(1, Math.ceil(s / 60))} мин.`,
    offline: 'Сервер дашборда не отвечает. Проверьте, что контейнеры запущены: docker compose ps',
    expired: 'Сессия закончилась. Войдите снова.', loggedOut: 'Вы вышли из системы.',
    showPw: 'Показать пароль', hidePw: 'Скрыть пароль',
    setTitle: 'Придумайте пароль', setSub: 'Вы вошли со стартовым паролем из логов контейнера. Задайте свой, и стартовый перестанет работать.',
    newPw: 'Новый пароль', repeat: 'Повторите пароль', setBtn: 'Сохранить и войти',
    tagline: 'Тонер, барабаны и печки всех принтеров колледжа в одном окне' },
  pw: { short: 'Минимум 8 символов', long: 'Слишком длинный пароль (максимум 256 символов)', locked: 'Слишком много неверных попыток, подождите 5 минут', mismatch: 'Пароли не совпадают', current: 'Текущий пароль указан неверно', weak: 'Новый пароль не должен совпадать со старым или с логином',
    lvl: ['Слабый', 'Так себе', 'Хороший', 'Надёжный'] },
  acc: { pwTitle: 'Пароль', pwSub: 'После смены все остальные устройства выйдут из системы.', current: 'Текущий пароль', change: 'Сменить пароль', changed: 'Пароль изменён',
    sessTitle: 'Активные сессии', sessSub: h => `Каждый вход действует ${h} ${plural(h, 'час', 'часа', 'часов')}. Завершите сессии, которые вам не знакомы.`,
    thisDevice: 'Это устройство', end: 'Завершить', endOthers: 'Завершить остальные', since: 'вход', till: 'до', ended: 'Сессия завершена',
    tokTitle: 'API-токен', tokSub: 'Для скриптов, Prometheus и Zabbix. Передаётся в заголовке Authorization. Токен даёт только чтение данных и запуск опроса.',
    tokNone: 'Токен ещё не выпущен.', tokHint: h => `Текущий токен: ${h}`, tokOnce: 'Скопируйте токен сейчас: он показывается один раз, в базе хранится только его хеш.',
    issue: 'Выпустить токен', copy: 'Копировать', copied: 'Скопировано', renew: 'Выпустить новый', renewQ: 'Старый токен перестанет работать во всех скриптах. Выпустить новый?', renewed: 'Выпущен новый токен' },
  sys: { poll: 'Последний опрос', pollSub: (n, s) => `${n} ${plural(n, 'принтер', 'принтера', 'принтеров')}, каждые ${Math.round(s / 60)} мин`, scan: 'Сканирование сети', scanSub: n => `найдено ${n}`, never: 'ещё не было',
    down: 'Нет связи', downSub: n => n ? 'см. список ниже' : 'все отвечают', srv: 'Сервер', srvSub: (up, mb) => `работает ${up}` + (mb ? `, ${mb} МБ` : ''), sec: s => `${s} с` },
  check: 'Проверить',
  probeTitle: 'SNMP-запрос к принтеру', probeSub: 'Впишите IP из локальной сети: сервис опросит именно этот адрес и покажет всё, что отдаёт принтер.',
  ipLabel: 'IP-адрес принтера', comLabel: 'SNMP community', comHint: 'по умолчанию из настроек',
  probeBtn: 'Отправить запрос', probing: ip => `Отправляю SNMP-запрос на ${ip}…`,
  probeOk: (ip, ms) => `Принтер ${ip} ответил за ${fmtInt(ms)} мс`,
  probeFail: ip => `${ip} не ответил по SNMP`, probeFailSub: 'Проверьте, что принтер включён, SNMP включён в его веб-интерфейсе и community совпадает. Веб-страницу сервис тоже проверил.',
  raw: 'Что отдал принтер', addMon: 'Добавить в мониторинг', inMon: 'Уже в мониторинге', added: 'Принтер добавлен, опрашиваю…',
  manualTitle: 'Добавленные вручную', manualSub: 'Принтеры, которые опрашиваются по IP независимо от сканирования', manualEmpty: 'Пока ничего не добавлено.',
  netTitle: 'Сканирование сети', netSub: 'Подсети, в которых принтеры ищутся автоматически (раз в час)',
  addSubnet: 'Добавить', subnetPh: '192.168.10.0/24', saveNet: 'Сохранить подсети', rescan: 'Пересканировать сейчас',
  ovTitle: 'Скрытые и переименованные', ovSub: 'Ваши правки поверх данных принтеров', ovEmpty: 'Правок нет.',
  reset: 'Сбросить',
  editTitle: 'Правка принтера', nameLabel: 'Отображаемое имя', locLabel: 'Расположение', hideLabel: 'Скрыть с дашборда', save: 'Сохранить', cancel: 'Отмена',
  settingsTitle: 'Настройки', settingsSub: 'Изменения применяются сразу и сохраняются в базе данных',
  s: { hideWaste: 'Скрывать контейнер отработки, если принтер не сообщает его заполненность', sessionHours: 'Сколько действует вход, часов', orgName: 'Название организации', siteName: 'Заголовок дашборда', warnPct: 'Порог «мало», %', critPct: 'Порог «менять», %', pollSeconds: 'Опрос принтеров, сек',
    discoveryMinutes: 'Сканирование сети, мин', community: 'SNMP community', forgetDays: 'Забывать выключенные через, дней', historyDays: 'Хранить историю уровней, дней',
    excludeIps: 'Игнорировать IP (по одному в строке)' },
  readonly: 'Задаётся в .env, нужен перезапуск контейнера', saved: 'Сохранено', saveErr: 'Не удалось сохранить',
  logTitle: 'Журнал опросов', auto: 'Автообновление',
  apiTitle: 'REST API', apiSub: 'Все данные дашборда доступны по HTTP. Браузер пользуется сессией после входа, скрипты передают API-токен из раздела «Безопасность».',
  apiExample: 'Пример',
  done: 'Готово', err: 'Ошибка',
};

const ICO = {
  grid: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  printer: '<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/>',
  drop: '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
  sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  code: '<path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  trash: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  eye: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="M17.9 17.9A10.1 10.1 0 0 1 12 20C5 20 1 12 1 12a18.5 18.5 0 0 1 5.1-5.9M9.9 4.2A9.1 9.1 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.2 3.2M1 1l22 22"/><path d="M14.1 14.1a3 3 0 1 1-4.2-4.2"/>',
  send: '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  alert: '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  wifi: '<path d="M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M12 19.5h.01M1.5 9a15 15 0 0 1 21 0"/>',
  gauge: '<path d="M12 14l4-4"/><path d="M3.3 17a9 9 0 1 1 17.4 0"/>',
  refresh: '<path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 5v4h4"/><path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"/>',
  moon: '<path d="M12 3a7.5 7.5 0 0 0 8.3 12A9 9 0 1 1 12 3z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  search: '<circle cx="10" cy="10" r="7"/><path d="M21 21l-6-6"/>',
  x: '<path d="M18 6L6 18M6 6l12 12"/>',
  off: '<path d="M3 3l18 18"/><path d="M12 19h.01"/><path d="M9.2 15.6a4 4 0 0 1 5.6 0"/><path d="M6.3 12.6a8 8 0 0 1 3-1.8M14.6 10.9a8 8 0 0 1 3.1 1.7"/><path d="M3.4 9.6a12 12 0 0 1 3.2-2.2M11 6.1a12 12 0 0 1 9.6 3.5"/>',
  plug: '<path d="M9 7V3M15 7V3"/><path d="M6 7h12v4a6 6 0 0 1-12 0z"/><path d="M12 17v4"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v4h1"/>',
  ext: '<path d="M12 6H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6M11 13l9-9M15 4h5v5"/>',
  radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6-6"/>',
  shield: '<path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M14 9l2 2"/>',
  chev: '<path d="M6 9l6 6 6-6"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  server: '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
  monitor: '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
};
const ico = n => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICO[n]}</svg>`;

const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ORD = { crit: 0, warn: 1, offline: 2, nodata: 3, noip: 4, ok: 5 };
const TINTS = ['k', 'c', 'm', 'y'];
const CODE_RX = /\b([A-Z]{1,5}-?\d{2,5}[A-Z]{0,3}|\d{3}R\d{5})\b/;
const VENDOR_ORDER = ['Canon', 'Pantum', 'Xerox', 'HP', 'Kyocera', 'Brother', 'Ricoh', 'Epson', 'Lexmark', 'Konica Minolta', 'Samsung', 'OKI', 'Sharp', 'Toshiba', 'Katusha', 'Dell'];
const VENDOR_COLOR = { Canon: '#D92D20', Pantum: '#F79009', Xerox: '#E31937', HP: '#0096D6', Kyocera: '#6D6E71', Brother: '#0B3D91', Ricoh: '#CF142B', Epson: '#003399', Lexmark: '#12B76A', 'Konica Minolta': '#0072BC', Samsung: '#1428A0', OKI: '#004B87', Sharp: '#E60012', Toshiba: '#E60012', Katusha: '#7A5AF8', Dell: '#007DB8' };
const codeOf = s => { if (s.code) return s.code; const m = String(s.name || '').toUpperCase().match(CODE_RX); return m ? m[1] : null; };
const kindOf = s => s.kind || (TINTS.includes(s.color) ? 'toner' : (T.kindShort[s.color] ? s.color : 'other'));
const tintOf = s => s.tint || (TINTS.includes(s.color) ? s.color : null);
function label(s, sups) {
  const k = kindOf(s), t = tintOf(s);
  if (k === 'toner' || k === 'ink') return T.color[t] || T.kindShort[k];
  if ((k === 'drum' || k === 'dev') && t && (sups || []).filter(x => kindOf(x) === k).length > 1) return `${T.kindShort[k]} ${t.toUpperCase()}`;
  return T.kindShort[k] || T.kindShort.other;
}
const fullLabel = s => { const k = kindOf(s), t = tintOf(s); return T.kindFull[k] + (t && k !== 'waste' ? ', ' + T.colorLow[t] : ''); };
const vendorChip = v => v ? `<span class="vchip"><i style="--vc:${VENDOR_COLOR[v] || '#667085'}">${esc(v.slice(0, 1))}</i>${esc(v)}</span>` : `<span class="muted">${T.unknownVendor}</span>`;

const S = { data: null, etag: null, fail: false, route: 'dashboard', filter: 'all', vendor: '', q: '', sort: 'problem', group: 'none',
  kind: '', sstate: '', showHidden: false, intro: true, openId: null, editOpen: false, refreshing: false,
  me: null, started: false, probe: null, logAuto: true, logTimer: null, net: null, tickTimer: null, showDown: true };
try { const u = JSON.parse(localStorage.getItem('toner-ui') || '{}'); ['filter', 'sort', 'group', 'vendor', 'showDown'].forEach(k => { if (u[k] != null) S[k] = u[k]; }); localStorage.removeItem('toner-admin'); } catch (e) { }
const saveUi = () => { try { localStorage.setItem('toner-ui', JSON.stringify({ filter: S.filter, sort: S.sort, group: S.group, vendor: S.vendor, showDown: S.showDown })); } catch (e) { } };
const root = document.documentElement;

/* ---------- helpers ---------- */
function toast(text, kind = 'ok') {
  const d = document.createElement('div'); d.className = kind;
  d.innerHTML = ico(kind === 'ok' ? 'check' : 'alert') + `<span>${esc(text)}</span>`;
  $('toast').appendChild(d); setTimeout(() => d.remove(), 3500);
}
async function api(path, opt = {}) {
  const h = { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' };
  let r;
  try { r = await fetch(path, { method: opt.method || 'GET', headers: h, body: opt.body ? JSON.stringify(opt.body) : undefined, cache: 'no-store' }); }
  catch (e) { return { ok: false, status: 0, data: null }; }
  let j = null; try { j = await r.json(); } catch (e) { }
  if (!opt.auth && (r.status === 401 || r.status === 403)) authLost(r.status);
  return { ok: r.ok, status: r.status, data: j };
}
function ago(v) {
  const s = Math.max(0, (Date.now() - new Date(v).getTime()) / 1000);
  if (s < 60) return T.justNow; if (s < 3600) return T.minAgo(Math.floor(s / 60));
  if (s < 172800) return T.hAgo(Math.floor(s / 3600)); return T.dAgo(Math.floor(s / 86400));
}
const whenStr = unix => new Date(unix * 1000).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
const pillOf = p => p.noCartridge ? T.pillNoCart : p.error ? T.errPill : (p.stale ? T.pillStale : (T.pill[p.state] || p.state));
const badgeOf = p => `<span class="badge st st-${p.state}">${esc(pillOf(p))}</span>` + (p.hidden ? ` <span class="badge">${T.hiddenPill}</span>` : '');
const alertBadges = (p, max = 3) => (p.alerts || []).filter(a => T.alerts[a] && T.alerts[a][1]).slice(0, max).map(a => `<span class="badge ${T.alerts[a][1]}">${ico('alert')}${T.alerts[a][0]}</span>`).join('');
const isDown = p => p.state === 'offline' || p.state === 'noip';
const allP = () => (S.data && S.data.printers) || [];
const visP = () => allP().filter(p => !p.hidden);
const vendorsOf = ps => { const set = new Set(ps.map(p => p.vendor || '')); return [...set].sort((a, b) => { const ia = VENDOR_ORDER.indexOf(a), ib = VENDOR_ORDER.indexOf(b); return (a ? (ia < 0 ? 50 : ia) : 99) - (b ? (ib < 0 ? 50 : ib) : 99) || a.localeCompare(b); }); };
const staleNote = p => `<div class="note">${ico('off')}<span>${T.offSince(esc(whenStr(p.lastSeen)))}</span></div>`;

/* ---------- theme / chrome ---------- */
function applyTheme(t) { if (t) root.dataset.theme = t; else delete root.dataset.theme; }
try { applyTheme(localStorage.getItem('toner-theme')); } catch (e) { }
const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
function setThemeBtn() { const b = $('theme'); b.innerHTML = ico(isDark() ? 'sun' : 'moon'); b.title = isDark() ? T.themeToLight : T.themeToDark; }
$('theme').onclick = () => { const t = isDark() ? 'light' : 'dark'; applyTheme(t); try { localStorage.setItem('toner-theme', t); } catch (e) { } setThemeBtn(); };
$('burger').innerHTML = ico('menu');
$('burger').onclick = () => { $('sidebar').classList.add('open'); $('backdrop').classList.add('open'); };
$('backdrop').onclick = closeSidebar;
function closeSidebar() { $('sidebar').classList.remove('open'); $('backdrop').classList.remove('open'); }
$('sIco').outerHTML = ico('search');
$('q').placeholder = T.search;
$('q').addEventListener('input', e => { S.q = e.target.value.trim().toLowerCase(); if (['dashboard', 'printers', 'supplies'].includes(S.route)) renderView(false); });
$('refresh').innerHTML = ico('refresh'); $('refresh').title = T.refresh;
$('refresh').onclick = async () => {
  if (S.refreshing) return;
  S.refreshing = true; $('refresh').classList.add('spin'); renderHeader();
  const before = S.data && S.data.updated;
  await api('api/refresh', { method: 'POST' });
  const t0 = Date.now();
  while (Date.now() - t0 < 180000) {
    await sleep(1500);
    const h = (await api('api/health')).data; if (!S.started) break; if (h && !h.polling && h.updated && h.updated !== before) break;
  }
  S.refreshing = false; $('refresh').classList.remove('spin'); await load();
};
$('who').onclick = e => { e.stopPropagation(); const m = $('whoMenu'); m.hidden = !m.hidden; if (!m.hidden) renderWhoMenu(); };
document.addEventListener('click', e => { if (!e.target.closest('#whoMenu')) $('whoMenu').hidden = true; });
(function initStatic() {
  const fav = $('atom').outerHTML.replace('class="plogo" id="atom"', 'xmlns="http://www.w3.org/2000/svg"').replace(/currentColor/g, '#2E2F53').replace(/ class="nd" style="[^"]*"/g, '');
  const l = document.createElement('link'); l.rel = 'icon'; l.href = 'data:image/svg+xml,' + encodeURIComponent(fav); document.head.appendChild(l);
  const img = $('logoImg'); img.onload = () => { img.hidden = false; $('atom').style.display = 'none'; }; img.src = 'logo';
  setThemeBtn(); renderWho(); renderNav();
})();

function renderWho() {
  const u = (S.me && S.me.user) || 'admin';
  $('who').innerHTML = `<span class="av">${esc(u.slice(0, 1).toUpperCase())}</span><span class="nm">${esc(u)}</span>${ico('chev')}`;
  $('who').title = T.admin;
}
function renderWhoMenu() {
  const m = $('whoMenu'), me = S.me || {};
  const till = me.exp ? new Date(me.exp * 1000).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  m.innerHTML = `<div class="wm-head"><b>${esc(me.user || 'admin')}</b><span>${T.admin}</span>${till ? `<small>${ico('clock')}${esc(T.sessionTill(till))}</small>` : ''}</div>` +
    `<a href="#/account" class="wm-item">${ico('shield')}${T.nav.account}</a><a href="#/settings" class="wm-item">${ico('gear')}${T.nav.settings}</a>` +
    `<button type="button" class="wm-item danger" id="wmOut">${ico('logout')}${T.logout}</button>`;
  m.querySelectorAll('a').forEach(a => a.onclick = () => { m.hidden = true; });
  $('wmOut').onclick = logout;
}
function renderNav() {
  const ps = visP();
  const nCrit = ps.filter(p => p.state === 'crit').length;
  const item = (r, icon, text, extra = '') => `<a class="mi${S.route === r ? ' active' : ''}" href="#/${r === 'dashboard' ? '' : r}">${ico(icon)}<span>${text}</span>${extra}</a>`;
  const nDown = ps.filter(isDown).length;
  $('nav').innerHTML = `<h3>${T.nav.menu}</h3>` +
    item('dashboard', 'grid', T.nav.dashboard, nCrit ? `<span class="cnt err">${nCrit}</span>` : '') +
    item('printers', 'printer', T.nav.printers, ps.length ? `<span class="cnt">${ps.length}</span>` : '') +
    item('supplies', 'drop', T.nav.supplies) +
    `<h3>${T.nav.admin}</h3>` + item('manage', 'sliders', T.nav.manage, nDown ? `<span class="cnt">${nDown}</span>` : '') + item('settings', 'gear', T.nav.settings) + item('log', 'list', T.nav.log) + item('account', 'shield', T.nav.account) +
    `<h3>${T.nav.dev}</h3>` + item('api', 'code', T.nav.api);
  const d = S.data || {};
  $('orgShort').textContent = T.orgShort; $('appName').textContent = T.app;
  $('sbFoot').innerHTML = `${esc(d.orgName || T.org)}<br>${d.server ? 'Сервер ' + esc(d.server) + ', ' : ''}v${esc(d.version || '')}${d.demo ? ', ' + T.demo : ''}`;
}

/* ---------- data ---------- */
async function load() {
  let changed = true;
  try {
    const h = S.etag && S.data ? { 'If-None-Match': S.etag } : {};
    const r = await fetch('api/printers', { cache: 'no-store', headers: h });
    if (r.status === 401 || r.status === 403) { authLost(r.status); return; }
    if (r.status === 304) changed = false;
    else { if (!r.ok) throw new Error(r.status); S.data = await r.json(); S.etag = r.headers.get('ETag'); }
    S.fail = false;
  } catch (e) { S.fail = true; }
  renderHeader(); renderNav();
  if (changed && ['dashboard', 'printers', 'supplies'].includes(S.route)) renderView(false);
  if (changed && S.openId) renderModal();
}
function progressShort(p) {
  if (!p) return T.polling;
  if (p.phase === 'scan') return T.pScanShort(p.done, p.total);
  if (p.phase === 'queues') return T.pQueues;
  if (p.phase === 'poll') return T.pPollShort(p.done, p.total);
  return T.polling;
}
function progressLong(p) {
  if (!p) return T.polling;
  if (p.phase === 'scan') return T.pScan(p.done, p.total, p.found);
  if (p.phase === 'queues') return T.pQueues;
  if (p.phase === 'poll') return T.pPoll(p.done, p.total, p.current);
  return T.polling;
}
function renderHeader() {
  const d = S.data;
  document.title = (d && d.siteName) || T.title;
  const busy = !!(d && d.polling) || S.refreshing;
  document.body.classList.toggle('top-busy', busy);
  const u = $('upd');
  u.className = 'upd' + (S.fail ? ' dead' : (busy ? ' busy' : ''));
  let txt = '';
  if (S.fail) txt = T.lost;
  else if (d && d.polling) txt = progressShort(d.progress);
  else if (d && d.updated) txt = `${T.updated} ${new Date(d.updated).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}, ${ago(d.updated)}`;
  u.innerHTML = `<span class="live"></span><span class="t">${esc(txt)}</span>`;
}

/* ---------- routing ---------- */
const ROUTES = ['dashboard', 'printers', 'supplies', 'manage', 'settings', 'log', 'account', 'api'];
function route() {
  if (!S.started) return;
  const r = location.hash.replace(/^#\/?/, '').split('?')[0] || 'dashboard';
  S.route = ROUTES.includes(r) ? r : 'dashboard';
  closeSidebar(); renderNav(); $('whoMenu').hidden = true;
  if (S.logTimer) { clearInterval(S.logTimer); S.logTimer = null; }
  renderView(true);
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);
const pageHead = (title, right = '') => `<div class="ph"><div><h2>${title}</h2><div class="crumbs">${T.home} / <b>${title}</b></div></div>${right ? `<div class="tools">${right}</div>` : ''}</div>`;

function renderView(full) {
  const v = $('view');
  const r = S.route;
  if (r === 'dashboard') v.innerHTML = dashboardView();
  else if (r === 'printers') v.innerHTML = printersView();
  else if (r === 'supplies') v.innerHTML = suppliesView();
  else if (!full) return;
  else if (r === 'manage') { v.innerHTML = manageView(); bindManage(); }
  else if (r === 'settings') { v.innerHTML = `<div class="empty"><span class="loader"></span>${T.loading}</div>`; loadSettings(); }
  else if (r === 'log') { v.innerHTML = logView(); bindLog(); }
  else if (r === 'account') { v.innerHTML = accountView(); bindAccount(); }
  else if (r === 'api') { v.innerHTML = `<div class="empty"><span class="loader"></span>${T.loading}</div>`; loadApi(); }
  if (S.intro && S.data && (S.data.printers || []).length && r === 'dashboard') { v.classList.add('intro'); S.intro = false; setTimeout(() => v.classList.remove('intro'), 2600); }
}

/* ---------- dashboard ---------- */
function replaceItems(ps) {
  const out = [];
  ps.forEach(p => {
    const low = (p.supplies || []).filter(s => s.state === 'crit' || s.state === 'warn');
    if (p.noCartridge && !low.some(s => s.pct === 0)) out.push({ p, s: null, crit: true });
    low.forEach(s => out.push({ p, s, crit: s.state === 'crit' }));
  });
  return out.sort((a, b) => (a.crit ? 0 : 1) - (b.crit ? 0 : 1) || (a.s ? a.s.pct ?? 999 : -1) - (b.s ? b.s.pct ?? 999 : -1));
}
function lowest(ps) {
  let best = null;
  ps.forEach(p => { if (p.stale) return; (p.supplies || []).forEach(s => { const k = kindOf(s); if ((k === 'toner' || k === 'ink') && s.pct != null && (!best || s.pct < best.s.pct)) best = { p, s }; }); });
  return best;
}
function matchQ(p) {
  if (!S.q) return true;
  const hay = [p.name, p.model, p.vendor, p.ip, p.location, p.sysName, p.serial].concat((p.supplies || []).map(s => s.name + ' ' + label(s, p.supplies) + ' ' + (codeOf(s) || ''))).join(' ').toLowerCase();
  return hay.includes(S.q);
}
function matchState(p) {
  if (S.filter === 'off') return ['offline', 'noip', 'nodata'].includes(p.state);
  return S.filter === 'all' || p.state === S.filter;
}
const matchVendor = p => !S.vendor || (S.vendor === '-' ? !p.vendor : p.vendor === S.vendor);
function ipNum(ip) { const p = String(ip || '').split('.').map(Number); return p.length === 4 && p.every(n => n >= 0 && n < 256) ? ((p[0] * 256 + p[1]) * 256 + p[2]) * 256 + p[3] : 1e12; }
function whereCell(p) {
  const loc = p.location || '';
  if (!loc) return `<td class="muted">—</td>`;
  const i = loc.indexOf(','), head = i > 0 ? loc.slice(0, i) : loc, tail = i > 0 ? loc.slice(i + 1).trim() : '';
  return `<td class="where"><div class="t-main">${esc(tail || head)}</div>${tail ? `<div class="t-sub">${esc(head)}</div>` : ''}</td>`;
}
function reachText(p) {
  if (p.reach === 'port') return T.offPort(p.reachPort);
  if (p.reach === 'up') return T.offUp;
  if (p.reach === 'down') return T.offDown;
  return T.offMsg;
}
function sorter(a, b) {
  const da = isDown(a), db = isDown(b);
  if (da !== db) return da ? 1 : -1;
  if (S.sort === 'name') return a.name.localeCompare(b.name, 'ru', { numeric: true });
  if (S.sort === 'ip') return ipNum(a.ip) - ipNum(b.ip);
  if (S.sort === 'pages') return (b.pages || 0) - (a.pages || 0);
  return (ORD[a.state] ?? 9) - (ORD[b.state] ?? 9) || (a.minPct ?? 101) - (b.minPct ?? 101) || a.name.localeCompare(b.name, 'ru', { numeric: true });
}
function statusSeg(ps) {
  const c = { all: ps.length, crit: 0, warn: 0, off: 0, ok: 0 };
  ps.forEach(p => { if (['offline', 'noip', 'nodata'].includes(p.state)) c.off++; else if (c[p.state] != null) c[p.state]++; });
  return `<div class="seg" data-seg="filter">${Object.keys(T.f).map(k => `<button type="button" data-v="${k}" aria-pressed="${S.filter === k}">${T.f[k]} <b>${c[k]}</b></button>`).join('')}</div>`;
}
const vendorSel = ps => `<select class="sel" data-sel="vendor"><option value="">${T.allVendors}</option>${vendorsOf(ps).map(v => `<option value="${v ? esc(v) : '-'}"${S.vendor === (v || '-') ? ' selected' : ''}>${v ? esc(v) : T.unknownVendor}</option>`).join('')}</select>`;
const optSel = (key, dict) => `<select class="sel" data-sel="${key}">${Object.keys(dict).map(k => `<option value="${k}"${S[key] === k ? ' selected' : ''}>${dict[k]}</option>`).join('')}</select>`;

function metric(icon, cls, lbl, val, sub, badge = '') {
  return `<div class="metric"><div class="m-ic ${cls}">${ico(icon)}</div><div class="m-row"><div style="min-width:0"><span class="l">${lbl}</span><h4>${val}</h4>${sub ? `<div class="m-sub">${sub}</div>` : ''}</div>${badge}</div></div>`;
}

function dashboardView() {
  const d = S.data;
  if (!d) return pageHead(T.nav.dashboard) + (S.fail ? `<div class="empty">${T.lost}</div>` : `<div class="empty"><span class="loader"></span>${T.loading}</div>`);
  const all = visP();
  if (!all.length && !d.updated) {
    const p = d.progress, pct = p && p.total ? Math.round(p.done / p.total * 100) : 0;
    return pageHead(T.nav.dashboard) + `<div class="card"><div class="prog"><b><span class="loader"></span>${T.firstPoll}</b><span>${esc(progressLong(p))}</span>${p && p.total ? `<div class="bar"><i style="width:${pct}%"></i></div>` : ''}</div></div>`;
  }
  const items = replaceItems(all);
  const nC = items.filter(x => x.crit).length, nW = items.length - nC;
  const online = all.filter(p => p.online).length;
  let sum = 0, n = 0;
  all.forEach(p => (p.supplies || []).forEach(s => { const k = kindOf(s); if ((k === 'toner' || k === 'ink') && s.pct != null && !p.stale) { sum += s.pct; n++; } }));
  const lo = lowest(all);
  const loSub = lo ? esc(`${label(lo.s, lo.p.supplies)}, ${lo.p.name}`) : T.mNoneSub;
  const banner = S.fail ? `<div class="banner">${ico('alert')}${T.banner}</div>` : '';
  let html = pageHead(T.nav.dashboard, d.demo ? `<span class="badge brand">${T.demo}</span>` : '') + banner +
    `<div class="metrics">` +
    metric('alert', nC ? 'err' : 'ok', T.mReplace, nC, T.mReplaceSub(nW), nC ? `<span class="badge err">${T.f.crit}</span>` : `<span class="badge ok">${ico('check')}OK</span>`) +
    metric('wifi', 'brand', T.mOnline, `${online}<small> / ${all.length}</small>`, T.mOnlineSub(all.length - online)) +
    metric('gauge', '', T.mAvg, n ? Math.round(sum / n) + '<small>%</small>' : '—', n ? T.mAvgSub(n) : '') +
    metric('drop', lo && lo.s.state === 'crit' ? 'err' : (lo && lo.s.state === 'warn' ? 'warn' : 'ok'), T.mLow, lo ? lo.s.pct + '<small>%</small>' : T.mNone, loSub) +
    `</div>`;

  // replace table + fleet
  const rows = items.slice(0, 12).map(({ p, s }) => {
    if (!s) return `<tr class="click" data-id="${esc(p.id)}"><td><div class="sup-cell"><span class="sw" style="--col:var(--err)"></span><div><div class="t-main">${T.pillNoCart}</div></div></div></td>` +
      `<td><div class="t-main">${esc(p.name)}</div><div class="t-sub">${esc(p.model || p.ip || '')}</div></td>${whereCell(p)}<td class="pct st-crit">0%</td></tr>`;
    const cd = codeOf(s);
    return `<tr class="click st-${s.state}" data-id="${esc(p.id)}"><td><div class="sup-cell"><span class="sw c-${s.color}"></span><div><div class="t-main">${esc(label(s, p.supplies))}</div>${cd ? `<div class="t-sub">${esc(cd)}</div>` : ''}</div></div></td>` +
      `<td><div class="t-main">${esc(p.name)}${p.stale ? ` <span class="badge">${T.offShort}</span>` : ''}</div><div class="t-sub">${esc(p.model || p.ip || '')}</div></td>${whereCell(p)}` +
      `<td><div style="display:flex;align-items:center;gap:10px"><span class="pct">${s.pct != null ? s.pct + '%' : T.na}</span><div class="bar c-${s.color}" style="width:70px"><i style="width:${s.pct || 0}%"></i></div></div></td></tr>`;
  }).join('');
  const st = { ok: 0, warn: 0, crit: 0, off: 0 };
  all.forEach(p => { if (['offline', 'noip', 'nodata'].includes(p.state)) st.off++; else if (st[p.state] != null) st[p.state]++; });
  const segs = [['ok', 'var(--ok)'], ['warn', 'var(--warn)'], ['crit', 'var(--err)'], ['off', 'var(--faint)']];
  const C = 2 * Math.PI * 70; let off = 0;
  const arcs = segs.map(([k, col]) => { const len = all.length ? st[k] / all.length * C : 0; const a = len ? `<circle cx="90" cy="90" r="70" fill="none" stroke="${col}" stroke-width="18" stroke-dasharray="${Math.max(0, len - 3).toFixed(1)} ${C.toFixed(1)}" stroke-dashoffset="${(-off).toFixed(1)}" stroke-linecap="round"/>` : ''; off += len; return a; }).join('');
  const vend = vendorsOf(all).map(v => ({ v, n: all.filter(p => (p.vendor || '') === v).length })).sort((a, b) => b.n - a.n);
  const vmax = Math.max(1, ...vend.map(x => x.n));
  html += `<div class="grid12" style="margin-bottom:24px">` +
    `<div class="card flush span-8"><div class="card-h"><div><h3>${T.replaceTitle}</h3><p>${T.replaceSub}</p></div><a class="btn outline sm" href="#/supplies">${T.nav.supplies}</a></div>` +
    (rows ? `<div class="tbl-wrap"><table class="tbl" id="repTbl"><thead><tr><th>${T.col.supply}</th><th>${T.col.printer}</th><th>${T.col.where}</th><th>${T.col.left}</th></tr></thead><tbody>${rows}</tbody></table></div>`
      : `<div class="empty" style="padding:40px 24px">${ico('check')}<br>${T.replaceEmpty}</div>`) + `</div>` +
    `<div class="card span-4"><div class="card-h"><div><h3>${T.fleet}</h3><p>${T.fleetSub}</p></div></div><div class="donut-wrap">` +
    `<div class="donut"><svg viewBox="0 0 180 180"><circle cx="90" cy="90" r="70" fill="none" stroke="var(--line-2)" stroke-width="18"/>${arcs}</svg><div class="ctr"><b>${all.length}</b><span>${pl(all.length, ['принтер', 'принтера', 'принтеров'])}</span></div></div>` +
    `<div class="legend">${segs.map(([k, col]) => `<div><i style="--lc:${col}"></i>${T.legend[k]}<b>${st[k]}</b></div>`).join('')}</div>` +
    `<div class="divider"></div><div class="vbars">${vend.slice(0, 6).map(x => `<div class="vbar"><div class="top"><span>${x.v ? esc(x.v) : T.unknownVendor}</span><b>${x.n}</b></div><div class="bar"><i style="width:${x.n / vmax * 100}%;--vc:${VENDOR_COLOR[x.v] || 'var(--faint)'}"></i></div></div>`).join('')}</div>` +
    `</div></div></div>`;

  // printer cards
  html += `<div class="card"><div class="card-h"><h3>${T.cardsTitle}</h3><div class="tools">${statusSeg(all)}${vendorSel(all)}${optSel('group', T.group)}${optSel('sort', T.sort)}</div></div>${boardHtml(all)}</div>`;
  return html;
}

let CI = 0;
function tank(s, i, sups) {
  const known = s.pct != null;
  const h = known ? s.pct : (s.level === -3 ? 50 : 0);
  const val = known ? `${s.pct}<small>%</small>` : (s.level === -3 ? T.some : T.na);
  const cd = codeOf(s);
  const tip = `${fullLabel(s)}\n${s.name}` + (known ? `\n${s.pct}%` : '') + (s.waste ? ` (${T.free})` : '');
  return `<div class="tank c-${s.color} st-${s.state}${known ? '' : ' unk'}" title="${esc(tip)}" style="--i:${i}"><div class="vessel"><div class="liquid" style="--h:${h}%"></div></div>` +
    `<div class="tp">${val}</div><div class="tl"><b>${esc(label(s, sups))}</b>${cd ? `<span>${esc(cd)}</span>` : ''}</div></div>`;
}
const note = (icon, text, cls = '') => `<div class="note ${cls}">${ico(icon)}<span>${text}</span></div>`;
function card(p, clickable = true) {
  const ci = CI++;
  const sups = p.supplies || [];
  let body = '';
  if (p.noCartridge) body += note('alert', T.noCartMsg, 'err');
  if (p.state === 'noip') body += note('plug', T.noipMsg);
  else if (p.stale && sups.length) body += staleNote(p) + `<div class="tanks stale${sups.length > 4 ? ' many' : ''}">${sups.map((s, i) => tank(s, i, sups)).join('')}</div>`;
  else if (p.state === 'offline') body += note('off', reachText(p));
  else if (!sups.length) body += note('info', T.noSup);
  else body += `<div class="tanks${sups.length > 4 ? ' many' : ''}">${sups.map((s, i) => tank(s, i, sups)).join('')}</div>`;
  const foot = [];
  if (p.pages != null) foot.push(`<span><b>${fmtInt(p.pages)}</b> ${T.pages}</span>`);
  if (p.stale && p.lastSeen) foot.push(`<span>${T.dataFrom(ago(p.lastSeen * 1000))}</span>`);
  else if (p.jobs) foot.push(`<span>${T.inQueue(p.jobs)}</span>`);
  const al = (p.alerts || []).filter(a => a !== 'supplyMissing' && a !== 'noToner');
  const alHtml = al.length ? `<div class="pc-alerts">${alertBadges({ alerts: al })}</div>` : '';
  return `<article class="pcard st-${p.state}${p.hidden ? ' hid' : ''}" ${clickable ? `data-id="${esc(p.id)}" tabindex="0" role="button"` : ''} style="--ci:${ci}">` +
    `<div class="pc-head"><h4>${esc(p.name)}</h4>${badgeOf(p)}</div>` +
    `<div class="pc-meta"><div class="row">${p.vendor ? vendorChip(p.vendor) : ''}<span>${esc(p.model && p.model !== p.name ? p.model : '')}</span></div>` +
    `<div class="row">${p.ip ? `<span>${esc(p.ip)}</span>` : ''}${p.location ? `<span>${esc(p.location)}</span>` : ''}${p.via === 'web' && sups.length ? `<span class="badge">веб</span>` : ''}</div></div>` +
    alHtml + body + (foot.length ? `<footer class="pc-foot">${foot.join('')}</footer>` : '') + `</article>`;
}
function groupKey(p) {
  if (S.group === 'location') return (p.location || '').split(',')[0].trim() || T.noLocation;
  if (S.group === 'vendor') return p.vendor || T.unknownVendor;
  if (S.group === 'subnet') return /^\d+\.\d+\.\d+\.\d+$/.test(p.ip || '') ? p.ip.split('.').slice(0, 3).join('.') + '.0/24' : T.noIp;
  if (S.group === 'model') return p.model || T.noModel;
  return '';
}
function downBlock(list) {
  if (!list.length) return '';
  return `<section class="down-sec${S.showDown ? ' open' : ''}"><button type="button" class="down-head" id="downToggle" aria-expanded="${S.showDown}">${ico('off')}<span>${T.downTitle}</span><span class="badge">${list.length}</span><small>${T.downSub}</small>${ico('chev')}</button>` +
    (S.showDown ? `<div class="pgrid">${list.map(p => card(p)).join('')}</div>` : '') + `</section>`;
}
function boardHtml(all) {
  const list = all.filter(p => matchState(p) && matchVendor(p) && matchQ(p)).sort(sorter);
  CI = 0;
  if (!list.length) return `<div class="empty">${T.empty}</div>`;
  if (S.group === 'none') {
    const up = list.filter(p => !isDown(p)), down = list.filter(isDown);
    return (up.length ? `<div class="pgrid">${up.map(p => card(p)).join('')}</div>` : '') + downBlock(down);
  }
  const m = new Map();
  list.forEach(p => { const k = groupKey(p); if (!m.has(k)) m.set(k, []); m.get(k).push(p); });
  return [...m.keys()].sort((a, b) => a.localeCompare(b, 'ru', { numeric: true })).map(k => {
    const it = m.get(k), nc = it.filter(p => p.state === 'crit').length, nd = it.filter(isDown).length;
    return `<section class="group"><h4 class="g-head">${esc(k)}<span class="n">${T.printers(it.length)}</span>${nc ? `<span class="badge err">${T.f.crit} ${nc}</span>` : ''}${nd ? `<span class="badge">${T.downTitle} ${nd}</span>` : ''}</h4><div class="pgrid">${it.map(p => card(p)).join('')}</div></section>`;
  }).join('');
}

/* ---------- printers table ---------- */
function printersView() {
  const d = S.data;
  if (!d) return pageHead(T.nav.printers) + `<div class="empty"><span class="loader"></span>${T.loading}</div>`;
  const src = S.showHidden ? allP() : visP();
  const list = src.filter(p => matchState(p) && matchVendor(p) && matchQ(p)).sort(sorter);
  let firstDown = !list.some(p => !isDown(p));
  const rows = list.map(p => {
    const sups = (p.supplies || []).slice(0, 6);
    const bars = sups.length ? `<div class="minibars" title="${esc(sups.map(s => `${label(s, p.supplies)}: ${s.pct ?? '?'}%`).join('\n'))}">${sups.map(s => `<i class="c-${s.color}"><b style="height:${s.pct ?? 0}%"></b></i>`).join('')}</div>` : '<span class="muted">—</span>';
    const minS = (p.supplies || []).filter(s => !s.waste && s.pct != null).sort((a, b) => a.pct - b.pct)[0];
    const sep = isDown(p) && !firstDown ? (firstDown = true, `<tr class="sep"><td colspan="8">${ico('off')}${T.downTitle}</td></tr>`) : '';
    return sep + `<tr class="click${isDown(p) ? ' down' : ''}" data-id="${esc(p.id)}"><td><div class="t-main">${esc(p.name)}</div><div class="t-sub">${esc(p.model || '')}</div></td>` +
      `<td>${vendorChip(p.vendor)}</td><td class="nowrap">${esc(p.ip || '—')}</td><td>${esc(p.location || '')}</td>` +
      `<td><div style="display:flex;align-items:center;gap:10px">${bars}${minS ? `<span class="pct st-${minS.state}">${minS.pct}%</span>` : ''}</div></td>` +
      `<td class="num">${p.pages != null ? fmtInt(p.pages) : '—'}</td><td>${badgeOf(p)}${alertBadges({ alerts: (p.alerts || []).filter(a => a !== 'supplyMissing' && a !== 'noToner') }, 1) ? '<br>' + alertBadges({ alerts: (p.alerts || []).filter(a => a !== 'supplyMissing' && a !== 'noToner') }, 1) : ''}</td>` +
      `<td class="muted small nowrap">${p.stale && p.lastSeen ? ago(p.lastSeen * 1000) : (T.src[p.source] || '')}</td></tr>`;
  }).join('');
  const hid = `<label class="toggle"><input type="checkbox" data-chk="showHidden"${S.showHidden ? ' checked' : ''}><i></i>${T.showHidden}</label>`;
  return pageHead(T.nav.printers, `<a class="btn primary" href="#/manage">${ico('plus')}${T.addMon}</a>`) +
    `<div class="card flush"><div class="card-h"><div class="tools">${statusSeg(src)}${vendorSel(src)}${optSel('sort', T.sort)}${hid}</div></div>` +
    `<div class="tbl-wrap" style="margin-top:18px">${rows ? `<table class="tbl"><thead><tr><th>${T.col.printer}</th><th>${T.col.vendor}</th><th>${T.col.ip}</th><th>${T.col.location}</th><th>${T.col.toner}</th><th class="num">${T.col.pages}</th><th>${T.col.status}</th><th>${T.col.source}</th></tr></thead><tbody>${rows}</tbody></table>` : `<div class="empty">${T.empty}</div>`}</div></div>`;
}

/* ---------- supplies table ---------- */
function suppliesView() {
  const d = S.data;
  if (!d) return pageHead(T.nav.supplies) + `<div class="empty"><span class="loader"></span>${T.loading}</div>`;
  const ps = visP().filter(p => matchVendor(p) && matchQ(p));
  const flat = [];
  ps.forEach(p => (p.supplies || []).forEach(s => flat.push({ p, s })));
  const kinds = [...new Set(flat.map(x => kindOf(x.s)))];
  const list = flat.filter(({ s }) => (!S.kind || kindOf(s) === S.kind) && (!S.sstate || s.state === S.sstate))
    .sort((a, b) => (ORD[a.s.state] ?? 3) - (ORD[b.s.state] ?? 3) || (a.s.pct ?? 999) - (b.s.pct ?? 999));
  const rows = list.map(({ p, s }) => {
    const cd = codeOf(s);
    return `<tr class="click st-${s.state}" data-id="${esc(p.id)}"><td><div class="sup-cell"><span class="sw c-${s.color}"></span><div><div class="t-main">${esc(label(s, p.supplies))}${cd ? ` <span class="t-sub">${esc(cd)}</span>` : ''}</div><div class="t-sub">${esc(s.name)}</div></div></div></td>` +
      `<td class="muted">${esc(fullLabel(s))}</td><td><div class="t-main">${esc(p.name)}${p.stale ? ` <span class="badge">${T.offShort}</span>` : ''}</div><div class="t-sub">${esc([p.vendor, p.location].filter(Boolean).join(', '))}</div></td>` +
      `<td><div style="display:flex;align-items:center;gap:10px"><span class="pct" style="min-width:38px">${s.pct != null ? s.pct + '%' : T.na}</span><div class="bar c-${s.color}" style="width:90px"><i style="width:${s.pct || 0}%"></i></div></div></td>` +
      `<td><span class="badge st st-${s.state}">${{ crit: T.f.crit, warn: T.f.warn, ok: T.f.ok }[s.state] || T.na}</span></td></tr>`;
  }).join('');
  const kindSel = `<select class="sel" data-sel="kind"><option value="">${T.kinds}</option>${kinds.map(k => `<option value="${k}"${S.kind === k ? ' selected' : ''}>${T.kindFull[k] || k}</option>`).join('')}</select>`;
  const stSel = `<select class="sel" data-sel="sstate"><option value="">${T.states}</option>${['crit', 'warn', 'ok', 'unknown'].map(k => `<option value="${k}"${S.sstate === k ? ' selected' : ''}>${{ crit: T.f.crit, warn: T.f.warn, ok: T.f.ok, unknown: T.na }[k]}</option>`).join('')}</select>`;
  return pageHead(T.nav.supplies, `<a class="btn outline" href="api/export.csv">${ico('download')}${T.csv}</a>`) +
    `<div class="card flush"><div class="card-h"><div class="tools">${kindSel}${stSel}${vendorSel(visP())}</div><span class="muted">${list.length}</span></div>` +
    `<div class="tbl-wrap" style="margin-top:18px">${rows ? `<table class="tbl"><thead><tr><th>${T.col.supply}</th><th>${T.col.kind}</th><th>${T.col.printer}</th><th>${T.col.left}</th><th>${T.col.status}</th></tr></thead><tbody>${rows}</tbody></table>` : `<div class="empty">${T.empty}</div>`}</div></div>`;
}

/* ---------- manage ---------- */
function manageView() {
  const ps = allP();
  const manual = ps.filter(p => p.source === 'manual');
  const ov = ps.filter(p => p.hidden || p.renamed || (p.origLocation !== undefined && p.location !== p.origLocation));
  const down = ps.filter(p => isDown(p) && !p.hidden).sort((a, b) => ipNum(a.ip) - ipNum(b.ip));
  const downCard = down.length ? `<div class="card flush span-12"><div class="card-h"><div><h3>${T.downTitle}</h3><p>${T.downSub.split('.')[0]}.</p></div><span class="badge">${down.length}</span></div>` +
    `<div class="tbl-wrap" style="margin-top:18px"><table class="tbl"><tbody>${down.map(p => `<tr><td><div class="t-main">${esc(p.name)}</div><div class="t-sub">${esc([p.ip, p.vendor].filter(Boolean).join(', '))}</div></td>` +
      `<td>${esc(p.location || '')}</td><td><span class="reach r-${esc(p.reach || 'down')}">${esc(p.reach === 'port' ? T.reach.port(p.reachPort) : (T.reach[p.reach] || T.reach.down))}</span></td>` +
      `<td class="muted small nowrap">${p.lastSeen ? T.dataFrom(ago(p.lastSeen * 1000)) : ''}</td>` +
      `<td style="text-align:right;white-space:nowrap">${p.ip ? `<button class="btn outline sm" data-probe="${esc(p.ip)}">${ico('send')}${T.check}</button>` : ''}</td></tr>`).join('')}</tbody></table></div></div>` : '';
  return pageHead(T.nav.manage, `<button class="btn outline" id="btnRescan">${ico('radar')}${T.rescan}</button>`) +
    `<div class="sys" id="sysBox"></div>` +
    `<div class="card" style="margin-bottom:24px"><div class="card-h"><div><h3>${T.probeTitle}</h3><p>${T.probeSub}</p></div></div>` +
    `<form id="probeForm" class="tools" style="align-items:flex-end"><div class="field" style="flex:1 1 220px"><label for="pIp">${T.ipLabel}</label><input class="inp" id="pIp" placeholder="192.168.3.40" inputmode="decimal" required pattern="\\d{1,3}(\\.\\d{1,3}){3}"></div>` +
    `<div class="field" style="flex:1 1 180px"><label for="pCom">${T.comLabel}</label><input class="inp" id="pCom" placeholder="${T.comHint}"></div>` +
    `<button class="btn primary" type="submit" id="pBtn">${ico('send')}${T.probeBtn}</button></form><div id="probeOut"></div></div>` +
    `<div class="grid12"><div class="card flush span-6"><div class="card-h"><div><h3>${T.manualTitle}</h3><p>${T.manualSub}</p></div></div>` +
    (manual.length ? `<div class="tbl-wrap" style="margin-top:18px"><table class="tbl"><tbody>${manual.map(p => `<tr><td><div class="t-main">${esc(p.ip)}</div><div class="t-sub">${esc(p.name)}</div></td><td>${badgeOf(p)}</td><td style="text-align:right"><button class="icon-btn" data-rm="${esc(p.id)}" title="${T.remove}">${ico('trash')}</button></td></tr>`).join('')}</tbody></table></div>` : `<div class="empty" style="padding:28px">${T.manualEmpty}</div>`) + `</div>` +
    `<div class="card span-6"><div class="card-h"><div><h3>${T.netTitle}</h3><p>${T.netSub}</p></div></div><div id="netBox"><span class="loader"></span></div></div>` +
    downCard + `<div class="card flush span-12"><div class="card-h"><div><h3>${T.ovTitle}</h3><p>${T.ovSub}</p></div></div>` +
    (ov.length ? `<div class="tbl-wrap" style="margin-top:18px"><table class="tbl"><tbody>${ov.map(p => `<tr><td><div class="t-main">${esc(p.name)}</div><div class="t-sub">${esc(p.ip || '')}${p.renamed ? ', было: ' + esc(p.origName) : ''}</div></td><td>${esc(p.location || '')}</td><td>${badgeOf(p)}</td><td style="text-align:right;white-space:nowrap"><button class="btn outline sm" data-edit="${esc(p.id)}">${ico('edit')}${T.edit}</button> <button class="btn ghost sm" data-reset="${esc(p.id)}">${T.reset}</button></td></tr>`).join('')}</tbody></table></div>` : `<div class="empty" style="padding:28px">${T.ovEmpty}</div>`) +
    `</div></div>`;
}
async function bindManage() {
  $('probeForm').onsubmit = async e => { e.preventDefault(); runProbe($('pIp').value.trim(), $('pCom').value.trim()); };
  $('btnRescan').onclick = async () => { const r = await api('api/admin/discover', { method: 'POST' }); toast(r.ok ? T.done : T.err, r.ok ? 'ok' : 'err'); setTimeout(load, 1500); };
  $('view').querySelectorAll('[data-rm]').forEach(b => b.onclick = async () => {
    if (!confirm(T.remove + '?')) return;
    const r = await api(`api/admin/printers/${encodeURIComponent(b.dataset.rm)}/remove`, { method: 'POST', body: {} });
    toast(r.ok ? T.done : T.err, r.ok ? 'ok' : 'err'); await sleep(900); await load(); renderView(true);
  });
  $('view').querySelectorAll('[data-edit]').forEach(b => b.onclick = () => { openModal(b.dataset.edit); S.editOpen = true; renderModal(); });
  $('view').querySelectorAll('[data-reset]').forEach(b => b.onclick = async () => {
    const r = await api(`api/admin/printers/${encodeURIComponent(b.dataset.reset)}/override`, { method: 'POST', body: {} });
    toast(r.ok ? T.done : T.err, r.ok ? 'ok' : 'err'); await sleep(900); await load(); renderView(true);
  });
  $('view').querySelectorAll('[data-probe]').forEach(b => b.onclick = () => { $('pIp').value = b.dataset.probe; $('pCom').value = ''; window.scrollTo({ top: 0, behavior: 'smooth' }); runProbe(b.dataset.probe, ''); });
  if (S.probe) renderProbe();
  loadSys();
  const r = await api('api/admin/config');
  if (!r.ok || S.route !== 'manage') return;
  S.net = (r.data.subnets || []).slice();
  renderNet();
}
function dur(sec) {
  sec = Math.max(0, sec | 0);
  const d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60);
  if (d) return `${d} д ${h} ч`; if (h) return `${h} ч ${m} мин`; return `${m} мин`;
}
async function loadSys() {
  const r = await api('api/admin/status');
  const box = $('sysBox'); if (!r.ok || !box) return;
  const s = r.data;
  const tile = (icon, cls, lbl, val, sub) => `<div class="sys-t"><div class="m-ic ${cls}">${ico(icon)}</div><div><span>${lbl}</span><b>${val}</b><small>${sub}</small></div></div>`;
  box.innerHTML =
    tile('refresh', 'brand', T.sys.poll, s.lastCycleSec != null ? T.sys.sec(s.lastCycleSec) : '—', T.sys.pollSub(s.printers, s.pollSeconds)) +
    tile('radar', '', T.sys.scan, s.lastDiscovery ? esc(ago(s.lastDiscovery)) : T.sys.never, T.sys.scanSub(s.discovered)) +
    tile('off', s.offline ? 'warn' : 'ok', T.sys.down, s.offline, T.sys.downSub(s.offline)) +
    tile('server', '', T.sys.srv, esc(s.server), T.sys.srvSub(dur(s.uptimeSec), s.memoryMB));
}
function renderNet() {
  const box = $('netBox'); if (!box) return;
  box.innerHTML = `<div class="chips" style="margin-bottom:16px">${S.net.map((s, i) => `<span class="chip">${esc(s)}<button type="button" data-rmnet="${i}" title="${T.remove}">${ico('x')}</button></span>`).join('')}</div>` +
    `<form id="netForm" class="tools"><input class="inp" id="netIn" placeholder="${T.subnetPh}" style="flex:1 1 180px"><button class="btn outline" type="submit">${ico('plus')}${T.addSubnet}</button><button class="btn primary" type="button" id="netSave">${T.saveNet}</button></form>`;
  box.querySelectorAll('[data-rmnet]').forEach(b => b.onclick = () => { S.net.splice(+b.dataset.rmnet, 1); renderNet(); });
  $('netForm').onsubmit = e => { e.preventDefault(); const v = $('netIn').value.trim(); if (/^\d+\.\d+\.\d+\.\d+(\/\d{1,2})?$/.test(v) && !S.net.includes(v)) { S.net.push(v.includes('/') ? v : v + '/24'); renderNet(); } };
  $('netSave').onclick = async () => { const r = await api('api/admin/config', { method: 'POST', body: { subnets: S.net } }); toast(r.ok ? T.saved : T.saveErr, r.ok ? 'ok' : 'err'); };
}
async function runProbe(ip, community) {
  if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(ip)) return;
  S.probe = { ip, busy: true };
  renderProbe();
  const r = await api('api/admin/probe', { method: 'POST', body: { ip, community } });
  if (!r.ok) { S.probe = { ip, busy: false, error: (r.data && r.data.error) || T.err }; renderProbe(); return; }
  const id = r.data.id, t0 = Date.now();
  while (Date.now() - t0 < 90000) {
    await sleep(700);
    const g = await api(`api/admin/probe/${id}`);
    if (g.ok && g.data && g.data.done) { S.probe = Object.assign({ busy: false }, g.data); break; }
  }
  if (S.probe.busy) S.probe = { ip, busy: false, error: T.err };
  renderProbe();
}
function renderProbe() {
  const o = $('probeOut'); if (!o) return;
  const p = S.probe;
  $('pBtn').disabled = !!p.busy; $('pBtn').classList.toggle('spin', !!p.busy);
  if (p.busy) { o.innerHTML = `<div class="alert info" style="margin-top:20px"><span class="loader"></span><div><b>${esc(T.probing(p.ip))}</b></div></div>`; return; }
  if (p.error) { o.innerHTML = `<div class="alert err" style="margin-top:20px">${ico('alert')}<div><b>${T.err}</b><span>${esc(p.error)}</span></div></div>`; return; }
  const rec = p.record || {};
  const raw = (p.raw || []).map(x => `<tr><td class="t-main nowrap">${esc(x.name)}</td><td><code class="m">${esc(x.oid)}</code></td><td>${x.value == null ? '<span class="muted">—</span>' : esc(x.value)}</td></tr>`).join('');
  const head = p.ok ? `<div class="alert ok" style="margin-top:20px">${ico('check')}<div><b>${esc(T.probeOk(p.ip, p.ms))}</b><span>${esc([rec.vendor, rec.model].filter(Boolean).join(' '))}</span></div></div>`
    : `<div class="alert err" style="margin-top:20px">${ico('alert')}<div><b>${esc(T.probeFail(p.ip))}</b><span>${T.probeFailSub}</span></div></div>`;
  const addBtn = p.monitored ? `<button class="btn outline" disabled>${ico('check')}${T.inMon}</button>` : `<button class="btn primary" id="addMon">${ico('plus')}${T.addMon}</button>`;
  o.innerHTML = head + `<div class="grid12" style="margin-top:20px"><div class="span-4">${rec.online ? card(rec, false) : ''}<div class="tools" style="margin-top:14px">${addBtn}</div></div>` +
    (raw ? `<div class="span-8"><div class="card flush" style="border-radius:12px"><div class="card-h"><h3 style="font-size:15px">${T.raw}</h3></div><div class="tbl-wrap" style="margin-top:12px"><table class="tbl"><tbody>${raw}</tbody></table></div></div></div>` : '') + `</div>`;
  const b = $('addMon');
  if (b) b.onclick = async () => {
    b.disabled = true;
    const r = await api('api/admin/printers', { method: 'POST', body: { ip: p.ip } });
    toast(r.ok ? T.added : T.err, r.ok ? 'ok' : 'err');
    if (r.ok) { S.probe.monitored = true; setTimeout(async () => { await load(); if (S.route === 'manage') renderView(true); }, 5000); }
  };
}

/* ---------- settings ---------- */
async function loadSettings() {
  const r = await api('api/admin/config');
  if (!r.ok || S.route !== 'settings') return;
  const c = r.data;
  const f = (k, type = 'text', extra = '') => `<div class="field"><label for="s_${k}">${T.s[k]}</label><input class="inp" id="s_${k}" type="${type}" value="${esc(c[k])}" ${extra}></div>`;
  const tg = k => `<label class="toggle wide"><input type="checkbox" id="s_${k}"${c[k] ? ' checked' : ''}><i></i>${T.s[k]}</label>`;
  const ta = (k, arr) => `<div class="field wide"><label for="s_${k}">${T.s[k]}</label><textarea class="inp" id="s_${k}" rows="4">${esc((arr || []).join('\n'))}</textarea></div>`;
  $('view').innerHTML = pageHead(T.nav.settings) +
    `<div class="card"><div class="card-h"><div><h3>${T.settingsTitle}</h3><p>${T.settingsSub}</p></div></div><form id="setForm"><div class="form-grid">` +
    f('orgName') + f('siteName') + f('warnPct', 'number', 'min="1" max="99"') + f('critPct', 'number', 'min="0" max="99"') + f('pollSeconds', 'number', 'min="30"') + f('discoveryMinutes', 'number', 'min="5"') +
    f('community') + f('forgetDays', 'number', 'min="1"') + f('sessionHours', 'number', 'min="1" max="720"') + f('historyDays', 'number', 'min="7"') +
    tg('hideWaste') + ta('excludeIps', c.excludeIps) +
    `<div class="field wide"><label>${T.readonly}</label><div class="muted">Порт ${esc(c.port)} на ${esc(c.bind)}, хранилище: ${esc(c.storage)}, администратор: ${esc(c.adminUser)}</div></div>` +
    `</div><div class="m-foot"><button class="btn primary" type="submit">${T.save}</button></div></form></div>`;
  $('setForm').onsubmit = async e => {
    e.preventDefault();
    const v = id => $('s_' + id).value;
    const lines = id => v(id).split(/\r?\n/).map(x => x.trim()).filter(Boolean);
    const body = { orgName: v('orgName'), siteName: v('siteName'), warnPct: +v('warnPct'), critPct: +v('critPct'), pollSeconds: +v('pollSeconds'), discoveryMinutes: +v('discoveryMinutes'),
      community: v('community'), forgetDays: +v('forgetDays'), historyDays: +v('historyDays'),
      hideWaste: $('s_hideWaste').checked, sessionHours: +v('sessionHours'), excludeIps: lines('excludeIps') };
    const r = await api('api/admin/config', { method: 'POST', body });
    toast(r.ok ? T.saved : ((r.data && r.data.error) || T.saveErr), r.ok ? 'ok' : 'err');
    if (r.ok) setTimeout(load, 800);
  };
}

/* ---------- log ---------- */
function logView() {
  return pageHead(T.nav.log, `<label class="toggle"><input type="checkbox" id="logAuto"${S.logAuto ? ' checked' : ''}><i></i>${T.auto}</label><button class="btn outline" id="logRef">${ico('refresh')}</button>`) +
    `<div class="card"><div class="card-h"><div><h3>${T.logTitle}</h3><p id="logFile"></p></div></div><pre class="log" id="logPre"><span class="loader"></span></pre></div>`;
}
function bindLog() {
  const pull = async () => {
    const r = await api('api/admin/log?lines=400');
    if (!r.ok || S.route !== 'log') return;
    const pre = $('logPre'); const atEnd = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 20;
    pre.textContent = (r.data.lines || []).join('\n') || '—';
    $('logFile').textContent = r.data.file || '';
    if (atEnd) pre.scrollTop = pre.scrollHeight;
  };
  pull();
  $('logRef').onclick = pull;
  $('logAuto').onchange = e => { S.logAuto = e.target.checked; setTimer(); };
  const setTimer = () => { if (S.logTimer) clearInterval(S.logTimer); S.logTimer = S.logAuto ? setInterval(pull, 5000) : null; };
  setTimer();
}

/* ---------- api docs ---------- */
async function loadApi() {
  const docs = (await api('api')).data;
  if (S.route !== 'api') return;
  const rows = ((docs && docs.endpoints) || []).map(e => `<tr><td><span class="badge ${e.method === 'GET' ? 'ok' : 'brand'}">${e.method}</span></td><td><code class="m">${esc(e.path)}</code>${e.query ? `<div class="t-sub" style="margin-top:4px">${esc(e.query)}</div>` : ''}</td><td class="muted">${esc(e.description)}</td></tr>`).join('');
  const host = location.origin;
  $('view').innerHTML = pageHead(T.nav.api) + `<div class="card flush"><div class="card-h"><div><h3>${T.apiTitle}</h3><p>${T.apiSub}</p></div></div>` +
    `<div class="tbl-wrap" style="margin-top:18px"><table class="tbl"><tbody>${rows}</tbody></table></div></div>` +
    `<div class="card" style="margin-top:24px"><div class="card-h"><h3>${T.apiExample}</h3></div><pre class="log">curl -H "Authorization: Bearer TOKEN" ${esc(host)}/api/replace?days=14\ncurl -H "Authorization: Bearer TOKEN" "${esc(host)}/api/printers?vendor=Canon,Pantum"\nInvoke-RestMethod ${esc(host)}/api/stats -Headers @{ Authorization = 'Bearer TOKEN' }\n\n# Prometheus: bearer_token: TOKEN, metrics_path: /api/metrics</pre></div>`;
}

/* ---------- account (security) ---------- */
function pwScore(v) {
  if (!v) return 0;
  const cls = [/[a-zа-яё]/, /[A-ZА-ЯЁ]/, /\d/, /[^\wа-яё]/i].filter(r => r.test(v)).length;
  let s = 0;
  if (v.length >= 8) s++;
  if (v.length >= 12) s++;
  if (cls >= 3) s++;
  if (v.length >= 16 || (cls === 4 && v.length >= 10)) s++;
  return v.length < 8 ? Math.min(s, 1) : Math.max(1, s);
}
const meterHtml = id => `<div class="meter" id="${id}" data-s="0"><i class="c-c"></i><i class="c-m"></i><i class="c-y"></i><i class="c-k"></i><span></span></div>`;
function bindMeter(inputId, meterId) {
  const upd = () => { const v = $(inputId).value, s = pwScore(v), m = $(meterId); m.dataset.s = s; m.querySelector('span').textContent = v ? (v.length < 8 ? T.pw.short : T.pw.lvl[s - 1]) : ''; };
  $(inputId).addEventListener('input', upd); upd();
}
const pwField = (id, label, ac, extra = '') => `<div class="field"><label for="${id}">${label}</label><div class="pw-wrap"><input class="inp" id="${id}" type="password" autocomplete="${ac}" required ${extra}>` +
  `<button type="button" class="pw-eye" data-eye="${id}" title="${T.gate.showPw}" aria-label="${T.gate.showPw}">${ico('eye')}</button></div></div>`;
function bindEyes(rootEl) {
  rootEl.querySelectorAll('[data-eye]').forEach(b => b.onclick = () => {
    const i = $(b.dataset.eye), show = i.type === 'password';
    i.type = show ? 'text' : 'password'; b.innerHTML = ico(show ? 'eyeOff' : 'eye');
    b.title = b.ariaLabel = show ? T.gate.hidePw : T.gate.showPw; i.focus();
  });
}
function device(ua) {
  ua = ua || '';
  const b = /Edg\//.test(ua) ? 'Edge' : /YaBrowser/.test(ua) ? 'Яндекс Браузер' : /OPR\//.test(ua) ? 'Opera' : /Firefox\//.test(ua) ? 'Firefox' : /Chrome\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : /PowerShell|curl|python/i.test(ua) ? 'Скрипт' : 'Браузер';
  const os = /Windows/.test(ua) ? 'Windows' : /Android/.test(ua) ? 'Android' : /iPhone|iPad/.test(ua) ? 'iOS' : /Mac OS/.test(ua) ? 'macOS' : /Linux/.test(ua) ? 'Linux' : '';
  return os ? `${b}, ${os}` : b;
}
function accountView() {
  return pageHead(T.nav.account) + `<div class="grid12">` +
    `<div class="card span-6"><div class="card-h"><div><h3>${T.acc.pwTitle}</h3><p>${T.acc.pwSub}</p></div></div>` +
    `<form id="pwForm" class="stack">` + pwField('aCur', T.acc.current, 'current-password') + pwField('aNew', T.gate.newPw, 'new-password', 'minlength="8"') + meterHtml('aMeter') +
    pwField('aRep', T.gate.repeat, 'new-password') + `<div class="g-msg" id="aMsg" role="alert"></div><div><button class="btn primary" type="submit">${T.acc.change}</button></div></form></div>` +
    `<div class="card span-6"><div class="card-h"><div><h3>${T.acc.tokTitle}</h3><p>${T.acc.tokSub}</p></div></div><div id="tokBox"><span class="loader"></span></div></div>` +
    `<div class="card flush span-12"><div class="card-h"><div><h3>${T.acc.sessTitle}</h3><p>${T.acc.sessSub((S.me && S.me.hours) || 12)}</p></div><button class="btn outline sm" id="endOthers">${ico('logout')}${T.acc.endOthers}</button></div><div id="sessBox" style="margin-top:18px"><div class="empty"><span class="loader"></span></div></div></div>` +
    `</div>`;
}
async function bindAccount() {
  const v = $('view');
  bindEyes(v); bindMeter('aNew', 'aMeter');
  $('pwForm').onsubmit = async e => {
    e.preventDefault();
    const cur = $('aCur').value, nw = $('aNew').value, rp = $('aRep').value, msg = $('aMsg');
    if (nw.length < 8) { msg.textContent = T.pw.short; return; }
    if (nw !== rp) { msg.textContent = T.pw.mismatch; return; }
    const r = await api('api/auth/password', { method: 'POST', body: { current: cur, new: nw }, auth: true });
    if (r.ok) { msg.textContent = ''; $('pwForm').reset(); bindMeter('aNew', 'aMeter'); toast(T.acc.changed); loadSessions(); }
    else msg.textContent = T.pw[(r.data && r.data.error) || 'current'] || T.err;
  };
  $('endOthers').onclick = async () => { const r = await api('api/auth/sessions/revoke-others', { method: 'POST' }); toast(r.ok ? T.acc.ended : T.err, r.ok ? 'ok' : 'err'); loadSessions(); };
  loadSessions(); loadToken();
}
async function loadSessions() {
  const r = await api('api/auth/sessions'); const box = $('sessBox');
  if (!r.ok || !box) return;
  const t = u => new Date(u * 1000).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  box.innerHTML = `<div class="tbl-wrap"><table class="tbl"><tbody>${(r.data || []).map(s => `<tr><td><div class="sess-dev"><span class="m-ic${s.current ? ' brand' : ''}">${ico('monitor')}</span><div><div class="t-main">${esc(device(s.ua))}${s.current ? ` <span class="badge brand">${T.acc.thisDevice}</span>` : ''}</div><div class="t-sub">${esc(s.ip)}</div></div></div></td>` +
    `<td class="muted small">${T.acc.since} ${esc(t(s.created))}<br>${T.acc.till} ${esc(t(s.exp))}</td><td class="muted small nowrap">${esc(ago(s.last * 1000))}</td>` +
    `<td style="text-align:right">${s.current ? '' : `<button class="btn ghost sm" data-end="${esc(s.id)}">${T.acc.end}</button>`}</td></tr>`).join('')}</tbody></table></div>`;
  box.querySelectorAll('[data-end]').forEach(b => b.onclick = async () => { await api(`api/auth/sessions/${b.dataset.end}/revoke`, { method: 'POST' }); toast(T.acc.ended); loadSessions(); });
}
async function loadToken(renew) {
  const r = await api('api/auth/token', renew ? { method: 'POST' } : {}); const box = $('tokBox');
  if (!r.ok || !box) return;
  const tok = r.data.token || '';
  const top = tok
    ? `<div class="tok"><code id="tokVal">${esc(tok)}</code><button class="icon-btn" id="tokCopy" title="${T.acc.copy}">${ico('copy')}</button></div><div class="g-msg info" style="margin-top:12px">${ico('info')}<span>${T.acc.tokOnce}</span></div>`
    : `<div class="tok"><code>${esc(r.data.exists ? T.acc.tokHint(r.data.hint || '') : T.acc.tokNone)}</code></div>`;
  box.innerHTML = top +
    `<pre class="log tok-ex">curl -H "Authorization: Bearer TOKEN" ${esc(location.origin)}/api/replace</pre><div style="margin-top:14px"><button class="btn outline sm" id="tokNew">${ico(r.data.exists ? 'refresh' : 'key')}${r.data.exists ? T.acc.renew : T.acc.issue}</button></div>`;
  if ($('tokCopy')) $('tokCopy').onclick = async () => {
    try { await navigator.clipboard.writeText(tok); toast(T.acc.copied); }
    catch (e) { const ta = document.createElement('textarea'); ta.value = tok; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); toast(T.acc.copied); } catch (x) { } ta.remove(); }
  };
  $('tokNew').onclick = async () => { if (r.data.exists && !confirm(T.acc.renewQ)) return; await loadToken(true); toast(T.acc.renewed); };
}

/* ---------- login gate ---------- */
function gateShell(inner) {
  const logo = $('atom').outerHTML.replace('class="plogo" id="atom"', 'class="gate-logo" aria-hidden="true"');
  return `<div class="plate"><div class="ht ht-c"></div><div class="ht ht-m"></div><div class="ht ht-y"></div>` +
    `<i class="crop c1"></i><i class="crop c2"></i><i class="crop c3"></i><i class="crop c4"></i>` +
    `<div class="plate-in">${logo}<h1>${T.orgShort}</h1><p class="plate-app">${T.app}</p><p class="plate-tag">${T.gate.tagline}</p></div>` +
    `<div class="plate-foot">${esc(T.org)}</div></div>` +
    `<div class="gate-side"><button class="circ gate-theme" id="gTheme" type="button"></button><div class="gate-box">${inner}</div></div>`;
}
function mountGate(inner) {
  document.body.classList.add('gated');
  const g = $('gate'); g.hidden = false; g.innerHTML = gateShell(inner);
  const tb = $('gTheme'); const st = () => { tb.innerHTML = ico(isDark() ? 'sun' : 'moon'); tb.title = isDark() ? T.themeToLight : T.themeToDark; };
  st(); tb.onclick = () => { $('theme').click(); st(); };
  bindEyes(g);
}
function gateMsg(text, kind = 'err') { const m = $('gMsg'); if (!m) return; m.className = 'g-msg ' + kind; m.innerHTML = text ? ico(kind === 'ok' ? 'check' : 'alert') + `<span>${esc(text)}</span>` : ''; }
async function showLogin(msg, kind) {
  mountGate(`<form id="gForm" class="stack" novalidate><div class="gate-h"><h2>${T.gate.title}</h2><p>${T.gate.sub}</p></div>` +
    `<div class="field"><label for="gUser">${T.gate.user}</label><input class="inp" id="gUser" autocomplete="username" autocapitalize="off" spellcheck="false" required></div>` +
    pwField('gPw', T.gate.password, 'current-password') +
    `<div class="g-msg" id="gMsg" role="alert"></div><button class="btn primary block" id="gBtn" type="submit">${T.gate.enter}</button>` +
    `<p class="g-note" id="gNote">${ico('clock')}<span>${T.gate.remember(12)}</span></p></form>`);
  if (msg) gateMsg(msg, kind);
  let last = ''; try { last = localStorage.getItem('toner-user') || ''; } catch (e) { }
  $('gUser').value = last || 'admin';
  $('gPw').focus();
  api('api/auth/info', { auth: true }).then(r => { if (r.ok && r.data && $('gNote')) { $('gNote').querySelector('span').textContent = T.gate.remember(r.data.hours || 12); if (!last && r.data.user) $('gUser').value = r.data.user; } });
  $('gForm').onsubmit = async e => {
    e.preventDefault();
    const user = $('gUser').value.trim(), pw = $('gPw').value, btn = $('gBtn');
    if (!user || !pw) { gateMsg(T.gate.wrong(0)); (user ? $('gPw') : $('gUser')).focus(); return; }
    btn.disabled = true; btn.innerHTML = `<span class="loader"></span>${T.gate.entering}`; gateMsg('');
    const r = await api('api/auth/login', { method: 'POST', body: { user, password: pw }, auth: true });
    btn.disabled = false; btn.textContent = T.gate.enter;
    if (r.ok && r.data && r.data.ok) {
      try { localStorage.setItem('toner-user', user); } catch (x) { }
      S.me = { user: r.data.user, exp: r.data.exp, hours: r.data.hours, mustChange: r.data.mustChange };
      if (r.data.mustChange) showSetPw(pw); else startApp();
      return;
    }
    if (r.status === 0) gateMsg(T.gate.offline);
    else if (r.status === 429) gateMsg(T.gate.locked((r.data && r.data.retry) || 300));
    else gateMsg(T.gate.wrong(r.data && r.data.attemptsLeft != null ? r.data.attemptsLeft : 0));
    const f = $('gForm'); f.classList.remove('shake'); void f.offsetWidth; f.classList.add('shake');
    $('gPw').select();
  };
}
function showSetPw(startPw) {
  mountGate(`<form id="gForm" class="stack" novalidate><div class="gate-h"><div class="m-ic brand">${ico('key')}</div><h2>${T.gate.setTitle}</h2><p>${T.gate.setSub}</p></div>` +
    (startPw ? '' : pwField('gCur', T.acc.current, 'current-password')) +
    pwField('gNew', T.gate.newPw, 'new-password', 'minlength="8"') + meterHtml('gMeter') + pwField('gRep', T.gate.repeat, 'new-password') +
    `<div class="g-msg" id="gMsg" role="alert"></div><button class="btn primary block" id="gBtn" type="submit">${T.gate.setBtn}</button>` +
    `<button class="btn ghost block" type="button" id="gOut">${ico('logout')}${T.logout}</button></form>`);
  bindMeter('gNew', 'gMeter');
  (startPw ? $('gNew') : $('gCur')).focus();
  $('gOut').onclick = logout;
  $('gForm').onsubmit = async e => {
    e.preventDefault();
    const cur = startPw || $('gCur').value, nw = $('gNew').value, rp = $('gRep').value;
    if (nw.length < 8) { gateMsg(T.pw.short); $('gNew').focus(); return; }
    if (nw !== rp) { gateMsg(T.pw.mismatch); $('gRep').focus(); return; }
    const btn = $('gBtn'); btn.disabled = true;
    const r = await api('api/auth/password', { method: 'POST', body: { current: cur, new: nw }, auth: true });
    btn.disabled = false;
    if (r.ok) { S.me.mustChange = false; toast(T.acc.changed); startApp(); return; }
    if (r.status === 401) { showLogin(T.gate.expired); return; }
    gateMsg(T.pw[(r.data && r.data.error) || 'current'] || T.err);
  };
}
function startApp() {
  const g = $('gate');
  g.classList.add('leaving');
  setTimeout(() => { g.hidden = true; g.classList.remove('leaving'); g.innerHTML = ''; }, 380);
  document.body.classList.remove('gated');
  S.started = true; S.intro = true;
  renderWho(); renderNav(); route(); tick();
  api('api/auth/me', { auth: true }).then(r => { if (r.ok) { S.me = r.data; renderWho(); } });
}
function stopApp() {
  S.started = false;
  if (S.tickTimer) { clearTimeout(S.tickTimer); S.tickTimer = null; }
  if (S.logTimer) { clearInterval(S.logTimer); S.logTimer = null; }
  if (S.openId) closeModal();
  $('whoMenu').hidden = true;
  S.data = null; S.etag = null; S.probe = null; S.me = null;
  $('view').innerHTML = '';
}
function authLost(status) {
  if (!S.started) return;
  stopApp();
  if (status === 403) { S.me = S.me || {}; showSetPw(null); return; }
  showLogin(T.gate.expired, 'info');
}
async function logout() {
  await api('api/auth/logout', { method: 'POST', auth: true });
  stopApp();
  showLogin(T.gate.loggedOut, 'ok');
}
async function boot() {
  const r = await api('api/auth/me', { auth: true });
  if (r.ok && r.data) { S.me = r.data; if (r.data.mustChange) showSetPw(null); else startApp(); }
  else if (r.status === 0) showLogin(T.gate.offline);
  else showLogin();
}

/* ---------- details modal ---------- */
function spark(pts, color) {
  if (!pts || pts.length < 2) return `<span class="muted small">${T.noHistory}</span>`;
  const W = 120, H = 34, t0 = pts[0][0], span = Math.max(1, pts[pts.length - 1][0] - t0);
  const vs = pts.map(p => p[1]);
  let lo = Math.max(0, Math.min(...vs) - 5), hi = Math.min(100, Math.max(...vs) + 5);
  if (hi - lo < 20) { const mid = (hi + lo) / 2; lo = Math.max(0, mid - 10); hi = Math.min(100, lo + 20); }
  const xy = pts.map(([t, v]) => [(t - t0) / span * (W - 6) + 3, H - 3 - (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo) * (H - 6)]);
  const d = xy.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const e = xy[xy.length - 1];
  return `<svg class="spark c-${color}" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true"><path d="${d}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/><circle cx="${e[0].toFixed(1)}" cy="${e[1].toFixed(1)}" r="2.8" fill="currentColor"/></svg>`;
}
function srow(s) {
  const known = s.pct != null;
  const val = known ? `${s.pct}%` : (s.level === -3 ? T.some : T.na);
  const sub = [fullLabel(s), codeOf(s), s.waste ? T.free : ''].filter(Boolean).join(', ');
  return `<div class="srow st-${s.state}"><span class="sw c-${s.color}"></span><div class="sname">${esc(s.name)}<small>${esc(sub)}</small></div><div class="sval">${val}</div>` +
    `<div class="sbar"><i class="c-${s.color}" style="width:${known ? s.pct : 0}%"></i></div><div class="sspark">${spark(s.spark, s.color)}</div></div>`;
}
function renderModal() {
  const p = allP().find(x => x.id === S.openId);
  if (!p) { closeModal(); return; }
  const sups = p.supplies || [];
  const status = [pillOf(p)];
  if (p.deviceStatus != null && T.dev[p.deviceStatus]) status.push(T.dev[p.deviceStatus]);
  if (p.printerStatus != null && T.prn[p.printerStatus]) status.push(T.prn[p.printerStatus]);
  const web = p.webUrl || (p.ip ? 'http://' + p.ip + '/' : '');
  const kv = [[T.kv.status, esc(status.join(', '))], [T.kv.vendor, p.vendor ? vendorChip(p.vendor) : ''], [T.kv.model, esc(p.model)],
    [T.kv.ip, p.ip ? `<a href="${esc(web)}" target="_blank" rel="noopener">${esc(p.ip)}</a>` : ''], [T.kv.serial, esc(p.serial)], [T.kv.sysName, esc(p.sysName)],
    [T.kv.location, esc(p.location)], [T.kv.pages, p.pages != null ? fmtInt(p.pages) : ''], [T.kv.source, esc(T.src[p.source] || p.source)],
    [T.kv.via, p.via && sups.length ? esc(T.via[p.via] || p.via) : '']].filter(r => r[1]);
  let body = p.stale ? `<div style="margin-top:16px">${staleNote(p)}</div>` : '';
  if (p.noCartridge) body += `<div style="margin-top:12px">${note('alert', T.noCartMsg, 'err')}</div>`;
  const al = alertBadges({ alerts: (p.alerts || []).filter(a => !(p.noCartridge && (a === 'supplyMissing' || a === 'noToner'))) }, 20);
  if (al) body += `<div class="pc-alerts" style="margin-top:14px">${al}</div>`;
  body += `<div class="kv">${kv.map(r => `<div><span>${r[0]}</span>${r[1]}</div>`).join('')}</div>`;
  if (p.display && p.display.length) body += `<div class="m-sec">${T.display}</div><pre class="lcd">${esc(p.display.join('\n'))}</pre>`;
  if (sups.length) body += `<div class="m-sec">${T.supplies}</div><div${p.stale ? ' class="tanks stale" style="display:block"' : ''}>${sups.map(srow).join('')}</div>`;
  else if (p.state === 'noip') body += note('plug', T.noipMsg);
  else if (p.state === 'offline') body += note('off', reachText(p));
  else body += note('info', T.noSup);
  const queues = p.queues || [];
  if (queues.length) body += `<div class="m-sec">${T.queues}</div><table class="tbl"><tbody>${queues.map(q => `<tr><td>${esc(q.name)}</td><td class="muted" style="text-align:right">${T.jobs(q.jobs)}</td></tr>`).join('')}</tbody></table>`;
  if (S.editOpen) {
    body += `<form class="edit-box" id="editForm"><h3 style="margin:0 0 14px;font-size:16px">${T.editTitle}</h3><div class="form-grid">` +
      `<div class="field"><label for="eName">${T.nameLabel}</label><input class="inp" id="eName" value="${esc(p.renamed ? p.name : '')}" placeholder="${esc(p.origName || p.name)}"></div>` +
      `<div class="field"><label for="eLoc">${T.locLabel}</label><input class="inp" id="eLoc" value="${esc(p.origLocation !== undefined && p.location !== p.origLocation ? p.location : '')}" placeholder="${esc(p.origLocation || p.location || '')}"></div>` +
      `<label class="toggle wide"><input type="checkbox" id="eHid"${p.hidden ? ' checked' : ''}><i></i>${T.hideLabel}</label></div>` +
      `<div class="m-foot" style="margin-top:16px"><button class="btn primary" type="submit">${T.save}</button><button class="btn outline" type="button" id="eCancel">${T.cancel}</button></div></form>`;
  }
  const actions = [];
  if (p.ip) actions.push(`<a class="btn primary" href="${esc(web)}" target="_blank" rel="noopener">${ico('ext')}${T.openWeb}</a>`, `<button type="button" class="btn outline" id="mpoll">${ico('refresh')}<span>${T.pollNow}</span></button>`);
  {
    if (!S.editOpen) actions.push(`<button type="button" class="btn outline" id="medit">${ico('edit')}${T.edit}</button>`);
    actions.push(`<button type="button" class="btn outline" id="mhide">${ico(p.hidden ? 'eye' : 'eyeOff')}${p.hidden ? T.show : T.hide}</button>`);
    if (p.source === 'manual') actions.push(`<button type="button" class="btn danger" id="mrm">${ico('trash')}${T.remove}</button>`);
  }
  $('sheet').innerHTML = `<div class="m-head"><h2>${esc(p.name)}</h2>${badgeOf(p)}<button type="button" class="icon-btn" id="mclose" title="${T.close}">${ico('x')}</button></div>` + body + `<div class="m-foot">${actions.join('')}</div>`;
  $('mclose').onclick = closeModal;
  const mp = $('mpoll');
  if (mp) mp.onclick = async () => { mp.classList.add('spin'); mp.disabled = true; await api(`api/printers/${encodeURIComponent(p.id)}/refresh`, { method: 'POST' }); mp.querySelector('span').textContent = T.pollQueued; setTimeout(load, 5000); };
  const saveOv = async body => { const r = await api(`api/admin/printers/${encodeURIComponent(p.id)}/override`, { method: 'POST', body }); toast(r.ok ? T.saved : T.saveErr, r.ok ? 'ok' : 'err'); await sleep(700); S.editOpen = false; await load(); renderModal(); if (S.route === 'manage') renderView(true); };
  if ($('medit')) $('medit').onclick = () => { S.editOpen = true; renderModal(); };
  if ($('mhide')) $('mhide').onclick = () => saveOv({ name: p.renamed ? p.name : '', location: p.origLocation !== undefined && p.location !== p.origLocation ? p.location : '', hidden: !p.hidden });
  if ($('mrm')) $('mrm').onclick = async () => { if (!confirm(T.remove + '?')) return; const r = await api(`api/admin/printers/${encodeURIComponent(p.id)}/remove`, { method: 'POST', body: {} }); toast(r.ok ? T.done : T.err, r.ok ? 'ok' : 'err'); closeModal(); await sleep(900); load(); };
  if ($('editForm')) {
    $('eCancel').onclick = () => { S.editOpen = false; renderModal(); };
    $('editForm').onsubmit = e => { e.preventDefault(); saveOv({ name: $('eName').value.trim(), location: $('eLoc').value.trim(), hidden: $('eHid').checked }); };
  }
}
function openModal(id) { S.openId = id; S.editOpen = false; renderModal(); $('modal').hidden = false; document.body.classList.add('lock'); $('sheet').focus(); }
function closeModal() { S.openId = null; S.editOpen = false; $('modal').hidden = true; document.body.classList.remove('lock'); }

/* ---------- events ---------- */
$('view').addEventListener('click', e => {
  if (e.target.closest('#downToggle')) { S.showDown = !S.showDown; saveUi(); renderView(false); return; }
  const seg = e.target.closest('[data-seg] button');
  if (seg) { S[seg.parentNode.dataset.seg] = seg.dataset.v; saveUi(); renderView(false); return; }
  const c = e.target.closest('[data-id]');
  if (c && !e.target.closest('button,a,input,select')) openModal(c.dataset.id);
});
$('view').addEventListener('change', e => {
  const s = e.target.closest('[data-sel]'); if (s) { S[s.dataset.sel] = s.value; saveUi(); renderView(false); return; }
  const k = e.target.closest('[data-chk]'); if (k) { S[k.dataset.chk] = k.checked; renderView(false); }
});
$('view').addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('.pcard[data-id]')) { e.preventDefault(); openModal(e.target.dataset.id); } });
$('modal').addEventListener('click', e => { if (e.target === $('modal')) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && S.openId) closeModal(); });

async function tick() {
  if (!S.started) return;
  if (!S.refreshing) await load();
  if (!S.started) return;
  S.tickTimer = setTimeout(tick, S.data && S.data.polling ? 2500 : 20000);
}
setInterval(() => { if (S.started) renderHeader(); }, 30000);
boot();
})();
