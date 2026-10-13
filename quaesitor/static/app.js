/*
 * OSInt Graph - graphical exploration of OSINT data for investigative cases
 * Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * This program is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version, with the additional terms in the file NOTICE.
 * See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.
 */
// "Fallaces sunt rerum species." (Seneca, De Beneficiis)
// The appearances of things are deceptive.
/* ================= DOM HELPERS ================= */
const $ = s => document.querySelector(s);
const on = (sel, evt, fn) => {
  const el = typeof sel === 'string' ? $(sel) : sel;
  if (el) el.addEventListener(evt, fn);
};

/* ================= ICON & COLOUR ONTOLOGY ================= */
const BRAND = {
  instagram: 'E4405F', snapchat: 'FFC400', facebook: '0866FF', google: '4285F4',
  discord: '5865F2', apple: '333333', amazon: 'FF9900', x: '111111', tiktok: '111111',
  threads: '111111', linkedin: '0A66C2', github: '111111', vk: '0077FF', airbnb: 'FF5A5F',
  zynga: 'D6291E', yahoo: '8A2FF2', microsoft: '00A4EF', telegram: '26A5E4',
  whatsapp: '25D366', spotify: '1DB954',
  // messaging and additional services (if the CDN lacks the icon, the badge stays)
  viber: '7360F2', signal: '3A76F0', skype: '00AFF0', line: '00C300',
  wechat: '07C160', youtube: 'FF0000', botim: '00A5E3', imo: '15C0F5',
  zangi: 'E9401A', tango: 'FF4B4B', icq: '21A9F1', threema: '3FE669',
  kakaotalk: 'FFCD00'
};

// NB: red (#dc2626) is RESERVED for the border of the "starting data" (seed).
// No type colour may come close to it, or it would be confused with that border.
const TYPE_COLOR = {
  target: '#d97706', account: '#2563eb', phone: '#059669', email: '#db2777',
  username: '#7c3aed', domain: '#ea580c', breach: '#9333ea', generic: '#4b5563',
  vehicle: '#b45309', latin: '#0891b2', photo: '#0d9488', link: '#0284c7',
  text: '#65a30d', name: '#c026d3', place: '#4f46e5'
};
Object.entries(window.ONTOLOGY || {}).forEach(([k, v]) => { TYPE_COLOR[k] = v.color; });

/* ================= OPENING SOCIAL PROFILES (Alt+Click) ================= */
/* Known platforms -> how to build the profile URL from the handle. */
const SOCIAL_URL = {
  instagram: h => `https://www.instagram.com/${h}/`,
  tiktok:    h => `https://www.tiktok.com/@${h}`,
  facebook:  h => `https://www.facebook.com/${h}`,
  x:         h => `https://x.com/${h}`,
  twitter:   h => `https://x.com/${h}`,
  threads:   h => `https://www.threads.net/@${h}`,
  telegram:  h => `https://t.me/${h}`,
  // VK: the profile is vk.com/id<number>; a bare number gets the "id" prefix
  vk:        h => `https://vk.com/${/^\d+$/.test(h) ? 'id' + h : h}`,
  snapchat:  h => `https://www.snapchat.com/add/${h}`,
  linkedin:  h => `https://www.linkedin.com/in/${h}`,
  github:    h => `https://github.com/${h}`,
  youtube:   h => /^UC[A-Za-z0-9_-]{20,}$/.test(h)
                    ? `https://www.youtube.com/channel/${h}`   // channel ID (case-sensitive)
                    : `https://www.youtube.com/@${h}`,          // custom handle
  spotify:   h => `https://open.spotify.com/user/${h}`,
  pinterest: h => `https://www.pinterest.com/${h}/`,
  reddit:    h => `https://www.reddit.com/user/${h}`,
  whatsapp:  h => `https://wa.me/${h.replace(/\D/g, '')}`,
  vkontakte: h => `https://vk.com/${/^\d+$/.test(h) ? 'id' + h : h}`
};

/* ---- Recognising a social URL: host -> platform, path -> handle ---- */
const SOCIAL_HOSTS = {
  'instagram.com': 'instagram', 'tiktok.com': 'tiktok',
  'facebook.com': 'facebook', 'fb.com': 'facebook', 'fb.me': 'facebook',
  'x.com': 'x', 'twitter.com': 'x',
  'threads.net': 'threads', 'threads.com': 'threads',
  't.me': 'telegram', 'telegram.me': 'telegram', 'telegram.org': 'telegram',
  'vk.com': 'vk', 'vk.ru': 'vk', 'vkontakte.ru': 'vk', 'vk.cc': 'vk',
  'snapchat.com': 'snapchat', 'linkedin.com': 'linkedin', 'github.com': 'github',
  'youtube.com': 'youtube', 'youtu.be': 'youtube',
  'spotify.com': 'spotify', 'pinterest.com': 'pinterest',
  'reddit.com': 'reddit', 'wa.me': 'whatsapp', 'whatsapp.com': 'whatsapp'
};

/* From a profile URL derive {platform, handle}. null if not recognised. */
function parseSocialUrl(raw) {
  let u;
  try {
    u = new URL(String(raw).trim().replace(/^(?!https?:\/\/)/i, 'https://'));
  } catch (_) { return null; }
  const host = u.hostname.toLowerCase().replace(/^(www|m|mobile|open|api)\./, '');
  const platform = SOCIAL_HOSTS[host];
  if (!platform) return null;

  const segs = u.pathname.split('/').filter(Boolean).map(s => decodeURIComponent(s));
  const strip = s => String(s || '').replace(/^@+/, '').trim();
  let h = '';

  if (platform === 'facebook' && /profile\.php$/i.test(u.pathname)) {
    h = u.searchParams.get('id') || '';
  } else if (platform === 'youtube') {
    if (segs[0] === 'channel' || segs[0] === 'c' || segs[0] === 'user') h = segs[1] || '';
    else h = strip(segs[0]);
  } else if (platform === 'snapchat') {
    h = segs[0] === 'add' ? (segs[1] || '') : strip(segs[0]);
  } else if (platform === 'linkedin') {
    h = (segs[0] === 'in' || segs[0] === 'company') ? (segs[1] || '') : strip(segs[0]);
  } else if (platform === 'reddit') {
    h = (segs[0] === 'user' || segs[0] === 'u') ? (segs[1] || '') : strip(segs[0]);
  } else if (platform === 'spotify') {
    h = segs[0] === 'user' ? (segs[1] || '') : strip(segs[0]);
  } else if (platform === 'whatsapp') {
    h = (u.searchParams.get('phone') || segs[0] || '').replace(/\D/g, '');
  } else {
    h = strip(segs[0]);                       // instagram, tiktok, x, vk, telegram...
  }
  h = strip(h).replace(/\/+$/, '');
  return h ? { platform, handle: h } : null;
}

/* Platforms where a "generic" handle is not reliable: a username taken
   from any card is not necessarily the profile name on that social network.
   VK: only id<number> identifiers (or the bare number) are valid. */
const HANDLE_STRICT = {
  vk: h => /^(id)?\d+$/i.test(h)
};

/* Extractors for "dirty" ids: some nodes have as identifier a descriptive
   text from the dossier or an id with a different separator. */
const HANDLE_EXTRACT = {
  whatsapp: s => { const d = String(s).replace(/\D/g, ''); return d.length >= 8 ? d : ''; },
  telegram: s => { const m = String(s).match(/\b(\d{6,})\b/); return m ? m[1] : ''; },
  facebook: s => {
    const m = String(s).match(/profile\.php\?id=(\d{5,})/i) || String(s).match(/\b(\d{8,})\b/);
    return m ? m[1] : '';
  },
  instagram: s => { const m = String(s).match(/\b(\d{8,})\b/); return m ? m[1] : ''; },
  vk: s => { const m = String(s).match(/\bid(\d+)\b/i) || String(s).match(/\b(\d{6,})\b/);
             return m ? 'id' + m[1] : ''; }
};

/* Handle derived from the node's cards: username/screen_name fields or a
   profile URL present in the data. Needed for nodes whose id is an opaque hash.
   A URL of the platform is always reliable; a generic username field
   is accepted only if it passes the strict check, where there is one. */
function handleFromRecords(d) {
  const HANDLE = /^[A-Za-z0-9._-]{2,}$/;
  const strict = HANDLE_STRICT[d.platform];
  for (const r of (d.records || [])) {
    let rows = [];
    try { rows = flatten(r.raw); } catch (_) { continue; }
    for (const [k, v] of rows) {
      const s = String(v || '').trim();
      if (/^https?:\/\//i.test(s)) {                    // a URL in the data
        const p = parseSocialUrl(s);
        if (p && p.platform === d.platform && p.handle) return p.handle;
      }
      if (/(^|\.)(usernames?|screen_?name|nickname|login|handle|slug)$/i.test(k)) {
        const c = s.replace(/^@+/, '').split(/[,;\s]+/)[0];
        if (HANDLE.test(c) && (!strict || strict(c))) return c;
      }
    }
  }
  return '';
}

/* Handle to use in the URL: try the id value (acct:svc:VALUE), then
   the label, then the aliases; a text handle is preferred to a numeric one. */
function socialHandle(d) {
  const HANDLE = /^[A-Za-z0-9._-]{2,}$/;
  const parts = String(d.id || '').split(':');
  const idVal = parts.length >= 3 ? parts.slice(2).join(':') : '';
  const raw = [idVal, d.label, ...(d.aliases || [])]
    .map(c => String(c || '').trim()).filter(Boolean);
  const labels = [d.label, ...(d.aliases || [])]
    .map(c => String(c || '').trim().replace(/^@+/, ''))
    .filter(c => HANDLE.test(c));
  // 1) label that is the same handle as the id but with the right capitalisation
  if (idVal) {
    const m = labels.find(c => c.toLowerCase() === idVal.toLowerCase());
    if (m) return m;
  }
  // 2) the canonical id, if textual (not an opaque numeric id)
  if (idVal && HANDLE.test(idVal) && !/^\d+$/.test(idVal)) return idVal;
  // 3) a textual, non-numeric label
  const nonNum = labels.find(c => !/^\d+$/.test(c));
  if (nonNum) return nonNum;
  // 4) fallback: numeric id (facebook/vk accept it) or first label
  const fallback = (idVal && HANDLE.test(idVal) ? idVal : '') || labels[0] || '';
  if (fallback) return fallback;
  // 5) platform-specific extractor: recovers the identifier even
  //    from "dirty" ids (acct:whatsapp-39..., profile.php?id=..., free text)
  const ex = HANDLE_EXTRACT[d.platform];
  if (ex) { for (const s of raw) { const h = ex(s); if (h) return h; } }
  // 6) last resort: look for a username or a URL inside the cards
  return handleFromRecords(d);
}

/* Opens a URL in a NEW BACKGROUND TAB, without moving the focus away from the
   graph. window.open opens in the foreground: instead a Ctrl+Click (Cmd on
   Mac) is simulated on a target=_blank link, which browsers open in the background. */
/* Opens the profile in a SEPARATE WINDOW instead of a tab.
   Reason: a new tab covers the graph and Chrome, if it decides to activate it,
   cannot be overridden via JS. A separate window instead leaves the
   graph window where it is, always visible; then we try to give it the focus back.
   The window opens side by side (right half of the screen) and is reused. */
function openSocialWindow(url) {
  const sw = window.screen.availWidth || 1280;
  const sh = window.screen.availHeight || 800;
  const w = Math.max(720, Math.floor(sw * 0.46));
  const h = Math.max(600, sh - 80);
  const left = sw - w;                       // side by side, on the right
  const feats = `popup=yes,width=${w},height=${h},left=${left},top=20,` +
                'menubar=no,toolbar=no,location=yes,status=no,resizable=yes,scrollbars=yes';
  let win = null;
  try {
    // no 'noopener': the handle is needed to try to take the focus away
    win = window.open(url, 'social_profile', feats);
  } catch (_) { win = null; }
  if (!win) return false;                    // blocked by the popup blocker
  // give the focus back to the graph at once (several attempts: Chrome sometimes ignores it)
  const refocus = () => { try { win.blur(); } catch (_) {} try { window.focus(); } catch (_) {} };
  refocus();
  setTimeout(refocus, 0);
  setTimeout(refocus, 120);
  return true;
}

/* Opening in a background tab (simulated Ctrl/Cmd+Click). Used only if
   the user chooses the "tab" mode. */
function openBackgroundTab(url) {
  const isMac = /Mac|iPhone|iPad|iPod/.test(navigator.platform || navigator.userAgent || '');
  const a = document.createElement('a');
  a.href = url;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  a.style.position = 'fixed';
  a.style.left = '-9999px';
  document.body.appendChild(a);
  a.dispatchEvent(new MouseEvent('click', {
    bubbles: true, cancelable: true, view: window,
    button: 0, ctrlKey: !isMac, metaKey: isMac, shiftKey: false, altKey: false
  }));
  a.remove();
}

/* Copy to clipboard: fallback always available, never moves the focus. */
function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text);
      return true;
    }
  } catch (_) {}
  try {
    const t = document.createElement('textarea');
    t.value = text;
    t.style.position = 'fixed';
    t.style.left = '-9999px';
    document.body.appendChild(t);
    t.select();
    document.execCommand('copy');
    t.remove();
    return true;
  } catch (_) { return false; }
}

/* Opening mode chosen by the user (remembered in the browser):
   'window' = side-by-side window (default: the graph always stays visible)
   'tab'    = background tab
   'copy'   = only copies the link */
let openMode = (() => {
  try { return localStorage.getItem('socialOpenMode') || 'window'; } catch (_) { return 'window'; }
})();
function setOpenMode(m) {
  openMode = m;
  try { localStorage.setItem('socialOpenMode', m); } catch (_) {}
}

/* Opens the node's social profile according to the chosen mode. */
function openSocial(node) {
  const d = node.data();
  // a node with its own URL (generic link added by hand) opens directly
  let url = /^https?:\/\//i.test(d.url || '') ? d.url : '';
  if (!url && d.ntype === 'place') {         // place without a link: search on Google Maps
    const q = d.lat && d.lon ? `${d.lat},${d.lon}`
            : String(d.label || '').split(/\s+[—–]\s+/).reverse().join(', ');
    if (q) url = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(q);
  }
  if (!url) {
    const make = SOCIAL_URL[d.platform];
    if (!make) return { ok: false, reason: 'non-social' };
    const h = socialHandle(d);
    if (!h) return { ok: false, reason: 'no-handle' };
    url = make(h);
  }

  if (openMode === 'copy') {
    return { ok: true, url, mode: 'copy', copied: copyToClipboard(url) };
  }
  if (openMode === 'tab') {
    openBackgroundTab(url);
    return { ok: true, url, mode: 'tab' };
  }
  const opened = openSocialWindow(url);      // 'window' (default)
  if (!opened) {                             // popup blocked: fall back to a tab
    openBackgroundTab(url);
    return { ok: true, url, mode: 'tab-fallback' };
  }
  return { ok: true, url, mode: 'window' };
}

const IDENT_TYPES = ['phone', 'email', 'username', 'vehicle'];

/* ================= CATEGORIES (show/hide filters) =================
   Each node belongs to ONE category (first match).
   The last one ('altro') is the safety net: it catches everything else. */
/* The label is a translation key: it is resolved at drawing time. */
const CATEGORIES = [
  { key: 'target',   color: TYPE_COLOR.target,   match: n => n.ntype === 'target' },
  { key: 'social',   color: TYPE_COLOR.account,  match: n => n.ntype === 'account' },
  { key: 'phone',    color: TYPE_COLOR.phone,    match: n => n.ntype === 'phone' },
  { key: 'email',    color: TYPE_COLOR.email,    match: n => n.ntype === 'email' },
  { key: 'username', color: TYPE_COLOR.username, match: n => n.ntype === 'username' },
  { key: 'veicoli',  color: TYPE_COLOR.vehicle,  match: n => n.ntype === 'vehicle' },
  { key: 'link',     color: TYPE_COLOR.link,     match: n => n.ntype === 'link' },
  { key: 'text',     color: TYPE_COLOR.text,     match: n => n.ntype === 'text' },
  { key: 'name',     color: TYPE_COLOR.name,     match: n => n.ntype === 'name' },
  { key: 'place',    color: TYPE_COLOR.place,    match: n => n.ntype === 'place' },
  { key: 'domini',   color: TYPE_COLOR.domain,   match: n => n.ntype === 'domain' },
  { key: 'breach',   color: TYPE_COLOR.breach,   match: n => n.ntype === 'breach' },
  { key: 'foto',     color: TYPE_COLOR.photo,    match: n => n.ntype === 'photo' },
  { key: 'translit', color: TYPE_COLOR.latin,    match: n => n.ntype === 'latin' },
  // one category per group of investigative items (weapons, drugs...)
  ...[...new Set(Object.values(window.ONTOLOGY || {}).sort((a, b) => a.order - b.order)
        .map(o => o.group))].map(g => ({
    key: 'onto_' + g, group: g,
    color: (Object.values(window.ONTOLOGY).find(o => o.group === g) || {}).color || TYPE_COLOR.generic,
    match: n => (window.ONTOLOGY[n.ntype] || {}).group === g
  })),
  { key: 'altro',    color: TYPE_COLOR.generic,  match: () => true }
];
/* Texts of the investigative types in the chosen language (ontology_i18n.py). The
   saved value stays the Italian one: only what is shown is translated. */
const ot = s => (LANG === 'it' || !s) ? s : ((((window.ONTO_I18N || {})[LANG]) || {})[s] || s);
const ONTO_GROUP_IT = { Soggetti: 'Organizzazioni', Fatti: 'Eventi / reati', Beni: 'Immobili' };
const catLabel = key => key.startsWith('onto_')
  ? ot(ONTO_GROUP_IT[key.slice(5)] || key.slice(5))
  : t('cat.' + key);
const CAT_BY_KEY = Object.fromEntries(CATEGORIES.map(c => [c.key, c]));
const categoryOf = n => (CATEGORIES.find(c => c.match(n)) || CAT_BY_KEY.altro).key;

/* All icons are 64x64 SVGs with an explicit viewBox:
   without intrinsic dimensions the Cytoscape canvas anchors the image
   at the top left instead of centring it (social icons bug when zoomed out). */
const wrapSvg = inner =>
  'data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24">' + inner + '</svg>'
  );

const strokeSvg = i => wrapSvg(
  '<g fill="none" stroke="#1e293b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' + i + '</g>'
);

/* Font Awesome Free icons (static/vendor/fa, inserted into the page by app.py).
   The original SVG has a rectangular viewBox: it is made square and with a
   margin, so the icon stays centred and the same size in the circle. */
const _faCache = {};
function faIcon(name, color = '#1e293b') {
  const k = name + color;
  if (_faCache[k]) return _faCache[k];
  const src = (window.FA_ICONS || {})[name] || (window.FA_ICONS || {})['circle-question'];
  if (!src) return null;
  const vb = (src.match(/viewBox="([^"]+)"/) || [, '0 0 512 512'])[1].split(/\s+/).map(Number);
  const w = vb[2], h = vb[3], S = Math.max(w, h), pad = S * 0.14;
  const inner = src.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" ` +
    `viewBox="${vb[0] - (S - w) / 2 - pad} ${vb[1] - (S - h) / 2 - pad} ${S + 2 * pad} ${S + 2 * pad}">` +
    `<g fill="${color}">${inner}</g></svg>`;
  return (_faCache[k] = 'data:image/svg+xml;utf8,' + encodeURIComponent(svg));
}

// icon per node type (person, phone, email...): table in ontology.py
const SVG = Object.fromEntries(Object.entries(window.BASE_ICONS || {}).map(([k, v]) => [k, faIcon(v)]));
SVG.generic = SVG.generic || faIcon('circle-question');

// Badge with initial: used at once for the platforms, then replaced
// by the real brand icon (downloaded and resized) when available.
const letterIcon = (name, hex) => {
  const ch = (String(name || '?').trim()[0] || '?').toUpperCase();
  return wrapSvg(
    `<rect x="1" y="1" width="22" height="22" rx="6" fill="#${hex}"/>` +
    `<text x="12" y="17" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-size="13" font-weight="700" fill="#ffffff">${ch}</text>`
  );
};

/* Brand icons already downloaded: so a node added AFTER loading gets
   the same icon as the imported ones at once, without waiting for a reload. */
const BRAND_ICON = {};

const ONTO = window.ONTOLOGY || {};
// colour icons of the node types (static/icons/entities, scripts/icons/install.py):
// they come before the Font Awesome glyphs, which stay as fallback
const ENT_ICON = Object.fromEntries((window.ENTITY_ICONS || []).map(k => [k, `/static/icons/entities/${k}.png`]));
const iconFor = n => {
  if (n.ntype === 'photo' && n.image) return n.image;   // photo thumbnail
  if (n.pic && n.image) return n.image;                 // person pictured by an imported photo
  const brand = n.ntype === 'account' && (BRAND_ICON[n.platform] || BRAND[n.platform]);
  if (!brand) {                                         // a social profile keeps its platform logo
    if (n.ficon && ENT_ICON[n.ficon]) return ENT_ICON[n.ficon];
    if (ENT_ICON[n.ntype]) return ENT_ICON[n.ntype];
  }
  if (n.ficon) return faIcon(n.ficon);                  // e.g. cannabis, syringe, passport
  if (ONTO[n.ntype]) return faIcon(ONTO[n.ntype].icon);
  if (SVG[n.ntype]) return SVG[n.ntype];
  if (BRAND_ICON[n.platform]) return BRAND_ICON[n.platform];
  if (BRAND[n.platform]) return letterIcon(n.platform, BRAND[n.platform]);
  return SVG.generic;
};

/* Loads the brand icons from static/vendor/icons/ (NOT from the internet: the app
   must work on machines without a connection) and forces width/height, so
   they stay perfectly centred at any zoom level.
   If an icon is missing, the badge with the initial stays, as always. */
async function upgradeBrandIcons() {
  // list of the icons actually present: avoids pointless requests (useless 404s
  // in the console, which would end up hiding the real errors)
  let disponibili = null;
  try {
    const r = await fetch('/api/brand-icons');
    if (r.ok) disponibili = new Set(await r.json());
  } catch (_) { /* try anyway, at worst the badge stays */ }
  const slugs = [...new Set(cy.nodes().map(n => n.data('platform')))]
    .filter(p => BRAND[p] && (!disponibili || disponibili.has(p)));
  await Promise.all(slugs.map(async slug => {
    try {
      const r = await fetch(`/static/vendor/icons/${slug}.svg`);
      if (!r.ok) return;
      let t = (await r.text()).trim();
      if (!/^<svg/i.test(t)) return;
      t = t.replace(/<svg([^>]*)>/i, (m, a) => {
        a = a.replace(/\s(width|height)\s*=\s*"[^"]*"/gi, '');
        if (!/viewBox/i.test(a)) a += ' viewBox="0 0 24 24"';
        return `<svg${a} width="64" height="64">`;
      });
      const uri = 'data:image/svg+xml;utf8,' + encodeURIComponent(t);
      BRAND_ICON[slug] = uri;                 // stored for future nodes
      cy.batch(() => {
        cy.nodes().forEach(n => {
          if (n.data('platform') === slug && !SVG[n.data('ntype')]) n.data('icon', uri);
        });
      });
    } catch (_) { /* icon missing: the badge with the initial stays */ }
  }));
}

/* ================= UTILITY ================= */
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const short = u => u.replace(/^https?:\/\//, '').slice(0, 60);
const SKIP = /^(sstt|epid|hd_profile_pic_versions|checksums|crypted_custom_password|salt|FidoParams|threads_profile_glyph_url|profile_pic_url_hd|profile_pic_url|avatarLarger|profile_photo_hash|avatar|hd_profile_pic_url_info)$/i;
const NOISE = /^(is_|has_|can_|show_|enable_|allow_|should_|eligible|include_|remove_|disable_|highlight_|open_|feed_|live_|reels_|stories_|posts_|trial_|spam_|request_|profile_reels|not_meta|meta_verified_benefits|recs_from|avatar_status|profile_overlay|profile_mentions|profile_hours|pinned_channels|qa_freeform)/i;

function flatten(o, p = '', out = []) {
  if (out.length > 150) return out;
  if (Array.isArray(o)) {
    if (o.length && typeof o[0] !== 'object') { out.push([p, o.join(', ')]); return out; }
    o.slice(0, 8).forEach((v, i) => flatten(v, `${p}[${i}]`, out));
  } else if (o && typeof o === 'object') {
    for (const k in o) {
      if (SKIP.test(k)) continue;
      if (NOISE.test(k) && typeof o[k] !== 'object') continue;
      flatten(o[k], p ? `${p}.${k}` : k, out);
    }
  } else if (o !== null && o !== '' && o !== false) {
    // Long texts are NOT discarded: they would be found by the search but
    // would not be visible in the card. They are shown shortened, expandable.
    const v = String(o);
    if (v.length <= MAX_VAL) out.push([p, v]);
    else out.push([p, v.slice(0, MAX_VAL) + '…']);
  }
  return out;
}
const MAX_VAL = 10000;        // safety cap for abnormal values
const CLAMP_VAL = 400;        // beyond this length the value starts shortened

const IMG_URL = /^https?:\/\/[^\s]+\.(jpg|jpeg|png|webp|gif|bmp)(\?|#|$)/i;
const linkify = v => {
  if (!/^https?:\/\//.test(v)) return esc(v);
  if (IMG_URL.test(v)) return `<img class="thumb" src="${esc(v)}" loading="lazy" alt="" onerror="this.remove()">`;
  return `<a href="${v}" target="_blank" rel="noopener">${esc(short(v))}</a>`;
};

/* Value of a card: long texts are shown shortened with "show all". */
const renderVal = v => {
  if (/^https?:\/\//.test(v) || v.length <= CLAMP_VAL) return linkify(v);
  return `<span class="lv">${esc(v)}</span>` +
         `<button type="button" class="lv-more">${esc(t('card.showMore'))}</button>`;
};

/* ================= LINK PROPERTIES =================
   The same block of controls (name, arrows, shape, bend point, line type,
   colour, width) appears in three windows: adding a node ('add'),
   linking selected nodes ('link') and editing a link
   ('edg'). It is generated here once per window, with ids "<prefix>-…". */
const EDGE_DEFAULT_COLOR = '#94a3b8';
const EDGE_PALETTE = ['#94a3b8', '#0f172a', '#dc2626', '#ea580c', '#d97706', '#16a34a',
                      '#0891b2', '#2563eb', '#7c3aed', '#db2777'];
const EDGE_DEFAULT_BEND = 40;
const EDGE_DEFAULTS = { label: '', arrow: 'none', curve: 'bezier', lstyle: '', color: '',
                        width: 0, bend: EDGE_DEFAULT_BEND };
/* All Cytoscape shapes suitable for a link with arrows
   ('haystack' is left out: it does not draw arrows). */
const EDGE_CURVES = ['bezier', 'straight', 'unbundled-bezier', 'segments', 'round-segments',
                     'taxi', 'round-taxi', 'straight-triangle'];
const BEND_CURVES = ['unbundled-bezier', 'segments', 'round-segments'];   // with adjustable bend point

function buildEdgeProps(box) {
  const p = box.dataset.prefix;
  box.innerHTML = `
    <label class="af-lb" for="${p}-edge-ftm" data-i18n="edge.ftm"></label>
    <select id="${p}-edge-ftm">
      <option value="">${esc(t('edge.ftmNone'))}</option>
      ${Object.keys(FTM_EDGES).sort((a, b) => ftmEdgeLabel(a).localeCompare(ftmEdgeLabel(b)))
        .map(k => `<option value="${esc(k)}">${esc(ftmEdgeLabel(k))} · ${esc(ftmEdgeVerb(k))}</option>`).join('')}
    </select>
    <div id="${p}-edge-ftm-fields" class="ep-ftm"></div>
    <label class="af-lb" for="${p}-edge-label" data-i18n="add.edgeName"></label>
    <input id="${p}-edge-label" autocomplete="off" maxlength="300" data-i18n-ph="add.edgeNamePh">
    <label class="af-lb" for="${p}-edge-shape" data-i18n="add.edgeShape"></label>
    <select id="${p}-edge-shape">
      ${EDGE_CURVES.map(c => `<option value="${c}" data-i18n="curve.${c}"></option>`).join('')}
    </select>
    <div class="ep-bend" id="${p}-bend-row" hidden>
      <label class="af-lb" for="${p}-edge-bend" data-i18n="edge.bend"></label>
      <div class="ep-bend-ctl">
        <input type="range" id="${p}-edge-bend" min="-200" max="200" step="5" value="${EDGE_DEFAULT_BEND}">
        <span id="${p}-edge-bend-val" class="ep-bend-val"></span>
        <button type="button" class="mini" id="${p}-bend-flip" data-i18n-title="edge.bendFlip">⇅</button>
      </div>
    </div>
    <div class="ep-row2">
      <div>
        <label class="af-lb" for="${p}-edge-lstyle" data-i18n="edge.lineStyle"></label>
        <select id="${p}-edge-lstyle">
          <option value="" data-i18n="edge.lsDefault"></option>
          <option value="solid" data-i18n="edge.lsSolid"></option>
          <option value="dashed" data-i18n="edge.lsDashed"></option>
          <option value="dotted" data-i18n="edge.lsDotted"></option>
        </select>
      </div>
      <div>
        <label class="af-lb" for="${p}-edge-width" data-i18n="edge.width"></label>
        <select id="${p}-edge-width">
          <option value="0" data-i18n="edge.lsDefault"></option>
          <option value="1">1</option><option value="2">2</option>
          <option value="3">3</option><option value="4">4</option>
          <option value="6">6</option><option value="8">8</option>
          <option value="12">12</option>
        </select>
      </div>
    </div>
    <label class="af-lb" data-i18n="edge.color"></label>
    <div class="ep-color">
      <input type="color" id="${p}-edge-color" value="${EDGE_DEFAULT_COLOR}">
      ${EDGE_PALETTE.map(c => `<button type="button" class="ep-sw" data-sw="${c}" style="background:${c}" title="${c}"></button>`).join('')}
      <label class="af-cb-label"><input type="checkbox" id="${p}-edge-color-def" checked>
        <span data-i18n="edge.colorDefault"></span></label>
    </div>
    <div class="af-prev-head">
      <label class="af-lb" data-i18n="edge.preview"></label>
      <span class="af-hint" data-i18n="edge.previewHint"></span>
    </div>
    <div id="${p}-arrow-preview" class="af-arrow-preview" data-arrow="none"></div>`;

  const upd = () => updateEdgePreview(p);
  box.addEventListener('input', upd);
  box.addEventListener('change', upd);
  box.querySelector(`#${p}-edge-ftm`).addEventListener('change', e => {
    renderFtmEdgeFields(p, e.target.value, {});
    $(`#${p}-edge-label`).placeholder = e.target.value ? ftmEdgeVerb(e.target.value) + ' (…)' : t('add.edgeNamePh');
  });

  // Interactive preview: it is the only control for the arrows. A click on the half
  // of the source node adds or removes the head towards that node (backward
  // arrow), a click on the half of the target node does the same with the
  // forward arrow. It also works from the keyboard (Tab, Enter or Space).
  const prev = box.querySelector(`#${p}-arrow-preview`);
  const toggleHead = (side, refocus) => {
    const { fwd, bwd } = arrowHeads(p);
    setArrowHeads(p, side === 'dst' ? !fwd : fwd, side === 'src' ? !bwd : bwd);
    upd();
    if (refocus) { const g = prev.querySelector(`[data-side="${side}"]`); if (g) g.focus(); }
  };
  prev.addEventListener('click', e => {
    const h = e.target.closest('[data-side]');
    if (h) toggleHead(h.dataset.side, false);
  });
  prev.addEventListener('keydown', e => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const h = e.target.closest('[data-side]');
    if (h) { e.preventDefault(); toggleHead(h.dataset.side, true); }
  });
  box.querySelector(`#${p}-edge-color`).addEventListener('input', () => {
    box.querySelector(`#${p}-edge-color-def`).checked = false; upd();
  });
  box.querySelectorAll('.ep-sw').forEach(b => b.addEventListener('click', () => {
    box.querySelector(`#${p}-edge-color`).value = b.dataset.sw;
    box.querySelector(`#${p}-edge-color-def`).checked = false;
    upd();
  }));
  box.querySelector(`#${p}-bend-flip`).addEventListener('click', () => {
    const r = box.querySelector(`#${p}-edge-bend`);
    r.value = String(-parseInt(r.value, 10) || 0);
    upd();
  });
}
/* ---- Follow the Money relations on the links (window.FTM_EDGES) ---- */
const FTM_EDGES = window.FTM_EDGES || {};
const ftmLabelIn = (labels, fallback) => (labels && labels[LANG]) || fallback;
const ftmEdgeLabel = k => FTM_EDGES[k] ? ftmLabelIn(FTM_EDGES[k].labels, FTM_EDGES[k].label) : k;
const ftmEdgeVerb = k => FTM_EDGES[k] ? (LANG === 'it' ? FTM_EDGES[k].verb_it : FTM_EDGES[k].verb) : '';
function ftmEdgeFieldLabel(k, key) {
  const f = ((FTM_EDGES[k] || {}).fields || []).find(x => x.key === key);
  return f ? ftmLabelIn(f.labels, f.label) : key;
}
function renderFtmEdgeFields(p, schema, values) {
  const box = $(`#${p}-edge-ftm-fields`);
  if (!box) return;
  const e = FTM_EDGES[schema];
  box.hidden = !e;
  if (!e) { box.innerHTML = ''; return; }
  const v = values || {};
  box.innerHTML = e.fields.map(f => `
    <div class="af-of"><label class="af-lb" for="${p}-ftm-${f.key}">${esc(ftmLabelIn(f.labels, f.label))}</label>
      <input id="${p}-ftm-${f.key}" data-ftmk="${esc(f.key)}" type="${f.type === 'date' ? 'date' : 'text'}"
             autocomplete="off" maxlength="300" value="${esc(v[f.key] || '')}"></div>`).join('');
}
function readFtmEdgeProps(p) {
  const out = {};
  document.querySelectorAll(`#${p}-edge-ftm-fields [data-ftmk]`).forEach(i => {
    if (i.value.trim()) out[i.dataset.ftmk] = i.value.trim();
  });
  return out;
}
document.querySelectorAll('.edge-props').forEach(buildEdgeProps);

/* Arrow state of a window: it lives on the preview (data-arrow), which is
   also the control used to change it. Values: none | target | source | both. */
const EDGE_ARROWS = ['none', 'target', 'source', 'both'];
const arrowHeads = p => {
  const a = $(`#${p}-arrow-preview`).dataset.arrow || 'none';
  return { fwd: a === 'target' || a === 'both', bwd: a === 'source' || a === 'both' };
};
function setArrowHeads(p, fwd, bwd) {
  $(`#${p}-arrow-preview`).dataset.arrow = fwd && bwd ? 'both' : fwd ? 'target' : bwd ? 'source' : 'none';
}

function readEdgeProps(p) {
  const curve = $(`#${p}-edge-shape`).value;
  const v = {
    label: $(`#${p}-edge-label`).value.trim(),
    arrow: $(`#${p}-arrow-preview`).dataset.arrow || 'none',
    curve,
    lstyle: $(`#${p}-edge-lstyle`).value,
    color: $(`#${p}-edge-color-def`).checked ? '' : $(`#${p}-edge-color`).value,
    width: parseFloat($(`#${p}-edge-width`).value) || 0,
    ftm: ($(`#${p}-edge-ftm`) && $(`#${p}-edge-ftm`).value) || '',
  };
  v.ftm_props = v.ftm ? readFtmEdgeProps(p) : {};
  if (BEND_CURVES.includes(curve)) v.bend = parseInt($(`#${p}-edge-bend`).value, 10) || 0;
  return v;
}

function writeEdgeProps(p, props) {
  const v = Object.assign({}, EDGE_DEFAULTS, props || {});
  $(`#${p}-edge-label`).value = v.label || '';
  $(`#${p}-arrow-preview`).dataset.arrow = EDGE_ARROWS.includes(v.arrow) ? v.arrow : 'none';
  $(`#${p}-edge-shape`).value = EDGE_CURVES.includes(v.curve) ? v.curve : 'bezier';
  $(`#${p}-edge-bend`).value = String(v.bend ?? EDGE_DEFAULT_BEND);
  $(`#${p}-edge-lstyle`).value = v.lstyle || '';
  const w = $(`#${p}-edge-width`);
  w.value = String(v.width || 0);
  if (w.value === '' && v.width) {                 // width not in the list
    w.insertAdjacentHTML('beforeend', `<option value="${v.width}">${v.width}</option>`);
    w.value = String(v.width);
  }
  $(`#${p}-edge-color`).value = v.color || EDGE_DEFAULT_COLOR;
  $(`#${p}-edge-color-def`).checked = !v.color;
  const fs = $(`#${p}-edge-ftm`);
  if (fs) {
    fs.value = FTM_EDGES[v.ftm] ? v.ftm : '';
    renderFtmEdgeFields(p, fs.value, v.ftm_props || {});
    $(`#${p}-edge-label`).placeholder = fs.value ? ftmEdgeVerb(fs.value) + ' (…)' : t('add.edgeNamePh');
  }
  updateEdgePreview(p);
}

/* Current properties of a graph link (those not set = defaults). */
const edgePropsOf = e => ({
  label: e.data('label') || '', arrow: e.data('arrow') || 'none',
  curve: e.data('curve') || 'bezier', lstyle: e.data('lstyle') || '',
  color: e.data('color') || '', width: e.data('width') || 0,
  bend: e.data('bend') ?? EDGE_DEFAULT_BEND,
  ftm: e.data('ftm') || '', ftm_props: e.data('ftm_props') || {}
});

/* Applies the properties to a graph link: empty keys are removed, so
   the default style (or that of the relation type) applies again. */
function setEdgeProps(e, props) {
  const v = Object.assign({}, EDGE_DEFAULTS, props || {});
  const want = {
    label: v.label || '', arrow: v.arrow !== 'none' ? v.arrow : '',
    curve: v.curve !== 'bezier' ? v.curve : '', lstyle: v.lstyle || '',
    color: v.color || '', width: v.width || 0
  };
  for (const k in want) {
    if (want[k]) e.data(k, want[k]); else e.removeData(k);
  }
  if (BEND_CURVES.includes(v.curve)) e.data('bend', typeof v.bend === 'number' ? v.bend : EDGE_DEFAULT_BEND);
  else e.removeData('bend');
}

/* ---- Preview: the two REAL nodes (icon, colour, name) and the line as it
   will appear in the graph. Each window registers its two nodes. ---- */
const previewNodes = {};
const nodeView = n => n && n.length
  ? { icon: n.data('icon'), label: n.data('label'), color: n.data('color'), ntype: n.data('ntype') }
  : null;
function setPreviewNodes(p, a, b) {
  previewNodes[p] = [a, b];
  updateEdgePreview(p);
}

function previewNodeSvg(n, x, y, r, id) {
  const col = (n && n.color) || '#475569';
  const photo = n && n.ntype === 'photo';
  const bg = n && n.ntype === 'target' ? '#fef3c7' : '#ffffff';
  const lab = n ? String(n.label || '') : '';
  const short = lab.length > 22 ? lab.slice(0, 21) + '…' : lab;
  const clip = photo
    ? `<clipPath id="${id}"><rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" rx="5"/></clipPath>`
    : `<clipPath id="${id}"><circle cx="${x}" cy="${y}" r="${r}"/></clipPath>`;
  const shape = photo
    ? `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" rx="5" fill="${bg}" stroke="${col}" stroke-width="2.5"/>`
    : `<circle cx="${x}" cy="${y}" r="${r}" fill="${bg}" stroke="${col}" stroke-width="2.5"/>`;
  const s = photo ? 2 * r : r * 1.24;                // as in the graph: icon at 62%
  const img = n && n.icon
    ? `<image href="${esc(n.icon)}" x="${x - s / 2}" y="${y - s / 2}" width="${s}" height="${s}" ` +
      `preserveAspectRatio="${photo ? 'xMidYMid slice' : 'xMidYMid meet'}" clip-path="url(#${id})"/>`
    : '';
  const txt = short
    ? `<text x="${x}" y="${y + r + 13}" text-anchor="middle" font-size="10.5" font-weight="600" ` +
      `fill="${n.ntype === 'target' ? '#b45309' : '#0f172a'}" stroke="#fff" stroke-width="3" ` +
      `paint-order="stroke">${esc(short)}</text>` : '';
  return clip + shape + img + txt;
}

function updateEdgePreview(p) {
  const box = $(`#${p}-arrow-preview`);
  if (!box) return;
  const v = readEdgeProps(p);
  const bendRow = $(`#${p}-bend-row`);
  if (bendRow) bendRow.hidden = !BEND_CURVES.includes(v.curve);
  const bv = $(`#${p}-edge-bend-val`);
  if (bv) bv.textContent = `${parseInt($(`#${p}-edge-bend`).value, 10) || 0} px`;

  const [na, nb] = previewNodes[p] || [];
  const col = v.color || EDGE_DEFAULT_COLOR;
  const w = v.width || (v.curve === 'straight-triangle' ? 8 : 2);
  const R = 17;
  const A = { x: 52, y: 62 }, B = { x: 308, y: 86 };  // slightly staggered, as in a real graph
  const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy);
  const nx = dy / len, ny = -dx / len;                 // normal (towards "above" the line)
  const bend = (v.bend ?? EDGE_DEFAULT_BEND) * 0.26;   // reduced scale: fits in the box
  const M = { x: (A.x + B.x) / 2, y: (A.y + B.y) / 2 };
  const K = { x: M.x + nx * bend, y: M.y + ny * bend };   // bend point / control point

  // start and end points on the BORDER of the nodes, along the exit direction
  const edgeAt = (P, Q) => { const l = Math.hypot(Q.x - P.x, Q.y - P.y) || 1;
    return { x: P.x + (Q.x - P.x) / l * R, y: P.y + (Q.y - P.y) / l * R }; };
  let d = '', firstDir = B, lastDir = A, labelAt = M;
  const f = n => n.toFixed(1);
  switch (v.curve) {
    case 'unbundled-bezier': {
      const C = { x: 2 * K.x - M.x, y: 2 * K.y - M.y };   // the curve passes through K
      const s = edgeAt(A, C), e = edgeAt(B, C);
      d = `M${f(s.x)} ${f(s.y)} Q${f(C.x)} ${f(C.y)} ${f(e.x)} ${f(e.y)}`;
      firstDir = C; lastDir = C; labelAt = K; break;
    }
    case 'segments': case 'round-segments': {
      const s = edgeAt(A, K), e = edgeAt(B, K);
      if (v.curve === 'segments') d = `M${f(s.x)} ${f(s.y)} L${f(K.x)} ${f(K.y)} L${f(e.x)} ${f(e.y)}`;
      else {
        const r = 16, a1 = edgeAt(K, A), b1 = edgeAt(K, B);   // rounded joint
        const k1 = { x: K.x + (a1.x - K.x) * r / R, y: K.y + (a1.y - K.y) * r / R };
        const k2 = { x: K.x + (b1.x - K.x) * r / R, y: K.y + (b1.y - K.y) * r / R };
        d = `M${f(s.x)} ${f(s.y)} L${f(k1.x)} ${f(k1.y)} Q${f(K.x)} ${f(K.y)} ${f(k2.x)} ${f(k2.y)} L${f(e.x)} ${f(e.y)}`;
      }
      firstDir = K; lastDir = K; labelAt = K; break;
    }
    case 'taxi': case 'round-taxi': {
      const X = M.x, s = { x: A.x + R, y: A.y }, e = { x: B.x - R, y: B.y };
      if (v.curve === 'taxi') d = `M${s.x} ${s.y} L${X} ${A.y} L${X} ${B.y} L${e.x} ${e.y}`;
      else {
        const r = 12;
        d = `M${s.x} ${s.y} L${X - r} ${A.y} Q${X} ${A.y} ${X} ${A.y + r} ` +
            `L${X} ${B.y - r} Q${X} ${B.y} ${X + r} ${B.y} L${e.x} ${e.y}`;
      }
      firstDir = { x: A.x + 100, y: A.y }; lastDir = { x: B.x - 100, y: B.y };
      labelAt = { x: X, y: M.y }; break;
    }
    case 'straight-triangle': {
      const s = edgeAt(A, B), e = edgeAt(B, A), h = w / 2;
      d = `M${f(s.x + nx * h)} ${f(s.y + ny * h)} L${f(e.x)} ${f(e.y)} L${f(s.x - nx * h)} ${f(s.y - ny * h)} Z`;
      break;
    }
    default: {                                           // bezier (auto) and straight
      const s = edgeAt(A, B), e = edgeAt(B, A);
      d = `M${f(s.x)} ${f(s.y)} L${f(e.x)} ${f(e.y)}`;
    }
  }
  const tri = v.curve === 'straight-triangle';
  const dash = tri ? '' : v.lstyle === 'dashed' ? `stroke-dasharray="${w * 3} ${w * 2}"`
             : v.lstyle === 'dotted' ? `stroke-dasharray="0.1 ${w * 2}" stroke-linecap="round"` : '';
  // arrowhead: triangle resting on the node border. The "ghost" one
  // (dashed, semi-transparent) appears on mouse hover where the
  // head is not there yet, to show that a click adds it.
  const head = (P, from, ghost) => {
    const l = Math.hypot(P.x - from.x, P.y - from.y) || 1;
    const ux = (P.x - from.x) / l, uy = (P.y - from.y) / l;
    const tip = { x: P.x - ux * R, y: P.y - uy * R };
    const s = 5 + w * 1.6, b = { x: tip.x - ux * s * 1.4, y: tip.y - uy * s * 1.4 };
    const look = ghost
      ? `class="pv-ghost" fill="${col}" fill-opacity=".35" stroke="${col}" stroke-width="1" stroke-dasharray="2 1.5"`
      : `class="pv-head" fill="${col}"`;
    return `<path d="M${f(tip.x)} ${f(tip.y)} L${f(b.x - uy * s * 0.7)} ${f(b.y + ux * s * 0.7)} ` +
           `L${f(b.x + uy * s * 0.7)} ${f(b.y - ux * s * 0.7)} Z" ${look}/>`;
  };
  const fwd = v.arrow === 'target' || v.arrow === 'both';
  const bwd = v.arrow === 'source' || v.arrow === 'both';
  // clickable zones: the half of the source node and the half of the
  // target node of the preview; each adds/removes its own head
  const W = 360, H = 132;
  const side = (key, P, from, active, name) => {
    const tip = t(active ? 'edge.headRemove' : 'edge.headAdd', { n: name });
    const half = key === 'src' ? `x="0" y="0" width="${f(M.x)}" height="${H}"`
                               : `x="${f(M.x)}" y="0" width="${f(W - M.x)}" height="${H}"`;
    return `<g class="pv-side${active ? ' on' : ''}" data-side="${key}" tabindex="0" role="button" ` +
           `aria-pressed="${active}" aria-label="${esc(tip)}"><title>${esc(tip)}</title>` +
           `<rect class="pv-hit" ${half} rx="6"/>` + head(P, from, !active) + `</g>`;
  };
  const nameA = (na && na.label) || t('link.from');
  const nameB = (nb && nb.label) || (p === 'add' ? t('add.newNode') : t('link.to'));
  const lbl = v.label ? v.label.slice(0, 40) : '';
  const lw = lbl.length * 5.6 + 10;
  box.innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">` +
    (tri ? `<path d="${d}" fill="${col}"/>`
         : `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}" stroke-linejoin="round" ${dash}/>`) +
    side('src', A, firstDir, bwd, nameA) + side('dst', B, lastDir, fwd, nameB) +
    (lbl ? `<rect x="${f(labelAt.x - lw / 2)}" y="${f(labelAt.y - 17)}" width="${f(lw)}" height="15" rx="4" ` +
           `fill="#fff" stroke="#cbd5e1"/>` +
           `<text x="${f(labelAt.x)}" y="${f(labelAt.y - 6)}" text-anchor="middle" font-size="9.5" ` +
           `font-weight="600" fill="#334155">${esc(lbl)}</text>` : '') +
    previewNodeSvg(na, A.x, A.y, R, `pv-${p}-a`) + previewNodeSvg(nb, B.x, B.y, R, `pv-${p}-b`) +
    `</svg>`;
}

/* ================= GRAPH CONTEXT MENU ================= */
function showCtxMenu(x, y) {
  const m = $('#ctxmenu');
  if (!m) return;
  m.hidden = false;
  // stays inside the window even near the edges
  const r = m.getBoundingClientRect();
  m.style.left = Math.max(0, Math.min(x, window.innerWidth - r.width - 4)) + 'px';
  m.style.top = Math.max(0, Math.min(y, window.innerHeight - r.height - 4)) + 'px';
}
function hideCtxMenu() {
  const m = $('#ctxmenu');
  if (m) m.hidden = true;
}

/* ================= GLOBAL STATE ================= */
let cy = null;
let hasCase = false;             // is a case open? (without one, no nodes)
let showIds = true;
let pathOnly = false;
let degFilter = 0;
const hiddenCats = new Set();    // categories currently switched off (state of the buttons)
const catHidden = new Set();     // nodes removed from the view because their category is switched off
let curLayout = 'fcose';
let searchTimer = null;
const MIN_SEARCH = 3;            // minimum characters to show the results
let INDEX = [];                  // precomputed search index
const VOCAB = new Map();         // word -> ids of the nodes that contain it
const TOKEN_RE = /[\p{L}\p{N}][\p{L}\p{N}._]*/gu;
const expanded = new Set();      // expanded nodes
const selected = new Set();      // selected nodes (ctrl+click)
const visibleNodes = new Set();  // nodes added by hand (search/modal)
const pinned = new Set();        // nodes of the highlighted path
const placed = new Set();        // nodes that already have a stable position

const depthVal = () => parseInt(($('#depth') && $('#depth').value) || '1', 10) || 1;

/* ================= HIGHLIGHT LINKS (H+Click) =================
   Holding H down and clicking a node, that node and its visible DIRECT
   links stay highlighted; everything else is dimmed.
   A normal click (or H+Click on the same node) restores the view. */
let focusId = null;
let hDown = false;
let nDown = false;
const hiddenNodes = new Set();   // nodes hidden by hand with N+Click (this session only)

const typingInField = () => {
  const el = document.activeElement;
  return !!(el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable));
};

document.addEventListener('keydown', e => {
  if (typingInField()) return;
  if (e.key === 'h' || e.key === 'H') hDown = true;
  if (e.key === 'n' || e.key === 'N') nDown = true;
});
document.addEventListener('keyup', e => {
  if (e.key === 'h' || e.key === 'H') hDown = false;
  if (e.key === 'n' || e.key === 'N') nDown = false;
});
window.addEventListener('blur', () => { hDown = false; nDown = false; });

/* N+Click: removes the node from the view (with its links). Does not touch the data:
   it is a display-only choice, valid for this session. */
function hideNode(node) {
  const id = node.id();
  hiddenNodes.add(id);
  visibleNodes.delete(id);
  expanded.delete(id);
  if (focusId === id) clearFocus(true);
  refresh(false);
  syncHiddenBtn();
  $('#stat').textContent = t('stat.nodeHidden', { label: node.data('label'), n: hiddenNodes.size });
}

function showHiddenNodes() {
  if (!hiddenNodes.size) return;
  const n = hiddenNodes.size;
  hiddenNodes.clear();
  refresh(true);
  syncHiddenBtn();
  $('#stat').textContent = t('stat.hiddenRestored', { n });
}

/* The restore button appears only if something is hidden. */
function syncHiddenBtn() {
  const b = $('#showHidden');
  if (!b) return;
  b.hidden = !hiddenNodes.size;
  b.textContent = t('btn.showHidden', { n: hiddenNodes.size });
}

function clearFocus(silent) {
  if (!focusId) return;
  focusId = null;
  if (cy) cy.elements().removeClass('dim foc foc-src');
  if (!silent && cy) refreshStat();
}

/* Applies the highlighting based on focusId (also called after refresh,
   because changing the visible nodes also changes what must be dimmed). */
function applyFocus() {
  if (!cy || !focusId) return;
  const node = cy.getElementById(focusId);
  if (!node.length || node.hasClass('hidden')) { clearFocus(true); return; }

  const visible = cy.elements().not('.hidden');
  const keep = node.closedNeighborhood().not('.hidden');   // node + neighbours + links
  cy.batch(() => {
    cy.elements().removeClass('dim foc foc-src');
    visible.difference(keep).addClass('dim');
    keep.addClass('foc');
    node.removeClass('foc').addClass('foc-src');
  });
  return keep.nodes().length - 1;                          // how many direct links
}

function toggleFocus(node) {
  if (focusId === node.id()) { clearFocus(); return; }
  focusId = node.id();
  const n = applyFocus();
  $('#stat').textContent = t('stat.focusOn', { label: node.data('label'), n: n || 0 });
}

/* ================= LOADING ================= */
/* Without Cytoscape the graph is not created and EVERYTHING goes silent: search, filters, export.
   That was the case of the executable taken to a machine without a connection,
   when the libraries came from the internet. Now they live in static/vendor/, but
   if for any reason they failed to load the user must SEE it, not
   be left facing a search that does not respond. */
function graphLibReady() {
  if (typeof cytoscape !== 'undefined') return true;
  const box = $('#stat');
  if (box) { box.textContent = t('stat.libMissing'); box.classList.add('fatal'); }
  console.error('Cytoscape non caricato: static/vendor/ non trovata o illeggibile.');
  return false;
}

async function load() {
  if (!graphLibReady()) return;
  let g;
  try {
    const r = await fetch('/api/graph');
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    g = await r.json();
    if (g.error) throw new Error(g.error);
    if (g.translit_mode) TRANSLIT_MODE = g.translit_mode;
  } catch (err) {
    console.error('Caricamento fallito:', err);
    $('#stat').textContent = t('stat.loadError', { e: err.message });
    return;
  }
  // without data the graph is created anyway (empty): nodes can be created by hand,
  // a file imported or the AI used even on a fresh installation
  const empty = !g || !g.nodes || !g.nodes.length;
  if (empty) g = { nodes: [], edges: [], no_case: !!(g && g.no_case) };

  const deg = {};
  g.edges.forEach(e => { deg[e.source] = (deg[e.source] || 0) + 1; deg[e.target] = (deg[e.target] || 0) + 1; });

  const els = [];
  INDEX = [];
  VOCAB.clear();
  for (const n of g.nodes) {
    const ident = IDENT_TYPES.includes(n.ntype);
    n.deg = deg[n.id] || 0;
    n.ident = ident;
    n.cat = categoryOf(n);
    n.bridge = ident && n.deg > 1;
    n.size = n.ntype === 'target' ? 50 : n.ntype === 'photo' ? 46
           : n.ntype === 'account' ? 32 : (n.bridge ? 26 : 22);

    indexNode(n);      // search index (label, aliases, notes AND cards)

    els.push({ data: { ...n, icon: iconFor(n), color: TYPE_COLOR[n.ntype] || TYPE_COLOR.generic, disp: dispOf(n) } });
  }
  g.edges.forEach(e => els.push({ data: { ...e, rel: e.rel || '' } }));

  render(els);
  if (g.no_case) $('#stat').textContent = t('case.noneHint');
  else if (empty) $('#stat').textContent = t('stat.noData');
}

/* ================= RELOAD DATA (without restarting the app) =================
   Rereads the target folders and aligns the LIVE graph: adds the new
   nodes, removes those that disappeared, updates those that changed. The current view
   (open nodes, positions, zoom) stays intact. */
/* Label drawn on the node: with transliteration as an attribute
   (translit_mode = 'attribute') the Latin form sits under the name. */
let TRANSLIT_MODE = 'attribute';
function dispOf(n) {
  const r = n.roman;
  if (TRANSLIT_MODE === 'attribute' && r && r.toLowerCase() !== String(n.label || '').toLowerCase()) {
    return `${n.label}\n${r}`;
  }
  return n.label;
}

function indexNode(d) {
  let hay = `${d.label} ${d.id} ${d.platform} ${d.ntype} ${d.roman || ''} ` +
            `${d.script || ''} ${(d.aliases || []).join(' ')} ` +
            `${(d.alias_ids || []).join(' ')} ${d.note || ''}`;
  const headLen = hay.toLowerCase().length;
  for (const r of (d.records || [])) {
    hay += ' ' + (r.collection || '');
    try { hay += ' ' + JSON.stringify(r.raw); } catch (_) {}
  }
  hay = hay.toLowerCase().slice(0, 20000);
  INDEX.push({ id: d.id, hay, headLen });
  const toks = hay.match(TOKEN_RE);
  if (toks) {
    let c = 0;
    for (const w of new Set(toks)) {
      if (w.length < 2 || w.length > 40) continue;
      let post = VOCAB.get(w);
      if (!post) { post = []; VOCAB.set(w, post); }
      if (post.length < 8000) post.push(d.id);
      if (++c > 600) break;
    }
  }
}

function rebuildIndex() {
  INDEX = [];
  VOCAB.clear();
  cy.nodes().forEach(n => indexNode(n.data()));
}

/* Aligns the LIVE graph to a graph just received from the server: adds the new
   nodes, removes those that disappeared (including those merged into another card after
   a rename) and updates those that changed. The current view stays intact. */
function applyGraphData(g) {
  if (g.translit_mode) TRANSLIT_MODE = g.translit_mode;
  {
    const deg = {};
    g.edges.forEach(e => { deg[e.source] = (deg[e.source] || 0) + 1;
                           deg[e.target] = (deg[e.target] || 0) + 1; });
    const newIds = new Set(g.nodes.map(n => n.id));
    const newEdgeIds = new Set(g.edges.map(e => e.id));
    let added = 0, removed = 0, updated = 0;

    cy.batch(() => {
      // 1) drop the nodes that no longer exist in the data
      cy.nodes().forEach(n => {
        const id = n.id();
        if (newIds.has(id)) return;
        [visibleNodes, expanded, selected, pinned, placed, hiddenNodes]
          .forEach(s => s.delete(id));
        if (focusId === id) focusId = null;
        n.remove();
        removed++;
      });
      // 2) add the new ones and update the existing ones
      g.nodes.forEach(d => {
        d.deg = deg[d.id] || 0;
        d.ident = IDENT_TYPES.includes(d.ntype);
        d.cat = categoryOf(d);
        d.bridge = d.ident && d.deg > 1;
        d.size = d.ntype === 'target' ? 50 : d.ntype === 'photo' ? 46
               : d.ntype === 'account' ? 32 : (d.bridge ? 26 : 22);
        const ex = cy.getElementById(d.id);
        if (!ex.length) { addNodeToCy(d); added++; return; }
        Object.keys(d).forEach(k => ex.data(k, d[k]));   // cards, notes, label…
        ['url', 'edited', 'note'].forEach(k => { if (!(k in d)) ex.removeData(k); });
        ex.data('renamed', !!d.renamed);                // restored: goes back to false
        ex.data('label_orig', d.label_orig || '');
        ex.data('disp', dispOf(d));
        ex.data('icon', iconFor(d));
        ex.data('color', TYPE_COLOR[d.ntype] || TYPE_COLOR.generic);
        ex.toggleClass('noted', !!d.note);
        updated++;
      });
      // 3) links: remove the outdated ones, add the new ones, update name and style
      //    of the remaining ones (edited with right-click)
      cy.edges().forEach(e => { if (!newEdgeIds.has(e.id())) e.remove(); });
      g.edges.forEach(e => {
        const ex = cy.getElementById(e.id);
        if (ex.length) {
          if (ex.data('source') !== e.source || ex.data('target') !== e.target) {
            if (cy.getElementById(e.source).length && cy.getElementById(e.target).length) {
              ex.move({ source: e.source, target: e.target });
            }
          }
          setEdgeProps(cy.getElementById(e.id), e);   // move() recreates the link
          return;
        }
        if (cy.getElementById(e.source).length && cy.getElementById(e.target).length) {
          cy.add({ group: 'edges', data: Object.assign({ rel: '' }, e) });
        }
      });
    });

    rebuildIndex();
    ADJ = null;
    refreshTranslitBtn();
    clearFocus(true);
    buildLegend(); buildCatFilters(); buildDegFilter();
    syncHiddenBtn(); syncDegOnlyBtn(); renderSel();
    refresh(added > 0);
    upgradeBrandIcons();
    return { tot: g.nodes.length, add: added, del: removed, upd: updated };
  }
}

/* Rereads the graph from the server WITHOUT rereading the target files: needed after
   a change to the annotations (note, label, link). */
async function syncGraph() {
  const r = await fetch('/api/graph');
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const g = await r.json();
  if (g.error) throw new Error(g.error);
  return applyGraphData(g);
}

async function reloadData() {
  const btn = $('#reloadData');
  if (btn) { btn.disabled = true; btn.textContent = t('btn.reloading'); }
  try {
    const g = await apiPost('/api/reload', {});
    $('#stat').textContent = t('stat.reloaded', applyGraphData(g));
  } catch (err) {
    alert(t('err.reloadFailed', { e: err.message }));
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = t('btn.reloadData'); }
  }
}
on('#reloadData', 'click', reloadData);

/* ================= TRANSLITERATION WITH THE CHATBOT =================
   The button appears only if chatbot.conf has an endpoint. If the chatbot
   does not respond nothing happens: work continues with the hand-compiled
   dictionary and the usual automatic transliteration. */
async function refreshTranslitBtn() {
  const b = $('#aiTranslit');
  if (!b) return;
  try {
    const r = await fetch('/api/translit/status');
    if (!r.ok) { b.hidden = true; return; }
    const s = await r.json();
    b.hidden = !s.enabled;
    b.disabled = !s.todo;
    b.textContent = s.todo ? t('btn.aiTranslitN', { n: s.todo }) : t('btn.aiTranslitOk');
    b.title = (s.down && s.reason) ? t('ai.down', { e: s.reason })
                                   : t('ai.hint', { model: s.model || '' });
  } catch (_) {
    b.hidden = true;
  }
}

on('#aiTranslit', 'click', async () => {
  const b = $('#aiTranslit');
  const testo = b.textContent;
  b.disabled = true;
  b.textContent = t('btn.aiWorking');
  try {
    const j = await apiPost('/api/translit/ai', {});
    if (j.tradotte) {
      await reloadData();                 // the Latin labels must be redone
      $('#stat').textContent = t('stat.aiDone', { n: j.tradotte, rest: j.restano });
    } else {
      $('#stat').textContent = t('stat.aiNothing');
    }
  } catch (err) {
    alert(t('err.aiFailed', { e: err.message }));
  } finally {
    b.textContent = testo;
    b.disabled = false;
    refreshTranslitBtn();
  }
});

/* ================= GRAPH ================= */
function render(els) {
  cy = cytoscape({
    container: $('#graph'),
    elements: els,
    wheelSensitivity: 0.25,
    minZoom: 0.05,
    maxZoom: 3,
    zoom: 1,                 // no automatic fit at startup (it started at zoom 3)
    pan: { x: 0, y: 0 },
    motionBlur: false,
    layout: { name: 'preset', fit: false },
    // Ctrl (or Shift) + drag on the background = selection box:
    // with panning active Cytoscape starts it only if a modifier is held down
    boxSelectionEnabled: true,
    selectionType: 'additive',
    style: [
      { selector: 'node', style: {
        'width': 'data(size)', 'height': 'data(size)',
        'shape': 'ellipse',
        'background-color': '#ffffff',
        'background-image': 'data(icon)',
        'background-fit': 'contain',
        'background-clip': 'none',
        'background-image-containment': 'inside',
        'background-position-x': '50%',
        'background-position-y': '50%',
        'background-offset-x': 0,
        'background-offset-y': 0,
        'background-width': '62%', 'background-height': '62%',
        'background-width-relative-to': 'inner',
        'background-height-relative-to': 'inner',
        'border-width': 2.5,
        'border-color': 'data(color)',
        'label': 'data(disp)',
        'color': '#0f172a',
        'font-size': 11,
        'font-weight': '600',
        'text-valign': 'bottom',
        'text-margin-y': 5,
        'text-wrap': 'wrap',
        'text-max-width': 110,
        'text-outline-color': '#ffffff',
        'text-outline-width': 3,
        'min-zoomed-font-size': 7
      } },
      { selector: 'node[ntype="target"]', style: {
        'font-size': 14, 'font-weight': 'bold', 'color': '#b45309',
        'border-width': 4, 'background-color': '#fef3c7'
      } },
      // starting data (from the target's initial file): red border.
      // The target is excluded: it already has its own distinctive gold style.
      { selector: 'node[?seed][ntype != "target"]', style: {
        'border-color': '#dc2626', 'border-width': 4
      } },
      { selector: 'node.exp', style: { 'border-style': 'double', 'border-width': 6 } },
      { selector: 'edge', style: {
        'width': 2, 'line-color': '#94a3b8', 'opacity': 0.8, 'curve-style': 'bezier',
        'target-arrow-shape': 'none', 'source-arrow-shape': 'none',
        'target-arrow-color': '#94a3b8', 'source-arrow-color': '#94a3b8',
        'arrow-scale': 1.25
      } },
      // Directional arrows
      { selector: 'edge[arrow = "target"]', style: {
        'target-arrow-shape': 'triangle', 'source-arrow-shape': 'none'
      } },
      { selector: 'edge[arrow = "source"]', style: {
        'target-arrow-shape': 'none', 'source-arrow-shape': 'triangle'
      } },
      { selector: 'edge[arrow = "both"]', style: {
        'target-arrow-shape': 'triangle', 'source-arrow-shape': 'triangle'
      } },
      { selector: 'edge[arrow = "none"]', style: {
        'target-arrow-shape': 'none', 'source-arrow-shape': 'none'
      } },
      // Link shapes (curve, straight, segments)
      { selector: 'edge[curve = "straight"]', style: {
        'curve-style': 'straight'
      } },
      { selector: 'edge[curve = "bezier"]', style: {
        'curve-style': 'bezier'
      } },
      { selector: 'edge[curve = "unbundled-bezier"]', style: {
        'curve-style': 'unbundled-bezier', 'control-point-weights': 0.5,
        'control-point-distances': e => -(e.data('bend') ?? EDGE_DEFAULT_BEND)
      } },
      { selector: 'edge[curve = "segments"], edge[curve = "round-segments"]', style: {
        'curve-style': 'segments', 'segment-weights': 0.5,
        'segment-distances': e => -(e.data('bend') ?? EDGE_DEFAULT_BEND)
      } },
      { selector: 'edge[curve = "round-segments"]', style: {
        'curve-style': 'round-segments', 'segment-radius': 18
      } },
      { selector: 'edge[curve = "taxi"], edge[curve = "round-taxi"]', style: {
        'curve-style': 'taxi', 'taxi-direction': 'auto', 'taxi-turn': '50%'
      } },
      { selector: 'edge[curve = "round-taxi"]', style: {
        'curve-style': 'round-taxi', 'taxi-radius': 14
      } },
      { selector: 'edge[curve = "straight-triangle"]', style: {
        'curve-style': 'straight-triangle', 'width': 8
      } },
      // Link labels
      { selector: 'edge[?label]', style: {
        'label': 'data(label)',
        'text-rotation': 'autorotate',
        'text-margin-y': -8,
        'font-size': 9.5,
        'font-weight': '600',
        'color': '#334155',
        'text-background-opacity': 0.92,
        'text-background-color': '#ffffff',
        'text-background-padding': '3px',
        'text-background-shape': 'roundrectangle',
        'text-border-color': '#cbd5e1',
        'text-border-width': 1,
        'text-border-opacity': 0.8,
        'text-wrap': 'ellipsis',
        'text-max-width': 140
      } },
      { selector: 'edge[rel="alias"]', style: {
        'line-color': '#f59e0b', 'target-arrow-color': '#f59e0b', 'source-arrow-color': '#f59e0b',
        'line-style': 'dashed', 'width': 3, 'opacity': 1
      } },
      { selector: 'edge[rel="phone-link"]', style: {
        'line-color': '#059669', 'target-arrow-color': '#059669', 'source-arrow-color': '#059669',
        'line-style': 'dashed', 'width': 2.5
      } },
      { selector: 'edge[rel="email-alias"]', style: {
        'line-color': '#db2777', 'target-arrow-color': '#db2777', 'source-arrow-color': '#db2777',
        'line-style': 'dashed', 'width': 2.5
      } },
      { selector: 'edge[rel="translit"]', style: {
        'line-color': '#0891b2', 'target-arrow-color': '#0891b2', 'source-arrow-color': '#0891b2',
        'line-style': 'dotted', 'width': 3, 'opacity': 1
      } },
      { selector: 'node[ntype="latin"]', style: { 'color': '#0e7490', 'border-style': 'dashed' } },
      { selector: 'node[ntype="photo"]', style: {
        'background-fit': 'cover', 'background-width': '100%', 'background-height': '100%',
        'background-clip': 'node', 'border-width': 3, 'shape': 'round-rectangle',
        'color': '#0f766e'
      } },
      { selector: 'edge[rel="photo"]', style: {
        'line-color': '#14b8a6', 'target-arrow-color': '#14b8a6', 'source-arrow-color': '#14b8a6', 'width': 2.5
      } },
      { selector: 'node[?pic]', style: {
        'background-fit': 'cover', 'background-width': '100%', 'background-height': '100%',
        'background-clip': 'node', 'border-width': 3
      } },
      // evidence imported from Cognitor or from a transcription
      { selector: 'edge[evid = "seen"]', style: {
        'line-color': '#b45309', 'target-arrow-color': '#b45309', 'source-arrow-color': '#b45309',
        'width': 'mapData(seen_n, 1, 12, 2, 9)', 'opacity': 1
      } },
      { selector: 'edge[evid = "speaks"]', style: {
        'line-color': '#7c3aed', 'target-arrow-color': '#7c3aed', 'line-style': 'dashed', 'width': 2.5
      } },
      { selector: 'edge[evid = "appears"]', style: {
        'line-color': '#0f766e', 'target-arrow-color': '#0f766e', 'line-style': 'dotted', 'width': 2.5
      } },
      // Style chosen by the user for the single link: it wins over that
      // of the relation type (but not over the highlights below)
      { selector: 'edge[?color]', style: {
        'line-color': 'data(color)', 'target-arrow-color': 'data(color)',
        'source-arrow-color': 'data(color)', 'opacity': 1
      } },
      { selector: 'edge[lstyle = "solid"]', style: { 'line-style': 'solid' } },
      { selector: 'edge[lstyle = "dashed"]', style: { 'line-style': 'dashed', 'line-dash-pattern': [8, 5] } },
      { selector: 'edge[lstyle = "dotted"]', style: { 'line-style': 'dotted' } },
      { selector: 'edge[?width]', style: { 'width': 'data(width)' } },
      // Style chosen for ALL links from the left panel: it sits at the
      // bottom, so it wins over the styles of the single link (to go
      // back, choose «as set»)
      { selector: 'edge.gs-bezier', style: { 'curve-style': 'bezier' } },
      { selector: 'edge.gs-straight', style: { 'curve-style': 'straight' } },
      { selector: 'edge.gs-unbundled-bezier', style: {
        'curve-style': 'unbundled-bezier', 'control-point-weights': 0.5,
        'control-point-distances': e => -(e.data('bend') ?? EDGE_DEFAULT_BEND)
      } },
      { selector: 'edge.gs-segments, edge.gs-round-segments', style: {
        'curve-style': 'segments', 'segment-weights': 0.5,
        'segment-distances': e => -(e.data('bend') ?? EDGE_DEFAULT_BEND)
      } },
      { selector: 'edge.gs-round-segments', style: { 'curve-style': 'round-segments', 'segment-radius': 18 } },
      { selector: 'edge.gs-taxi, edge.gs-round-taxi', style: {
        'curve-style': 'taxi', 'taxi-direction': 'auto', 'taxi-turn': '50%'
      } },
      { selector: 'edge.gs-round-taxi', style: { 'curve-style': 'round-taxi', 'taxi-radius': 14 } },
      { selector: 'edge.gs-straight-triangle', style: { 'curve-style': 'straight-triangle' } },
      { selector: 'edge.gl-solid', style: { 'line-style': 'solid' } },
      { selector: 'edge.gl-dashed', style: { 'line-style': 'dashed', 'line-dash-pattern': [8, 5] } },
      { selector: 'edge.gl-dotted', style: { 'line-style': 'dotted' } },
      { selector: 'edge.gw-1', style: { 'width': 1 } },
      { selector: 'edge.gw-2', style: { 'width': 2 } },
      { selector: 'edge.gw-3', style: { 'width': 3 } },
      { selector: 'edge.gw-4', style: { 'width': 4 } },
      { selector: 'edge.gw-6', style: { 'width': 6 } },
      { selector: 'edge.gw-8', style: { 'width': 8 } },
      { selector: 'edge:active', style: { 'overlay-opacity': 0.12, 'overlay-padding': 6 } },
      { selector: 'edge.edg-hi', style: {
        'underlay-color': '#f59e0b', 'underlay-opacity': 0.35, 'underlay-padding': 5
      } },
      { selector: '.hidden', style: { 'display': 'none' } },
      { selector: 'node.sel', style: {
        'border-color': '#f59e0b', 'border-width': 5,
        'background-color': '#fef3c7', 'z-index': 120
      } },
      { selector: 'node.fresh', style: { 'border-color': '#2563eb', 'border-width': 5 } },
      // H+Click: the node and its direct links stay highlighted,
      // everything else is dimmed
      { selector: 'node.dim', style: { 'opacity': 0.13, 'text-opacity': 0.13 } },
      { selector: 'edge.dim', style: { 'opacity': 0.05 } },
      { selector: 'node.foc', style: {
        'border-color': '#7c3aed', 'border-width': 5, 'z-index': 140
      } },
      { selector: 'node.foc-src', style: {
        'border-color': '#6d28d9', 'border-width': 7,
        'background-color': '#ede9fe', 'z-index': 150
      } },
      { selector: 'edge.foc', style: {
        'line-color': '#7c3aed', 'target-arrow-color': '#7c3aed', 'source-arrow-color': '#7c3aed',
        'width': 4, 'opacity': 1, 'z-index': 140
      } },
      // nodes with a note NO longer change appearance (no yellow outline):
      // the note stays in the tooltip, in the card and in the search.
      { selector: 'node.path', style: { 'border-color': '#10b981', 'border-width': 5, 'z-index': 110 } },
      { selector: 'edge.path', style: {
        'line-color': '#10b981', 'target-arrow-color': '#10b981', 'source-arrow-color': '#10b981',
        'line-style': 'solid', 'width': 4, 'opacity': 1, 'z-index': 110
      } },
      { selector: 'node.path.sel', style: { 'border-color': '#f59e0b', 'border-width': 6, 'background-color': '#d1fae5', 'z-index': 125 } },
      { selector: 'node.path-hi', style: { 'border-color': '#0ea5e9', 'border-width': 7, 'z-index': 130 } },
      { selector: 'edge.path-hi', style: {
        'line-color': '#0ea5e9', 'target-arrow-color': '#0ea5e9', 'source-arrow-color': '#0ea5e9',
        'width': 6, 'opacity': 1, 'z-index': 130
      } }
    ]
  });

  cy.nodes().forEach(n => { if (n.data('note')) n.addClass('noted'); });
  buildDegFilter();
  buildCatFilters();
  buildLegend();
  if ($('#openMode')) $('#openMode').value = openMode;   // restore the saved choice
  syncHiddenBtn();
  syncDegOnlyBtn();
  refresh(false);            // at startup: empty graph
  upgradeBrandIcons();
  refreshViews();            // fill the drop-down of saved views
  loadSrcStatus();           // state of the document sources index

  cy.on('tap', 'node', e => {
    const oe = e.originalEvent;
    if (oe && oe.altKey) {                       // Alt+Click = open social profile
      const r = openSocial(e.target);
      const s = $('#stat');
      if (r.ok && r.mode === 'copy') s.textContent = t('stat.linkCopied', { url: r.url });
      else if (r.ok) s.textContent = t('stat.profileOpened', { url: r.url });
      else if (r.reason === 'no-handle') s.textContent = t('stat.noHandle');
      else s.textContent = t('stat.notSocial');
      return;
    }
    if (nDown) { hideNode(e.target); return; }      // N+Click = hide the node
    if (hDown) { toggleFocus(e.target); return; }   // H+Click = highlight the links
    clearFocus(true);                                // normal click: full view
    if (oe && (oe.ctrlKey || oe.metaKey || oe.shiftKey)) toggleSel(e.target);
    else toggleExpand(e.target);
  });
  cy.on('cxttap', 'node', e => { hideTip(); openModal(e.target); });
  // selection box: the enclosed nodes are ADDED to the app's
  // selection (the same as Ctrl+Click, used by paths and "Link")
  let boxed = [];
  cy.on('boxselect', 'node', e => { boxed.push(e.target); });
  cy.on('boxend', () => setTimeout(() => {
    let n = 0;
    boxed.forEach(node => {
      if (node.hasClass('hidden') || selected.has(node.id())) return;
      selected.add(node.id()); node.addClass('sel'); n++;
    });
    boxed = [];
    cy.elements().unselect();              // the "real" selection is the app's
    if (n) {
      renderSel(); refresh(false);
      $('#stat').textContent = t('stat.boxSelected', { n, tot: selected.size });
    }
  }, 0));
  // dragging a selected node moves all the other selected ones
  // with it (the app's selection is not Cytoscape's, which
  // would otherwise do it by itself)
  let group = null;                        // { grabbed, last: {x,y}, others }
  cy.on('grab', 'node', e => {
    const n = e.target;
    group = null;
    if (!selected.has(n.id()) || selected.size < 2) return;
    const others = cy.collection();
    selected.forEach(id => {
      const m = cy.getElementById(id);
      if (id !== n.id() && m.length && !m.hasClass('hidden') && !m.locked()) others.merge(m);
    });
    if (others.length) group = { grabbed: n, last: { ...n.position() }, others };
  });
  cy.on('drag', 'node', e => {
    if (!group || e.target !== group.grabbed) return;
    const p = e.target.position();
    const dx = p.x - group.last.x, dy = p.y - group.last.y;
    group.last = { x: p.x, y: p.y };
    if (dx || dy) group.others.positions(m => {
      const q = m.position();
      return { x: q.x + dx, y: q.y + dy };
    });
  });
  cy.on('free', 'node', () => {
    if (group) group.others.forEach(m => placed.add(m.id()));
    group = null;
  });
  // right-click on a link: name, arrows, colour, line…
  cy.on('cxttap', 'edge', e => { hideTip(); openEdgeModal(e.target); });
  cy.on('mouseover', 'edge', e => showEdgeTip(e.target));
  cy.on('mousemove', 'edge', e => moveTip(e));
  cy.on('mouseout', 'edge', hideTip);
  cy.on('tap', e => {
    if (e.target === cy) {
      cy.elements().removeClass('path-hi');
      clearFocus();                                  // click on the background: full view
      hideResults();
      // click on the background WITHOUT Ctrl/Cmd/Shift: the whole selection is lost
      // (with the modifier held down the selection stays, as in the box)
      const oe = e.originalEvent;
      if (selected.size && !(oe && (oe.ctrlKey || oe.metaKey || oe.shiftKey))) clearSel();
    }
  });
  cy.on('mouseover', 'node', e => showTip(e.target));
  cy.on('mousemove', 'node', e => moveTip(e));
  cy.on('mouseout', 'node', hideTip);
  cy.on('drag zoom pan', () => { hideTip(); hideCtxMenu(); });
  // right-click on the background: menu with «New node»
  cy.on('cxttap', e => {
    if (e.target !== cy) return;
    hideTip();
    const oe = e.originalEvent;
    showCtxMenu(oe ? oe.clientX : 0, oe ? oe.clientY : 0);
  });

  $('#stat').textContent = t('stat.ready', { n: cy.nodes().length });
}

/* ================= SEARCH ================= */
let lastMatches = [];
let DIST = new Map();

/* Bounded Levenshtein distance: returns max+1 if it exceeds the threshold */
function lev(a, b, max) {
  if (a === b) return 0;
  const la = a.length, lb = b.length;
  if (Math.abs(la - lb) > max) return max + 1;
  if (!la) return lb; if (!lb) return la;
  let prev = new Array(lb + 1), cur = new Array(lb + 1);
  for (let j = 0; j <= lb; j++) prev[j] = j;
  for (let i = 1; i <= la; i++) {
    cur[0] = i;
    const from = Math.max(1, i - max), to = Math.min(lb, i + max);
    if (from > 1) cur[from - 1] = max + 1;
    let best = max + 1;
    for (let j = from; j <= to; j++) {
      const cost = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (cur[j] < best) best = cur[j];
    }
    for (let j = to + 1; j <= lb; j++) cur[j] = max + 1;
    if (best > max) return max + 1;
    const t = prev; prev = cur; cur = t;
  }
  return prev[lb];
}

/* Nodes containing a word within distance max of the term.
   Scans the global vocabulary (unique words of the graph), not the nodes:
   the cost depends not on the number of nodes but on the number of distinct words. */
function termHits(term, max) {
  const hit = new Map();
  for (const it of INDEX) if (it.hay.includes(term)) hit.set(it.id, 0);   // exact
  // the vocabulary is tokenised: compare without punctuation at the edges (+39, "mario,"...)
  const t = term.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '') || term;
  for (const [w, ids] of VOCAB) {
    if (Math.abs(w.length - t.length) > max) continue;
    const d = lev(t, w, max);
    if (d > max) continue;
    for (const id of ids) {
      const p = hit.get(id);
      if (p === undefined || d < p) hit.set(id, d);
    }
  }
  return hit;
}

/* Intersection of the terms: a node is valid only if it satisfies them all */
function fuzzySearch(terms, max) {
  let acc = null;
  for (const t of terms) {
    const hit = termHits(t, max);
    if (acc === null) acc = hit;
    else {
      const next = new Map();
      for (const [id, d] of hit) {
        const p = acc.get(id);
        if (p !== undefined) next.set(id, p + d);
      }
      acc = next;
    }
    if (!acc.size) break;
  }
  return [...(acc || new Map())].sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]));
}

/* Realigns the search index of a node (used after saving a note,
   so the text of the note is searchable without reloading the page). */
function reindexNode(node) {
  const d = node.data();
  const it = INDEX.find(x => x.id === d.id);
  if (!it) return;
  const base = `${d.label} ${d.id} ${d.platform} ${d.ntype} ${d.roman || ''} ` +
               `${d.script || ''} ${(d.aliases || []).join(' ')} ${(d.alias_ids || []).join(' ')} ` +
               `${d.note || ''}`;
  // keeps the "cards" part already indexed, replacing only the header
  const tail = it.hay.slice(it.headLen || 0);
  const head = base.toLowerCase();
  it.headLen = head.length;
  it.hay = (head + tail).slice(0, 20000);
  // vocabulary: adds the words of the note for the approximate search
  const toks = String(d.note || '').toLowerCase().match(TOKEN_RE);
  if (toks) {
    for (const w of new Set(toks)) {
      if (w.length < 2 || w.length > 40) continue;
      let post = VOCAB.get(w);
      if (!post) { post = []; VOCAB.set(w, post); }
      if (!post.includes(d.id)) post.push(d.id);
    }
  }
}

function searchNodes(q) {
  const list = $('#search-results');
  if (!list) return;
  const query = q.trim();
  if (!cy || !query) { list.innerHTML = ''; DIST = new Map(); hideResults(); return; }
  // at least 3 characters are needed: with 1-2 the results would be thousands
  // with ideograms two characters are enough (Chinese names often have two)
  const minChars = /[\u3400-\u9FFF\uF900-\uFAFF]/.test(query) ? 2 : MIN_SEARCH;
  if (query.length < minChars) {
    DIST = new Map(); lastMatches = [];
    list.innerHTML = `<li class="no-res">${esc(t('search.minChars', { n: minChars }))}</li>`;
    list.style.display = 'block';
    return;
  }

  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const fuzzy = $('#fuzzy') && $('#fuzzy').checked;
  const maxD = parseInt(($('#fuzzyLevel') && $('#fuzzyLevel').value) || '1', 10);
  const ids = [];

  if (!fuzzy) {
    for (const it of INDEX) {
      let ok = true;
      for (const t of terms) { if (!it.hay.includes(t)) { ok = false; break; } }
      if (ok) ids.push(it.id);
    }
  } else {
    const scored = fuzzySearch(terms, maxD);
    DIST = new Map(scored);
    scored.forEach(([id]) => ids.push(id));
  }

  // sort the results by name (ascending). With the approximate search
  // the most similar stay at the top (distance); at equal distance it is alphabetical.
  const labelOf = id => {
    const n = cy.getElementById(id);
    return n.length ? String(n.data('label') || '') : '';
  };
  const byName = (a, b) => labelOf(a).localeCompare(labelOf(b), undefined,
                                                    { sensitivity: 'base', numeric: true });
  if (fuzzy) ids.sort((a, b) => (DIST.get(a) - DIST.get(b)) || byName(a, b));
  else ids.sort(byName);

  lastMatches = ids;

  list.innerHTML = '';
  if (!ids.length) {
    list.innerHTML = `<li class="no-res">${esc(t('search.noRes'))}</li>`;
    list.style.display = 'block';
    return;
  }

  const frag = document.createDocumentFragment();
  ids.slice(0, 80).forEach(id => {
    const n = cy.getElementById(id);
    if (!n.length) return;
    const li = document.createElement('li');
    li.dataset.id = id;
    if (visibleNodes.has(id)) li.classList.add('added');
    const d = DIST.get(id);
    li.innerHTML = `<img src="${n.data('icon')}" alt=""><span>${esc(n.data('label'))}</span>` +
      (d ? `<em class="dist">~${d}</em>` : '') + `<small>${esc(n.data('ntype'))}</small>`;
    frag.appendChild(li);
  });
  list.appendChild(frag);

  const foot = document.createElement('li');
  foot.className = 'res-foot';
  foot.textContent = t('search.foot', { n: ids.length });
  list.appendChild(foot);
  list.style.display = 'block';
}

// Delegation: the results stay clickable even after new searches
on('#search-results', 'click', e => {
  e.stopPropagation();
  if (e.target.closest('li.res-foot')) { showAllMatches(); return; }
  const li = e.target.closest('li[data-id]');
  if (!li) return;
  addToGraph([li.dataset.id], true);
  li.classList.add('added');
});

function hideResults() {
  const l = $('#search-results');
  if (l) l.style.display = 'none';
}

/* Adds nodes to the graph WITHOUT removing those already present */
function addToGraph(ids, focus) {
  if (!cy || !ids || !ids.length) return;
  const fresh = ids.filter(id => !visibleNodes.has(id) && cy.getElementById(id).length);
  ids.forEach(id => { if (cy.getElementById(id).length) visibleNodes.add(id); });
  unhide(ids);                       // adding by hand wins over a hiding
  refresh(true);

  const want = new Set(ids);
  const eles = cy.nodes().filter(n => want.has(n.id()) && !n.hasClass('hidden'));
  if (!eles.length) return;

  cy.nodes('.fresh').removeClass('fresh');
  eles.addClass('fresh');
  setTimeout(() => eles.removeClass('fresh'), 1600);

  if (focus) bringIntoView(eles);
  const s = $('#stat');
  if (s && !fresh.length) s.textContent += t('stat.alreadyThere');
}

/* Limits the zoom after an automatic fit (avoids gigantic nodes) */
function capZoom(max = 1.5) {
  try {
    if (cy.zoom() > max) cy.zoom({ level: max, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  } catch (_) {}
}

/* Brings the nodes into view moving the camera as little as possible */
function bringIntoView(eles) {
  const bb = eles.boundingBox();
  const ext = cy.extent();
  const inside = bb.x1 >= ext.x1 && bb.x2 <= ext.x2 && bb.y1 >= ext.y1 && bb.y2 <= ext.y2;
  if (inside) return;
  const z = cy.zoom();
  const w = cy.width(), h = cy.height();
  const cx = (bb.x1 + bb.x2) / 2, cyy = (bb.y1 + bb.y2) / 2;
  cy.animate({ pan: { x: w / 2 - cx * z, y: h / 2 - cyy * z } }, { duration: 350 });
}

function showAllMatches() {
  if (!lastMatches.length) return;
  addToGraph(lastMatches.slice(0, 300), true);
  const l = $('#search-results');
  if (l) l.querySelectorAll('li[data-id]').forEach(li => li.classList.add('added'));
}

/* ================= VISIBILITY & EXPANSION ================= */
function nbhd(node, depth) {
  let set = cy.collection().union(node);
  for (let i = 0; i < depth; i++) set = set.union(set.neighborhood('node'));
  return set;
}

function visibleSet() {
  const vis = new Set(visibleNodes);
  const d = depthVal();
  expanded.forEach(id => {
    const n = cy.getElementById(id);
    if (!n.length) return;
    vis.add(id);
    nbhd(n, d).forEach(m => vis.add(m.id()));
  });
  selected.forEach(id => vis.add(id));
  pinned.forEach(id => vis.add(id));
  // "Links" filter: reveals the nodes with EXACTLY N links,
  // together with the nodes they are linked to (otherwise they would appear isolated)
  computeDegReveal();
  degReveal.forEach(id => vis.add(id));
  return vis;
}

/* Set of the nodes shown by the filter on the number of links:
   those with the exact degree + their direct neighbours. */
let degReveal = new Set();
let degOnly = false;          // true = only the nodes with that degree, without the neighbours
function computeDegReveal() {
  degReveal = new Set();
  if (!cy || !degFilter) return;
  cy.nodes().forEach(n => {
    if ((n.data('deg') || 0) !== degFilter) return;
    degReveal.add(n.id());
    if (!degOnly) n.neighborhood('node').forEach(m => degReveal.add(m.id()));
  });
}

/* The "hide/show the others" button makes sense only with the filter active. */
function syncDegOnlyBtn() {
  const b = $('#degOnly');
  if (!b) return;
  b.hidden = !degFilter;
  b.textContent = degOnly ? t('btn.showOthers') : t('btn.hideOthers');
  b.classList.toggle('on', degOnly);
}

function allowed(n) {
  const id = n.id();
  if (hiddenNodes.has(id)) return false;      // hidden by hand (N+Click)
  if (catHidden.has(id)) return false;        // category switched off by the buttons
  if (pathOnly && pinned.size) return pinned.has(id) || selected.has(id);
  // "Links" filter active: it alone decides, even for nodes already in the
  // view (otherwise the filter would add nodes without ever removing any, and
  // "Hide the others" would have no effect)
  if (degFilter > 0) return degReveal.has(id);
  // NB: categories are NOT a permanent filter: they are applied on request
  // to the visible graph ("Apply" button). So expanding a node always shows
  // all its links, without category constraints.
  if (visibleNodes.has(id) || selected.has(id) || pinned.has(id)) return true;
  if (!showIds && n.data('ident')) return false;
  return true;
}

function refresh(doLayout = false) {
  if (!cy) return;
  const vis = visibleSet();
  const freshIds = [];

  cy.batch(() => {
    cy.nodes().forEach(n => {
      const show = vis.has(n.id()) && allowed(n);
      n.toggleClass('hidden', !show);
      n.toggleClass('exp', expanded.has(n.id()));
      if (show && !placed.has(n.id())) freshIds.push(n.id());
    });
    cy.edges().forEach(e => {
      const s = cy.getElementById(e.data('source'));
      const t = cy.getElementById(e.data('target'));
      let ok = s.length && t.length && !s.hasClass('hidden') && !t.hasClass('hidden');
      e.toggleClass('hidden', !ok);
    });
  });

  applyGStyle();          // style chosen for all links
  // NB: no global layout and no camera movement: expanding a node
  // positions only the new nodes, everything else stays where it is
  if (doLayout && freshIds.length) placeFresh(freshIds);

  if (focusId) applyFocus();     // the highlighting follows the nodes now visible
  refreshStat();
}

/* Status line with the count of the visible nodes. */
function refreshStat() {
  if (!cy) return;
  const c = cy.nodes().not('.hidden').length;
  $('#stat').textContent = t('stat.visible', { v: c, t: cy.nodes().length, e: expanded.size });
}

/* An explicit user action (expansion, addition) takes precedence over the
   hidings done before: the nodes involved become visible again. So the
   category filters do not constrain later operations. */
function unhide(ids) {
  let n = 0;
  ids.forEach(id => {
    if (hiddenNodes.delete(id)) n++;
    catHidden.delete(id);            // an explicit action also wins over switched-off categories
  });
  if (n) syncHiddenBtn();
}

/* Click on a node: the first expands it (shows its links), the second
   collapses it. Collapsing hides the neighbours that were visible because of this
   expansion, even if they had been added in another way (search, import);
   those expanded in turn stay, as do those neighbouring another expanded node,
   the selected ones and the node at the centre of the highlighting. */
function toggleExpand(node) {
  if (!cy || !node) return;
  const id = node.id();
  visibleNodes.add(id);              // the node stays on the graph even after collapsing
  if (expanded.has(id)) {
    expanded.delete(id);
    const keep = new Set([id]);
    expanded.forEach(eid => {
      const en = cy.getElementById(eid);
      if (en.length) nbhd(en, depthVal()).forEach(m => keep.add(m.id()));
    });
    nbhd(node, depthVal()).forEach(m => {
      const mid = m.id();
      if (keep.has(mid) || selected.has(mid) || mid === focusId) return;
      visibleNodes.delete(mid);
      placed.delete(mid);            // at the next expansion it is rearranged around the node
    });
  } else {
    expanded.add(id);
    // expanding means "I want to see its links", all of them
    unhide([id, ...nbhd(node, depthVal()).map(m => m.id())]);
  }
  refresh(true);
}

/* ================= LAYOUT ================= */
/* Positions ONLY the new nodes, in a ring around the node they come from.
   No global layout, no movement of existing nodes, camera still. */
function placeFresh(freshIds) {
  // footprints already taken by visible, positioned nodes
  const busy = [];
  cy.nodes().not('.hidden').forEach(n => {
    if (placed.has(n.id())) {
      const p = n.position();
      busy.push({ x: p.x, y: p.y, r: (n.data('size') || 24) / 2 + 26 });
    }
  });
  const free = (x, y, rad) =>
    busy.every(p => (p.x - x) ** 2 + (p.y - y) ** 2 > (p.r + rad) ** 2);
  const put = (id, x, y) => {
    const n = cy.getElementById(id);
    n.position({ x, y });
    busy.push({ x, y, r: (n.data('size') || 24) / 2 + 26 });
    placed.add(id);
  };

  // group the new nodes by origin node (the anchor already positioned)
  const groups = new Map();
  const orphans = [];
  freshIds.forEach(id => {
    const n = cy.getElementById(id);
    if (!n.length) return;
    const anch = n.neighborhood('node').filter(m => placed.has(m.id()) && !m.hasClass('hidden'));
    if (anch.length) {
      const a = anch[0].id();
      if (!groups.has(a)) groups.set(a, []);
      groups.get(a).push(id);
    } else orphans.push(id);
  });

  for (const [aid, ids] of groups) {
    const anchor = cy.getElementById(aid);
    const a = anchor.position();
    const base = 120 + (anchor.data('size') || 24);
    const slots = Math.max(ids.length, 6);
    const step = (2 * Math.PI) / slots;
    ids.forEach((id, i) => {
      let done = false;
      for (let ring = 0; ring < 8 && !done; ring++) {
        const rad = base + ring * 75;
        for (let k = 0; k < slots * 2 && !done; k++) {
          const ang = step * i + k * (step / 3) + ring * 0.35;
          const x = a.x + Math.cos(ang) * rad;
          const y = a.y + Math.sin(ang) * rad;
          if (free(x, y, 26)) { put(id, x, y); done = true; }
        }
      }
      if (!done) put(id, a.x + Math.cos(step * i) * (base + 650),
                        a.y + Math.sin(step * i) * (base + 650));
    });
  }

  // nodes without links already on the graph: at the centre of the current view
  if (orphans.length) {
    const ext = cy.extent();
    const cx = (ext.x1 + ext.x2) / 2, cy0 = (ext.y1 + ext.y2) / 2;
    orphans.forEach((id, i) => {
      const ang = 2.399 * i;                 // golden angle: uniform distribution
      let rad = i ? 100 + 26 * i : 0, t = 0;
      let x = cx + Math.cos(ang) * rad, y = cy0 + Math.sin(ang) * rad;
      while (!free(x, y, 26) && t < 60) {
        t++;
        x = cx + Math.cos(ang + t * 0.45) * (rad + t * 28);
        y = cy0 + Math.sin(ang + t * 0.45) * (rad + t * 28);
      }
      put(id, x, y);
    });
  }
}

function runLayout(extra = {}) {
  if (!cy) return;
  const eles = cy.elements().not('.hidden');
  if (!eles.length) return;
  if (eles.nodes().length === 1) { cy.center(eles); placed.add(eles.nodes()[0].id()); return; }

  const name = curLayout === 'untangle' ? 'fcose' : curLayout;
  const big = eles.nodes().length > 220;
  const opts = Object.assign({
    name,
    animate: !big,
    animationDuration: 380,
    fit: true,
    padding: 60,
    nodeDimensionsIncludeLabels: true,
    randomize: curLayout === 'untangle',
    idealEdgeLength: 110,
    nodeRepulsion: 9000,
    numIter: big ? 1200 : 2500,
    quality: big ? 'draft' : 'default'
  }, extra);
  if (name === 'breadthfirst') { opts.directed = false; opts.spacingFactor = 1.3; }
  if (opts.fit) opts.stop = () => capZoom();
  if (name !== 'fcose') delete opts.fixedNodeConstraint;

  try {
    cy.stop();
    eles.layout(opts).run();
  } catch (err) {
    console.warn('layout fallback', err);
    eles.layout({ name: 'cose', animate: false, fit: true, padding: 60 }).run();
  }
  eles.nodes().forEach(n => placed.add(n.id()));
}

/* ================= REDUCE CROSSINGS =================
   fcose (like "Organic") does not minimise crossings: repeating the layout
   with different seeds and keeping the one with fewest intersecting links gives
   a much more readable graph, and stably so. */
let untangling = false;

/* Segments of the visible links (in model coordinates). */
function edgeSegs() {
  const segs = [];
  cy.edges().not('.hidden').forEach(e => {
    const a = e.source(), b = e.target();
    if (a.empty() || b.empty()) return;
    const p = a.position(), q = b.position();
    segs.push({ x1: p.x, y1: p.y, x2: q.x, y2: q.y, s: e.data('source'), t: e.data('target') });
  });
  return segs;
}

/* Do two segments cross? Links that share a node do not count. */
function crosses(p, q) {
  if (p.s === q.s || p.s === q.t || p.t === q.s || p.t === q.t) return false;
  const sgn = (ax, ay, bx, by, cx, cy) => Math.sign((bx - ax) * (cy - ay) - (by - ay) * (cx - ax));
  const d1 = sgn(p.x1, p.y1, p.x2, p.y2, q.x1, q.y1);
  const d2 = sgn(p.x1, p.y1, p.x2, p.y2, q.x2, q.y2);
  const d3 = sgn(q.x1, q.y1, q.x2, q.y2, p.x1, p.y1);
  const d4 = sgn(q.x1, q.y1, q.x2, q.y2, p.x2, p.y2);
  return d1 !== d2 && d3 !== d4;
}

function countCrossings() {
  const s = edgeSegs();
  let c = 0;
  for (let i = 0; i < s.length; i++)
    for (let j = i + 1; j < s.length; j++)
      if (crosses(s[i], s[j])) c++;
  return c;
}

/* A single high-quality fcose pass, without animation: the Promise
   resolves when the layout is done, so several attempts can be compared. */
function fcoseOnce(extra = {}) {
  return new Promise(resolve => {
    let done = false;
    const finish = () => { if (!done) { done = true; resolve(); } };
    const eles = cy.elements().not('.hidden');
    // "Clean" parameters: fcose does not minimise crossings, so there is little
    // point in pushing it (packing/tiling make it worse); the real gain is keeping the
    // best of many randomised attempts.
    const lay = eles.layout(Object.assign({
      name: 'fcose',
      animate: false,
      fit: false,
      randomize: true,
      quality: 'default',
      nodeDimensionsIncludeLabels: true,
      idealEdgeLength: 110,
      nodeRepulsion: 9000,
      numIter: 2500
    }, extra));
    lay.one('layoutstop', finish);
    lay.run();
    setTimeout(finish, 6000);            // safety net: never get stuck
  });
}

function snapshotPos() {
  const m = new Map();
  cy.nodes().not('.hidden').forEach(n => { const p = n.position(); m.set(n.id(), { x: p.x, y: p.y }); });
  return m;
}
function restorePos(m) {
  cy.batch(() => m.forEach((p, id) => { const n = cy.getElementById(id); if (n.length) n.position(p); }));
}

async function untangle() {
  if (!cy || untangling) return;
  const eles = cy.elements().not('.hidden');
  const nN = eles.nodes().length, nE = eles.edges().length;
  if (nN < 3) { runLayout({ fit: true }); return; }

  untangling = true;
  const btn = $('#lyUntangle');
  const label = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = '✂ …'; }
  curLayout = 'fcose';
  await new Promise(r => setTimeout(r, 0));    // lets the "in progress" state paint before the computation

  try {
    cy.stop();
    // An fcose pass blocks the thread (it is synchronous): on hundreds of nodes
    // 'default' quality takes a few seconds, so above a threshold it
    // switches to 'draft' (fast) so as not to freeze the UI. Each pass is very
    // variable: it repeats while time remains and keeps the one with fewest crossings.
    const quality = nN > 1200 ? 'draft' : 'default';   // beyond ~1200 nodes 'default' risks long freezes
    const numIter = nN > 1200 ? 1000 : 2500;
    const measure = nE <= 5000;                  // the O(E²) count stays cheap
    // Each attempt blocks the thread: on large graphs it lasts ~3s, so the
    // low budget limits them to a few passes (there the variance is low and they are
    // not needed); on small ones (~250ms/attempt) plenty remain anyway.
    const budgetMs = 4000;
    const maxRuns = 16;
    let best = null, bestC = Infinity, k = 0;
    const start = performance.now();

    do {
      await fcoseOnce({ quality, numIter, idealEdgeLength: 100 + (k % 3) * 30 });
      k++;
      const c = measure ? countCrossings() : 0;
      if (c < bestC) { bestC = c; best = snapshotPos(); }
      if (!measure || bestC === 0) break;        // huge graph (no measurement) or already perfect
      await new Promise(r => setTimeout(r));      // yields the thread to the UI between one attempt and the next
    } while (k < maxRuns && performance.now() - start < budgetMs);

    if (best) restorePos(best);
    eles.nodes().forEach(n => placed.add(n.id()));

    cy.fit(eles, 60);
    capZoom();
    const s = $('#stat');
    if (s) s.textContent = measure
      ? t('stat.untangled', { n: bestC, k })
      : t('stat.untangledBig', { n: nN });
  } catch (err) {
    console.warn('untangle fallback', err);
    runLayout({ fit: true, randomize: true });
  } finally {
    untangling = false;
    if (btn) { btn.disabled = false; btn.textContent = label || t('ly.untangle'); }
  }
}

function setLayout(kind, btnId) {
  curLayout = kind;
  document.querySelectorAll('.ly').forEach(b => b.classList.remove('on'));
  const b = $(btnId);
  if (b) b.classList.add('on');
  runLayout({ fit: true });
}

/* ================= TOOLTIP ================= */
function showTip(n) {
  const box = $('#tip');
  if (!box || !n) return;
  const d = n.data();
  const openable = /^https?:\/\//i.test(d.url || '') ||
                   (SOCIAL_URL[d.platform] && socialHandle(d));
  const hint = openable ? `<u>${esc(t('tip.altclick'))}</u>` : '';
  // the node's note, if present, appears prominently in the tooltip
  const note = d.note
    ? `<div class="tip-note"><b>${esc(t('card.note'))}</b>${esc(d.note)}</div>` : '';
  box.innerHTML = `<small>${esc(d.ntype)} · ${esc(d.platform)}</small><b>${esc(d.label)}</b>` +
    `<i>${d.deg} ${esc(t('card.links'))}</i>${note}${hint}`;
  box.style.display = 'block';
}
const ARROW_SYM = { none: '—', target: '→', source: '←', both: '↔' };
function showEdgeTip(e) {
  const box = $('#tip');
  if (!box || !e) return;
  const d = e.data();
  const s = e.source().data('label'), tg = e.target().data('label');
  const fp = d.ftm && d.ftm_props ? Object.entries(d.ftm_props)
    .map(([k, v]) => `${esc(ftmEdgeFieldLabel(d.ftm, k))}: ${esc(v)}`).join(' · ') : '';
  box.innerHTML = `<small>${esc(t('edge.tipKind'))}${d.rel ? ' · ' + esc(d.rel) : ''}` +
    (d.ftm ? ` · FtM ${esc(ftmEdgeLabel(d.ftm))}` : '') + `</small>` +
    (d.label ? `<b>${esc(d.label)}</b>` : '') + (fp ? `<small>${fp}</small>` : '') +
    `<i>${esc(s)} ${ARROW_SYM[d.arrow || 'none']} ${esc(tg)}</i>` +
    `<u>${esc(t('edge.tipHint'))}</u>`;
  box.style.display = 'block';
}
function moveTip(e) {
  const box = $('#tip');
  if (!box || !e.originalEvent) return;
  box.style.left = (e.originalEvent.clientX + 15) + 'px';
  box.style.top = (e.originalEvent.clientY + 15) + 'px';
}
const hideTip = () => { const box = $('#tip'); if (box) box.style.display = 'none'; };

/* ================= SELECTION ================= */
function toggleSel(node) {
  const id = node.id();
  if (selected.has(id)) { selected.delete(id); node.removeClass('sel'); }
  else { selected.add(id); node.addClass('sel'); visibleNodes.add(id); }
  renderSel();
  refresh(false);
}

function renderSel() {
  const cnt = $('#selcount'), lst = $('#sellist'), fp = $('#findpath');
  if (cnt) cnt.textContent = selected.size;
  if (fp) fp.disabled = selected.size < 2;
  const lk = $('#linknodes');
  if (lk) lk.disabled = selected.size < 2;
  if (!lst) return;
  lst.innerHTML = [...selected].map(id => {
    const n = cy.getElementById(id);
    return `<li><img src="${n.data('icon')}" alt=""><span>${esc(n.data('label'))}</span><b data-id="${id}">✕</b></li>`;
  }).join('');
}
on('#sellist', 'click', e => {
  if (e.target.tagName === 'B') toggleSel(cy.getElementById(e.target.dataset.id));
});

function clearSel() {
  selected.forEach(id => cy.getElementById(id).removeClass('sel'));
  selected.clear();
  renderSel();
  refresh(false);
}

function clearHl() {
  if (!cy) return;
  cy.elements().removeClass('path').removeClass('path-hi');
  pinned.clear();
  const pi = $('#pathinfo');
  if (pi) pi.textContent = '';
  pathOnly = false;
  const po = $('#pathonly');
  if (po) { po.hidden = true; po.classList.remove('on'); po.textContent = t('btn.hideRest'); }
  refresh(false);
}

/* ================= PATHS (ALL) ================= */
const MAX_PATHS_PAIR = 400;   // limit of paths per pair
const MAX_STEPS = 400000;     // limit of DFS steps (anti-freeze)

// Precomputed adjacency: enumerating paths with the Cytoscape API is too slow
let ADJ = null;
function buildAdj() {
  ADJ = new Map();
  cy.nodes().forEach(n => ADJ.set(n.id(), []));
  cy.edges().forEach(e => {
    const s = e.data('source'), t = e.data('target');
    if (s === t || !ADJ.has(s) || !ADJ.has(t)) return;
    ADJ.get(s).push(t);
    ADJ.get(t).push(s);
  });
}

/* All simple paths src→dst within maxHops links.
   Bidirectional pruning: only what can still reach dst is explored. */
function allSimplePaths(srcId, dstId, maxHops) {
  if (!ADJ) buildAdj();
  if (srcId === dstId || !ADJ.has(srcId) || !ADJ.has(dstId)) return [];

  // BFS distance from dst (limited to maxHops)
  const dist = new Map([[dstId, 0]]);
  let frontier = [dstId];
  for (let d = 1; d <= maxHops && frontier.length; d++) {
    const next = [];
    for (const id of frontier) {
      for (const m of ADJ.get(id)) {
        if (!dist.has(m)) { dist.set(m, d); next.push(m); }
      }
    }
    frontier = next;
  }
  const d0 = dist.get(srcId);
  if (d0 === undefined || d0 > maxHops) return [];

  const paths = [];
  const stack = [srcId];
  const onPath = new Set([srcId]);
  let steps = 0;

  (function dfs(cur, hopsLeft) {
    if (paths.length >= MAX_PATHS_PAIR || steps > MAX_STEPS) return;
    if (cur === dstId) { paths.push(stack.slice()); return; }
    if (hopsLeft === 0) return;
    for (const nid of ADJ.get(cur)) {
      if (paths.length >= MAX_PATHS_PAIR || ++steps > MAX_STEPS) return;
      if (onPath.has(nid)) continue;
      const d = dist.get(nid);
      if (d === undefined || d > hopsLeft - 1) continue;   // would never reach dst
      onPath.add(nid); stack.push(nid);
      dfs(nid, hopsLeft - 1);
      stack.pop(); onPath.delete(nid);
    }
  })(srcId, maxHops);

  return paths;
}

function findPath() {
  if (!cy || selected.size < 2) return;
  clearHl();
  buildAdj();

  const maxHops = parseInt(($('#maxHops') && $('#maxHops').value) || '4', 10);
  const ids = [...selected];
  const all = [];
  let truncated = false;

  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const ps = allSimplePaths(ids[i], ids[j], maxHops);
      if (ps.length >= MAX_PATHS_PAIR) truncated = true;
      all.push(...ps);
    }
  }

  if (!all.length) {
    $('#pathinfo').innerHTML = t('path.none', { n: maxHops });
    return;
  }

  // Highlights ALL the paths found (union of nodes and links)
  const nodeIds = new Set();
  const edgeIds = new Set();
  all.forEach(p => {
    p.forEach(id => nodeIds.add(id));
    for (let k = 0; k < p.length - 1; k++) {
      cy.getElementById(p[k]).edgesWith(cy.getElementById(p[k + 1])).forEach(e => edgeIds.add(e.id()));
    }
  });

  cy.batch(() => {
    nodeIds.forEach(id => { pinned.add(id); cy.getElementById(id).addClass('path'); });
    edgeIds.forEach(id => cy.getElementById(id).addClass('path'));
  });
  selected.forEach(id => cy.getElementById(id).addClass('sel'));

  const po = $('#pathonly');
  if (po) { po.hidden = false; po.textContent = pathOnly ? t('btn.showRest') : t('btn.hideRest'); }

  refresh(true);
  cy.fit(cy.elements().not('.hidden'), 60);
  capZoom(1.6);

  all.sort((a, b) => a.length - b.length);
  const lbl = id => cy.getElementById(id).data('label') || id;
  const rows = all.slice(0, 25).map(p =>
    `<div class="p-row" data-path="${esc(p.join('|'))}">${p.map(lbl).map(esc).join(' → ')}</div>`).join('');

  $('#pathinfo').innerHTML =
    t('path.found', { n: all.length, tr: truncated ? t('path.truncated') : '',
                      nodes: nodeIds.size, edges: edgeIds.size }) +
    `<div class="p-list">${rows}${all.length > 25
      ? `<div class="p-more">${esc(t('path.more', { n: all.length - 25 }))}</div>` : ''}</div>`;
}

// Mouse hover on a path in the list: highlights it on the graph
on('#pathinfo', 'mouseover', e => {
  const row = e.target.closest('.p-row');
  if (!row || !cy) return;
  const ids = row.dataset.path.split('|');
  cy.elements().removeClass('path-hi');
  cy.batch(() => {
    ids.forEach((id, i) => {
      cy.getElementById(id).addClass('path-hi');
      if (i) cy.getElementById(ids[i - 1]).edgesWith(cy.getElementById(id)).addClass('path-hi');
    });
  });
});
on('#pathinfo', 'mouseout', e => {
  if (e.target.closest('.p-row') && cy) cy.elements().removeClass('path-hi');
});

/* ================= MODAL ================= */
let modalNode = null;

function openModal(node) {
  if (!node) return;
  modalNode = node;
  const d = node.data();
  const cards = (d.records || []).length;
  $('#modal-ic').src = d.icon;
  const ttl = $('#modal-title');
  ttl.textContent = d.label;
  ttl.className = 'cp';                       // the title can be copied too
  ttl.dataset.cp = d.label;
  ttl.title = t('cp.hint');
  $('#modal-sub').textContent =
    `${d.ntype} · ${d.platform} · ${d.deg} ${t('card.links')} · ` +
    (cards === 1 ? t('card.card', { n: cards }) : t('card.cards', { n: cards })) +
    ((d.merged || 1) > 1 ? ' · ' + t('card.merged', { n: d.merged }) : '') +
    (d.renamed ? ' · ' + t('card.renamed') : '');
  $('#modal-body').innerHTML = bodyFor(node);
  $('#modal-exp').textContent = expanded.has(d.id) ? t('modal.collapse') : t('modal.expand');
  if ($('#modal-src')) { $('#modal-src').hidden = true; $('#modal-src-res').innerHTML = ''; }
  if ($('#modal-src-btn')) $('#modal-src-btn').hidden = !srcState.indexed;
  if ($('#modal-osa')) $('#modal-osa').hidden = !(osaConf && osaConf.ready && OSA_SCHEMA_OF_TYPE[d.ntype]);
  if ($('#modal-ep')) {
    const can = epConf && epConf.ready && (d.ntype === 'email' || d.ntype === 'phone');
    $('#modal-ep').hidden = !can;
    if (can) $('#modal-ep').textContent = (epSearches[d.id] || []).length ? t('modal.epUpdate') : t('modal.ep');
  }
  $('#modal').hidden = false;
  $('#modal-body').scrollTop = 0;
}
function closeModal() { $('#modal').hidden = true; modalNode = null; }

/* ---- Linked nodes, for the card summary ----
   A target is explored to 2 hops (the phones hang not from it but
   from the account); any other node stops at the DIRECT links.
   In any case a target node met along the way is never
   expanded: it is a boundary, otherwise half the graph would be pulled in. */
function collectAround(node, hops = 1) {
  const seen = new Set([node.id()]);
  let frontier = [node];
  const found = [];
  for (let i = 0; i < hops; i++) {
    const next = [];
    frontier.forEach(n => {
      n.neighborhood('node').forEach(m => {
        if (seen.has(m.id())) return;
        seen.add(m.id());
        found.push(m);
        if (m.data('ntype') !== 'target') next.push(m);   // targets are not traversed
      });
    });
    frontier = next;
    if (!frontier.length) break;
  }
  return found;
}

/* Translated title of a group of identifiers (by ntype). */
const GROUP_KEYS = ['target', 'phone', 'email', 'username', 'vehicle',
                    'photo', 'latin', 'domain', 'breach', 'link', 'text',
                    'name', 'place', 'generic'];
const groupTitle = nt => nt === 'account' ? t('card.social')
                       : GROUP_KEYS.includes(nt) ? t('grp.' + nt) : nt;

/* Grouped summary: first the social accounts by platform, then the other types. */
function groupedSummary(node) {
  // target: 2 hops (phones/emails hang from the accounts). Other nodes: only
  // the direct links, otherwise the whole neighbourhood of the targets would appear.
  const around = collectAround(node, node.data('ntype') === 'target' ? 2 : 1);
  if (!around.length) return '';

  const isTarget = node.data('ntype') === 'target';
  const socials = {};      // platform -> account nodes
  const others = {};       // ntype -> nodes
  around.forEach(m => {
    const nt = m.data('ntype');
    if (nt === 'account') {
      const p = m.data('platform') || 'generic';
      (socials[p] = socials[p] || []).push(m);
    } else if (nt === 'target') {
      // for any node, the targets it belongs to are the most useful
      // information; in a target's card, instead, they are not needed
      if (!isTarget) (others[nt] = others[nt] || []).push(m);
    } else {
      (others[nt] = others[nt] || []).push(m);
    }
  });

  const row = m => {
    const dd = m.data();
    // the name is copied with a click; the arrow (visible on mouse
    // hover) leads to the node in the graph
    const name = `<span class="g-name cp" data-cp="${esc(dd.label)}" ` +
                 `title="${esc(t('cp.hint'))}">${esc(dd.label)}</span>` +
                 `<button class="g-go" data-goto="${esc(m.id())}" ` +
                 `title="${esc(t('cp.goto'))}">↗</button>`;

    // photo: visible thumbnail (click = enlargement)
    if (dd.ntype === 'photo' && dd.image) {
      return `<li class="g-photo"><img class="g-thumb" src="${esc(dd.image)}" ` +
             `loading="lazy" alt="" onerror="this.remove()">${name}</li>`;
    }

    // transliteration: original term -> Latin form
    if (dd.ntype === 'latin') {
      const orig = m.connectedEdges('[rel="translit"]').connectedNodes()
                    .filter(x => x.id() !== m.id());
      const origLab = orig.length
        ? [...new Set(orig.map(x => x.data('label')))].join(' · ')
        : '';
      const scr = dd.script || (orig.length ? orig[0].data('script') : '');
      return `<li class="g-tr"><span class="g-orig cp" dir="auto" ` +
             `data-cp="${esc(origLab)}" title="${esc(t('cp.hint'))}">${esc(origLab || '—')}</span>` +
             `<span class="g-arrow">→</span>${name}` +
             (scr ? `<em class="g-scr">${esc(scr)}</em>` : '') + '</li>';
    }

    // the node's own URL (generic link) or rebuilt from the platform
    const mk = SOCIAL_URL[dd.platform];
    const hnd = mk ? socialHandle(dd) : '';
    const url = /^https?:\/\//i.test(dd.url || '') ? dd.url : (mk && hnd ? mk(hnd) : '');
    const link = url
      ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(url)}</a>`
      : '';
    return `<li>${name} ${link}</li>`;
  };

  const blk = (title, color, list, cls) => {
    list = list.sort((a, b) => String(a.data('label')).localeCompare(String(b.data('label'))));
    return `<div class="g-blk${cls ? ' ' + cls : ''}"><h5><i style="background:${color}"></i>` +
           `${esc(title)} <b>${list.length}</b></h5><ul class="g-list">` +
           list.map(row).join('') + '</ul></div>';
  };
  const byCount = (a, b) => socials[b].length - socials[a].length || a.localeCompare(b);

  const plats = Object.keys(socials);
  const known = plats.filter(p => SOCIAL_URL[p]).sort(byCount);   // social accounts that can be opened
  const rest = plats.filter(p => !SOCIAL_URL[p]).sort(byCount);   // other services

  let h = `<div class="d-sec g-sum"><h4>${esc(t('card.summary'))}</h4>`;

  if (known.length) {
    h += `<div class="g-cat">${esc(t('card.social'))}</div>`;
    known.forEach(p => { h += blk(p, TYPE_COLOR.account, socials[p], 'g-social'); });
  }

  // non-account types (phones, emails, usernames, vehicles, photos...)
  const otherTypes = Object.keys(others)
    .sort((a, b) => others[b].length - others[a].length || a.localeCompare(b));
  if (otherTypes.length) {
    h += `<div class="g-cat">${esc(t('card.identifiers'))}</div>`;
    otherTypes.forEach(nt => {
      h += blk(groupTitle(nt), TYPE_COLOR[nt] || TYPE_COLOR.generic, others[nt]);
    });
  }

  if (rest.length) {
    const tot = rest.reduce((s, p) => s + socials[p].length, 0);
    h += `<details class="g-more"><summary>` +
         esc(t('card.otherServices', { p: rest.length, n: tot })) + '</summary>';
    rest.forEach(p => { h += blk(p, TYPE_COLOR.generic, socials[p]); });
    h += '</details>';
  }

  return h + '</div>';
}

/* opts.print = version for the PDF: no cloud of chips with the node
   icons, the references remain as a list/table. */
function bodyFor(node, opts = {}) {
  const d = node.data();
  let h = '';

  // User's note, clearly visible at the top
  if (d.note) {
    h += `<div class="d-note"><b>${esc(t('card.note'))}</b><div>${esc(d.note).replace(/\n/g, '<br>')}</div></div>`;
  }

  // Latin form of the label (transliteration as a node attribute)
  if (d.roman && d.roman.toLowerCase() !== String(d.label || '').toLowerCase()) {
    h += `<div class="d-ren"><b>${esc(t('card.roman'))}</b>` +
         `<span class="cp" data-cp="${esc(d.roman)}" title="${esc(t('cp.hint'))}">${esc(d.roman)}</span>` +
         (d.roman_manual ? ` <span class="dict-src dict-src-manual">${esc(t('dict.srcManual'))}</span>` : '') +
         `</div>`;
  }

  // Label changed by hand: the one from the source data is always shown
  if (d.renamed && d.label_orig) {
    h += `<div class="d-ren"><b>${esc(t('card.renamedFrom'))}</b>` +
         `<span class="cp" data-cp="${esc(d.label_orig)}" title="${esc(t('cp.hint'))}">` +
         `${esc(d.label_orig)}</span></div>`;
  }

  // Grouped summary: for targets (and for every highly linked node)
  if (d.ntype === 'target' || (d.deg || 0) >= 4) {
    h += groupedSummary(node);
  }

  // Alternative labels of the merged nodes
  if (d.aliases && d.aliases.length) {
    h += `<div class="d-sec"><h4>${esc(t('card.aliases', { n: d.aliases.length }))}</h4><div class="d-imgs-list">` +
      d.aliases.map(a => `<span class="chip static cp" data-cp="${esc(a)}" ` +
        `title="${esc(t('cp.hint'))}">${esc(a)}</span>`).join('') + '</div></div>';
  }

  // Cloud of linked nodes (with icons): only on screen, not in the PDF
  const nbr = node.neighborhood('node');
  if (nbr.length && !opts.print) {
    h += `<div class="d-sec"><h4>${esc(t('card.connectedTo', { n: nbr.length }))}</h4><div class="d-imgs-list">` +
      nbr.map(m => `<span class="chip" data-goto="${esc(m.id())}"><img src="${m.data('icon')}" alt="">${esc(m.data('label'))}</span>`).join('') +
      '</div></div>';
  }

  // ALL the node's cards (including those coming from the merged nodes)
  const recs = d.records || [];
  if (recs.length) h += `<h4 class="d-count">${esc(recs.length === 1
      ? t('card.card', { n: recs.length }) : t('card.cards', { n: recs.length }))}</h4>`;
  recs.forEach((r, i) => {
    h += '<div class="d-card">';
    h += `<div class="d-badge">${esc(t('card.recordBadge', { i: i + 1, n: recs.length,
      coll: r.collection || t('card.sheet') }))}</div>`;
    if (r.images && r.images.length) {
      h += '<div class="d-imgs">' +
        r.images.slice(0, 12).map(u => `<img src="${esc(u)}" loading="lazy" alt="" onerror="this.remove()">`).join('') +
        '</div>';
    }
    // the value is copied with a click (handy for searching on other portals)
    h += '<div class="d-grid">' + flatten(r.raw).map(([k, v]) =>
      `<div>${esc(k)}</div><div class="cp" data-cp="${esc(v)}" ` +
      `title="${esc(t('cp.hint'))}">${renderVal(v)}</div>`).join('') + '</div>';
    h += '</div>';
  });

  return h || `<div class="empty">${esc(t('card.empty'))}</div>`;
}

/* ================= MANUAL LINKS ================= */
/* Inserts links into the live graph, without reloading. */
function injectEdges(edges) {
  let n = 0;
  cy.batch(() => {
    edges.forEach(e => {
      if (cy.getElementById(e.id).length) return;              // already present
      const s = cy.getElementById(e.source), t = cy.getElementById(e.target);
      if (!s.length || !t.length) return;
      cy.add({ group: 'edges', data: Object.assign({}, e) });
      s.data('deg', (s.data('deg') || 0) + 1);
      t.data('deg', (t.data('deg') || 0) + 1);
      n++;
    });
  });
  if (n) { ADJ = null; buildDegFilter(); }
  return n;
}

/* Links the chosen nodes. With two nodes the direction is chosen (From → To); with more
   nodes every pair is linked (a,b,c -> ab, ac, bc). In both cases the
   name, arrows, shape, colour and line type of the link are set.
   Between two nodes there can be several links, each with its own name. */
let linkIds = [];

function openLinkModal(ids, preset) {
  if (!cy || !ids || ids.length < 2 || !requireCase()) return;
  linkIds = [...ids];
  const two = linkIds.length === 2;
  $('#link-endpoints').hidden = !two;
  const hint = $('#link-multi-hint');
  hint.hidden = two;
  if (!two) {
    const c = linkIds.length * (linkIds.length - 1) / 2;
    hint.textContent = t('link.multiHint', { n: linkIds.length, c });
  }
  syncLinkEndpoints();
  writeEdgeProps('link', preset || {});
  $('#linkmodal').hidden = false;
  setTimeout(() => $('#link-edge-label').focus(), 50);
}

function syncLinkEndpoints() {
  setPreviewNodes('link', nodeView(cy.getElementById(linkIds[0])),
                  nodeView(cy.getElementById(linkIds[1])));
  if (linkIds.length !== 2) return;
  $('#link-from-label').textContent = nodeLabel(linkIds[0]);
  $('#link-to-label').textContent = nodeLabel(linkIds[1]);
}

async function saveLink() {
  if (linkIds.length < 2) return;
  const btn = $('#linkmodal-save');
  btn.disabled = true;
  try {
    const payload = Object.assign({ ids: linkIds }, readEdgeProps('link'));
    if (linkIds.length === 2) { payload.source = linkIds[0]; payload.target = linkIds[1]; }
    const j = await apiPost('/api/link/add', payload);
    const n = injectEdges(j.edges || []);
    $('#linkmodal').hidden = true;
    refresh(false);
    $('#stat').textContent = j.created
      ? t('stat.linksCreated', { n: j.created, c: j.coppie, v: n })
      : t('stat.noNewLinks');
  } catch (err) {
    alert(t('err.linkFailed', { e: err.message }));
  } finally {
    btn.disabled = false;
  }
}

on('#linknodes', 'click', () => openLinkModal([...selected]));
on('#link-swap-btn', 'click', () => {
  if (linkIds.length !== 2) return;
  linkIds.reverse();
  syncLinkEndpoints();
});
on('#linkmodal-save', 'click', saveLink);
on('#linkmodal-close', 'click', () => { $('#linkmodal').hidden = true; });
on('#linkmodal', 'click', e => { if (e.target.id === 'linkmodal' && !dragEnd('linkmodal')) $('#linkmodal').hidden = true; });
on('#link-edge-label', 'keydown', e => { if (e.key === 'Enter') saveLink(); });

/* ================= EDITING A LINK (right-click) ================= */
let edgeEditId = null;

/* Where the link comes from: decides what can be done (delete it, restore it). */
const edgeKind = e => e.data('rel') === 'collegamento' ? 'link'
                    : e.data('manual') ? 'added' : 'data';

function openEdgeModal(edge) {
  if (!edge || !edge.length) return;
  if (edgeEditId) cy.getElementById(edgeEditId).removeClass('edg-hi');
  edgeEditId = edge.id();
  edge.addClass('edg-hi');
  const kind = edgeKind(edge);
  $('#edg-from-label').textContent = edge.source().data('label');
  $('#edg-to-label').textContent = edge.target().data('label');
  previewNodes.edg = [nodeView(edge.source()), nodeView(edge.target())];
  $('#edgemodal-sub').textContent = edge.data('rel') ? `${t('edge.relation')}: ${edge.data('rel')}` : '';
  $('#edg-kind').textContent = t('edge.kind.' + kind);
  $('#edgemodal-del').hidden = kind !== 'link';
  $('#edgemodal-reset').hidden = kind !== 'data';
  writeEdgeProps('edg', edgePropsOf(edge));

  // other links between the same two nodes: switch from one to the other
  const par = edge.parallelEdges();
  const others = $('#edg-others');
  if (par.length > 1) {
    others.innerHTML = `<div class="eo-t">${esc(t('edge.parallel', { n: par.length }))}</div>` +
      par.map(p => `<button type="button" data-eid="${esc(p.id())}" class="${p.id() === edgeEditId ? 'cur' : ''}">` +
        `${ARROW_SYM[p.data('arrow') || 'none']} ${esc(p.data('label') || t('edge.unnamed'))}` +
        `</button>`).join('');
  } else {
    others.innerHTML = '';
  }
  $('#edgemodal').hidden = false;
}

function closeEdgeModal() {
  if (edgeEditId && cy) cy.getElementById(edgeEditId).removeClass('edg-hi');
  edgeEditId = null;
  $('#edgemodal').hidden = true;
}

async function saveEdge(reset) {
  const e = edgeEditId && cy.getElementById(edgeEditId);
  if (!e || !e.length) return;
  const props = readEdgeProps('edg');
  try {
    const j = await apiPost('/api/link/update',
      reset ? { id: e.id(), reset: true } : Object.assign({ id: e.id() }, props));
    setEdgeProps(e, reset ? EDGE_DEFAULTS : j.props || props);
    closeEdgeModal();
    $('#stat').textContent = reset ? t('edge.resetDone') : t('edge.saved');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
}

on('#edgemodal-save', 'click', () => saveEdge(false));
on('#edgemodal-reset', 'click', () => saveEdge(true));
on('#edgemodal-close', 'click', closeEdgeModal);
on('#edgemodal', 'click', e => { if (e.target.id === 'edgemodal' && !dragEnd('edgemodal')) closeEdgeModal(); });
on('#edg-edge-label', 'keydown', e => { if (e.key === 'Enter') saveEdge(false); });
/* reverses the direction: the arrows are swapped (the link stays the same) */
on('#edg-swap-btn', 'click', () => {
  const { fwd, bwd } = arrowHeads('edg');
  setArrowHeads('edg', bwd, fwd);
  updateEdgePreview('edg');
});
on('#edg-others', 'click', e => {
  const b = e.target.closest('[data-eid]');
  if (b) openEdgeModal(cy.getElementById(b.dataset.eid));
});
on('#edgemodal-new', 'click', () => {
  const e = edgeEditId && cy.getElementById(edgeEditId);
  if (!e || !e.length) return;
  const ids = [e.source().id(), e.target().id()];
  closeEdgeModal();
  openLinkModal(ids);
});
on('#edgemodal-del', 'click', async () => {
  const e = edgeEditId && cy.getElementById(edgeEditId);
  if (!e || !e.length) return;
  const a = e.source(), b = e.target();
  if (!confirm(t('man.confirmLink', { a: a.data('label'), b: b.data('label') }))) return;
  try {
    await apiPost('/api/link/delete', { id: e.id() });
    [a, b].forEach(m => m.data('deg', Math.max(0, (m.data('deg') || 0) - 1)));
    closeEdgeModal();
    e.remove();
    ADJ = null;
    refresh(false); buildDegFilter();
    $('#stat').textContent = t('stat.linkDeleted');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
});

/* ================= MANUAL ADDITION OF A NODE ================= */
let addParent = null;

/* Label and placeholder of the value field, by node type (i18n keys). */
const ADD_FIELDS = {
  social:   { label: 'add.urlLabel',   ph: 'add.urlPh' },
  link:     { label: 'add.linkLabel',  ph: 'add.linkPh' },
  phone:    { label: 'add.phoneLabel', ph: 'add.phonePh' },
  email:    { label: 'add.emailLabel', ph: 'add.emailPh' },
  username: { label: 'add.userLabel',  ph: 'add.userPh' },
  vehicle:  { label: 'add.plateLabel', ph: 'add.platePh' },
  name:     { label: 'add.nameOnly',   ph: 'add.nameOnlyPh' },
  place:    { label: 'add.cityLabel',  ph: 'add.cityPh' },
  text:     { label: '',               ph: '' },   // uses only title + text
  photo:    { label: '',               ph: '' }    // uses the image area
};

/* Which fields to show for each type. */
const ADD_LAYOUT = {
  social:   { value: true,  name: true,  text: false, photo: false, nameKey: 'add.nameLabel',  namePh: 'add.namePh' },
  link:     { value: true,  name: true,  text: false, photo: false, nameKey: 'add.nameLabel',  namePh: 'add.linkNamePh' },
  phone:    { value: true,  name: false, text: false, photo: false },
  email:    { value: true,  name: false, text: false, photo: false },
  username: { value: true,  name: false, text: false, photo: false },
  vehicle:  { value: true,  name: true,  text: false, photo: false, vehicle: true, nameKey: 'add.vehNameLabel', namePh: 'add.vehNamePh' },
  name:     { value: false, name: false, text: false, photo: false, person: true },
  place:    { value: true,  name: false, text: false, photo: false, place: true },
  text:     { value: false, name: true,  text: true,  photo: false, nameKey: 'add.titleLabel',   namePh: 'add.titlePh' },
  photo:    { value: false, name: true,  text: false, photo: true,  nameKey: 'add.photoNameLabel', namePh: 'add.photoNamePh' }
};

let addPhoto = null;   // { dataUrl, filename, path } of the chosen image

/* node = starting node (the new node is linked to it); null = standalone "New
   node": the link section is not needed and is hidden. */
function openAdd(node, opts = {}) {
  if (!requireCase()) return;
  addParent = node || null;
  $('#addmodal-title').textContent = node ? t('add.title') : t('add.titleNew');
  $('#addmodal-sub').textContent = node ? t('add.toNode', { name: node.data('label') })
                                        : t('add.standalone');
  $('#add-edge-sec').hidden = !node;
  resetAi();
  setAiMode(false);
  syncAiSide();
  $('#add-value').value = '';
  $('#add-name').value = '';
  $('#add-text').value = '';
  ['#add-address', '#add-civico', '#add-lat', '#add-lon'].forEach(s => { if ($(s)) $(s).value = ''; });
  fillToponimi();
  ['#add-cognome', '#add-nome', '#add-nascita', '#add-colore'].forEach(s => { if ($(s)) $(s).value = ''; });
  if ($('#add-target')) $('#add-target').checked = !!opts.target;
  if (opts.kind) $('#add-type').value = opts.kind;
  $('#add-onto-row').dataset.kind = '';          // empty ontology fields
  setAddPhoto(null);
  previewNodes.add = [node ? nodeView(node) : null, null];
  writeEdgeProps('add', EDGE_DEFAULTS);
  syncAddType();
  $('#addmodal').hidden = false;
  const first = $('#add-type').value === 'name' ? '#add-cognome' : '#add-value';
  setTimeout(() => $(first).focus(), 50);
}

/* Person: same identity as on the server (name regardless of order + date of birth). */
function foldName(s) {
  return String(s || '').normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
}
function personKey(full) { return foldName(full).split(/\s+/).filter(Boolean).sort().join(' '); }
function birthIt(iso) { return iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : ''; }

/* ---- investigative items (weapons, drugs, valuables...): the form
   fields come from ontology.py ---- */
const ontoLabel = o => ot(o.label);

/* One drop-down section per group (Weapons, Drugs, Valuables...), in the order
   of ontology.py (the page JSON has its keys in alphabetical order). */
function fillOntoOptions() {
  const sel = $('#add-type');
  if (!sel) return;
  const cur = sel.value;
  sel.querySelectorAll('optgroup').forEach(g => g.remove());
  const items = Object.entries(ONTO).sort((a, b) => a[1].order - b[1].order);
  const groups = [...new Set(items.map(([, o]) => o.group))];
  groups.forEach(gr => {
    const og = document.createElement('optgroup');
    og.label = catLabel('onto_' + gr);
    og.innerHTML = items.filter(([, o]) => o.group === gr)
      .map(([k, o]) => `<option value="${esc(k)}">${esc(ontoLabel(o))}</option>`).join('');
    sel.appendChild(og);
  });
  if (cur) sel.value = cur;
}

function renderOntoFields(kind) {
  const box = $('#add-onto-row');
  const o = ONTO[kind];
  box.dataset.kind = kind;
  box.innerHTML = o.fields.filter(f => !f.hidden).map(f => {
    const id = `onto-f-${f.key}`;
    const lab = ot(f.label);
    if (f.type === 'check') {
      return `<label class="af-check af-wide"><input type="checkbox" id="${id}" data-k="${f.key}">` +
             `<span>${esc(lab)}</span></label>`;
    }
    let input;
    if (f.type === 'select') {
      input = `<select id="${id}" data-k="${f.key}"><option value="">—</option>` +
        f.options.map(x => `<option value="${esc(x)}">${esc(ot(x))}</option>`).join('') + `</select>`;
    } else {
      const typ = f.type === 'number' ? 'text" inputmode="decimal' : f.type === 'date' ? 'date' : 'text';
      input = `<input id="${id}" data-k="${f.key}" type="${typ}" autocomplete="off" placeholder="${esc(ot(f.ph || ''))}">`;
    }
    const wide = /descrizione|confezionamento|seriali|tagli/.test(f.key) ? ' af-wide' : '';
    return `<div class="af-of${wide}"><label class="af-lb" for="${id}">${esc(lab)}</label>${input}</div>`;
  }).join('');
}

function readOntoFields() {
  const out = {};
  $('#add-onto-row').querySelectorAll('[data-k]').forEach(el => {
    if (el.type === 'checkbox') { if (el.checked) out[el.dataset.k] = true; }
    else if (el.value.trim()) out[el.dataset.k] = el.value.trim();
  });
  return out;
}

/* Preview of the label (the real one is built by the server). */
function ontoPreviewLabel(kind, f) {
  const o = ONTO[kind];
  const skip = /descrizione|confezionamento|seriali|tagli|intestatario|traente|beneficiario|sede|stato/;
  return o.fields.filter(x => f[x.key] && f[x.key] !== true && !skip.test(x.key) && x.type !== 'date')
    .map(x => ot(f[x.key])).join(' ') || ontoLabel(o);
}

function syncAddType() {
  const kind = $('#add-type').value;
  const f = ADD_FIELDS[kind] || ADD_FIELDS.username;
  const L = ONTO[kind] ? { onto: true } : (ADD_LAYOUT[kind] || ADD_LAYOUT.username);
  $('#add-onto-row').hidden = !L.onto;
  if (L.onto && $('#add-onto-row').dataset.kind !== kind) renderOntoFields(kind);

  $('#add-value-row').hidden = !L.value;
  if (L.value) {
    $('#add-vlabel').textContent = t(f.label);
    $('#add-value').placeholder = t(f.ph);
  }
  $('#add-name-row').hidden = !L.name;
  if (L.name) {
    $('#add-nlabel').textContent = t(L.nameKey || 'add.nameLabel');
    $('#add-name').placeholder = t(L.namePh || 'add.namePh');
  }
  $('#add-text-row').hidden = !L.text;
  $('#add-photo-row').hidden = !L.photo;
  $('#add-place-row').hidden = !L.place;
  $('#add-person-row').hidden = !L.person;
  $('#add-vehicle-row').hidden = !L.vehicle;
  updateAddPreview();
}

/* ---- image: chosen from file, drag and drop or paste ---- */
function setAddPhoto(dataUrl, filename) {
  addPhoto = dataUrl ? { dataUrl, filename: filename || 'immagine' } : null;
  const img = $('#add-thumb'), txt = $('#add-drop-txt');
  if (addPhoto) {
    img.src = dataUrl; img.hidden = false;
    txt.textContent = addPhoto.filename;
  } else {
    img.hidden = true; img.removeAttribute('src');
    txt.textContent = t('add.photoDrop');
  }
  updateAddPreview();
}

function readImageFile(file) {
  if (!file || !/^image\//i.test(file.type)) return;
  const r = new FileReader();
  r.onload = () => setAddPhoto(r.result, file.name);
  r.readAsDataURL(file);
}

/* What will be created: platform and identifier extracted from the URL.
   Any type can be marked as a target (tick box in the form). */
function addPayload() {
  const p = addPayloadOf($('#add-type').value);
  if (!p.err) p.target = !!($('#add-target') && $('#add-target').checked);
  return p;
}
function addPayloadOf(kind) {
  const v = $('#add-value').value.trim();
  const nome = ($('#add-name') && $('#add-name').value.trim()) || '';

  // types that do not use the "value" field
  if (kind === 'text') {
    if (!nome) return { err: '' };
    const corpo = ($('#add-text') && $('#add-text').value.trim()) || '';
    if (!corpo) return { err: t('add.errText') };
    return { ntype: 'text', platform: 'text', value: nome, label: nome, text: corpo };
  }
  if (ONTO[kind]) {
    const fields = readOntoFields();
    if (!Object.keys(fields).length) return { err: '' };
    const label = ontoPreviewLabel(kind, fields);
    return { ntype: kind, platform: kind, onto: true, fields, label, value: '' };
  }
  if (kind === 'photo') {
    if (!addPhoto) return { err: '' };
    return { ntype: 'photo', platform: 'photo', value: '', label: nome, photo: true };
  }

  if (kind === 'name') {
    const cognome = ($('#add-cognome').value || '').trim().replace(/\s+/g, ' ');
    const nomeP = ($('#add-nome').value || '').trim().replace(/\s+/g, ' ');
    const nascita = ($('#add-nascita').value || '').trim();      // YYYY-MM-DD
    const full = `${cognome} ${nomeP}`.trim();
    if (!full) return { err: '' };
    if (full.length < 2) return { err: t('add.errName') };
    return { ntype: 'name', platform: 'name', value: full, cognome, nome: nomeP, nascita,
             label: nascita ? `${full} (${birthIt(nascita)})` : full };
  }
  if (!v) return { err: '' };
  if (kind === 'place') {
    const nomeVia = ($('#add-address') && $('#add-address').value.trim()) || '';
    const topo = ($('#add-toponimo') && $('#add-toponimo').value) || '';
    // type from the drop-down, if the name does not already contain one ("Piazza Duomo")
    const strada = nomeVia && topo && !STREET_TYPE_RE.test(nomeVia) ? `${topo} ${nomeVia}` : nomeVia;
    const civico = ($('#add-civico') && $('#add-civico').value.trim()) || '';
    const via = `${strada} ${civico}`.trim();
    const lat = ($('#add-lat') && $('#add-lat').value.trim().replace(',', '.')) || '';
    const lon = ($('#add-lon') && $('#add-lon').value.trim().replace(',', '.')) || '';
    const num = /^-?\d{1,3}(\.\d+)?$/;
    if ((lat && !lon) || (lon && !lat)) return { err: t('add.errCoordPair') };
    if (lat && (!num.test(lat) || Math.abs(+lat) > 90)) return { err: t('add.errLat') };
    if (lon && (!num.test(lon) || Math.abs(+lon) > 180)) return { err: t('add.errLon') };
    return { ntype: 'place', platform: 'place', value: v,
             label: via ? `${v} — ${via}` : v, address: strada, civico, lat, lon };
  }
  if (kind === 'vehicle') {
    const targa = v.replace(/\s+/g, '').toUpperCase();
    if (targa.length < 3) return { err: t('add.errPlate') };
    const colore = ($('#add-colore') && $('#add-colore').value.trim()) || '';
    return { ntype: 'vehicle', platform: 'vehicle', value: v, colore,
             label: nome ? `${targa} ${nome}` : targa };
  }
  if (kind === 'link') {
    if (!/^https?:\/\/\S+$/i.test(v)) return { err: t('add.errLink') };
    const nome = ($('#add-name') && $('#add-name').value.trim()) || '';
    return { ntype: 'link', platform: 'link', value: v, label: nome || v, url: v };
  }
  if (kind === 'social') {
    const p = parseSocialUrl(v);
    if (!p) return { err: t('add.errUrl') };
    const nome = ($('#add-name') && $('#add-name').value.trim()) || '';
    return { ntype: 'account', platform: p.platform, value: p.handle,
             label: nome || p.handle, url: v };
  }
  if (kind === 'phone') {
    const d = v.replace(/\D/g, '');
    if (d.length < 6) return { err: t('add.errPhone') };
    return { ntype: 'phone', value: v, label: v };
  }
  if (kind === 'email') {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return { err: t('add.errEmail') };
    return { ntype: 'email', value: v, label: v };
  }
  if (!/^[A-Za-z0-9._@-]{2,}$/.test(v)) return { err: t('add.errUser') };
  return { ntype: 'username', value: v.replace(/^@+/, ''), label: v.replace(/^@+/, '') };
}

/* Preview of the link in the add window: the starting node and
   the node being created, with the icon and colour of the chosen type. */
const ADD_KIND_NTYPE = { social: 'account' };
function addPreviewNode(p) {
  if (!previewNodes.add) return;
  const kind = $('#add-type').value;
  const d = (p && !p.err && p.ntype) ? Object.assign({}, p)
          : { ntype: ADD_KIND_NTYPE[kind] || kind, platform: kind === 'social' ? '' : kind,
              label: $('#add-value').value.trim() || $('#add-name').value.trim() || t('add.newNode') };
  if (d.ntype === 'photo' && addPhoto) d.image = addPhoto.dataUrl;
  if ($('#add-target') && $('#add-target').checked) d.ntype = 'target';   // as the server will do
  previewNodes.add[1] = { icon: iconFor(d), label: d.label || d.value || t('add.newNode'),
                          color: TYPE_COLOR[d.ntype] || TYPE_COLOR.generic, ntype: d.ntype };
  updateEdgePreview('add');
}

/* Street types of the drop-down (toponyms). They do not count when comparing
   addresses: "Via Giacomo Leopardi" and "Giacomo Leopardi" are the same street. */
const TOPONIMI = ['Via', 'Viale', 'Piazza', 'Piazzale', 'Piazzetta', 'Corso', 'Largo',
  'Vicolo', 'Vico', 'Strada', 'Contrada', 'Località', 'Frazione', 'Borgo', 'Lungomare',
  'Lungolago', 'Salita', 'Traversa', 'Galleria', 'Circonvallazione', 'Calle', 'Rue',
  'Avenue', 'Boulevard', 'Avenida', 'Plaza'];
const STREET_TYPE_RE = new RegExp('^(' + TOPONIMI.join('|') +
  '|v\\.le|p\\.?za|p\\.le|c\\.so|l\\.go|loc\\.)(\\s|\\.|$)', 'i');

function fillToponimi() {
  const s = $('#add-toponimo');
  if (!s) return;
  if (!s.options.length) {
    s.innerHTML = `<option value="">—</option>` +
      TOPONIMI.map(x => `<option value="${esc(x)}">${esc(x)}</option>`).join('');
  }
  s.value = 'Via';
}
fillToponimi();

function updateAddPreview() {
  const box = $('#add-preview');
  const p = addPayload();
  addPreviewNode(p);
  if (p.err === '') { box.className = 'af-prev'; box.textContent = ''; return; }
  if (p.err) { box.className = 'af-prev af-err'; box.textContent = '⚠ ' + p.err; return; }
  // the photo gets its id only after the upload to the server
  if (p.ntype === 'photo') {
    box.className = 'af-prev af-ok';
    box.innerHTML = `<b>${esc(t('cat.foto'))}</b> · ${esc(addPhoto.filename)}` +
                    `<br><i>${esc(t('add.photoWillSave'))}</i>`;
    return;
  }
  if (p.onto) {
    box.className = 'af-prev af-ok';
    box.innerHTML = `<b>${esc(ontoLabel(ONTO[p.ntype]))}</b> · ${esc(p.label)}`;
    return;
  }
  const id = p.ntype === 'account' ? `acct:${p.platform}:${p.value.toLowerCase()}`
           : p.ntype === 'name' ? (p.nascita ? `person:${personKey(p.value)}|${p.nascita}` : 'name:' + personKey(p.value))
           : p.ntype === 'place' ? 'place:' + `${p.value} ${p.address || ''} ${p.civico || ''}`.replace(/\s+/g, ' ').trim().toLowerCase()
           : p.ntype === 'link' ? 'link:' + p.value.replace(/\/+$/, '').toLowerCase()
           : p.ntype === 'vehicle' ? 'vehicle:' + p.value.replace(/\s+/g, '').toUpperCase()
           : p.ntype === 'text' ? 'text:' + p.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60)
           : p.ntype === 'phone' ? 'phone:' + p.value.replace(/\D/g, '')
           : p.ntype === 'email' ? 'email:' + p.value.toLowerCase()
           : 'user:' + p.value.toLowerCase();
  const exists = cy && cy.getElementById(id).length > 0;
  box.className = 'af-prev af-ok';
  box.innerHTML =
    (p.platform ? `<b>${esc(p.platform)}</b> · ` : '') +
    `${esc(t('add.identifier'))}: <b>${esc(p.value)}</b><br><code>${esc(id)}</code>` +
    (exists ? `<br><i>${esc(t('add.exists'))}</i>` : '');
}

/* Adds a node to cytoscape with the same fields computed at load time
   (icon, colour, category, size) and indexes it for the search.
   If it already exists, it simply returns it. */
function addNodeToCy(nodeData) {
  const existing = cy.getElementById(nodeData.id);
  if (existing.length) return existing;

  const n = Object.assign({}, nodeData);
  n.ident = IDENT_TYPES.includes(n.ntype);
  n.cat = categoryOf(n);
  n.deg = n.deg || 0;
  n.bridge = n.ident && n.deg > 1;
  n.size = n.ntype === 'target' ? 50 : n.ntype === 'photo' ? 46
         : n.ntype === 'account' ? 32 : (n.bridge ? 26 : 22);
  cy.add({ group: 'nodes', data: Object.assign({}, n, {
    icon: iconFor(n), color: TYPE_COLOR[n.ntype] || TYPE_COLOR.generic, disp: dispOf(n)
  }) });

  // search index (label, id, platform, aliases, note)
  const hay = `${n.label} ${n.id} ${n.platform} ${n.ntype} ` +
              `${(n.aliases || []).join(' ')} ${n.note || ''}`.toLowerCase();
  if (!INDEX.some(it => it.id === n.id)) {
    INDEX.push({ id: n.id, hay, headLen: hay.length });
    const toks = hay.match(TOKEN_RE);
    if (toks) for (const w of new Set(toks)) {
      if (w.length < 2 || w.length > 40) continue;
      let post = VOCAB.get(w);
      if (!post) { post = []; VOCAB.set(w, post); }
      if (!post.includes(n.id)) post.push(n.id);
    }
  }
  return cy.getElementById(n.id);
}

/* Inserts the node just created into the LIVE graph, without reloading the page:
   the current view (open nodes, positions, zoom) stays intact. */
function injectNode(nodeData, edgeData, parentId) {
  const node = addNodeToCy(nodeData);

  if (edgeData && !cy.getElementById(edgeData.id).length) {
    cy.add({ group: 'edges', data: Object.assign({}, edgeData) });
    [edgeData.source, edgeData.target].forEach(id => {
      const m = cy.getElementById(id);
      if (m.length) m.data('deg', (m.data('deg') || 0) + 1);
    });
  }

  // makes the new node visible next to its parent
  visibleNodes.add(node.id());
  if (parentId) visibleNodes.add(parentId);
  const parent = parentId ? cy.getElementById(parentId) : null;
  if (parent && parent.length && placed.has(parentId) && !placed.has(node.id())) {
    const p = parent.position();
    node.position({ x: p.x + 140, y: p.y + 90 });
    placed.add(node.id());
  }
  refresh(true);
  ADJ = null;                                  // adjacency to be recomputed
  buildLegend();
  buildCatFilters();
  buildDegFilter();

  node.addClass('fresh');
  setTimeout(() => node.removeClass('fresh'), 2000);
  bringIntoView(node);
  // if the platform is new, download its icon (the others are already cached)
  upgradeBrandIcons();
  return node;
}

on('#modal-add', 'click', () => { if (modalNode) openAdd(modalNode); });
on('#newNode', 'click', () => { if (cy) openAdd(null); });
on('#addmodal-close', 'click', () => { $('#addmodal').hidden = true; });
on('#addmodal', 'click', e => {
  // a click on the background closes, but not if it is the end of a drag
  if (e.target.id === 'addmodal' && !dragEnd('addmodal')) $('#addmodal').hidden = true;
});

/* ---- draggable windows: they are grabbed by the title bar ----
   The move is a translation of the box (which stays centred by the
   flex container); the position is kept between one opening and the next and
   is brought back inside the screen when the window opens or changes
   size. Double click on the bar = back to the centre. */
const DRAG = {};                                     // state per window id
const dragEnd = id => !!(DRAG[id] && DRAG[id].justDragged);
function makeDraggable(id) {
  const modal = $(`#${id}`), box = $(`#${id}-box`), head = $(`#${id}-head`);
  if (!modal || !box || !head) return;
  const st = DRAG[id] = { dx: 0, dy: 0, justDragged: false };
  head.classList.add('draggable');
  const apply = () => { box.style.transform = (st.dx || st.dy) ? `translate(${st.dx}px, ${st.dy}px)` : ''; };
  // keeps the box inside the window (at least the title bar stays visible)
  const clamp = () => {
    if (modal.hidden) return;
    const r = box.getBoundingClientRect();
    const bx = r.left - st.dx, by = r.top - st.dy;          // position without translation
    const maxX = window.innerWidth - bx - 80, minX = -bx - r.width + 80;
    const maxY = window.innerHeight - by - 40, minY = -by;
    st.dx = Math.round(Math.max(minX, Math.min(maxX, st.dx)));
    st.dy = Math.round(Math.max(minY, Math.min(maxY, st.dy)));
    apply();
  };
  head.addEventListener('pointerdown', e => {
    if (e.button !== 0 || e.target.closest('button, input, select, a, label')) return;
    const sx = e.clientX - st.dx, sy = e.clientY - st.dy;
    let moved = false;
    const move = ev => {
      const nx = ev.clientX - sx, ny = ev.clientY - sy;
      if (!moved && Math.abs(nx - st.dx) < 3 && Math.abs(ny - st.dy) < 3) return;
      moved = true;
      st.dx = nx; st.dy = ny; apply();
      head.classList.add('dragging');
    };
    const up = () => {
      head.removeEventListener('pointermove', move);
      head.removeEventListener('pointerup', up);
      head.removeEventListener('pointercancel', up);
      head.classList.remove('dragging');
      if (moved) {
        clamp();
        st.justDragged = true;                       // the following click does not close
        setTimeout(() => { st.justDragged = false; }, 0);
      }
    };
    try { head.setPointerCapture(e.pointerId); } catch (_) {}
    head.addEventListener('pointermove', move);
    head.addEventListener('pointerup', up);
    head.addEventListener('pointercancel', up);
    e.preventDefault();
  });
  head.addEventListener('dblclick', e => {
    if (e.target.closest('button, input, select, a, label')) return;
    st.dx = 0; st.dy = 0; apply();
  });
  window.addEventListener('resize', clamp);
  new MutationObserver(clamp).observe(modal, { attributes: true, attributeFilter: ['hidden'] });
}
['modal', 'addmodal', 'linkmodal', 'edgemodal', 'editmodal', 'impmodal', 'aimodal',
 'casemodal', 'manmodal', 'dictmodal', 'ftmmodal', 'osamodal', 'delmodal', 'srcmodal', 'licmodal'].forEach(makeDraggable);
on('#add-type', 'change', syncAddType);
on('#add-value', 'input', updateAddPreview);
on('#add-name', 'input', updateAddPreview);
on('#add-text', 'input', updateAddPreview);
['#add-address', '#add-civico', '#add-lat', '#add-lon'].forEach(s => on(s, 'input', updateAddPreview));
on('#add-toponimo', 'change', updateAddPreview);

/* image: click to choose, drag and drop, paste from the clipboard */
on('#add-drop', 'click', () => $('#add-file').click());
on('#add-file', 'change', e => readImageFile(e.target.files && e.target.files[0]));
on('#add-drop', 'dragover', e => { e.preventDefault(); $('#add-drop').classList.add('over'); });
on('#add-drop', 'dragleave', () => $('#add-drop').classList.remove('over'));
on('#add-drop', 'drop', e => {
  e.preventDefault();
  $('#add-drop').classList.remove('over');
  const dt = e.dataTransfer;
  if (dt && dt.files && dt.files.length) readImageFile(dt.files[0]);
});
document.addEventListener('paste', e => {
  if ($('#addmodal').hidden || $('#add-photo-row').hidden) return;
  const items = (e.clipboardData && e.clipboardData.items) || [];
  for (const it of items) {
    if (it.kind === 'file' && /^image\//i.test(it.type)) {
      readImageFile(it.getAsFile());
      e.preventDefault();
      return;
    }
  }
});

/* ---- new target: creates the folder in data/ and puts the node in the graph ---- */
on('#add-value', 'keydown', e => { if (e.key === 'Enter') $('#addmodal-save').click(); });
['#add-cognome', '#add-nome', '#add-nascita', '#add-colore'].forEach(sel => {
  on(sel, 'input', updateAddPreview);
  on(sel, 'keydown', e => { if (e.key === 'Enter') $('#addmodal-save').click(); });
});
on('#add-target', 'change', updateAddPreview);

on('#addmodal-save', 'click', async () => {
  if (aiMode) { commitAi(); return; }
  const p = addPayload();
  if (p.err !== undefined) {
    updateAddPreview();
    if (p.err) alert(p.err); else alert(t('add.enterValue'));
    return;
  }
  const btn = $('#addmodal-save');
  btn.disabled = true;
  try {
    const parentId = addParent ? addParent.id() : '';
    let value = p.value;
    if (p.photo) {                     // first the image is uploaded, then the node
      const up = await apiPost('/api/upload', {
        data: addPhoto.dataUrl, filename: addPhoto.filename
      });
      value = up.path;                 // e.g. "media/foto_20260829-...png"
    }
    const j = await apiPost('/api/node/add', {
      parent: parentId, ntype: p.ntype, platform: p.platform || '',
      value, label: p.label, url: p.url || '', text: p.text || '',
      address: p.address || '', civico: p.civico || '', lat: p.lat || '', lon: p.lon || '',
      cognome: p.cognome || '', nome: p.nome || '', nascita: p.nascita || '', target: !!p.target,
      colore: p.colore || '', fields: p.fields || null,
      edge: parentId ? readEdgeProps('add') : null   // name, arrows, shape, colour, line
    });
    $('#addmodal').hidden = true;
    // live insertion: the graph stays as it is, with the new node highlighted
    const isNew = !cy.getElementById(j.id).length;
    const node = injectNode(j.node, j.edge, parentId || null);
    if (!parentId && isNew) {                // standalone node: at the centre of the view
      const ex = cy.extent();
      node.position({ x: (ex.x1 + ex.x2) / 2, y: (ex.y1 + ex.y2) / 2 });
      placed.add(node.id());
    }
    // non-Latin label: sync to make the Latin node appear
    // (transliteration) and show it together with the node just added
    if (j.script) {
      try {
        await syncGraph();
        const m = cy.getElementById(j.id);
        const lat = m.length ? m.neighborhood('node').filter(x => x.data('ntype') === 'latin') : cy.collection();
        addToGraph([j.id, ...lat.map(x => x.id())], false);
      } catch (_) {}
    }
    // place or person: the server merges them with identical nodes (one more card)
    // and links them with a dashed line to those in the same street / with the same
    // name; sync to see those links and the linked nodes at once
    if (p.ntype === 'place' || p.ntype === 'name' || ONTO[p.ntype]) {
      try {
        await syncGraph();
        const m = cy.getElementById(j.id);
        const via = m.length ? m.connectedEdges('[rel = "stessa_via"], [rel = "stesso_nome"]').connectedNodes() : cy.collection();
        addToGraph([j.id, ...via.map(x => x.id())], false);
      } catch (_) {}
    }
    if (modalNode && modalNode.id() === parentId) {
      $('#modal-body').innerHTML = bodyFor(modalNode);   // update the summary
    }
    $('#stat').textContent = parentId
      ? t('add.done', { label: j.label, parent: addParent.data('label') })
      : (j.existed ? t('add.existedNew', { label: j.label }) : t('add.doneNew', { label: j.label }));
    void node;
  } catch (err) {
    alert(t('add.failed', { e: err.message }));
  } finally {
    btn.disabled = false;
  }
});

/* ================= BULK IMPORT FROM CSV / EXCEL =================
   Each row: node 1 name, node 1 type, link, node 2 name, node 2 type
   (+ optional columns: url, platform, text, address, lat, lon, note
   for each node; arrows, shape, colour, line, width for the link).
   The server reads the file and shows the preview; then it imports the ticked rows. */
let impFile = null;                 // { filename, data } of the chosen file
let impRows = [];

const IMPORT_TEMPLATE = [
  ['nome1', 'tipo1', 'collegamento', 'nome2', 'tipo2', 'url1', 'url2', 'frecce', 'forma', 'colore', 'linea', 'nota1', 'nota2'],
  ['Mario Rossi', 'persona', 'utenza', '+39 333 1234567', 'telefono', '', '', '->', 'retta', '', '', 'soggetto principale', ''],
  ['Mario Rossi', 'persona', 'profilo', 'mario.rossi', 'instagram', '', 'https://www.instagram.com/mario.rossi/', '->', '', 'blu', '', '', ''],
  ['Mario Rossi', 'persona', 'email', 'mario.rossi@example.com', 'email', '', '', '->', '', '', '', '', ''],
  ['Mario Rossi', 'persona', 'socio', 'ACME srl', 'persona', '', '', '<->', 'curva', 'rosso', 'tratteggiata', '', ''],
  ['ACME srl', 'persona', 'sito web', 'Sito ACME', 'link', '', 'https://www.acme.example', '->', 'spezzata', '', '', '', ''],
  ['ACME srl', 'persona', 'sede', 'Milano', 'luogo', '', '', '', '', '', '', '', ''],
  ['Mario Rossi', 'persona', 'veicolo', 'AB123CD', 'veicolo', '', '', '->', '', '', 'punteggiata', '', ''],
  ['Luca Bianchi', 'persona', '', '', '', '', '', '', '', '', '', 'nodo senza collegamenti', '']
];

function downloadTemplate() {
  const q = v => /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const csv = '\ufeff' + IMPORT_TEMPLATE.map(r => r.map(q).join(';')).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'modello_importazione.csv';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

/* ---- wizard: 1 file, 2 columns, 3 preview ---- */
let impCols = null;                 // response of /api/import/columns
let impMapping = {};                // {column index: key}
const IMP_NODE_KEYS = ['name', 'type', 'label', 'url', 'platform', 'text', 'cognome', 'nascita',
                       'colore', 'flag', 'address', 'civico', 'lat', 'lon', 'note'];
const IMP_EDGE_KEYS = ['rel', 'arrow', 'curve', 'color', 'lstyle', 'width'];

function impStep(n) {
  [1, 2, 3].forEach(k => { $(`#imp-step${k}`).hidden = k !== n; });
  document.querySelectorAll('.imp-step').forEach(el => {
    const k = +el.dataset.step;
    el.classList.toggle('on', k === n); el.classList.toggle('done', k < n);
  });
  $('#impmodal-back').hidden = n === 1;
  $('#impmodal-next').hidden = n !== 2;
  $('#impmodal-go').hidden = n !== 3;
}

function openImport() {
  if (!requireCase()) return;
  impFile = null; impRows = []; impCols = null; impMapping = {};
  $('#imp-file').value = '';
  $('#imp-drop-txt').textContent = t('imp.drop');
  $('#imp-res').innerHTML = ''; $('#imp-sum').textContent = '';
  $('#imp-map').innerHTML = ''; $('#imp-map-msg').textContent = '';
  $('#imp-def-rel').value = '';
  fillImpTypeSelects();
  impStep(1);
  $('#impmodal').hidden = false;
}

/* default node types: the same as in the «New node» window (except the photo) */
function fillImpTypeSelects() {
  const src = $('#add-type');
  const opts = `<option value="">${esc(t('imp.auto'))}</option>` +
    [...src.querySelectorAll('option')].filter(o => o.value && o.value !== 'photo')
      .map(o => `<option value="${esc(o.value)}">${esc(o.textContent)}</option>`).join('');
  ['#imp-def-type1', '#imp-def-type2'].forEach(sel => { $(sel).innerHTML = opts; });
}

function readImportFile(file) {
  if (!file) return;
  if (/\.json$/i.test(file.name)) {
    // a saved Epieos response ({"result": {...}}) goes to its own import;
    // everything else is Follow the Money entities
    const fr = new FileReader();
    fr.onload = () => {
      let obj = null;
      try { obj = JSON.parse(fr.result); } catch (_) { obj = null; }
      $('#impmodal').hidden = true;
      if (isEpieosJson(obj)) epImportFile(file.name, fr.result, obj);
      else openFtmImport(file);
    };
    fr.readAsText(file);
    return;
  }
  if (/\.(jsonl|ftm|ndjson|zip)$/i.test(file.name)) {  // Follow the Money entities (zip: Cognitor bundle)
    $('#impmodal').hidden = true;
    openFtmImport(file);
    return;
  }
  const r = new FileReader();
  r.onload = () => { impFile = { filename: file.name, data: r.result }; loadImportColumns(); };
  r.readAsDataURL(file);
  $('#imp-drop-txt').textContent = file.name;
}

async function loadImportColumns() {
  if (!impFile) return;
  $('#imp-map').innerHTML = `<div class="empty">${esc(t('err.loading'))}</div>`;
  impStep(2);
  try {
    impCols = await apiPost('/api/import/columns', impFile);
  } catch (err) {
    impStep(1);
    $('#imp-drop-txt').textContent = `⚠ ${err.message}`;
    impFile = null;
    return;
  }
  $('#imp-header').checked = !!impCols.header;
  // initial mapping: the columns recognised from the headers; the others
  // become additional fields of node 1 (so no value is lost)
  impMapping = {};
  impCols.columns.forEach(c => {
    // free column: goes to node 2 if the name ends in 2 (e.g. 'jurisdiction2'), otherwise to node 1
    impMapping[c.index] = c.auto || (impCols.header && c.name ? `extra${/2$/.test(c.name) ? '2' : '1'}:${c.name}` : '');
  });
  renderImportMapping();
}

function impColName(c) {
  return $('#imp-header').checked && c.name ? c.name : t('imp.colN', { n: c.index + 1 });
}

function impMapOptions(sel) {
  const opt = (v, lab) => `<option value="${esc(v)}"${v === sel ? ' selected' : ''}>${esc(lab)}</option>`;
  const grp = (lab, inner) => `<optgroup label="${esc(lab)}">${inner}</optgroup>`;
  return opt('', t('imp.ignore')) +
    grp(t('imp.grpNode1'), IMP_NODE_KEYS.map(k => opt(k + '1', t('imp.f.' + k))).join('') + opt('extra1', t('imp.extra1'))) +
    grp(t('imp.grpEdge'), IMP_EDGE_KEYS.map(k => opt(k, t('imp.e.' + k))).join('')) +
    grp(t('imp.grpNode2'), IMP_NODE_KEYS.map(k => opt(k + '2', t('imp.f.' + k))).join('') + opt('extra2', t('imp.extra2')));
}

function renderImportMapping() {
  if (!impCols) return;
  const header = $('#imp-header').checked;
  const auto = impCols.columns.filter(c => c.auto).length;
  $('#imp-detected').textContent = t('imp.detected', { n: auto, t: impCols.columns.length, r: impCols.rows + (header ? 0 : 1) });
  $('#imp-map').innerHTML = `<table class="imp-t imp-map-t"><thead><tr>` +
    `<th>${esc(t('imp.colName'))}</th><th>${esc(t('imp.colSamples'))}</th><th>${esc(t('imp.colMap'))}</th></tr></thead><tbody>` +
    impCols.columns.map(c => {
      const v = impMapping[c.index] || '';
      const sel = v.startsWith('extra1:') ? 'extra1' : v.startsWith('extra2:') ? 'extra2' : v;
      const samples = (header ? c.samples : [impCols.first_row[c.index], ...c.samples]).filter(Boolean).slice(0, 3);
      return `<tr><td><b>${esc(impColName(c))}</b></td>` +
        `<td class="imp-samples">${samples.map(x => esc(x)).join(' · ')}</td>` +
        `<td><select data-col="${c.index}">${impMapOptions(sel)}</select></td></tr>`;
    }).join('') + '</tbody></table>';
  $('#imp-map-msg').textContent = '';
}

function readImportMapping() {
  const header = $('#imp-header').checked;
  const m = {};
  document.querySelectorAll('#imp-map select[data-col]').forEach(sel => {
    const c = impCols.columns[+sel.dataset.col];
    let v = sel.value;
    if (v === 'extra1' || v === 'extra2') v = `${v}:${impColName(c)}`;
    if (v) m[c.index] = v;
  });
  impMapping = m;
  return { mapping: m, header, defaults: {
    type1: $('#imp-def-type1').value, type2: $('#imp-def-type2').value, rel: $('#imp-def-rel').value.trim() } };
}

on('#imp-header', 'change', () => {
  // without a header the columns have no name: «additional fields» make no sense
  if (!$('#imp-header').checked) {
    Object.keys(impMapping).forEach(k => { if (String(impMapping[k]).startsWith('extra')) impMapping[k] = ''; });
  }
  renderImportMapping();
});
on('#imp-map', 'change', e => {
  const sel = e.target.closest('select[data-col]');
  if (!sel) return;
  const c = impCols.columns[+sel.dataset.col];
  impMapping[c.index] = (sel.value === 'extra1' || sel.value === 'extra2') ? `${sel.value}:${impColName(c)}` : sel.value;
  // the same key on two columns: the previous one goes back to «ignore»
  Object.keys(impMapping).forEach(k => {
    if (+k !== c.index && impMapping[k] && impMapping[k] === impMapping[c.index] && !impMapping[k].startsWith('extra')) {
      impMapping[k] = '';
    }
  });
  renderImportMapping();
});

const impNode = n => n
  ? `<span class="imp-n${n.exists ? ' ex' : ''}" title="${esc(n.id)}">` +
    `<img src="${iconFor(n)}" alt=""><span>${esc(n.label)}</span>` +
    `<small>${esc(n.ntype === 'account' ? n.platform : n.ntype)}</small></span>`
  : '<span class="imp-none">—</span>';

/* Preview table (plan rows: node 1, link, node 2), used
   by the file import and by the AI. Rows with errors are not imported;
   the others have a box to exclude them. */
function planTableHtml(rows) {
  return `<table class="imp-t"><thead><tr><th></th><th>#</th>` +
    `<th>${esc(t('imp.node1'))}</th><th>${esc(t('imp.link'))}</th><th>${esc(t('imp.node2'))}</th></tr></thead><tbody>` +
    rows.slice(0, 1000).map(r => {
      const [a, b] = [r.nodes.find(n => n.side === '1'), r.nodes.find(n => n.side === '2')];
      const e = r.edge;
      return `<tr class="${r.error ? 'imp-err' : ''}">` +
        `<td>${r.error ? '⚠' : `<input type="checkbox" data-row="${r.row}" checked>`}</td>` +
        `<td>${r.row}</td>` +
        (r.error ? `<td colspan="3">${esc(r.error)}</td>`
          : `<td>${impNode(a)}</td><td class="imp-e">${e ? `<i style="color:${esc(e.color || '#64748b')}">${ARROW_SYM[e.arrow] || '—'}</i> ${esc(e.label || '')}` : ''}</td><td>${impNode(b)}</td>`) +
        '</tr>';
    }).join('') + '</tbody></table>' +
    (rows.length > 1000 ? `<div class="af-hint">${esc(t('imp.more', { n: rows.length - 1000 }))}</div>` : '');
}

/* Plan counts for the summary line. */
function planCounts(rows) {
  const ok = rows.filter(r => !r.error);
  const newN = new Set(), oldN = new Set();
  ok.forEach(r => r.nodes.forEach(n => (n.exists ? oldN : newN).add(n.id)));
  return { rows: rows.length, nn: newN.size, on: oldN.size,
           l: ok.filter(r => r.nodes.length === 2).length, err: rows.length - ok.length };
}

async function previewImport() {
  if (!impFile || !impCols) return;
  const opts = readImportMapping();
  if (!Object.values(opts.mapping).includes('name1')) {
    $('#imp-map-msg').textContent = t('imp.needName');
    return;
  }
  impStep(3);
  $('#imp-res').innerHTML = `<div class="empty">${esc(t('err.loading'))}</div>`;
  $('#impmodal-go').disabled = true;
  try {
    const j = await apiPost('/api/import/preview', Object.assign({}, impFile, opts));
    impRows = j.rows || [];
    const ok = impRows.filter(r => !r.error);
    $('#imp-sum').textContent = t('imp.summary', planCounts(impRows));
    $('#imp-res').innerHTML = planTableHtml(impRows);
    $('#impmodal-go').disabled = !ok.length;
  } catch (err) {
    $('#imp-res').innerHTML = `<div class="empty imp-fail">⚠ ${esc(err.message)}</div>`;
    $('#imp-sum').textContent = '';
  }
}

async function commitImport() {
  if (!impFile) return;
  const skip = [...document.querySelectorAll('#imp-res input[data-row]')]
    .filter(c => !c.checked).map(c => +c.dataset.row);
  const btn = $('#impmodal-go');
  btn.disabled = true;
  btn.textContent = t('imp.working');
  try {
    const j = await apiPost('/api/import/commit', Object.assign({ skip }, impFile, readImportMapping()));
    await syncGraph();
    $('#impmodal').hidden = true;
    const ids = (j.ids || []).filter(id => cy.getElementById(id).length);
    if (ids.length) {
      addToGraph(ids, false);
      cy.fit(cy.nodes().filter(n => ids.includes(n.id())), 60); capZoom(1.4);
    }
    $('#stat').textContent = t('imp.done', { n: j.nodes, l: j.links, s: j.same_links,
                                             err: (j.errors || []).length });
    if ((j.errors || []).length) {
      alert(t('imp.errList') + '\n\n' +
        j.errors.slice(0, 30).map(e => `${t('imp.rowN', { n: e.row })}: ${e.error}`).join('\n'));
    }
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally {
    btn.disabled = false;
    btn.textContent = t('imp.go');
  }
}

on('#importData', 'click', openImport);

// ---- video transcription (1.6.0): audio/ modules, a job polled every 700 ms ----
let trTimer = null;
async function openTranscribe() {
  if (!requireCase()) return;
  $('#trmodal').hidden = false;
  $('#tr-result').textContent = '';
  try {
    const st = await (await fetch('/api/transcribe/status')).json();
    $('#tr-status').textContent = st.available
      ? (st.diarize_models_cached ? t('tr.ready') : t('tr.readyDownload'))
      : t('tr.missing', { pkgs: (st.missing || []).join(', ') });
    $('#tr-go').disabled = !st.available;
    if (st.running) pollTranscribe();
  } catch (err) {
    $('#tr-status').textContent = t('tr.failed', { e: err.message });
  }
}
async function startTranscribe() {
  const body = {
    path: $('#tr-path').value.trim().replace(/^"|"$/g, ''), model_size: $('#tr-model').value,
    diarize: $('#tr-diarize').checked, speakers: parseInt($('#tr-speakers').value || '0', 10) || 0,
    translate: ['en', 'it'].filter(l => $('#tr-' + l).checked),
  };
  if (!body.path) return;
  $('#tr-result').textContent = ''; $('#tr-log').textContent = ''; $('#tr-bar-fill').style.width = '0';
  try {
    await apiPost('/api/transcribe', body);
    pollTranscribe();
  } catch (err) {
    $('#tr-result').textContent = t('tr.failed', { e: err.message });
  }
}
function pollTranscribe() {
  $('#tr-go').disabled = true; $('#tr-stop').disabled = false;
  clearInterval(trTimer);
  trTimer = setInterval(transcribeTick, 700);
  transcribeTick();
}
async function transcribeTick() {
  let p;
  try { p = await (await fetch('/api/transcribe/progress')).json(); } catch (_) { return; }
  const log = $('#tr-log');
  log.textContent = (p.log || []).join('\n');
  log.scrollTop = log.scrollHeight;
  const stage = t('tr.stage.' + (p.stage || 'hash'));
  $('#tr-prog-txt').textContent = p.total ? `${stage} ${p.done}/${p.total}` : stage;
  if (p.total) $('#tr-bar-fill').style.width = Math.round(100 * p.done / p.total) + '%';
  if (p.running) return;
  clearInterval(trTimer); trTimer = null;
  $('#tr-go').disabled = false; $('#tr-stop').disabled = true;
  if (!p.finished) return;
  if (p.error) { $('#tr-result').textContent = t('tr.failed', { e: p.error }); return; }
  const r = p.result || {};
  $('#tr-bar-fill').style.width = '100%';
  $('#tr-result').textContent = t('tr.result', { segments: r.segments, speakers: r.speakers,
    nodes: r.nodes, links: r.links, updated: r.updated }) + (r.partial ? ' ' + t('tr.partial') : '');
  $('#stat').textContent = $('#tr-result').textContent;
  await reloadData();
}
on('#transcribeVideo', 'click', openTranscribe);
on('#tr-go', 'click', startTranscribe);
on('#tr-stop', 'click', () => apiPost('/api/transcribe/stop', {}).catch(() => {}));
on('#tr-done', 'click', () => { $('#trmodal').hidden = true; });
on('#trmodal-close', 'click', () => { $('#trmodal').hidden = true; });
on('#tr-path', 'keydown', e => { if (e.key === 'Enter') startTranscribe(); });

/* ---- export of the case to Follow the Money (JSON lines) ---- */
on('#exportFtm', 'click', async () => {
  if (!requireCase()) return;
  const visible = cy ? cy.nodes().map(n => n.id()) : [];
  let ids = null;
  if (visible.length && confirm(t('ftm.exportAsk', { n: visible.length }))) ids = visible;
  const btn = $('#exportFtm');
  btn.disabled = true;
  try {
    const r = await fetch('/api/ftm/export', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify(ids ? { ids } : {}) });
    if (!r.ok) {
      let msg = `HTTP ${r.status}`;
      try { msg = (await r.json()).error || msg; } catch (_) {}
      throw new Error(msg);
    }
    const blob = await r.blob();
    const sum = JSON.parse(r.headers.get('X-Ftm-Summary') || '{}');
    const cd = r.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename=([^;]+)/);
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = m ? m[1].trim() : 'caso.ftm.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    const skipped = Object.entries(sum.skipped || {}).map(([k, v]) => `${k} ${v}`).join(', ');
    $('#stat').textContent = t('ftm.exported', { nodes: sum.nodes || 0, links: sum.links || 0,
      prop: sum.as_property || 0, skipped: skipped || '—' });
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally { btn.disabled = false; }
});

/* ================= FOLLOW THE MONEY IMPORT =================
   FtM entity files, even large ones: inspection (counts per schema), filters,
   background import with progress (/api/ftm/*). */
let ftmFile = null, ftmInfo = null;
const FTM_WARN_NODES = 5000;

function ftmStep(n) {
  document.querySelectorAll('#ftmmodal .imp-step').forEach(el => {
    const k = +el.dataset.step;
    el.classList.toggle('on', k === n);
    el.classList.toggle('done', k < n);
  });
  for (const k of [1, 2, 3]) $(`#ftm-step${k}`).hidden = k !== n;
  $('#ftmmodal-back').hidden = n !== 2;
  $('#ftmmodal-go').hidden = n !== 2;
  $('#ftmmodal-done').hidden = n !== 3;
}

function openFtmImport(file) {
  if (!requireCase()) return;
  ftmFile = null; ftmInfo = null;
  $('#ftm-file').value = '';
  $('#ftm-path').value = '';
  $('#ftm-drop-txt').textContent = t('ftm.drop');
  $('#ftm-schemas').innerHTML = ''; $('#ftm-sum').textContent = ''; $('#ftm-warn').textContent = '';
  $('#ftm-result').textContent = ''; $('#ftm-prog-txt').textContent = ''; $('#ftm-bar-fill').style.width = '0';
  ftmStep(1);
  $('#ftmmodal').hidden = false;
  if (file) readFtmFile(file);
}

function readFtmFile(file) {
  if (!file) return;
  const r = new FileReader();
  r.onload = () => { ftmFile = { filename: file.name, data: r.result }; inspectFtm(); };
  r.readAsDataURL(file);
  $('#ftm-drop-txt').textContent = file.name;
}

function readFtmPath() {
  const path = $('#ftm-path').value.trim().replace(/^"|"$/g, '');
  if (!path) return;
  ftmFile = { filename: path.split(/[\\/]/).pop(), path };
  $('#ftm-drop-txt').textContent = ftmFile.filename;
  inspectFtm();
}

async function inspectFtm() {
  if (!ftmFile) return;
  $('#ftm-sum').textContent = t('err.loading');
  ftmStep(2);
  try {
    ftmInfo = await apiPost('/api/ftm/inspect', ftmFile);
  } catch (err) {
    ftmStep(1);
    $('#ftm-drop-txt').textContent = `⚠ ${err.message}`;
    ftmFile = null;
    return;
  }
  const ds = Object.keys(ftmInfo.datasets || {});
  if (ftmInfo.bundle && ftmInfo.dataset) ds.unshift(ftmInfo.dataset);
  $('#ftm-sum').textContent = t('ftm.sumLine', { n: ftmInfo.entities, nodes: ftmInfo.nodes,
    edges: ftmInfo.edges, ds: ds.length ? ds.join(', ') : '—' }) +
    (ftmInfo.bundle ? ' ' + t('ftm.bundleLine', { name: ftmInfo.case_name || ftmInfo.case_id || '—',
      images: ftmInfo.images, transcripts: ftmInfo.transcripts }) : '');
  $('#ftm-dataset').value = ds.length === 1 ? ds[0] : (ftmFile.filename || '').replace(/\.[^.]+$/, '');
  const entries = Object.entries(ftmInfo.schemas || {}).sort((a, b) => b[1] - a[1]);
  $('#ftm-schemas').innerHTML = entries.map(([sc, n]) => {
    const typ = (ftmInfo.native || {})[sc] || 'text';
    const o = ONTO[typ];
    const as = o ? ontoLabel(o) : t('add.kind.' + typ, {}) === 'add.kind.' + typ ? typ : t('add.kind.' + typ);
    return `<label><input type="checkbox" data-schema="${esc(sc)}" checked> ${esc((ftmInfo.labels || {})[sc] || sc)}` +
           ` <i>${esc(t('ftm.asType'))} ${esc(as)}</i><small>${n}</small></label>`;
  }).join('') +
  `<div class="jm-msg"><button type="button" class="mini" id="ftm-all">${esc(t('ftm.all'))}</button> ` +
  `<button type="button" class="mini" id="ftm-none">${esc(t('ftm.none'))}</button></div>`;
  ftmWarn();
}

function ftmSelectedSchemas() {
  return [...document.querySelectorAll('#ftm-schemas input[data-schema]:checked')].map(i => i.dataset.schema);
}

function ftmWarn() {
  if (!ftmInfo) return;
  const sel = new Set(ftmSelectedSchemas());
  let n = 0;
  for (const [sc, c] of Object.entries(ftmInfo.schemas || {})) if (sel.has(sc)) n += c;
  const max = parseInt($('#ftm-max').value || '0', 10) || 0;
  if (max) n = Math.min(n, max);
  $('#ftm-warn').textContent = (n > FTM_WARN_NODES && !$('#ftm-text').value.trim())
    ? t('ftm.warnBig', { n: FTM_WARN_NODES }) : '';
  $('#ftmmodal-go').disabled = !sel.size;
}

async function runFtmImport() {
  if (!ftmFile) return;
  const payload = Object.assign({}, ftmFile, {
    schemas: ftmSelectedSchemas(), text: $('#ftm-text').value.trim(),
    max_entities: parseInt($('#ftm-max').value || '0', 10) || 0,
    connected_only: $('#ftm-connected').checked, dataset: $('#ftm-dataset').value.trim(),
  });
  ftmStep(3);
  $('#ftm-prog-txt').textContent = t('ftm.stageParse');
  $('#ftmmodal-done').disabled = true;
  try {
    await apiPost('/api/ftm/import', payload);
    for (;;) {
      await sleep(400);
      const r = await fetch('/api/ftm/progress');
      const p = await r.json();
      if (p.stage === 'files') $('#ftm-prog-txt').textContent = t('ftm.stageFiles');
      if (p.stage === 'filter') $('#ftm-prog-txt').textContent = t('ftm.stageFilter');
      if (p.stage === 'import' && p.total) {
        $('#ftm-prog-txt').textContent = t('ftm.stageImport', { i: p.done, n: p.total });
        $('#ftm-bar-fill').style.width = Math.round(100 * p.done / p.total) + '%';
      }
      if (p.finished) {
        if (p.error) throw new Error(p.error);
        $('#ftm-bar-fill').style.width = '100%';
        $('#ftm-result').textContent = t('ftm.result', { nodes: p.nodes, links: p.links,
          updated: p.updated, same: p.same_links, errors: p.errors }) +
          (ftmInfo && ftmInfo.bundle ? ' ' + t('ftm.bundleResult', { images: p.images || 0,
            refused: p.images_refused || 0, transcripts: p.transcripts || 0 }) : '');
        $('#stat').textContent = $('#ftm-result').textContent;
        await reloadData();
        break;
      }
    }
  } catch (err) {
    $('#ftm-result').textContent = t('ftm.failed', { e: err.message });
  } finally {
    $('#ftmmodal-done').disabled = false;
  }
}

on('#ftmmodal-close', 'click', () => { $('#ftmmodal').hidden = true; });
on('#ftmmodal-done', 'click', () => { $('#ftmmodal').hidden = true; });
on('#ftmmodal', 'click', e => { if (e.target.id === 'ftmmodal' && !dragEnd('ftmmodal')) $('#ftmmodal').hidden = true; });
on('#ftm-drop', 'click', () => $('#ftm-file').click());
on('#ftm-path-go', 'click', readFtmPath);
on('#ftm-path', 'keydown', e => { if (e.key === 'Enter') readFtmPath(); });
on('#ftm-file', 'change', e => readFtmFile(e.target.files && e.target.files[0]));
on('#ftm-drop', 'dragover', e => { e.preventDefault(); $('#ftm-drop').classList.add('over'); });
on('#ftm-drop', 'dragleave', () => $('#ftm-drop').classList.remove('over'));
on('#ftm-drop', 'drop', e => {
  e.preventDefault(); $('#ftm-drop').classList.remove('over');
  readFtmFile(e.dataTransfer.files && e.dataTransfer.files[0]);
});
on('#ftmmodal-back', 'click', () => ftmStep(1));
on('#ftmmodal-go', 'click', runFtmImport);
on('#ftm-schemas', 'change', ftmWarn);
on('#ftm-schemas', 'click', e => {
  if (e.target.id === 'ftm-all' || e.target.id === 'ftm-none') {
    document.querySelectorAll('#ftm-schemas input[data-schema]').forEach(i => { i.checked = e.target.id === 'ftm-all'; });
    ftmWarn();
  }
});
on('#ftm-max', 'input', ftmWarn);
on('#ftm-text', 'input', ftmWarn);

on('#modal-ai', 'click', () => { if (modalNode) { openAdd(modalNode); setAiMode(true); } });
on('#impmodal-close', 'click', () => { $('#impmodal').hidden = true; });
on('#impmodal', 'click', e => { if (e.target.id === 'impmodal' && !dragEnd('impmodal')) $('#impmodal').hidden = true; });
on('#imp-template', 'click', downloadTemplate);
on('#imp-drop', 'click', () => $('#imp-file').click());
on('#imp-file', 'change', e => readImportFile(e.target.files && e.target.files[0]));
on('#imp-drop', 'dragover', e => { e.preventDefault(); $('#imp-drop').classList.add('over'); });
on('#imp-drop', 'dragleave', () => $('#imp-drop').classList.remove('over'));
on('#imp-drop', 'drop', e => {
  e.preventDefault();
  $('#imp-drop').classList.remove('over');
  const dt = e.dataTransfer;
  if (dt && dt.files && dt.files.length) readImportFile(dt.files[0]);
});
on('#impmodal-go', 'click', commitImport);
on('#impmodal-next', 'click', previewImport);
on('#impmodal-back', 'click', () => impStep($('#imp-step3').hidden ? 1 : 2));

/* ================= AI: FROM FREE TEXT TO NODES =================
   In the "Add" / "New node" window the ✨ AI button turns the
   form into a single text area: the chatbot reads the text, proposes nodes and
   links, the user chooses which to keep and adds them to the graph. */
let aiConf = null;                  // public configuration (without the key)
let aiMode = false;
let aiItems = [];                   // rows proposed by the server (to be sent back at commit)
let aiRows = [];

async function loadAiConf() {
  try {
    const r = await fetch('/api/ai/config');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    aiConf = await r.json();
  } catch (_) { aiConf = null; }
  syncAiSide();
}

function syncAiSide() {
  const sw = $('#aiSwitch'), st = $('#aiSideStatus'), tg = $('#add-ai-toggle');
  const on = !!(aiConf && aiConf.enabled);
  if (sw) sw.checked = on;
  if (st) {
    st.className = 'ai-side-st ' + (aiConf && aiConf.ready ? 'ok' : 'off');
    st.textContent = !aiConf ? t('ai.unavailable')
      : !aiConf.endpoint ? t('ai.noEndpoint')
      : `${aiConf.model} · ${aiConf.endpoint.replace(/^https?:\/\//, '')}`;
  }
  if (tg) tg.classList.toggle('off', !(aiConf && aiConf.ready));
}

function setAiMode(onoff) {
  aiMode = !!onoff;
  $('#add-form').hidden = aiMode;
  $('#add-ai-sec').hidden = !aiMode;
  $('#add-ai-toggle').classList.toggle('on', aiMode);
  $('#addmodal-box').classList.toggle('ai-mode', aiMode);
  $('#addmodal-save').textContent = aiMode ? t('ai.addAll') : t('add.save');
  syncAiSave();
  if (aiMode) {
    const g = $('#ai-glow');
    g.classList.remove('intro'); void g.offsetWidth;      // restart the animation
    g.classList.add('intro');
    setTimeout(() => g.classList.remove('intro'), 1700);
    setTimeout(() => $('#ai-text').focus(), 60);
  }
}

function resetAi() {
  aiItems = []; aiRows = [];
  $('#ai-text').value = '';
  $('#ai-res').innerHTML = '';
  aiStatus('');
}

function aiStatus(msg, kind) {
  const el = $('#ai-status');
  el.textContent = msg || '';
  el.className = 'ai-status' + (kind ? ' ' + kind : '');
}

function syncAiSave() {
  const b = $('#addmodal-save');
  if (aiMode) b.disabled = !aiRows.some(r => !r.error);
  else b.disabled = false;
}

on('#add-ai-toggle', 'click', () => {
  if (!aiMode && !(aiConf && aiConf.ready)) {       // AI off or not configured
    if (confirm(t('ai.needConfig'))) openAiConfig();
    return;
  }
  setAiMode(!aiMode);
});

async function runAi() {
  const text = $('#ai-text').value.trim();
  if (text.length < 3) { aiStatus(t('ai.empty'), 'err'); return; }
  const btn = $('#ai-run'), g = $('#ai-glow');
  btn.disabled = true; g.classList.add('busy');
  $('#ai-text').readOnly = true;
  aiStatus(t('ai.working'), 'shimmer');
  $('#ai-res').innerHTML = '';
  aiRows = []; syncAiSave();
  try {
    const j = await apiPost('/api/ai/nodes', { text, parent: addParent ? addParent.id() : '' });
    aiItems = j.items || [];
    aiRows = j.rows || [];
    const c = planCounts(aiRows);
    aiStatus(t('ai.found', c));
    $('#ai-res').innerHTML = planTableHtml(aiRows);
  } catch (err) {
    aiStatus('⚠ ' + err.message, 'err');
  } finally {
    btn.disabled = false; g.classList.remove('busy');
    $('#ai-text').readOnly = false;
    syncAiSave();
  }
}
on('#ai-run', 'click', runAi);
on('#ai-text', 'keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runAi(); });

/* Adds the ticked rows of the proposal to the graph. */
async function commitAi() {
  const skip = [...document.querySelectorAll('#ai-res input[data-row]')]
    .filter(c => !c.checked).map(c => +c.dataset.row);
  const btn = $('#addmodal-save');
  btn.disabled = true;
  try {
    const j = await apiPost('/api/ai/commit', { items: aiItems, skip });
    await syncGraph();
    $('#addmodal').hidden = true;
    const ids = (j.ids || []).filter(id => cy.getElementById(id).length);
    if (addParent) ids.push(addParent.id());
    if (ids.length) addToGraph(ids, true);
    if (modalNode && addParent && modalNode.id() === addParent.id()) openModal(cy.getElementById(addParent.id()));
    $('#stat').textContent = t('ai.done', { n: j.nodes, l: j.links });
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally {
    syncAiSave();
  }
}

/* ---------------- configuration panel (chatbot.conf) ---------------- */
function openAiConfig() {
  const c = aiConf || {};
  $('#aic-enabled').checked = !!c.enabled;
  $('#aic-endpoint').value = c.endpoint || '';
  $('#aic-key').value = '';
  $('#aic-key').type = 'password';
  $('#aic-key').placeholder = c.has_key ? t('aicfg.keyKeep', { h: c.key_hint }) : t('aicfg.keyNone');
  $('#aic-model').value = c.model || '';
  $('#aic-api').value = c.api || 'auto';
  $('#aic-timeout').value = c.timeout || 25;
  $('#aic-header').value = c.auth_header || '';
  $('#aic-prefix').value = c.auth_prefix || '';
  $('#aic-auto').checked = !!c.auto;
  const r = $('#aic-test-res'); r.textContent = ''; r.className = 'aic-test';
  $('#aimodal').hidden = false;
}

function aiConfPayload() {
  const p = {
    enabled: $('#aic-enabled').checked, endpoint: $('#aic-endpoint').value.trim(),
    model: $('#aic-model').value.trim(), api: $('#aic-api').value,
    timeout: $('#aic-timeout').value, auth_header: $('#aic-header').value.trim(),
    auth_prefix: $('#aic-prefix').value.trim(), auto: $('#aic-auto').checked
  };
  const k = $('#aic-key').value.trim();
  if (k) p.api_key = k;                // empty = the saved one stays
  return p;
}

async function saveAiConfig() {
  const btn = $('#aimodal-save');
  btn.disabled = true;
  try {
    aiConf = await apiPost('/api/ai/config', aiConfPayload());
    syncAiSide();
    $('#aimodal').hidden = true;
    $('#stat').textContent = t('aicfg.saved');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally {
    btn.disabled = false;
  }
}

async function testAiConfig() {
  const r = $('#aic-test-res'), btn = $('#aimodal-test');
  btn.disabled = true;
  r.className = 'aic-test'; r.textContent = t('aicfg.testing');
  try {
    // the SAVED configuration is tested: the form's one is saved first
    aiConf = await apiPost('/api/ai/config', aiConfPayload());
    syncAiSide();
    $('#aic-key').value = '';
    $('#aic-key').placeholder = aiConf.has_key ? t('aicfg.keyKeep', { h: aiConf.key_hint }) : t('aicfg.keyNone');
    const j = await apiPost('/api/ai/test', {});
    r.className = 'aic-test ' + (j.ok ? 'ok' : 'err');
    r.textContent = j.ok ? t('aicfg.testOk', { ms: j.ms, model: j.model, api: j.api || '' })
                         : t('aicfg.testErr', { e: j.error, ms: j.ms });
  } catch (err) {
    r.className = 'aic-test err'; r.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

on('#aiSettings', 'click', openAiConfig);

/* ================= OPENSANCTIONS =================
   Online search (yente API) and import of the matches as FtM
   entities. Off = no calls; the switch asks for confirmation. */
let osaConf = null, osaLast = [];

function syncOsaSide() {
  const c = osaConf || {};
  const sw = $('#osaSwitch'), st = $('#osaSideStatus');
  if (sw) sw.checked = !!c.enabled;
  if (st) {
    st.textContent = !c.enabled ? t('osa.off') : !c.endpoint ? t('osa.noEndpoint')
      : c.has_key ? t('osa.on', { ep: c.endpoint.replace(/^https?:\/\//, '') }) : t('osa.noKey');
  }
  const q = $('#osaQuery'), b = $('#osaSearch');
  if (q) q.disabled = !c.ready;
  if (b) b.disabled = !c.ready;
}

async function loadOsaConf() {
  try {
    const r = await fetch('/api/osa/config');
    osaConf = r.ok ? await r.json() : null;
  } catch (_) { osaConf = null; }
  syncOsaSide();
}

on('#osaSwitch', 'change', async e => {
  const want = e.target.checked;
  if (want && !confirm(t('osa.warn'))) { e.target.checked = false; return; }
  try {
    osaConf = await apiPost('/api/osa/config', { enabled: want });
    $('#stat').textContent = want ? t('osa.switchedOn') : t('osa.switchedOff');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
  syncOsaSide();
});

function openOsaConfig() {
  const c = osaConf || {};
  $('#osac-enabled').checked = !!c.enabled;
  $('#osac-endpoint').value = c.endpoint || '';
  $('#osac-key').value = ''; $('#osac-key').type = 'password';
  $('#osac-key').placeholder = c.has_key ? t('aicfg.keyKeep', { h: c.key_hint }) : t('aicfg.keyNone');
  $('#osac-dataset').value = c.dataset || 'default';
  $('#osac-timeout').value = c.timeout || 20;
  const r = $('#osac-test-res'); r.textContent = ''; r.className = 'aic-test';
  $('#osamodal').hidden = false;
}
function osaConfPayload() {
  const p = { enabled: $('#osac-enabled').checked, endpoint: $('#osac-endpoint').value.trim(),
              dataset: $('#osac-dataset').value.trim(), timeout: $('#osac-timeout').value };
  const k = $('#osac-key').value.trim();
  if (k) p.api_key = k;
  return p;
}
async function saveOsaConfig() {
  const btn = $('#osamodal-save');
  btn.disabled = true;
  try {
    if ($('#osac-enabled').checked && !(osaConf && osaConf.enabled) && !confirm(t('osa.warn'))) return;
    osaConf = await apiPost('/api/osa/config', osaConfPayload());
    syncOsaSide();
    $('#osamodal').hidden = true;
    $('#stat').textContent = t('osacfg.saved');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally { btn.disabled = false; }
}
async function testOsaConfig() {
  const r = $('#osac-test-res'), btn = $('#osamodal-test');
  btn.disabled = true; r.className = 'aic-test'; r.textContent = t('aicfg.testing');
  try {
    osaConf = await apiPost('/api/osa/config', osaConfPayload());
    syncOsaSide();
    $('#osac-key').value = '';
    $('#osac-key').placeholder = osaConf.has_key ? t('aicfg.keyKeep', { h: osaConf.key_hint }) : t('aicfg.keyNone');
    const j = await apiPost('/api/osa/test', {});
    r.className = 'aic-test ok'; r.textContent = t('osacfg.testOk', { n: j.total ?? '?' });
  } catch (err) {
    r.className = 'aic-test err'; r.textContent = t('osacfg.testErr', { e: err.message });
  } finally { btn.disabled = false; }
}
on('#osaSettings', 'click', openOsaConfig);
on('#osamodal-save', 'click', saveOsaConfig);
on('#osamodal-test', 'click', testOsaConfig);
on('#osamodal-close', 'click', () => { $('#osamodal').hidden = true; });
on('#osamodal', 'click', e => { if (e.target.id === 'osamodal' && !dragEnd('osamodal')) $('#osamodal').hidden = true; });
on('#osac-key-eye', 'click', () => { const k = $('#osac-key'); k.type = k.type === 'password' ? 'text' : 'password'; });

function renderOsaResults(q, rows, total) {
  const box = $('#osaResults');
  osaLast = rows || [];
  if (!osaLast.length) { box.innerHTML = `<div class="osa-empty">${esc(t('osa.none', { q }))}</div>`; return; }
  box.innerHTML = `<div class="osa-empty">${esc(t('osa.total', { n: total ?? osaLast.length, q, shown: osaLast.length }))}</div>` +
    osaLast.map((r, i) => `
      <div class="osa-r" data-i="${i}">
        <b dir="auto">${esc(r.caption || r.id)}</b>
        <button type="button" class="mini" data-osaadd="${esc(r.id)}">${esc(t('osa.add'))}</button>
        <small>${esc(r.schema)}${r.birth ? ' · ' + esc(r.birth) : ''}${r.score != null ? ' · ' + Math.round(r.score * 100) + '%' : ''}</small>
        <div class="osa-tags">${(r.countries || []).map(c => `<span>${esc(c)}</span>`).join('')}
          ${(r.topics || []).map(c => `<span class="topic">${esc(c)}</span>`).join('')}
          ${(r.datasets || []).slice(0, 2).map(c => `<span>${esc(c)}</span>`).join('')}</div>
      </div>`).join('');
}

async function osaSearch(q, schema) {
  q = (q || '').trim();
  if (q.length < 2) return;
  $('#osaQuery').value = q;
  $('#osaResults').innerHTML = `<div class="osa-empty">${esc(t('osa.searching'))}</div>`;
  try {
    const r = await fetch(`/api/osa/search?q=${encodeURIComponent(q)}&schema=${encodeURIComponent(schema || '')}&limit=20`);
    const j = await r.json();
    if (j.error) throw new Error(j.error);
    renderOsaResults(q, j.results, j.total);
  } catch (err) {
    $('#osaResults').innerHTML = `<div class="osa-err">${esc(err.message)}</div>`;
  }
}
on('#osaSearch', 'click', () => osaSearch($('#osaQuery').value));
on('#osaQuery', 'keydown', e => { if (e.key === 'Enter') { e.preventDefault(); osaSearch($('#osaQuery').value); } });
on('#osaResults', 'click', async e => {
  const b = e.target.closest('[data-osaadd]');
  if (!b || !requireCase()) return;
  b.disabled = true; const old = b.textContent; b.textContent = t('osa.adding');
  try {
    const j = await apiPost('/api/osa/import', { ids: [b.dataset.osaadd] });
    $('#stat').textContent = t('osa.added', { e: j.entities, nodes: j.nodes, links: j.links, updated: j.updated });
    await reloadData();
    b.textContent = '✓';
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
    b.disabled = false; b.textContent = old;
  }
});

/* from the card of a person or company: search the name on OpenSanctions */
const OSA_SCHEMA_OF_TYPE = { name: 'Person', target: 'Person', organization: 'Company', company: 'Company',
  ftmorganization: 'Organization', publicbody: 'PublicBody', legalentity: 'LegalEntity', vessel: 'Vessel', airplane: 'Airplane' };
on('#modal-osa', 'click', () => {
  if (!modalNode) return;
  const d = modalNode.data();
  const name = (d.label_orig || d.label || '').replace(/\s*\(\d{2}\/\d{2}\/\d{4}\)\s*$/, '');
  closeModal();
  const box = $('#osaResults');
  if (box) box.scrollIntoView({ block: 'nearest' });
  osaSearch(name, OSA_SCHEMA_OF_TYPE[d.ntype] || '');
});
loadOsaConf();

/* ======================= EPIEOS (paid search) ======================= */
let epConf = null, epSearches = {}, epPending = null;
const EP_MODULES_KNOWN = ['flickr', 'notion', 'gravatar', 'trello', 'hibp', 'foursquare', 'etsy', 'chess', 'substack',
  'mapstr', 'dropbox', 'google', 'holehe', 'skype', 'plex', 'linkedin', 'nikerunclub', 'fitbit', 'github', 'duolingo',
  'adobe', 'runkeeper', 'runtastic', 'samsung', 'strava', 'vivino', 'facebook', 'protonmail', 'phonechecker'];

function isEpieosJson(obj) {
  if (!obj || typeof obj !== 'object') return false;
  if (obj.epieos && typeof obj.epieos === 'object' && obj.epieos.result) return true;
  const r = obj.result;
  if (!r || typeof r !== 'object' || Array.isArray(r)) return false;
  const keys = Object.keys(r);
  return keys.length > 0 && keys.every(k => EP_MODULES_KNOWN.includes(k));
}

/* email or phone? ('' = not recognisable) */
function epKindOf(q) {
  q = (q || '').trim();
  if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(q)) return 'email';
  if (/^\+?[0-9][0-9\s().\-]{5,}$/.test(q)) return 'phone';
  return '';
}

function epCreditsText(c) {
  return (c && c.credits != null) ? t('ep.credits', { n: c.credits }) : t('ep.creditsUnknown');
}

function syncEpSide() {
  const c = epConf || {};
  const sw = $('#epSwitch'), st = $('#epSideStatus');
  if (sw) sw.checked = !!c.enabled;
  if (st) {
    st.textContent = !c.enabled ? t('ep.off') : !c.has_key ? t('ep.noKey')
      : t('ep.on', { ep: (c.endpoint || '').replace(/^https?:\/\//, ''), pack: c.pack || 'osinter', cr: epCreditsText(c) });
    st.className = 'ai-side-st ' + (c.ready ? 'ok' : 'off');
  }
  const q = $('#epQuery'), b = $('#epSearch');
  if (q) q.disabled = !c.ready;
  if (b) b.disabled = !c.ready;
  renderEpSearches();
}

async function loadEpConf() {
  try {
    const r = await fetch('/api/epieos/config');
    epConf = r.ok ? await r.json() : null;
  } catch (_) { epConf = null; }
  await loadEpSearches();
  syncEpSide();
}

async function loadEpSearches() {
  try {
    const r = await fetch('/api/epieos/searches');
    epSearches = r.ok ? await r.json() : {};
  } catch (_) { epSearches = {}; }
}

/* list of the searches saved in the case (click = opens the node) */
function renderEpSearches() {
  const box = $('#epResults');
  if (!box) return;
  const rows = [];
  Object.entries(epSearches).forEach(([anchor, list]) => list.forEach(s => rows.push({ anchor, ...s })));
  if (!rows.length) { box.innerHTML = ''; return; }
  rows.sort((x, y) => (y.fetched_at || '').localeCompare(x.fetched_at || ''));
  box.innerHTML = rows.slice(0, 30).map(s => `
    <div class="ep-r cp-node" data-node="${esc(s.anchor)}" title="${esc(t('ep.openNode'))}">
      <b dir="auto">${esc(s.query)}</b>
      <small>${esc(s.kind)} · ${esc(s.pack || '')} · ${esc(t('ep.modulesFound', { n: (s.modules || []).length }))}${s.fetched_at ? ' · ' + esc(s.fetched_at) : ''}</small>
    </div>`).join('');
}
on('#epResults', 'click', e => {
  const r = e.target.closest('[data-node]');
  if (!r || !cy) return;
  const n = cy.getElementById(r.dataset.node);
  if (n && n.length) { cy.animate({ center: { eles: n }, zoom: Math.max(cy.zoom(), 1.2) }, { duration: 300 }); openModal(n); }
});

on('#epSwitch', 'change', async e => {
  const want = e.target.checked;
  if (want && !confirm(t('ep.warn'))) { e.target.checked = false; return; }
  try {
    epConf = await apiPost('/api/epieos/config', { enabled: want });
    $('#stat').textContent = want ? t('ep.switchedOn') : t('ep.switchedOff');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
  syncEpSide();
});

function renderEpPacks(packs) {
  const box = $('#epc-packs'), dl = $('#epc-pack-list');
  if (!box) return;
  if (dl) dl.innerHTML = (packs || []).map(p => `<option value="${esc(p.pack)}">`).join('');
  if (!packs || !packs.length) { box.innerHTML = `<span>${esc(t('epcfg.noPacks'))}</span>`; return; }
  box.innerHTML = packs.map(p => `<div><b>${esc(p.pack)}</b> · ` +
    Object.entries(p.kinds || {}).map(([k, mods]) => `${esc(k)}: ${mods.length}`).join(' · ') +
    `<div class="ep-mods">${Object.entries(p.kinds || {}).map(([k, mods]) =>
      mods.map(m => `<span class="tag">${esc(k === 'phone' ? '☎ ' : '✉ ')}${esc(m)}</span>`).join('')).join('')}</div></div>`).join('');
}

function openEpConfig() {
  const c = epConf || {};
  $('#epc-enabled').checked = !!c.enabled;
  $('#epc-endpoint').value = c.endpoint || '';
  $('#epc-key').value = ''; $('#epc-key').type = 'password';
  $('#epc-key').placeholder = c.has_key ? t('aicfg.keyKeep', { h: c.key_hint }) : t('aicfg.keyNone');
  $('#epc-pack').value = c.pack || 'osinter';
  $('#epc-timeout').value = c.timeout || 120;
  renderEpPacks(c.packs);
  const r = $('#epc-test-res'); r.textContent = c.credits != null ? epCreditsText(c) : ''; r.className = 'aic-test';
  $('#epmodal').hidden = false;
}
function epConfPayload() {
  const p = { enabled: $('#epc-enabled').checked, endpoint: $('#epc-endpoint').value.trim(),
              pack: $('#epc-pack').value.trim(), timeout: $('#epc-timeout').value };
  const k = $('#epc-key').value.trim();
  if (k) p.api_key = k;
  return p;
}
async function saveEpConfig() {
  const btn = $('#epmodal-save');
  btn.disabled = true;
  try {
    if ($('#epc-enabled').checked && !(epConf && epConf.enabled) && !confirm(t('ep.warn'))) return;
    epConf = await apiPost('/api/epieos/config', epConfPayload());
    $('#stat').textContent = t('epcfg.saved');
    $('#epmodal').hidden = true;
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally { btn.disabled = false; syncEpSide(); }
}
/* GET /schema: packs and modules available for the key (free) */
async function readEpSchema() {
  const r = $('#epc-test-res'), btn = $('#epmodal-schema');
  btn.disabled = true; r.className = 'aic-test'; r.textContent = '…';
  try {
    epConf = await apiPost('/api/epieos/config', epConfPayload());
    $('#epc-key').value = '';
    $('#epc-key').placeholder = epConf.has_key ? t('aicfg.keyKeep', { h: epConf.key_hint }) : t('aicfg.keyNone');
    const j = await apiPost('/api/epieos/schema', {});
    epConf.packs = j.packs || [];
    if (j.credits != null) epConf.credits = j.credits;
    renderEpPacks(epConf.packs);
    r.className = 'aic-test ok'; r.textContent = t('epcfg.schemaOk', { n: epConf.packs.length });
  } catch (err) {
    r.className = 'aic-test err'; r.textContent = t('epcfg.schemaErr', { e: err.message });
  } finally { btn.disabled = false; syncEpSide(); }
}
on('#epSettings', 'click', openEpConfig);
on('#epmodal-save', 'click', saveEpConfig);
on('#epmodal-schema', 'click', readEpSchema);
on('#epmodal-close', 'click', () => { $('#epmodal').hidden = true; });
on('#epmodal', 'click', e => { if (e.target.id === 'epmodal' && !dragEnd('epmodal')) $('#epmodal').hidden = true; });
on('#epc-key-eye', 'click', () => { const k = $('#epc-key'); k.type = k.type === 'password' ? 'text' : 'password'; });

/* modules of the pack for the identifier type: from the schema read with the
   key, otherwise the known list of the osinter pack */
function epModulesFor(kind) {
  const c = epConf || {};
  const p = (c.packs || []).find(x => x.pack === (c.pack || 'osinter'));
  const mods = p && p.kinds && p.kinds[kind];
  return (mods && mods.length) ? mods : ((c.modules || {})[kind] || []);
}

/* confirmation window: identifier, modules (can be deselected), credits.
   No search starts without the click on «Search». */
function epConfirm(query, kind, anchor) {
  epPending = { query, kind, anchor };
  $('#epconfirm-query').textContent = query;
  $('#epconfirm-kind').textContent = kind === 'email' ? t('ep.kindEmail') : t('ep.kindPhone');
  const c = epConf || {};
  const again = (epSearches[anchor] || []).some(s => s.kind === kind);
  $('#epconfirm-cost').textContent = t('ep.confirmCost', { pack: c.pack || 'osinter', cr: epCreditsText(c) }) +
    (again ? ' ' + t('ep.confirmAgain') : '');
  const mods = epModulesFor(kind);
  $('#epconfirm-mods').innerHTML = mods.map(m =>
    `<label><input type="checkbox" value="${esc(m)}" checked> ${esc(m)}</label>`).join('');
  const r = $('#epconfirm-res'); r.textContent = ''; r.className = 'aic-test';
  $('#epconfirm-run').disabled = false;
  $('#epconfirm').hidden = false;
}
on('#epconfirm-all', 'click', () => $('#epconfirm-mods').querySelectorAll('input').forEach(i => { i.checked = true; }));
on('#epconfirm-none', 'click', () => $('#epconfirm-mods').querySelectorAll('input').forEach(i => { i.checked = false; }));
on('#epconfirm-close', 'click', () => { $('#epconfirm').hidden = true; epPending = null; });
on('#epconfirm-cancel', 'click', () => { $('#epconfirm').hidden = true; epPending = null; });
on('#epconfirm', 'click', e => { if (e.target.id === 'epconfirm' && !dragEnd('epconfirm')) { $('#epconfirm').hidden = true; epPending = null; } });
on('#epconfirm-run', 'click', async () => {
  if (!epPending) return;
  const all = [...$('#epconfirm-mods').querySelectorAll('input')];
  const chosen = all.filter(i => i.checked).map(i => i.value);
  const r = $('#epconfirm-res');
  if (!chosen.length) { r.className = 'aic-test err'; r.textContent = t('ep.noModules'); return; }
  const body = { query: epPending.query, kind: epPending.kind, anchor: epPending.anchor };
  if (chosen.length < all.length) body.modules = chosen;
  const btn = $('#epconfirm-run');
  btn.disabled = true; r.className = 'aic-test'; r.textContent = t('ep.searching');
  try {
    const j = await apiPost('/api/epieos/search', body);
    if (epConf) epConf.credits = j.credits;
    $('#epconfirm').hidden = true; epPending = null;
    await loadEpSearches();
    await reloadData();
    syncEpSide();
    $('#stat').textContent = t('ep.done', { q: j.query, m: (j.modules || []).length, r: j.records, cr: epCreditsText(epConf) });
  } catch (err) {
    r.className = 'aic-test err'; r.textContent = err.message;
    btn.disabled = false;
    loadEpConf();                                 // the credits may have changed
  }
});

/* side box: creates (or finds) the identifier's node and asks for confirmation */
async function epSearchFromBox(q) {
  q = (q || '').trim();
  const kind = epKindOf(q);
  if (!kind) { $('#stat').textContent = t('ep.badQuery'); return; }
  if (!requireCase()) return;
  try {
    const j = await apiPost('/api/node/add', { ntype: kind, value: q });
    await reloadData();
    epConfirm(q, kind, j.id);
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
}
on('#epSearch', 'click', () => epSearchFromBox($('#epQuery').value));
on('#epQuery', 'keydown', e => { if (e.key === 'Enter') { e.preventDefault(); epSearchFromBox($('#epQuery').value); } });

/* from the card of an email or a phone */
on('#modal-ep', 'click', () => {
  if (!modalNode) return;
  const d = modalNode.data();
  const kind = d.ntype === 'email' ? 'email' : d.ntype === 'phone' ? 'phone' : '';
  if (!kind) return;
  const q = d.ntype === 'email' ? (d.label_orig || d.label) : (d.label_orig || d.label);
  closeModal();
  epConfirm((q || '').trim(), kind, d.id);
});

/* JSON file with a saved Epieos response: no calls, no credits */
async function epImportFile(filename, text, obj) {
  if (!requireCase()) return;
  const w = obj.epieos || {};
  let q = w.query || '';
  if (!q) {
    const mods = Object.values(obj.result || {});
    const m = mods.find(x => x && typeof x === 'object' && x.query);
    q = m ? String(m.query) : '';
  }
  if (!q) {
    const mm = /(?:export|ricerca|search|lookup)[ _-]+(.+)\.json$/i.exec(filename);
    q = mm ? mm[1] : '';
  }
  q = (q || '').trim();
  const kind = w.kind || epKindOf(q);
  if (!q || !kind) { alert(t('ep.fileNoQuery')); return; }
  if (!confirm(t('ep.fileImport', { q, f: filename }))) return;
  try {
    const n = await apiPost('/api/node/add', { ntype: kind, value: q });
    const j = await apiPost('/api/epieos/import', { anchor: n.id, filename, content: text, query: q, kind });
    await loadEpSearches();
    await reloadData();
    syncEpSide();
    $('#stat').textContent = t('ep.imported', { q: j.query, m: (j.modules || []).length, r: j.records });
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
}
loadEpConf();
on('#aimodal-save', 'click', saveAiConfig);
on('#aimodal-test', 'click', testAiConfig);
on('#aimodal-close', 'click', () => { $('#aimodal').hidden = true; });
on('#aimodal', 'click', e => { if (e.target.id === 'aimodal' && !dragEnd('aimodal')) $('#aimodal').hidden = true; });
on('#aic-key-eye', 'click', () => {
  const k = $('#aic-key'); k.type = k.type === 'password' ? 'text' : 'password';
});
/* switch in the side bar: turns on/off at once (saved in chatbot.conf) */
on('#aiSwitch', 'change', async e => {
  const want = e.target.checked;
  try {
    aiConf = await apiPost('/api/ai/config', { enabled: want });
    $('#stat').textContent = want ? t('ai.switchedOn') : t('ai.switchedOff');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
  syncAiSide();
});
loadAiConf();

/* ================= MANUAL CHANGES PANEL ================= */
let manData = { added: [], links: [], labels: [] };   // last list received
let manShowAll = false;                   // false = only the first MAN_LIMIT entries
const MAN_LIMIT = 8;

async function openManual() {
  const box = $('#manmodal');
  if (!box) return;
  $('#manmodal-body').innerHTML = `<div class="empty">${esc(t('err.loading'))}</div>`;
  box.hidden = false;
  try {
    const r = await fetch('/api/manual');
    if (r.status === 404) throw new Error(t('err.restartServer'));
    manData = await r.json();
    renderManual();
  } catch (err) {
    $('#manmodal-body').innerHTML = `<div class="empty">${esc(t('err.generic', { e: err.message }))}</div>`;
    $('#manmodal-sub').textContent = '';
  }
}

/* Readable label of a node: from the graph if there, otherwise the id. */
const nodeLabel = id => {
  const n = cy && cy.getElementById(id);
  return (n && n.length && n.data('label')) || id;
};

/* Draws the list applying the text filter and the row limit.
   With many changes the list stays short: the button shows everything. */
function renderManual() {
  const q = (($('#man-filter') && $('#man-filter').value) || '').trim().toLowerCase();
  const hit = s => !q || String(s || '').toLowerCase().includes(q);

  const added = (manData.added || []).filter(a =>
    hit(a.label) || hit(a.id) || hit(a.platform) || hit(nodeLabel(a.parent)) || hit(a.url));
  const links = (manData.links || []).filter(l =>
    hit(nodeLabel(l.a)) || hit(nodeLabel(l.b)) || hit(l.a) || hit(l.b));
  const labels = (manData.labels || []).filter(x =>
    hit(x.label) || hit(x.orig) || hit(x.id) || hit(x.ntype));

  const totAll = (manData.added || []).length + (manData.links || []).length +
                 (manData.labels || []).length;
  const totHit = added.length + links.length + labels.length;
  $('#manmodal-sub').textContent =
    t('man.sub', { a: (manData.added || []).length, b: (manData.links || []).length,
                   c: (manData.labels || []).length });

  const cut = arr => (manShowAll ? arr : arr.slice(0, MAN_LIMIT));
  const shownA = cut(added), shownL = cut(links), shownE = cut(labels);
  const shown = shownA.length + shownL.length + shownE.length;

  // "show all / show less" button
  const btn = $('#man-showall');
  if (btn) {
    const needed = totHit > shown || manShowAll;
    btn.hidden = !needed;
    btn.textContent = manShowAll ? t('man.showLess') : t('man.showAllBtn', { n: totHit });
  }

  let h = '';
  if (q && !totHit) {
    h = `<div class="empty">${esc(t('man.noMatch'))}</div>`;
  } else {
    h += `<div class="mn-cat">${esc(t('man.addedNodes'))}</div>`;
    h += shownA.length ? shownA.map(a => `
        <div class="dl-row">
          <div class="dl-info">
            <div class="dl-lab">${esc(a.label || a.id)}</div>
            <div class="dl-meta">${esc([a.ntype, a.platform].filter(Boolean).join(' · '))}${a.at ? ' · ' + esc(a.at) : ''}</div>
            <div class="dl-tg">${esc(t('man.connectedTo'))} <span>${esc(nodeLabel(a.parent))}</span></div>
            ${a.url ? `<div class="mn-url">${esc(a.url)}</div>` : ''}
          </div>
          <button class="dl-btn danger" data-delnode="${esc(a.id)}">${esc(t('btn.delete'))}</button>
        </div>`).join('')
      : `<div class="empty">${esc(t('man.noNodes'))}</div>`;

    h += `<div class="mn-cat">${esc(t('man.createdLinks'))}</div>`;
    h += shownL.length ? shownL.map(l => `
        <div class="dl-row">
          <div class="dl-info">
            <div class="dl-lab mn-link">
              <span>${esc(nodeLabel(l.a))}</span><i>${ARROW_SYM[l.arrow || 'none']}</i><span>${esc(nodeLabel(l.b))}</span>
              ${l.label ? `<span class="mn-edge-lbl">${esc(l.label)}</span>` : ''}
            </div>
            <div class="dl-meta">${l.at ? esc(l.at) : ''}</div>
          </div>
          ${cy && cy.getElementById(l.edge_id || '').length
            ? `<button class="dl-btn" data-editedge="${esc(l.edge_id)}">${esc(t('edge.editBtn'))}</button>` : ''}
          <button class="dl-btn danger" data-dellink="${esc(l.a)}|${esc(l.b)}"
                  data-edge="${esc(l.edge_id || '')}">${esc(t('btn.delete'))}</button>
        </div>`).join('')
      : `<div class="empty">${esc(t('man.noLinks'))}</div>`;

    h += `<div class="mn-cat">${esc(t('man.renamedLabels'))}</div>`;
    h += shownE.length ? shownE.map(x => `
        <div class="dl-row">
          <div class="dl-info">
            <div class="dl-lab mn-link">
              <span>${esc(x.orig || x.id)}</span><i>→</i><span>${esc(x.label)}</span>
            </div>
            <div class="dl-meta">${esc([x.ntype].filter(Boolean).join(' · '))}${x.at ? ' · ' + esc(x.at) : ''}</div>
          </div>
          <button class="dl-btn" data-unrename="${esc(x.id)}">${esc(t('man.restoreLabel'))}</button>
        </div>`).join('')
      : `<div class="empty">${esc(t('man.noLabels'))}</div>`;

    if (totHit > shown) {
      h += `<div class="mn-more">${esc(t('man.showing', { shown, total: totHit }))}</div>`;
    }
  }
  void totAll;
  $('#manmodal-body').innerHTML = h;
}

on('#showManual', 'click', () => { manShowAll = false; if ($('#man-filter')) $('#man-filter').value = ''; openManual(); });
on('#man-filter', 'input', () => { manShowAll = false; renderManual(); });
on('#man-showall', 'click', () => { manShowAll = !manShowAll; renderManual(); });
on('#manmodal-close', 'click', () => { $('#manmodal').hidden = true; });
on('#manmodal', 'click', e => { if (e.target.id === 'manmodal' && !dragEnd('manmodal')) $('#manmodal').hidden = true; });

/* ================= TRANSLITERATION DICTIONARY =================
   List of the non-Latin words (pending, by hand, from the AI) with the Latin
   form editable in the row. Each save changes translit_version on the
   server: the graph is rebuilt and the Latin nodes are updated (reloadData). */
const DICT_LIMIT = 200;
let dictRows = [], dictOffset = 0, dictMore = false, dictTimer = null;
let dictLast = { counts: {}, engine: '' };          // to redraw on language change

async function openDict() {
  const box = $('#dictmodal');
  if (!box) return;
  box.hidden = false;
  dictOffset = 0;
  await loadDict(false);
  if ($('#dict-filter')) $('#dict-filter').focus();
}

async function loadDict(append) {
  const q = (($('#dict-filter') && $('#dict-filter').value) || '').trim();
  const src = ($('#dict-source') && $('#dict-source').value) || '';
  const url = `/api/translit/words?q=${encodeURIComponent(q)}&source=${encodeURIComponent(src)}` +
              `&limit=${DICT_LIMIT}&offset=${dictOffset}`;
  if (!append) $('#dictmodal-body').innerHTML = `<div class="empty">${esc(t('err.loading'))}</div>`;
  try {
    const r = await fetch(url);
    if (r.status === 404) throw new Error(t('err.restartServer'));
    const j = await r.json();
    if (j.error) throw new Error(j.error);
    dictRows = append ? dictRows.concat(j.rows || []) : (j.rows || []);
    dictMore = !!j.more;
    renderDict(j.counts || {}, j.engine || '');
  } catch (err) {
    $('#dictmodal-body').innerHTML = `<div class="empty">${esc(t('err.generic', { e: err.message }))}</div>`;
  }
}

const DICT_SRC_KEY = { manual: 'dict.srcManual', ai: 'dict.srcAi', pending: 'dict.srcPending' };

function renderDict(counts, engine) {
  dictLast = { counts: counts || {}, engine: engine || '' };
  $('#dictmodal-sub').textContent = t('dict.sub', {
    p: counts.pending || 0, m: counts.manual || 0, a: counts.ai || 0, engine: engine || '—' });
  const more = $('#dict-more');
  if (more) more.hidden = !dictMore;
  if (!dictRows.length) {
    $('#dictmodal-body').innerHTML = `<div class="empty">${esc(t('dict.empty'))}</div>`;
    return;
  }
  $('#dictmodal-body').innerHTML = dictRows.map(r => `
    <div class="dict-row" data-word="${esc(r.word)}">
      <div class="dict-word" dir="auto">${esc(r.word)}<span class="dict-script">${esc((r.script || '').toLowerCase())}</span></div>
      <input class="dict-val" value="${esc(r.value || '')}" autocomplete="off" spellcheck="false"
             placeholder="${esc(r.auto ? t('dict.autoPh', { v: r.auto }) : '')}">
      <span class="dict-src dict-src-${esc(r.source)}">${esc(t(DICT_SRC_KEY[r.source] || 'dict.srcPending'))}</span>
      <button class="mini" data-dictsave title="${esc(t('dict.save'))}">💾</button>
      <button class="mini danger" data-dictdel title="${esc(t('dict.delete'))}">🗑</button>
    </div>`).join('');
}

async function dictSave(rowEl) {
  const word = rowEl.dataset.word;
  const inp = rowEl.querySelector('.dict-val');
  const value = (inp.value || '').trim();
  const r = dictRows.find(x => x.word === word);
  if (r && (r.value || '') === value) return;          // nothing to save
  inp.disabled = true;
  try {
    const j = await apiPost('/api/translit/set', { word, value });
    if (r) { r.value = j.value; r.source = j.source; }
    const badge = rowEl.querySelector('.dict-src');
    badge.className = `dict-src dict-src-${j.source}`;
    badge.textContent = t(DICT_SRC_KEY[j.source]);
    rowEl.classList.add('saved');
    setTimeout(() => rowEl.classList.remove('saved'), 1200);
    $('#stat').textContent = value ? t('dict.saved', { w: word, v: value }) : t('dict.cleared', { w: word });
    await reloadData();                                // the Latin nodes must be redone
    refreshTranslitBtn();
  } catch (err) {
    alert(t('err.generic', { e: err.message }));
  } finally {
    inp.disabled = false;
  }
}

on('#showDict', 'click', openDict);

/* "separate Latin nodes" switch: node attribute (default) or
   twin nodes as in the original; global setting on the server */
async function syncTranslitModeSwitch() {
  const sw = $('#translitNodes');
  if (!sw) return;
  try {
    const r = await fetch('/api/translit/mode');
    const j = await r.json();
    TRANSLIT_MODE = j.mode || 'attribute';
    sw.checked = TRANSLIT_MODE === 'nodes';
  } catch (_) { /* old server: the default stays */ }
}
on('#translitNodes', 'change', async e => {
  const mode = e.target.checked ? 'nodes' : 'attribute';
  try {
    const j = await apiPost('/api/translit/mode', { mode });
    TRANSLIT_MODE = j.mode;
    $('#stat').textContent = t(mode === 'nodes' ? 'translit.modeNodesOn' : 'translit.modeNodesOff');
    await reloadData();
    if (cy) cy.nodes().forEach(n => n.data('disp', dispOf(n.data())));
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
    e.target.checked = !e.target.checked;
  }
});
syncTranslitModeSwitch();
on('#dictmodal-close', 'click', () => { $('#dictmodal').hidden = true; });
on('#dictmodal', 'click', e => { if (e.target.id === 'dictmodal' && !dragEnd('dictmodal')) $('#dictmodal').hidden = true; });
on('#dict-filter', 'input', () => {
  clearTimeout(dictTimer);
  dictTimer = setTimeout(() => { dictOffset = 0; loadDict(false); }, 250);
});
on('#dict-source', 'change', () => { dictOffset = 0; loadDict(false); });
on('#dict-more', 'click', () => { dictOffset += DICT_LIMIT; loadDict(true); });
on('#dict-collect', 'click', async () => {
  try {
    const j = await apiPost('/api/translit/collect', {});
    $('#stat').textContent = t('dict.collectDone', { n: j.added, t: j.total });
    dictOffset = 0;
    await loadDict(false);
    refreshTranslitBtn();
  } catch (err) { alert(t('err.generic', { e: err.message })); }
});
on('#dict-export', 'click', () => { window.open('/api/translit/export', '_blank'); });
on('#dict-import', 'change', async e => {
  const f = e.target.files && e.target.files[0];
  if (!f) return;
  try {
    const text = await f.text();
    const j = await apiPost('/api/translit/import', { text });
    $('#stat').textContent = t('dict.imported', { n: j.imported, s: j.skipped });
    if (j.errors && j.errors.length) console.warn('dizionario, righe scartate:', j.errors);
    dictOffset = 0;
    await loadDict(false);
    await reloadData();
    refreshTranslitBtn();
  } catch (err) { alert(t('err.generic', { e: err.message })); }
  finally { e.target.value = ''; }
});
on('#dictmodal-body', 'click', async e => {
  const row = e.target.closest('.dict-row');
  if (!row) return;
  if (e.target.closest('[data-dictsave]')) { await dictSave(row); return; }
  if (e.target.closest('[data-dictdel]')) {
    if (!confirm(t('dict.confirmDel', { w: row.dataset.word }))) return;
    try {
      await apiPost('/api/translit/delete', { word: row.dataset.word });
      dictRows = dictRows.filter(x => x.word !== row.dataset.word);
      row.remove();
      if (!dictRows.length) renderDict({}, '');
      await reloadData();
      refreshTranslitBtn();
    } catch (err) { alert(t('err.generic', { e: err.message })); }
  }
});
on('#dictmodal-body', 'keydown', e => {
  if (e.key !== 'Enter' || !e.target.classList.contains('dict-val')) return;
  e.preventDefault();
  dictSave(e.target.closest('.dict-row'));
});

on('#manmodal-body', 'click', async e => {
  const delNode = e.target.closest('[data-delnode]');
  const delLink = e.target.closest('[data-dellink]');
  const unRen = e.target.closest('[data-unrename]');
  const edEdge = e.target.closest('[data-editedge]');
  if (edEdge) {
    $('#manmodal').hidden = true;
    const ed = cy.getElementById(edEdge.dataset.editedge);
    if (ed.length) openEdgeModal(ed);
    return;
  }
  try {
    if (delNode) {
      const id = delNode.dataset.delnode;
      if (!confirm(t('man.confirmNode', { label: nodeLabel(id) }))) return;
      await apiPost('/api/node/remove_manual', { id });
      [visibleNodes, expanded, selected, pinned, placed].forEach(s => s.delete(id));
      cy.getElementById(id).remove();
      INDEX = INDEX.filter(it => it.id !== id);
      ADJ = null;
      renderSel(); refresh(false); buildLegend(); buildCatFilters(); buildDegFilter();
      $('#stat').textContent = t('stat.manualNodeDeleted');
    } else if (delLink) {
      const [a, b] = delLink.dataset.dellink.split('|');
      if (!confirm(t('man.confirmLink', { a: nodeLabel(a), b: nodeLabel(b) }))) return;
      const j = await apiPost('/api/link/delete', { id: delLink.dataset.edge || '', a, b });
      const eid = j.edge_id || delLink.dataset.edge;
      if (eid) {
        const ed = cy.getElementById(eid);
        if (ed.length) {
          [a, b].forEach(id => {
            const m = cy.getElementById(id);
            if (m.length) m.data('deg', Math.max(0, (m.data('deg') || 0) - 1));
          });
          ed.remove();
        }
      }
      ADJ = null;
      refresh(false); buildDegFilter();
      $('#stat').textContent = t('stat.linkDeleted');
    } else if (unRen) {
      const id = unRen.dataset.unrename;
      if (!confirm(t('man.confirmLabel'))) return;
      await apiPost('/api/node/label', { id, label: '' });
      await syncGraph();               // cancelling the rename skips the merge
      $('#stat').textContent = t('stat.renameReset');
    } else return;
    openManual();                       // reload the list
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
});

/* ================= DELETED NODES PANEL ================= */
async function openDeleted() {
  const box = $('#delmodal');
  if (!box) return;
  $('#delmodal-body').innerHTML = `<div class="empty">${esc(t('err.loading'))}</div>`;
  box.hidden = false;
  try {
    const r = await fetch('/api/deleted');
    if (r.status === 404) throw new Error(t('err.restartServer'));
    const j = await r.json();
    renderDeleted(j.items || []);
  } catch (err) {
    $('#delmodal-body').innerHTML = `<div class="empty">${esc(t('err.generic', { e: err.message }))}</div>`;
    $('#delmodal-sub').textContent = '';
  }
}

function renderDeleted(items) {
  $('#delmodal-sub').textContent = items.length
    ? t('del.sub', { n: items.length }) : t('del.noneSub');
  $('#delmodal-all').disabled = !items.length;
  if (!items.length) {
    $('#delmodal-body').innerHTML = `<div class="empty">${esc(t('del.none'))}</div>`;
    return;
  }
  $('#delmodal-body').innerHTML = items.map(it => {
    const tg = (it.targets || []).length
      ? `<div class="dl-tg">${esc(t('del.from'))} ` +
        (it.targets || []).map(x => `<span>${esc(x)}</span>`).join('') + '</div>'
      : `<div class="dl-tg dl-none">${esc(t('del.unknownOrigin'))}</div>`;
    const meta = [it.ntype, it.platform].filter(Boolean).map(esc).join(' · ');
    return `<div class="dl-row">
        <div class="dl-info">
          <div class="dl-lab">${esc(it.label || it.id)}</div>
          <div class="dl-meta">${meta}${it.at ? ' · ' + esc(it.at) : ''}</div>
          ${tg}
        </div>
        <button class="dl-btn" data-restore="${esc(it.id)}">${esc(t('del.restore'))}</button>
      </div>`;
  }).join('');
}

/* Live restore: the nodes come back into the graph without reloading the page,
   so the current view (open nodes, positions, zoom) stays intact. */
async function restoreDeleted(payload, msg) {
  try {
    const j = await apiPost('/api/node/restore', payload);
    const nodes = j.nodes || [], edges = j.edges || [];
    const back = [];

    cy.batch(() => {
      nodes.forEach(n => { addNodeToCy(n); back.push(n.id); });
      edges.forEach(e => {
        if (cy.getElementById(e.id).length) return;
        const s = cy.getElementById(e.source), tt = cy.getElementById(e.target);
        if (s.length && tt.length) cy.add({ group: 'edges', data: Object.assign({}, e) });
      });
    });

    // degrees are recomputed from the links actually present
    const touched = new Set(back);
    edges.forEach(e => { touched.add(e.source); touched.add(e.target); });
    touched.forEach(id => {
      const m = cy.getElementById(id);
      if (m.length) m.data('deg', m.connectedEdges().length);
    });

    // the restored nodes become visible, next to a neighbour already in view
    const eles = cy.collection();
    back.forEach(id => {
      const n = cy.getElementById(id);
      if (!n.length) return;
      visibleNodes.add(id);
      if (!placed.has(id)) {
        const anchor = n.neighborhood('node').filter(m => placed.has(m.id()))[0];
        if (anchor) {
          const p = anchor.position();
          const a = Math.random() * Math.PI * 2;
          n.position({ x: p.x + Math.cos(a) * 150, y: p.y + Math.sin(a) * 150 });
          placed.add(id);
        }
      }
      eles.merge(n);
    });

    ADJ = null;
    refresh(true);
    buildLegend(); buildCatFilters(); buildDegFilter();
    if (eles.length) {
      eles.addClass('fresh');
      setTimeout(() => eles.removeClass('fresh'), 2000);
      bringIntoView(eles);
    }
    openDeleted();                              // update the list of deleted nodes
    $('#stat').textContent = typeof msg === 'function' ? msg(j.restored) : msg;
  } catch (err) {
    alert(t('err.restoreFailed', { e: err.message }));
  }
}

on('#showDeleted', 'click', openDeleted);
on('#delmodal-close', 'click', () => { $('#delmodal').hidden = true; });
on('#delmodal', 'click', e => { if (e.target.id === 'delmodal' && !dragEnd('delmodal')) $('#delmodal').hidden = true; });
on('#delmodal-body', 'click', e => {
  const b = e.target.closest('[data-restore]');
  if (!b) return;
  restoreDeleted({ id: b.dataset.restore }, () => t('del.restored'));
});
on('#delmodal-all', 'click', () => {
  if (!confirm(t('del.confirmAll'))) return;
  restoreDeleted({ all: true }, n => t('del.restoredAll', { n }));
});

/* ================= IMAGE LIGHTBOX ================= */
function openLightbox(src) {
  const lb = $('#lightbox');
  if (!lb || !src) return;
  $('#lb-img').src = src;
  $('#lb-open').href = src;
  lb.hidden = false;
}
function closeLightbox() {
  const lb = $('#lightbox');
  if (!lb) return;
  lb.hidden = true;
  $('#lb-img').src = '';
}
// click on any image in the card -> enlargement
on('#modal-body', 'click', e => {
  if (e.target.tagName === 'IMG' && !e.target.closest('.chip')) {
    e.stopPropagation();
    openLightbox(e.target.currentSrc || e.target.src);
  }
});
on('#lightbox', 'click', e => { if (e.target.id !== 'lb-open') closeLightbox(); });
on('#lb-close', 'click', closeLightbox);

/* ================= LEGEND & FILTERS ================= */
function buildLegend() {
  const l = $('#legend');
  if (!l || !cy) return;
  const used = [...new Set(cy.nodes().map(n => n.data('ntype')))];
  const fused = cy.nodes().filter(n => (n.data('merged') || 1) > 1).length;
  const seed = cy.nodes().some(n => n.data('seed') && n.data('ntype') !== 'target');
  l.innerHTML = used.map(nt =>
      `<span><i style="background:${TYPE_COLOR[nt] || TYPE_COLOR.generic}"></i>` +
      `${esc(groupTitle(nt).replace(/^\S+\s/, ''))}</span>`).join('') +
    (fused ? `<span><i style="background:#f59e0b"></i>${esc(t('card.merged', { n: fused }))}</span>` : '') +
    (seed ? `<span><i class="lg-seed"></i>${esc(t('legend.seed'))}</span>` : '');
}

/* "Links" drop-down: list of the numbers of connections actually present
   in the graph. The selection is EXACT: each entry shows how many nodes have
   precisely that number of links. */
function buildDegFilter() {
  const sel = $('#minDeg');
  if (!sel || !cy) return;
  const counts = new Map();
  cy.nodes().forEach(n => {
    const d = n.data('deg') || 0;
    if (d >= 1) counts.set(d, (counts.get(d) || 0) + 1);
  });
  let html = `<option value="0">${esc(t('opt.all'))}</option>`;
  for (const d of [...counts.keys()].sort((a, b) => a - b)) {
    html += `<option value="${d}">${esc(t('opt.degree', { d, n: counts.get(d) }))}</option>`;
  }
  sel.innerHTML = html;
  sel.value = String(degFilter);
}

/* Category buttons: one for each category present in the graph, with count.
   Click = show/hide all nodes of that category. */
function buildCatFilters() {
  const box = $('#catFilters');
  if (!box || !cy) return;
  const counts = {};
  cy.nodes().forEach(n => { const c = n.data('cat') || 'altro'; counts[c] = (counts[c] || 0) + 1; });
  box.innerHTML = CATEGORIES.filter(c => counts[c.key]).map(c => {
    const off = hiddenCats.has(c.key);
    const lab = catLabel(c.key);
    return `<button class="cat-btn${off ? ' off' : ' on'}" data-cat="${c.key}" ` +
      `style="--cat:${c.color}" title="${esc(t('cat.toggle', { name: lab }))}">` +
      `<i class="cat-dot" style="background:${c.color}"></i>` +
      `<span class="cat-lb">${esc(lab)}</span>` +
      `<span class="cat-n">${counts[c.key]}</span></button>`;
  }).join('');
  syncCatButtons();
}

/* Keys of the categories actually present in the graph. */
function presentCatKeys() {
  const s = new Set();
  cy.nodes().forEach(n => s.add(n.data('cat') || 'altro'));
  return [...s];
}

/* Aligns the button classes to hiddenCats and updates the label of the
   "Hide/Show all" button according to the current state. */
function syncCatButtons() {
  document.querySelectorAll('#catFilters .cat-btn').forEach(b => {
    const off = hiddenCats.has(b.dataset.cat);
    b.classList.toggle('off', off);
    b.classList.toggle('on', !off);
  });
  const tg = $('#catToggleAll');
  if (tg) {
    const keys = presentCatKeys();
    const allHidden = keys.length > 0 && keys.every(k => hiddenCats.has(k));
    tg.textContent = allHidden ? t('btn.showAll') : t('btn.hideAll');
  }
}

/* ================= EVENT HANDLERS ================= */
on('#search', 'input', e => {
  const v = e.target.value;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => searchNodes(v), 160);
});
on('#search', 'keydown', e => {
  if (e.key === 'Enter') { clearTimeout(searchTimer); searchNodes($('#search').value); }
  if (e.key === 'Escape') hideResults();
});
on('#search', 'focus', () => { if ($('#search-results').children.length) $('#search-results').style.display = 'block'; });
on('#searchBtn', 'click', () => { clearTimeout(searchTimer); searchNodes($('#search').value); });
on('#addAll', 'click', showAllMatches);
/* Brings all the target nodes into the graph (without expanding them). */
on('#loadTargets', 'click', () => {
  if (!cy) return;
  const ids = cy.nodes().filter(n => n.data('ntype') === 'target').map(n => n.id());
  if (!ids.length) { $('#stat').textContent = t('stat.noTargets'); return; }
  addToGraph(ids, false);
  runLayout({ fit: true });
  $('#stat').textContent = t('stat.targetsLoaded', { n: ids.length });
});
on('#fuzzy', 'change', e => {
  $('#fuzzyLevel').disabled = !e.target.checked;
  if (!e.target.checked) DIST = new Map();
  searchNodes($('#search').value);
});
on('#fuzzyLevel', 'change', () => searchNodes($('#search').value));

on('#toggleIds', 'change', e => { showIds = e.target.checked; refresh(true); });
on('#depth', 'change', () => refresh(true));
on('#minDeg', 'change', e => {
  degFilter = parseInt(e.target.value, 10) || 0;
  if (!degFilter) degOnly = false;          // without a filter the command is not needed
  syncDegOnlyBtn();
  refresh(true);
});
on('#degOnly', 'click', () => {
  degOnly = !degOnly;
  syncDegOnlyBtn();
  refresh(true);
});

/* ---- language selector ---- */
function buildLangSelector() {
  const sel = $('#langSel');
  if (!sel) return;
  sel.innerHTML = LANGS.map(l =>
    `<option value="${l.code}">${esc(l.name)}</option>`).join('');
  sel.value = LANG;
}
on('#langSel', 'change', e => setLang(e.target.value));

/* Called by setLang(): redraws everything that contains translated text. */
function onLangChange() {
  const sel = $('#langSel');
  if (sel && sel.value !== LANG) sel.value = LANG;   // keeps the selector aligned
  document.querySelectorAll('.edge-props').forEach(b => updateEdgePreview(b.dataset.prefix));
  fillOntoOptions();                               // investigative types in the chosen language
  if (typeof syncOsaSide === 'function') syncOsaSide();   // OpenSanctions status in the chosen language
  if (typeof syncEpSide === 'function') syncEpSide();     // Epieos status in the chosen language
  document.querySelectorAll('select[id$="-edge-ftm"]').forEach(sel => {   // FtM relations
    [...sel.options].forEach(o => { o.textContent = o.value ? `${ftmEdgeLabel(o.value)} · ${ftmEdgeVerb(o.value)}` : t('edge.ftmNone'); });
  });
  if ($('#dictmodal') && !$('#dictmodal').hidden) renderDict(dictLast.counts, dictLast.engine);
  loadGStyle();                                    // link shapes
  if ($('#add-onto-row')) $('#add-onto-row').dataset.kind = '';
  if (!cy) {
    // graph not loaded yet: the dynamic texts of the side bar are
    // translated anyway (otherwise they stayed in Italian)
    const tg = $('#catToggleAll');
    if (tg) tg.textContent = t('btn.hideAll');
    const md = $('#minDeg');
    if (md && md.options[0]) md.options[0].textContent = t('opt.all');
    return;
  }
  buildLegend();
  buildCatFilters();
  buildDegFilter();
  refreshViews($('#viewList') ? $('#viewList').value : '');
  syncDegOnlyBtn();
  syncHiddenBtn();
  syncAddType();
  renderSel();
  refresh(false);
  if (!$('#manmodal').hidden) renderManual();
  syncAiSide();
  if (!$('#addmodal').hidden) $('#addmodal-save').textContent = aiMode ? t('ai.addAll') : t('add.save');
  if (!$('#linkmodal').hidden && linkIds.length > 2) {
    $('#link-multi-hint').textContent =
      t('link.multiHint', { n: linkIds.length, c: linkIds.length * (linkIds.length - 1) / 2 });
  }
  if (!$('#edgemodal').hidden && edgeEditId) {
    const e = cy.getElementById(edgeEditId);
    if (e.length) $('#edg-kind').textContent = t('edge.kind.' + edgeKind(e));
  }  if (modalNode) openModal(modalNode);            // reopens the translated card
  const po = $('#pathonly');
  if (po && !po.hidden) po.textContent = pathOnly ? t('btn.showRest') : t('btn.hideRest');
  refreshTranslitBtn();
}
on('#openMode', 'change', e => setOpenMode(e.target.value));
/* Show/hide a category: IMMEDIATE effect on the graph.
   - switching a category off removes its nodes from the view at once;
   - switching it back on puts them back;
   the button stays red while the category is off.
   It is not a permanent filter: if you later expand a node, its
   links appear anyway (you can switch the category off again to hide them).*/
function hideCat(cat) {
  hiddenCats.add(cat);
  cy.nodes().not('.hidden').forEach(n => {
    if ((n.data('cat') || 'altro') === cat) catHidden.add(n.id());
  });
}
function showCat(cat) {
  hiddenCats.delete(cat);
  [...catHidden].forEach(id => {
    const n = cy.getElementById(id);
    if (!n.length || (n.data('cat') || 'altro') === cat) catHidden.delete(id);
  });
}
on('#catFilters', 'click', e => {
  const b = e.target.closest('.cat-btn');
  if (!b || !cy) return;
  const cat = b.dataset.cat;
  if (hiddenCats.has(cat)) showCat(cat); else hideCat(cat);
  syncCatButtons();
  refresh(false);
});
on('#catToggleAll', 'click', () => {
  if (!cy) return;
  const keys = presentCatKeys();
  const allHidden = keys.length > 0 && keys.every(k => hiddenCats.has(k));
  if (allHidden) keys.forEach(showCat);            // they were all off -> switch them back on
  else keys.forEach(k => { if (!hiddenCats.has(k)) hideCat(k); });   // switch off the ones that are on
  syncCatButtons();
  refresh(false);
});

on('#lyFcose', 'click', () => setLayout('fcose', '#lyFcose'));
on('#lyCircle', 'click', () => setLayout('circle', '#lyCircle'));
on('#lyTree', 'click', () => setLayout('breadthfirst', '#lyTree'));
on('#lyGrid', 'click', () => setLayout('grid', '#lyGrid'));
on('#lyUntangle', 'click', untangle);

on('#expandAll', 'click', () => {
  const ids = [];
  cy.nodes().not('.hidden').forEach(n => {
    expanded.add(n.id()); visibleNodes.add(n.id());
    ids.push(n.id(), ...nbhd(n, depthVal()).map(m => m.id()));
  });
  unhide(ids);                       // expanding everything really shows everything
  refresh(true);
  runLayout({ fit: true });
});
on('#collapseAll', 'click', () => { expanded.clear(); refresh(false); });
on('#clearGraph', 'click', () => {
  expanded.clear(); visibleNodes.clear(); pinned.clear(); placed.clear();
  hiddenNodes.clear(); catHidden.clear(); clearFocus(true);
  // also reset the filters, otherwise the graph fills up again at once
  degFilter = 0; degOnly = false;
  if ($('#minDeg')) $('#minDeg').value = '0';
  hiddenCats.clear();
  syncHiddenBtn(); syncDegOnlyBtn(); syncCatButtons();
  clearSel(); clearHl(); refresh(false);
  document.querySelectorAll('#search-results li.added').forEach(li => li.classList.remove('added'));
});
on('#fit', 'click', () => { if (cy) { cy.fit(cy.elements().not('.hidden'), 50); capZoom(1.8); } });

/* ================= SAVED VIEWS ================= */
/* Takes a snapshot of the current graph state: on-screen nodes with their position,
   expanded nodes, hidings, filters and framing (zoom+pan). */
function captureView() {
  // save EVERY node currently on screen with its exact position, not only
  // those added by hand: so the neighbours shown by expansions also go back
  // to their place, without being repositioned from scratch.
  const nodes = [];
  cy.nodes().not('.hidden').forEach(n => {
    const p = n.position();
    nodes.push({ id: n.id(), x: Math.round(p.x), y: Math.round(p.y) });
  });
  return {
    nodes, expanded: [...expanded], pinned: [...pinned],
    hiddenNodes: [...hiddenNodes], catHidden: [...catHidden], hiddenCats: [...hiddenCats],
    degFilter, degOnly, showIds, depth: depthVal(),
    zoom: cy.zoom(), pan: { ...cy.pan() }
  };
}

/* Rebuilds the graph exactly as it was. Returns the number of nodes of the
   view that no longer exist (data changed in the meantime). */
function applyView(v) {
  if (!cy || !v) return 0;
  [visibleNodes, expanded, pinned, placed, hiddenNodes, catHidden, hiddenCats,
   selected].forEach(s => s.clear());
  clearFocus(true); clearHl();

  let missing = 0;
  cy.batch(() => {
    (v.nodes || []).forEach(it => {
      const n = cy.getElementById(it.id);
      if (!n.length) { missing++; return; }
      visibleNodes.add(it.id);
      if (typeof it.x === 'number') { n.position({ x: it.x, y: it.y }); placed.add(it.id); }
    });
  });
  (v.expanded || []).forEach(id => { if (cy.getElementById(id).length) expanded.add(id); });
  (v.pinned || []).forEach(id => { if (cy.getElementById(id).length) pinned.add(id); });
  (v.hiddenNodes || []).forEach(id => hiddenNodes.add(id));
  (v.catHidden || []).forEach(id => catHidden.add(id));
  (v.hiddenCats || []).forEach(c => hiddenCats.add(c));

  showIds = (v.showIds === undefined) ? true : !!v.showIds;
  if ($('#toggleIds')) $('#toggleIds').checked = showIds;
  degFilter = v.degFilter || 0;
  degOnly = !!v.degOnly;
  if ($('#minDeg')) $('#minDeg').value = String(degFilter);
  if ($('#depth') && v.depth) $('#depth').value = String(v.depth);
  computeDegReveal();

  syncCatButtons(); syncHiddenBtn(); syncDegOnlyBtn();
  refresh(false);                       // no layout: the positions are restored
  if (v.zoom && v.pan) { cy.zoom(v.zoom); cy.pan(v.pan); }
  else cy.fit(cy.elements().not('.hidden'), 50);
  return missing;
}

let viewsCache = [];
function fmtViewOpt(v) {
  const d = (v.at || '').slice(0, 16).replace('T', ' ');
  return `${v.name} · ${v.count} ${t('views.nodesShort')}${d ? ' · ' + d : ''}`;
}
async function refreshViews(selectId) {
  const sel = $('#viewList');
  if (!sel) return;
  try {
    const r = await fetch('/api/views');
    const j = await r.json();
    viewsCache = j.items || [];
  } catch (_) { viewsCache = []; }
  const none = `<option value="">${esc(t('views.none'))}</option>`;
  sel.innerHTML = none + viewsCache.map(v =>
    `<option value="${esc(v.id)}">${esc(fmtViewOpt(v))}</option>`).join('');
  if (selectId) sel.value = selectId;
  syncViewButtons();
}
function syncViewButtons() {
  const sel = $('#viewList');
  const has = sel && sel.value;
  if ($('#viewLoad')) $('#viewLoad').disabled = !has;
  if ($('#viewDelete')) $('#viewDelete').disabled = !has;
}
on('#viewList', 'change', syncViewButtons);

on('#viewSave', 'click', async () => {
  if (!cy || !requireCase()) return;
  const inp = $('#viewName');
  const name = (inp.value || '').trim();
  if (!name) { inp.focus(); $('#stat').textContent = t('views.needName'); return; }
  if (!visibleNodes.size) { $('#stat').textContent = t('views.empty'); return; }
  const dup = viewsCache.find(v => v.name.toLowerCase() === name.toLowerCase());
  if (dup && !confirm(t('views.confirmOverwrite', { name }))) return;
  try {
    const j = await apiPost('/api/views/save', { name, view: captureView() });
    inp.value = '';
    await refreshViews(j.id);
    $('#stat').textContent = t(j.overwritten ? 'views.updated' : 'views.saved',
      { name: j.name, n: j.count });
  } catch (e) { $('#stat').textContent = t('views.saveErr'); }
});

on('#viewLoad', 'click', async () => {
  const sel = $('#viewList');
  if (!sel || !sel.value) return;
  try {
    const j = await apiPost('/api/views/load', { id: sel.value });
    const missing = applyView(j.view);
    $('#stat').textContent = missing
      ? t('views.loadedPartial', { name: j.name, m: missing })
      : t('views.loaded', { name: j.name });
  } catch (e) { $('#stat').textContent = t('views.loadErr'); }
});

on('#viewDelete', 'click', async () => {
  const sel = $('#viewList');
  if (!sel || !sel.value) return;
  const v = viewsCache.find(x => x.id === sel.value);
  if (!confirm(t('views.confirmDelete', { name: v ? v.name : '' }))) return;
  try {
    await apiPost('/api/views/delete', { id: sel.value });
    await refreshViews();
    $('#stat').textContent = t('views.deleted');
  } catch (e) { $('#stat').textContent = t('views.deleteErr'); }
});

/* ================= DOCUMENT SOURCES ================= */
const srcState = { indexed: false, folder: '', count: 0, ocr: false };
const SRC_ICON = { '.pdf': '📕', '.docx': '📘', '.doc': '📘', '.xlsx': '📗',
  '.xls': '📗', '.csv': '📗', '.txt': '📄', '.md': '📄', '.log': '📄',
  '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.webp': '🖼️', '.gif': '🖼️',
  '.bmp': '🖼️', '.tif': '🖼️', '.tiff': '🖼️' };
const IMG_EXTS = new Set(['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff']);

/* Tesseract download from the interface: state of the job on the server. */
const ocrJob = { state: 'idle', stage: '', percent: 0, error: '' };

function ocrJobText() {
  if (ocrJob.stage === 'download') return t('src.ocrDownloading', { p: ocrJob.percent });
  if (ocrJob.stage === 'extract') return t('src.ocrExtracting');
  return t('src.ocrWorking');
}

function renderSrcStatus() {
  const el = $('#srcStatus');
  if (!el) return;
  const ocr = srcState.ocr
    ? `<span class="src-ocr on">${esc(t('src.ocrOn'))}</span>`
    : `<span class="src-ocr">${esc(t('src.ocrOff'))}</span>`;
  let html;
  if (srcState.indexed) {
    const port = srcState.portable ? ` · <span class="src-ocr on">${esc(t('src.portable'))}</span>` : '';
    // if portable, show the relative name (e.g. «sources»), not the absolute path
    const shown = (srcState.portable && srcState.folderRel) ? srcState.folderRel : srcState.folder;
    html = `<b>${srcState.count}</b> ${esc(t('src.files'))} · ${ocr}${port}` +
      `<div class="src-folder" title="${esc(srcState.folder)}">${esc(shown)}</div>`;
  } else {
    html = `<span class="src-none">${esc(t('src.noneYet'))}</span> · ${ocr}`;
  }
  // OCR missing: on Windows a button downloads Tesseract into tools/tesseract,
  // elsewhere it explains how to install it
  if (!srcState.ocr) {
    if (ocrJob.state === 'running') {
      html += `<div class="src-ocr-job">${esc(ocrJobText())}</div>`;
    } else {
      if (ocrJob.state === 'error') html += `<div class="src-ocr-job err">${esc(t('src.ocrErr', { e: ocrJob.error }))}</div>`;
      html += srcState.canInstall
        ? `<button type="button" id="ocrInstall" class="src-ocr-btn">${esc(t('src.ocrInstall'))}</button>`
        : `<div class="src-hint">${esc(t(srcState.ocrReason === 'module' ? 'src.ocrModule' : 'src.ocrUnix'))}</div>`;
    }
  }
  el.innerHTML = html;
}

async function pollOcrInstall() {
  for (;;) {
    await sleep(1000);
    try {
      const j = await fetch('/api/ocr/install/status').then(r => r.json());
      Object.assign(ocrJob, { state: j.state, stage: j.stage, percent: j.percent || 0, error: j.error || '' });
    } catch (_) { continue; }
    if (ocrJob.state !== 'running') break;
    renderSrcStatus();
  }
  if (ocrJob.state === 'done') $('#stat').textContent = t('src.ocrDone');
  await loadSrcStatus();                         // «OCR active» and no more button
}

async function startOcrInstall() {
  if (!confirm(t('src.ocrConfirm', { url: srcState.ocrUrl || '' }))) return;
  try {
    await apiPost('/api/ocr/install', {});
    Object.assign(ocrJob, { state: 'running', stage: 'download', percent: 0, error: '' });
    renderSrcStatus();
    pollOcrInstall();
  } catch (e) {
    Object.assign(ocrJob, { state: 'error', error: e.message });
    renderSrcStatus();
  }
}
on('#srcStatus', 'click', e => { if (e.target.closest('#ocrInstall')) startOcrInstall(); });

async function loadSrcStatus() {
  try {
    const r = await fetch('/api/sources/status');
    const j = await r.json();
    srcState.indexed = !!j.indexed;
    srcState.folder = j.folder || '';
    srcState.count = j.count || 0;
    srcState.ocr = !!j.ocr_available;
    srcState.portable = !!j.portable;
    srcState.folderRel = j.folder_rel || '';
    srcState.defaultFolder = j.default_folder || '';
    srcState.canInstall = !!j.ocr_can_install;
    srcState.ocrReason = j.ocr_reason || '';
    srcState.ocrUrl = j.ocr_url || '';
    // download already in progress (e.g. page reloaded): resume following it
    if (j.ocr_install === 'running' && ocrJob.state !== 'running') {
      ocrJob.state = 'running'; pollOcrInstall();
    }
    // the field is left EMPTY for the default 'sources' folder (portable):
    // so Scan always uses the relative path. I only prefill it if
  } catch (_) { srcState.indexed = false; }
  renderSrcStatus();
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

on('#srcScan', 'click', async () => {
  // ALWAYS scan the program's 'sources' folder: send the empty folder,
  // the server uses the default one and stores it as a relative path (portable).
  const folder = '';
  const btn = $('#srcScan');
  const old = btn.textContent;
  btn.disabled = true; btn.textContent = t('src.scanning');
  const st = $('#srcStatus');
  st.innerHTML = `<span class="src-busy">${esc(t('src.scanning'))}</span>`;
  try {
    await apiPost('/api/sources/scan', { folder });   // start in the background
    // follow the progress by polling /api/sources/progress
    for (;;) {
      await sleep(300);
      const r = await fetch('/api/sources/progress');
      const p = await r.json();
      if (p.error) throw new Error(p.error);
      if (p.running && p.total) {
        st.innerHTML = `<span class="src-busy">` +
          esc(t('src.indexing', { i: p.done, n: p.total })) +
          `</span><div class="src-folder" title="${esc(p.name)}">${esc(p.name)}</div>`;
      } else if (p.running) {
        st.innerHTML = `<span class="src-busy">${esc(t('src.scanning'))}</span>`;
      }
      if (p.finished) {
        if (p.error) throw new Error(p.error);
        const d = p.summary || {};
        srcState.indexed = true; srcState.folder = d.folder || folder;
        srcState.count = d.count || 0; srcState.ocr = !!d.ocr_available;
        srcState.portable = !!d.portable; srcState.folderRel = d.folder_rel || '';
        renderSrcStatus();
        $('#stat').textContent = t('src.scanned', { n: d.count || 0 });
        break;
      }
    }
  } catch (e) {
    st.innerHTML = `<span class="src-err">${esc(e.message || t('src.scanErr'))}</span>`;
  } finally { btn.disabled = false; btn.textContent = old; }
});

/* Highlights the term found inside a snippet, given the offset. */
function markSnippet(text, at, len) {
  if (typeof at !== 'number' || at < 0) return esc(text);
  return esc(text.slice(0, at)) + '<mark>' + esc(text.slice(at, at + len)) +
    '</mark>' + esc(text.slice(at + len));
}

/* HTML card of a source file, given the HTML of the already highlighted snippets. */
function srcFileCard(f, snipsHtml) {
  const ic = SRC_ICON[f.ext] || '📄';
  const url = '/api/sources/file/' + encodeURIComponent(f.id);
  const ocr = f.ocr ? ` <span class="src-badge">OCR</span>` : '';
  const prev = IMG_EXTS.has(f.ext)
    ? `<a href="${url}" target="_blank" rel="noopener" class="src-thumb">` +
      `<img src="${url}" loading="lazy" alt=""></a>` : '';
  return `<div class="src-file"><div class="src-file-h"><span class="src-ic">${ic}</span>` +
    `<span class="src-name" title="${esc(f.rel)}">${esc(f.name)}</span>` +
    `<span class="src-occ">${f.occ}×</span>${ocr}` +
    `<a class="src-open" href="${url}" target="_blank" rel="noopener">${esc(t('src.open'))}</a></div>` +
    prev + snipsHtml + `</div>`;
}

function renderSrcResultsInto(box, res, term) {
  if (!res.results || !res.results.length) {
    box.innerHTML = `<div class="src-empty">${esc(t('src.noHits', { q: term }))}</div>`;
    return;
  }
  box.innerHTML =
    `<div class="src-count">${esc(t('src.hits', { n: res.count }))}` +
    (res.truncated ? ' ' + esc(t('src.more')) : '') + `</div>` +
    res.results.map(f => {
      const snips = (f.snippets || []).map(s =>
        `<div class="src-snip">${markSnippet(s.text, s.at, s.len ?? term.length)}</div>`).join('');
      return srcFileCard(f, snips);
    }).join('');
}

/* Splits the card key (node label) into the terms to search for:
   words >= 3 letters, excluding bare numbers and codes like "A2". */
function labelTerms(label) {
  const raw = String(label || '').split(/[\s\-_/.,;:()·|]+/).map(s => s.trim()).filter(Boolean);
  const terms = raw.filter(s => s.length >= 3 && !/^\d+$/.test(s)
    && !/^[a-z]?\d+[a-z]?$/i.test(s));
  return [...new Set(terms)].slice(0, 12);
}

/* ---- search from the card: multi-term with selectable chips ---- */
let srcMulti = null;              // last multi-term result
const srcSel = new Set();         // terms currently selected

function renderMulti() {
  const box = $('#modal-src-res');
  if (!srcMulti || !srcMulti.terms.length) {
    box.innerHTML = `<div class="src-empty">${esc(t('src.noHitsCard'))}</div>`;
    return;
  }
  const chips = srcMulti.terms.map(tt => {
    const on = srcSel.has(tt.term);
    return `<button class="src-chip${on ? ' on' : ''}" data-term="${esc(tt.term)}">` +
      `${esc(tt.term)}<span class="src-chip-n">${tt.count}</span></button>`;
  }).join('');
  const files = srcMulti.results.filter(f => f.matched.some(m => srcSel.has(m)));
  let body;
  if (!srcSel.size) {
    body = `<div class="src-empty">${esc(t('src.pickTerm'))}</div>`;
  } else {
    body = `<div class="src-count">${esc(t('src.hits', { n: files.length }))}` +
      (srcMulti.truncated ? ' ' + esc(t('src.more')) : '') + `</div>` +
      files.map(f => {
        const snips = (f.snippets || []).filter(s => srcSel.has(s.term)).slice(0, 3)
          .map(s => `<div class="src-snip">${markSnippet(s.text, s.at, s.len)}</div>`).join('');
        return srcFileCard(f, snips);
      }).join('');
  }
  box.innerHTML = `<div class="src-chips">${chips}</div>` + body;
}

async function searchSources() {
  if (!modalNode) return;
  const label = modalNode.data('label') || '';
  let terms = labelTerms(label);
  if (!terms.length) terms = [label];
  const mode = $('#srcExact') && $('#srcExact').checked ? 'total' : 'partial';
  $('#modal-src').hidden = false;
  $('#modal-src-res').innerHTML = `<div class="src-busy">${esc(t('src.searching'))}</div>`;
  try {
    srcMulti = await apiPost('/api/sources/multi', { terms, mode });
    srcSel.clear();
    // at first select the most specific combination (the first: most words,
    // most results): it shows the best matches at once. You add the other chips.
    if (srcMulti.terms.length) srcSel.add(srcMulti.terms[0].term);
    renderMulti();
  } catch (e) {
    $('#modal-src-res').innerHTML = `<div class="src-err">${esc(e.message || t('src.searchErr'))}</div>`;
  }
}
on('#modal-src-btn', 'click', searchSources);
on('#srcExact', 'change', () => { if (modalNode && !$('#modal-src').hidden) searchSources(); });
// click on the chips: selects/deselects a term and refilters the results
on('#modal-src-res', 'click', e => {
  const chip = e.target.closest('.src-chip');
  if (!chip) return;
  const term = chip.dataset.term;
  if (srcSel.has(term)) srcSel.delete(term); else srcSel.add(term);
  renderMulti();
});

/* ---- free search in the sources (dedicated modal) ---- */
async function freeSearchSources(term) {
  const q = (term || '').trim();
  if (q.length < 2) { $('#srcQuery').focus(); return; }
  if (!srcState.indexed) { $('#stat').textContent = t('src.noneYet'); return; }
  $('#srcQuery2').value = q;
  $('#srcmodal').hidden = false;
  const box = $('#srcmodal-res');
  box.innerHTML = `<div class="src-busy">${esc(t('src.searching'))}</div>`;
  const mode = $('#srcQueryExact') && $('#srcQueryExact').checked ? 'total' : 'partial';
  try {
    const j = await apiPost('/api/sources/search', { q, mode });
    renderSrcResultsInto(box, j, q);
  } catch (e) {
    box.innerHTML = `<div class="src-err">${esc(e.message || t('src.searchErr'))}</div>`;
  }
}
on('#srcSearch', 'click', () => freeSearchSources($('#srcQuery').value));
on('#srcQuery', 'keydown', e => { if (e.key === 'Enter') freeSearchSources($('#srcQuery').value); });
on('#srcSearch2', 'click', () => freeSearchSources($('#srcQuery2').value));
on('#srcQuery2', 'keydown', e => { if (e.key === 'Enter') freeSearchSources($('#srcQuery2').value); });
on('#srcQueryExact', 'change', () => { if (!$('#srcmodal').hidden) freeSearchSources($('#srcQuery2').value); });
on('#srcmodal-close', 'click', () => { $('#srcmodal').hidden = true; });
on('#srcmodal', 'click', e => { if (e.target.id === 'srcmodal' && !dragEnd('srcmodal')) $('#srcmodal').hidden = true; });

on('#selclear', 'click', clearSel);
on('#findpath', 'click', findPath);
on('#clearpath', 'click', clearHl);
on('#pathonly', 'click', () => {
  pathOnly = !pathOnly;
  $('#pathonly').textContent = pathOnly ? t('btn.showRest') : t('btn.hideRest');
  $('#pathonly').classList.toggle('on', pathOnly);
  refresh(true);
  cy.fit(cy.elements().not('.hidden'), 60);
  capZoom(1.6);
});
on('#maxHops', 'change', () => { if (selected.size >= 2 && cy.nodes('.path').length) findPath(); });

on('#modal-close', 'click', closeModal);
on('#modal', 'click', e => { if (e.target.id === 'modal' && !dragEnd('modal')) closeModal(); });
on('#modal-exp', 'click', () => { if (modalNode) { toggleExpand(modalNode); openModal(modalNode); } });
on('#modal-focus', 'click', () => {
  if (!modalNode) return;
  const id = modalNode.id();
  closeModal();
  addToGraph([id], true);
});
on('#modal-body', 'click', e => {
  if (e.target.closest('a')) return;          // the summary links stay clickable
  const chip = e.target.closest('[data-goto]');
  if (!chip) return;
  const id = chip.dataset.goto;
  closeModal();
  addToGraph([id], true);
});

/* ---- Copy with a click on the card values ----
   Useful to reuse a piece of data quickly on other portals or in a document. */
function flashCopied(el) {
  el.classList.add('copied');
  setTimeout(() => el.classList.remove('copied'), 900);
}

function handleCopyClick(e) {
  // links, photos and buttons have their own behaviour
  if (e.target.closest('a') || e.target.tagName === 'IMG' ||
      e.target.closest('button')) return;
  const el = e.target.closest('[data-cp]');
  if (!el) return;
  const val = el.dataset.cp;
  if (!val) return;
  e.stopPropagation();
  if (copyToClipboard(val)) {
    flashCopied(el);
    $('#stat').textContent = t('cp.done', { v: val.length > 60 ? val.slice(0, 60) + '…' : val });
  }
}
on('#modal-body', 'click', handleCopyClick);
on('#modal-title', 'click', handleCopyClick);

/* "show all / show less" on the long values of the cards */
on('#modal-body', 'click', e => {
  const btn = e.target.closest('.lv-more');
  if (!btn) return;
  e.stopPropagation();
  const span = btn.previousElementSibling;
  if (!span || !span.classList.contains('lv')) return;
  const open = span.classList.toggle('open');
  btn.textContent = open ? t('card.showLess') : t('card.showMore');
});

/* POST JSON with meaningful errors: if the endpoint does not exist (server not
   restarted) the response is an HTML page and r.json() would give an
   incomprehensible message; here the case is detected and the user is told what to do. */
async function apiPost(url, payload) {
  let r;
  try {
    r = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch (e) {
    throw new Error(t('err.unreachable', { e: e.message }));
  }
  if (r.status === 404) {
    throw new Error(t('err.notFound', { url }));
  }
  const txt = await r.text();
  let j = null;
  try { j = JSON.parse(txt); } catch (_) {
    throw new Error(t('err.badResponse', { s: r.status }));
  }
  if (!r.ok || j.error) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}

/* ---- Note on the node ---- */
on('#modal-note', 'click', async () => {
  if (!modalNode) return;
  const d = modalNode.data();
  const cur = d.note || '';
  const txt = window.prompt(t('note.prompt', { label: d.label }), cur);
  if (txt === null) return;                   // cancelled
  try {
    const j = await apiPost('/api/note', { id: d.id, note: txt });
    modalNode.data('note', j.note || '');
    modalNode.toggleClass('noted', !!j.note);
    reindexNode(modalNode);                   // the note becomes searchable at once
    $('#modal-body').innerHTML = bodyFor(modalNode);
    $('#stat').textContent = j.note ? t('stat.noteSaved') : t('stat.noteRemoved');
  } catch (err) {
    alert(t('note.failedTitle', { e: err.message }));
  }
});

/* ---- Rename the card ----
   The new label lives in the annotations: the source files are not touched.
   If after the change another card represents the same identifier
   (e.g. the same number written with 00 and with +) the two become one. */
async function renameNode(node) {
  if (!node || !node.length) return;
  const d = node.data();
  const cur = String(d.label || '');
  const txt = window.prompt(t('rename.prompt', { label: cur }), cur);
  if (txt === null) return;                   // cancelled
  const nuovo = txt.trim();
  if (nuovo === cur.trim()) return;           // nothing to change
  try {
    const j = await apiPost('/api/node/label', { id: d.id, label: nuovo });
    await syncGraph();                        // the merge changes nodes and links
    const n = cy.getElementById(j.id);
    if (n && n.length) {
      if (!visibleNodes.has(j.id)) addToGraph([j.id], true);
      openModal(n);
    } else {
      closeModal();
    }
    $('#stat').textContent =
      j.merged ? t('stat.renameMerged', { label: j.label })
      : j.reset ? t('stat.renameReset')
      : t('stat.renamed', { label: j.label });
  } catch (err) {
    alert(t('rename.failed', { e: err.message }));
  }
}
/* ---- Editing ALL the node's values ----
   Label, URL, note, every field of every card and the fields added by hand.
   The source files are not touched: the changes live in annotations.json
   and can be undone all together. */
let editNode = null;

function edRow(key, val, attrs) {
  return `<div class="ed-row" ${attrs}>` +
    `<div class="ed-k" title="${esc(key)}">${esc(key)}</div>` +
    `<textarea rows="${Math.min(6, Math.max(1, Math.ceil(String(val).length / 60)))}">${esc(val)}</textarea>` +
    `<button type="button" class="mini ed-x" title="${esc(t('edit.delField'))}">✕</button></div>`;
}

function edExtraRow(key, val) {
  return `<div class="ed-row ed-extra">` +
    `<input class="ed-k" value="${esc(key)}" placeholder="${esc(t('edit.fieldName'))}">` +
    `<textarea rows="1" placeholder="${esc(t('edit.fieldValue'))}">${esc(val)}</textarea>` +
    `<button type="button" class="mini ed-x" title="${esc(t('edit.delField'))}">✕</button></div>`;
}

function openEditModal(node) {
  if (!node || !node.length) return;
  editNode = node;
  const d = node.data();
  $('#editmodal-sub').textContent = `${d.label} · ${d.ntype} · ${d.id}`;
  let h = `<div class="ed-sec ed-meta"><h4>${esc(t('edit.general'))}</h4>
      <label class="af-lb" for="ed-label">${esc(t('edit.label'))}</label>
      <input id="ed-label" value="${esc(d.label)}">
      <label class="af-lb" for="ed-url">${esc(t('edit.url'))}</label>
      <input id="ed-url" value="${esc(d.url || '')}" placeholder="https://…">
      <label class="af-lb" for="ed-note">${esc(t('card.note'))}</label>
      <textarea id="ed-note" rows="3">${esc(d.note || '')}</textarea>
      <label class="af-check"><input type="checkbox" id="ed-target"${d.ntype === 'target' ? ' checked' : ''}>
        <span>${esc(t('add.isTarget'))}</span></label>
    </div>`;
  const recs = d.records || [];
  let extra = [];
  recs.forEach((r, i) => {
    if (r.extra) { extra = Object.entries(r.raw || {}); return; }
    const rows = flatten(r.raw || {});
    h += `<div class="ed-sec"><h4>${esc(t('card.recordBadge', { i: i + 1, n: recs.length,
      coll: r.collection || t('card.sheet') }))}</h4>` +
      (rows.length ? rows.map(([k, v]) =>
        // shortened values (beyond MAX_VAL) are not edited: the rest would be lost
        edRow(k, v, `data-ri="${i}" data-path="${esc(k)}" data-orig="${esc(v)}"` +
          (v.length > MAX_VAL ? ' data-ro="1"' : ''))).join('')
        : `<div class="af-hint">${esc(t('card.empty'))}</div>`) +
      '</div>';
  });
  h += `<div class="ed-sec"><h4>${esc(t('edit.extra'))}</h4><div id="ed-extra">` +
       extra.map(([k, v]) => edExtraRow(k, v)).join('') + '</div>' +
       `<button type="button" id="ed-addfield" class="mini ed-add">${esc(t('edit.addField'))}</button></div>`;
  $('#editmodal-body').innerHTML = h;
  $('#editmodal-body').querySelectorAll('[data-ro] textarea').forEach(x => { x.readOnly = true; });
  $('#editmodal-reset').hidden = !d.edited;
  $('#editmodal').hidden = false;
}

on('#editmodal-body', 'input', e => {
  const row = e.target.closest('.ed-row[data-ri]');
  if (row) row.classList.toggle('ed-chg', e.target.value !== row.dataset.orig);
});
on('#editmodal-body', 'click', e => {
  if (e.target.id === 'ed-addfield') {
    $('#ed-extra').insertAdjacentHTML('beforeend', edExtraRow('', ''));
    $('#ed-extra').lastElementChild.querySelector('input').focus();
    return;
  }
  const x = e.target.closest('.ed-x');
  if (!x) return;
  const row = x.closest('.ed-row');
  if (row.classList.contains('ed-extra')) row.remove();      // added field: removed
  else if (!row.dataset.ro) row.classList.toggle('ed-del');  // card field: marked
});

async function saveEdit() {
  if (!editNode) return;
  const d = editNode.data();
  const fields = {};
  $('#editmodal-body').querySelectorAll('.ed-row[data-ri]').forEach(row => {
    if (row.dataset.ro) return;
    const key = `${row.dataset.ri}|${row.dataset.path}`;
    const v = row.querySelector('textarea').value;
    if (row.classList.contains('ed-del')) fields[key] = null;
    else if (v !== row.dataset.orig) fields[key] = v;
  });
  const extra = {};
  $('#editmodal-body').querySelectorAll('.ed-extra').forEach(row => {
    const k = row.querySelector('input').value.trim();
    const v = row.querySelector('textarea').value.trim();
    if (k && v) extra[k] = v;
  });
  const oldExtra = ((d.records || []).find(r => r.extra) || {}).raw || {};
  const url = $('#ed-url').value.trim();
  const note = $('#ed-note').value.trim();
  const label = $('#ed-label').value.trim();

  const payload = { id: d.id };
  if (Object.keys(fields).length) payload.fields = fields;
  if (JSON.stringify(extra) !== JSON.stringify(oldExtra)) payload.extra = extra;
  if (url !== (d.url || '')) payload.url = url;
  const btn = $('#editmodal-save');
  btn.disabled = true;
  try {
    if (Object.keys(payload).length > 1) await apiPost('/api/node/edit', payload);
    if (note !== (d.note || '').trim()) await apiPost('/api/note', { id: d.id, note });
    // any node can become (or stop being) a target
    const tgt = $('#ed-target') && $('#ed-target').checked;
    if (tgt !== (d.ntype === 'target')) await apiPost('/api/node/target', { id: d.id, target: tgt });
    let id = d.id;
    if (label && label !== String(d.label || '').trim()) {
      const j = await apiPost('/api/node/label', { id: d.id, label });
      id = j.id;                                   // the rename can merge the cards
    }
    await syncGraph();
    $('#editmodal').hidden = true;
    const n = cy.getElementById(id);
    if (n.length) {
      if (!visibleNodes.has(id)) addToGraph([id], false);
      if (modalNode) openModal(n);
    } else closeModal();
    $('#stat').textContent = t('edit.saved', { label: label || d.label });
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  } finally {
    btn.disabled = false;
  }
}

on('#modal-edit', 'click', () => openEditModal(modalNode));
on('#editmodal-save', 'click', saveEdit);
on('#editmodal-close', 'click', () => { $('#editmodal').hidden = true; });
on('#editmodal', 'click', e => { if (e.target.id === 'editmodal' && !dragEnd('editmodal')) $('#editmodal').hidden = true; });
on('#editmodal-reset', 'click', async () => {
  if (!editNode || !confirm(t('edit.confirmReset'))) return;
  try {
    await apiPost('/api/node/edit', { id: editNode.id(), reset: true });
    await syncGraph();
    $('#editmodal').hidden = true;
    const n = cy.getElementById(editNode.id());
    if (n.length && modalNode) openModal(n);
    $('#stat').textContent = t('edit.resetDone');
  } catch (err) {
    alert(t('err.opFailed', { e: err.message }));
  }
});

on('#modal-rename', 'click', () => renameNode(modalNode));
on('#modal-title', 'dblclick', () => renameNode(modalNode));

/* ---- Export the card to PDF ----
   It is printed in a hidden iframe: the browser offers "Save as PDF" without
   external libraries and without disturbing the graph page. */
function cardToPdf(node) {
  const d = node.data();
  const cards = (d.records || []).length;
  const sub = `${d.ntype} · ${d.platform} · ${d.deg} ${t('card.links')} · ` +
              (cards === 1 ? t('card.card', { n: cards }) : t('card.cards', { n: cards })) +
              ((d.merged || 1) > 1 ? ' · ' + t('card.merged', { n: d.merged }) : '');
  const css = `
    *{box-sizing:border-box}
    body{font:12px/1.5 system-ui,-apple-system,sans-serif;color:#0f172a;margin:24px}
    h1{font-size:18px;margin:0 0 2px}
    .sub{color:#64748b;font-size:11px;margin-bottom:4px}
    .gen{color:#94a3b8;font-size:10px;margin-bottom:14px;
         border-bottom:1px solid #e2e8f0;padding-bottom:10px}
    h4{font-size:12px;margin:14px 0 6px;color:#334155}
    h5{display:flex;gap:6px;align-items:center;font-size:11px;margin:8px 0 3px;color:#475569}
    h5 i{display:none}
    .g-cat{font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;
           border-bottom:1px solid #e2e8f0;padding-bottom:2px;margin:12px 0 6px}
    ul.g-list{list-style:none;margin:0;padding:0 0 0 12px}
    ul.g-list li{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 14px;
                 padding:2px 0;border-bottom:1px dotted #e2e8f0;font-size:11px}
    .g-name{font-weight:600;margin-right:8px}
    .g-go{display:none}                     /* pulsanti di navigazione: solo a schermo */
    /* in stampa i testi lunghi vanno per intero */
    .lv{display:block;max-height:none;white-space:pre-wrap;word-break:break-word}
    .lv-more{display:none}
    ul.g-list a{color:#1d4ed8;text-decoration:none;font-size:10px;word-break:break-all}
    ul.g-list li.g-photo{align-items:center;gap:8px;page-break-inside:avoid}
    .g-thumb{width:56px;height:56px;object-fit:cover;border:1px solid #e2e8f0;border-radius:5px}
    ul.g-list li.g-tr{gap:2px 8px}
    .g-orig{font-weight:700;font-size:12px}
    .g-arrow{color:#94a3b8}
    .g-scr{font-style:normal;font-size:8px;text-transform:uppercase;color:#64748b;
           background:#f1f5f9;border-radius:8px;padding:1px 5px}
    .d-note{background:#fef9c3;border:1px solid #eab308;border-left:4px solid #ca8a04;
            border-radius:6px;padding:8px 10px;margin-bottom:12px;color:#713f12}
    .d-note b{display:block;font-size:10px;text-transform:uppercase;margin-bottom:3px}
    .d-ren{background:#f1f5f9;border:1px solid #e2e8f0;border-left:4px solid #94a3b8;
           border-radius:6px;padding:6px 10px;margin-bottom:12px;color:#334155;
           display:flex;gap:8px;align-items:baseline}
    .d-ren b{font-size:10px;text-transform:uppercase;color:#64748b}
    .d-card{border:1px solid #e2e8f0;border-radius:6px;padding:8px;margin:8px 0;
            page-break-inside:avoid}
    .d-badge{font-size:10px;color:#2563eb;font-weight:700;margin-bottom:5px}
    .d-grid{display:grid;grid-template-columns:minmax(120px,32%) 1fr;gap:2px 10px;font-size:10px}
    .d-grid>div:nth-child(odd){color:#64748b;word-break:break-word}
    .d-grid>div:nth-child(even){word-break:break-word}
    .chip{display:inline-block;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;
          padding:1px 7px;margin:2px 3px 0 0;font-size:10px}
    .chip img,.d-imgs img,img.thumb{max-height:70px;max-width:110px;margin:3px}
    details{margin-top:8px} summary{font-size:11px;color:#475569}
    details[open] summary{margin-bottom:6px}
    @page{margin:14mm}`;
  const html = `<!doctype html><html lang="it"><head><meta charset="utf-8">
    <title>${esc(d.label)}</title><style>${css}</style></head><body>
    <h1>${esc(d.label)}</h1><div class="sub">${esc(sub)}</div>
    <div class="gen">${esc(t('card.generated', { date: new Date().toLocaleString(LANG) }))}</div>
    ${bodyFor(node, { print: true })}</body></html>`;

  printDoc(html);
}

/* Prints an HTML document in a hidden iframe: the browser offers
   "Save as PDF" without external libraries and without disturbing the page. */
function printDoc(html, waitMs) {
  const ifr = document.createElement('iframe');
  ifr.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden';
  document.body.appendChild(ifr);
  const doc = ifr.contentDocument;
  doc.open(); doc.write(html); doc.close();
  const go = () => {
    try { ifr.contentWindow.focus(); ifr.contentWindow.print(); } catch (_) {}
    setTimeout(() => ifr.remove(), 1500);      // removed once printing has started
  };
  // waits for the images to load, but without getting stuck
  setTimeout(go, waitMs !== undefined ? waitMs : (doc.images.length ? 700 : 120));
}

/* Common header of the printable documents. */
const REPORT_CSS = `
  *{box-sizing:border-box}
  body{font:11px/1.45 system-ui,-apple-system,sans-serif;color:#0f172a;margin:18px;
       -webkit-print-color-adjust:exact;print-color-adjust:exact}
  h1{font-size:17px;margin:0 0 2px}
  .gen{color:#94a3b8;font-size:10px;margin-bottom:12px;
       border-bottom:1px solid #e2e8f0;padding-bottom:8px}
  h2{font-size:13px;margin:16px 0 6px;color:#334155}
  table{width:100%;border-collapse:collapse;font-size:10px;table-layout:fixed}
  th{background:#f1f5f9;text-align:left;font-size:9px;text-transform:uppercase;
     letter-spacing:.04em;color:#475569;padding:4px 5px;border:1px solid #e2e8f0}
  td{padding:4px 5px;border:1px solid #e2e8f0;vertical-align:top;
     word-break:break-word;overflow-wrap:anywhere}
  tr{page-break-inside:avoid}
  thead{display:table-header-group}
  .num{color:#64748b;text-align:right}
  .ty{color:#2563eb;white-space:nowrap}
  a{color:#1d4ed8;text-decoration:none}
  img.th{max-width:54px;max-height:54px;object-fit:cover;border:1px solid #e2e8f0;border-radius:4px}
  .note{background:#fef9c3;color:#713f12;padding:2px 4px;border-radius:3px;display:inline-block}
  .sum{display:flex;gap:14px;flex-wrap:wrap;font-size:10px;color:#475569;margin-bottom:10px}
  .sum b{color:#0f172a}
  @page{margin:12mm}`;

/* ---- 1) Export the image of the visible graph ---- */
function exportGraphPdf() {
  const eles = cy.elements().not('.hidden');
  if (!eles.length) { alert(t('exp.empty')); return; }
  let png;
  try {
    png = cy.png({ full: true, scale: 2, bg: '#ffffff', maxWidth: 3000, maxHeight: 3000 });
  } catch (err) {
    alert(t('exp.failed', { e: err.message }));
    return;
  }
  const html = `<!doctype html><html lang="${LANG}"><head><meta charset="utf-8">
    <title>${esc(t('exp.graphTitle'))}</title><style>${REPORT_CSS}
    img.g{width:100%;height:auto;max-height:186mm;object-fit:contain}
    @page{size:A4 landscape;margin:10mm}</style></head><body>
    <h1>${esc(t('exp.graphTitle'))}</h1>
    <div class="gen">${esc(t('card.generated', { date: new Date().toLocaleString(LANG) }))}
      · ${eles.nodes().length} ${esc(t('exp.nodes'))} · ${eles.edges().length} ${esc(t('exp.edges'))}</div>
    <img class="g" src="${png}" alt=""></body></html>`;
  printDoc(html, 900);
  $('#stat').textContent = t('stat.pdfReady');
}

/* ---- 2) Tabular sheet of the nodes: analysis report ----
   Deliberately WITHOUT the links table: this document is the register
   of the entities present in the view, not the map of the relations (that is
   the graph PDF). The layout follows the structure of a report: heading,
   document details, quantitative summary, then the inventory by category. */
function exportTablePdf() {
  const nodes = cy.nodes().not('.hidden');
  if (!nodes.length) { alert(t('exp.empty')); return; }

  const urlOf = d => {
    if (/^https?:\/\//i.test(d.url || '')) return d.url;
    const mk = SOCIAL_URL[d.platform];
    const h = mk ? socialHandle(d) : '';
    return mk && h ? mk(h) : '';
  };
  // the category title without the leading emoji: in print it is just noise
  const catName = k => groupTitle(k).replace(/^\S+\s/, '');

  const rows = nodes.map(n => n.data());
  const tot = rows.length;

  // --- counts per category, from the most numerous to the least
  const byType = {};
  rows.forEach(d => { byType[d.ntype] = (byType[d.ntype] || 0) + 1; });
  const cats = Object.keys(byType).sort((a, b) =>
    byType[b] - byType[a] || catName(a).localeCompare(catName(b)));

  const quota = n => (n * 100 / tot);
  const distRows = cats.map(k => {
    const q = quota(byType[k]);
    return `<tr>
      <td class="cat">${esc(catName(k))}</td>
      <td class="num">${byType[k]}</td>
      <td class="pc"><span class="bar"><i style="width:${q.toFixed(1)}%"></i></span>
        <span class="pcv">${q.toFixed(1)}%</span></td>
    </tr>`;
  }).join('');

  // --- inventory: one section per category, single progressive numbering
  let np = 0;
  const sezioni = cats.map(k => {
    const lista = rows.filter(d => d.ntype === k)
      .sort((a, b) => String(a.label).localeCompare(String(b.label)));
    const trs = lista.map(d => {
      const u = urlOf(d);
      np += 1;
      return `<tr>
        <td class="num">${np}</td>
        <td>${d.image ? `<img class="th" src="${esc(d.image)}" onerror="this.remove()" alt="">` : ''}</td>
        <td><b dir="auto">${esc(d.label)}</b></td>
        <td>${esc(d.platform || '—')}</td>
        <td class="num">${d.deg || 0}</td>
        <td>${u ? `<a href="${esc(u)}">${esc(u)}</a>` : ''}</td>
        <td>${d.note ? `<span class="note">${esc(d.note)}</span>` : ''}</td>
      </tr>`;
    }).join('');
    return `<section class="sec">
      <h3>${esc(catName(k))}<span class="cnt">${lista.length}</span></h3>
      <table><colgroup><col class="c1"><col class="c2"><col><col class="c5">
        <col class="c6"><col class="c7"><col class="c8"></colgroup>
        <thead><tr><th>#</th><th>${esc(t('col.image'))}</th><th>${esc(t('col.label'))}</th>
        <th>${esc(t('col.platform'))}</th><th>${esc(t('col.degree'))}</th>
        <th>${esc(t('col.ref'))}</th><th>${esc(t('col.notes'))}</th></tr></thead>
        <tbody>${trs}</tbody></table>
    </section>`;
  }).join('');

  const meta = [
    [t('exp.metaDate'), new Date().toLocaleString(LANG)],
    [t('exp.metaScope'), t('exp.metaScopeVal')],
    [t('exp.metaNodes'), String(tot)],
    [t('exp.metaCats'), String(cats.length)],
  ].map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join('');

  const html = `<!doctype html><html lang="${LANG}"><head><meta charset="utf-8">
    <title>${esc(t('exp.tableTitle'))}</title><style>${REPORT_CSS}
    .rp-hd{border-bottom:2px solid #0f172a;padding-bottom:9px;margin-bottom:14px}
    .rp-kicker{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
               color:#64748b;margin-bottom:5px}
    .rp-hd h1{font-size:20px;letter-spacing:-.01em;margin:0}
    .rp-sub{font-size:11px;color:#475569;margin-top:2px}
    table.meta{width:min(360px,100%);margin:0 0 18px;font-size:10px}
    table.meta th{width:46%;background:#f8fafc;font-size:9px;letter-spacing:.05em}
    table.meta td{font-weight:600}
    h2{font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:#0f172a;
       border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:20px 0 9px}
    h2 .n{color:#2563eb;margin-right:6px}
    section.sec{margin-bottom:14px;break-inside:auto}
    section.sec h3{display:flex;align-items:center;gap:8px;font-size:11px;margin:13px 0 5px;
                   color:#334155;break-after:avoid;page-break-after:avoid}
    section.sec h3::after{content:"";flex:1;border-bottom:1px dotted #cbd5e1}
    section.sec h3 .cnt{order:3;font-size:9px;font-weight:700;color:#475569;
                        background:#f1f5f9;border:1px solid #e2e8f0;border-radius:9px;padding:0 7px}
    td.cat{font-weight:600}
    td.pc{white-space:nowrap}
    .bar{display:inline-block;width:64px;height:5px;background:#e2e8f0;border-radius:3px;
         overflow:hidden;vertical-align:middle;margin-right:6px}
    .bar i{display:block;height:100%;background:#2563eb}
    .pcv{color:#475569}
    .rp-foot{margin-top:22px;border-top:1px solid #e2e8f0;padding-top:7px;
             font-size:9px;color:#94a3b8}
    col.c1{width:34px} col.c2{width:56px} col.c5{width:74px} col.c6{width:38px}
    col.c7{width:31%} col.c8{width:17%}
    </style></head><body>

    <div class="rp-hd">
      <div class="rp-kicker">${esc(t('brand'))} · ${esc(t('exp.reportKicker'))}</div>
      <h1>${esc(t('exp.reportTitle'))}</h1>
      <div class="rp-sub">${esc(t('exp.reportSub'))}</div>
    </div>

    <table class="meta"><tbody>${meta}</tbody></table>

    <h2><span class="n">1</span>${esc(t('exp.secDist'))}</h2>
    <table><colgroup><col><col class="c6"><col class="c7"></colgroup>
      <thead><tr><th>${esc(t('col.category'))}</th><th>${esc(t('col.count'))}</th>
      <th>${esc(t('col.share'))}</th></tr></thead>
      <tbody>${distRows}</tbody></table>

    <h2><span class="n">2</span>${esc(t('exp.secInv'))}</h2>
    ${sezioni}

    <div class="rp-foot">${esc(t('exp.footNote'))}</div>
    </body></html>`;
  printDoc(html, 900);
  $('#stat').textContent = t('stat.pdfReady');
}

on('#expGraph', 'click', exportGraphPdf);
on('#expTable', 'click', exportTablePdf);
on('#showHidden', 'click', showHiddenNodes);

on('#modal-pdf', 'click', () => {
  if (!modalNode) return;
  cardToPdf(modalNode);
  $('#stat').textContent = t('stat.pdfReady');
});

/* ---- Node deletion (double confirmation) ---- */
on('#modal-del', 'click', async () => {
  if (!modalNode) return;
  const d = modalNode.data();
  if (!confirm(t('confirm.delete1', { label: d.label, ntype: d.ntype, deg: d.deg }))) return;
  if (!confirm(t('confirm.delete2', { label: d.label }))) return;
  try {
    // originating target: useful to recognise the node in the deleted list
    const targets = [...new Set(collectAround(modalNode, 2)
      .filter(m => m.data('ntype') === 'target')
      .map(m => m.data('label')))];
    await apiPost('/api/node/delete', {
      id: d.id, alias_ids: d.alias_ids || [],
      label: d.label, ntype: d.ntype, platform: d.platform, targets
    });
    const id = d.id;
    closeModal();
    // removes the node from the view and from all the state sets
    [visibleNodes, expanded, selected, pinned, placed].forEach(s => s.delete(id));
    cy.getElementById(id).remove();
    INDEX = INDEX.filter(it => it.id !== id);
    ADJ = null;
    renderSel();
    refresh(false);
    buildLegend();
    $('#stat').textContent = t('stat.nodeDeleted', { label: d.label });
  } catch (err) {
    alert(t('err.deleteFailed', { e: err.message }));
  }
});

/* ---- Credits: small banner with the developer's details ---- */
const setCredits = mostra => { const b = $('#credmodal'); if (b) b.hidden = !mostra; };
on('#creditsLink', 'click', () => setCredits(true));
on('#credmodal-close', 'click', () => setCredits(false));
// click outside the box = close, as in the other panels
on('#credmodal', 'click', e => { if (e.target.id === 'credmodal') setCredits(false); });

on('#ctx-new-node', 'click', () => { hideCtxMenu(); if (cy) openAdd(null); });
document.addEventListener('mousedown', e => { if (!e.target.closest('#ctxmenu')) hideCtxMenu(); });
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  if (!$('#ctxmenu').hidden) hideCtxMenu();
  else if (!$('#licmodal').hidden) $('#licmodal').hidden = true;
  else if (!$('#credmodal').hidden) setCredits(false);
  else if (!$('#lightbox').hidden) closeLightbox();
  else if (!$('#aimodal').hidden) $('#aimodal').hidden = true;
  else if (!$('#impmodal').hidden) $('#impmodal').hidden = true;
  else if (!$('#editmodal').hidden) $('#editmodal').hidden = true;
  else if (!$('#edgemodal').hidden) closeEdgeModal();
  else if (!$('#linkmodal').hidden) $('#linkmodal').hidden = true;
  else if (!$('#addmodal').hidden) $('#addmodal').hidden = true;
  else if (!$('#osamodal').hidden) $('#osamodal').hidden = true;
  else if (!$('#ftmmodal').hidden) $('#ftmmodal').hidden = true;
  else if (!$('#dictmodal').hidden) $('#dictmodal').hidden = true;
  else if (!$('#manmodal').hidden) $('#manmodal').hidden = true;
  else if (!$('#delmodal').hidden) $('#delmodal').hidden = true;
  else closeModal();
});
document.addEventListener('click', e => { if (!e.target.closest('.search-container')) hideResults(); });

document.addEventListener('contextmenu', e => {
  const el = e.target;
  if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)) return;
  e.preventDefault();
}, { capture: true });

/* ================= LICENCES =================
   The program (GPL v3 with additional clauses) and all the third-party
   components: list and texts in static/licenses/ (generated by tools/make_licenses.py). */
let licIndex = null, licCur = '';
const LIC_GROUPS = ['program', 'js', 'python', 'assets', 'tools'];

async function openLicenses() {
  $('#licmodal').hidden = false;
  if (!licIndex) {
    $('#lic-list').innerHTML = `<div class="lic-grp">${esc(t('lic.loading'))}</div>`;
    try {
      licIndex = await fetch('/static/licenses/index.json').then(r => r.json());
    } catch (e) {
      $('#lic-list').innerHTML = `<div class="lic-grp">${esc(e.message)}</div>`;
      return;
    }
  }
  renderLicList();
  showLicense(licCur || (licIndex[0] && licIndex[0].id));
}

const licRole = e => (e.role && (e.role[LANG] || e.role.en || e.role.it)) || '';

function renderLicList() {
  const box = $('#lic-list');
  box.innerHTML = LIC_GROUPS.map(g => {
    const items = licIndex.filter(e => e.group === g);
    if (!items.length) return '';
    return `<div class="lic-grp">${esc(t('lic.grp.' + g))}</div>` + items.map(e =>
      `<button type="button" class="lic-item${e.id === licCur ? ' cur' : ''}" data-lic="${esc(e.id)}">` +
      `${esc(e.name)}${e.version ? ` <small>${esc(e.version)}</small>` : ''}` +
      `<small>${esc(e.license)}${e.bundled ? '' : ` · <span class="lic-ext">${esc(t('lic.external'))}</span>`}</small></button>`
    ).join('');
  }).join('');
}

async function showLicense(id) {
  const e = licIndex && licIndex.find(x => x.id === id);
  if (!e) return;
  licCur = id;
  $('#lic-list').querySelectorAll('.lic-item').forEach(b => b.classList.toggle('cur', b.dataset.lic === id));
  $('#lic-meta').innerHTML =
    `<b>${esc(e.name)}</b>${e.version ? ` <span>${esc(e.version)}</span>` : ''}` +
    `<span class="lic-badge">${esc(e.license)}</span>` +
    `<div class="lic-role">${esc(licRole(e))}${e.bundled ? '' : ` · ${esc(t('lic.external'))}`}</div>` +
    (e.copyright ? `<div>${esc(e.copyright)}</div>` : '') +
    (e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.url)}</a>` : '');
  const pre = $('#lic-text');
  pre.textContent = t('lic.loading');
  if (!e.file) { pre.textContent = ''; return; }
  try {
    pre.textContent = await fetch('/static/licenses/' + e.file).then(r => r.text());
  } catch (err) {
    pre.textContent = err.message;
  }
  pre.scrollTop = 0;
}

on('#licLink', 'click', e => { e.preventDefault(); openLicenses(); });
/* user manual (static/manual/manual.html, six languages): opens in the interface language */
on('#manualLink', 'click', e => {
  e.preventDefault();
  window.open('/static/manual/manual.html?lang=' + encodeURIComponent(LANG), '_blank', 'noopener');
});
on('#lic-list', 'click', e => { const b = e.target.closest('[data-lic]'); if (b) showLicense(b.dataset.lic); });
on('#licmodal-close', 'click', () => { $('#licmodal').hidden = true; });
on('#licmodal', 'click', e => { if (e.target.id === 'licmodal' && !dragEnd('licmodal')) $('#licmodal').hidden = true; });

/* Translations applied BEFORE building the graph, so every dynamically
   generated text is born already in the chosen language. */
applyI18n();
buildLangSelector();
load();
refreshTranslitBtn();
/* investigative items in the node type drop-down */
fillOntoOptions();
on('#add-onto-row', 'input', updateAddPreview);
on('#add-onto-row', 'change', updateAddPreview);

/* ================= CASES (CASE FILES) =================
   Each case has its own nodes, cards, links, notes, views and imported JSON.
   Switching case reloads the page: the graph state belongs to the case. */
let casesList = [], caseMode = 'new';

async function loadCases() {
  try {
    const j = await fetch('/api/cases').then(r => r.json());
    casesList = j.items || [];
    const cur = casesList.find(c => c.id === j.current);
    hasCase = !!cur;
    const sel = $('#caseSel');
    sel.innerHTML = (hasCase ? '' : `<option value="">${esc(t('case.noneOpt'))}</option>`) +
      casesList.map(c => `<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');
    sel.value = hasCase ? j.current : '';
    $('#caseDesc').textContent = hasCase ? cur.description || '' : t('case.noneHint');
    $('.case-box').classList.toggle('no-case', !hasCase);
    $('#caseEdit').disabled = !hasCase;
    $('#caseDel').disabled = !hasCase;
    $('#caseMerge').disabled = casesList.length < 2;
    // first start (or last case deleted): asks at once to create a case
    if (!hasCase) openCaseModal('new');
  } catch (e) {
    $('#caseDesc').textContent = e.message;
  }
}

/* Without an open case nothing can be added: the window opens to create
   one (or choose an existing one from the drop-down) with a notice explaining why. */
function requireCase() {
  if (hasCase) return true;
  openCaseModal('new');
  $('#cm-msg').textContent = t('case.needCase');
  $('#stat').textContent = t('case.needCase');
  return false;
}

function openCaseModal(mode) {
  caseMode = mode;
  const cur = casesList.find(c => c.id === $('#caseSel').value) || {};
  $('#casemodal-title').textContent = t('case.title.' + mode);
  $('#casemodal-sub').textContent = mode === 'edit' ? cur.name
                                  : mode === 'new' && !hasCase ? t('case.firstHint')
                                  : t('case.sub.' + mode);
  $('#cm-merge').hidden = mode !== 'merge';
  $('#cm-name').value = mode === 'edit' ? cur.name || '' : '';
  $('#cm-desc').value = mode === 'edit' ? cur.description || '' : '';
  $('#cm-delsrc').checked = false;
  $('#cm-msg').textContent = '';
  if (mode === 'merge') {
    $('#cm-list').innerHTML = casesList.map(c =>
      `<label class="af-check"><input type="checkbox" value="${esc(c.id)}"${c.current ? ' checked' : ''}>` +
      `<span>${esc(c.name)}</span></label>`).join('');
  }
  $('#casemodal').hidden = false;
  setTimeout(() => $(mode === 'merge' ? '#cm-list input' : '#cm-name').focus(), 50);
}

async function saveCaseModal() {
  const name = $('#cm-name').value.trim(), description = $('#cm-desc').value.trim();
  const msg = $('#cm-msg');
  msg.classList.add('err');
  try {
    if (caseMode === 'merge') {
      const ids = [...$('#cm-list').querySelectorAll('input:checked')].map(i => i.value);
      if (ids.length < 2) { msg.textContent = t('case.needTwo'); return; }
      if ($('#cm-delsrc').checked && !confirm(t('case.confirmMergeDel', { n: ids.length }))) return;
      await apiPost('/api/cases/merge', { ids, name, description, delete_sources: $('#cm-delsrc').checked });
      location.reload();
    } else if (caseMode === 'edit') {
      if (!name) { msg.textContent = t('case.needName'); return; }
      await apiPost('/api/cases/update', { id: $('#caseSel').value, name, description });
      $('#casemodal').hidden = true;
      loadCases();
    } else {
      if (!name) { msg.textContent = t('case.needName'); return; }
      await apiPost('/api/cases/add', { name, description });
      location.reload();                       // the new case is empty
    }
  } catch (e) {
    msg.textContent = e.message;
  }
}

on('#caseSel', 'change', async e => {
  if (!e.target.value) return;                 // «no case» entry
  try {
    await apiPost('/api/cases/switch', { id: e.target.value });
    location.reload();
  } catch (err) { alert(err.message); loadCases(); }
});
on('#caseNew', 'click', () => openCaseModal('new'));
on('#caseEdit', 'click', () => openCaseModal('edit'));
on('#caseMerge', 'click', () => openCaseModal('merge'));
on('#caseDel', 'click', async () => {
  const cur = casesList.find(c => c.id === $('#caseSel').value);
  if (!cur || !confirm(t('case.confirmDel', { name: cur.name }))) return;
  try {
    await apiPost('/api/cases/delete', { id: cur.id });
    location.reload();
  } catch (e) { alert(e.message); }
});
on('#casemodal-close', 'click', () => { $('#casemodal').hidden = true; });
on('#casemodal-save', 'click', saveCaseModal);
on('#cm-name', 'keydown', e => { if (e.key === 'Enter') saveCaseModal(); });
loadCases();

/* ============ STYLE OF ALL LINKS (left panel) ============
   Applies to the whole graph and sits on top of the single link's style,
   which stays saved: with «as set» every link goes back to how it was.
   The choice is a viewer preference: it lives in the browser, not in the data. */
const GSTYLE = { shape: '', line: '', width: '' };

function loadGStyle() {
  try {
    Object.assign(GSTYLE, JSON.parse(localStorage.getItem('edgeStyle') || '{}'));
  } catch (_) { /* preference missing or unreadable: the current values stay */ }
  const sh = $('#gsShape');
  if (sh) {
    sh.innerHTML = `<option value="">${esc(t('gstyle.keep'))}</option>` +
      EDGE_CURVES.map(c => `<option value="${c}">${esc(t('curve.' + c))}</option>`).join('');
    sh.value = GSTYLE.shape || '';
  }
  if ($('#gsLine')) $('#gsLine').value = GSTYLE.line || '';
  if ($('#gsWidth')) $('#gsWidth').value = GSTYLE.width || '';
}

function applyGStyle() {
  if (!cy) return;
  cy.batch(() => {
    cy.edges().forEach(e => {
      const cls = e.classes().filter(c => /^g[slw]-/.test(c));
      if (cls.length) e.removeClass(cls.join(' '));
      if (GSTYLE.shape) e.addClass('gs-' + GSTYLE.shape);
      if (GSTYLE.line) e.addClass('gl-' + GSTYLE.line);
      if (GSTYLE.width) e.addClass('gw-' + GSTYLE.width);
    });
  });
}

function setGStyle(k, v) {
  GSTYLE[k] = v;
  try { localStorage.setItem('edgeStyle', JSON.stringify(GSTYLE)); } catch (_) {}
  applyGStyle();
}

on('#gsShape', 'change', e => setGStyle('shape', e.target.value));
on('#gsLine', 'change', e => setGStyle('line', e.target.value));
on('#gsWidth', 'change', e => setGStyle('width', e.target.value));
loadGStyle();
