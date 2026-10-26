// Archivio delle storie · piccolo server per salvare modifiche e allegati.
// Gira solo su 127.0.0.1: Caddy lo espone su /api/* dietro la stessa password del gobbo.
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = +process.env.PORT || 3270;
const ROOT = process.env.ARCHIVIO_ROOT || '/home/work/gobbo-corinne';
const DATA = path.join(ROOT, 'archivio', 'archivio.json');
const MEDIA = path.join(ROOT, 'archivio', 'media');
const BACKUP = path.join(ROOT, '_api', 'backup');
const MAX_JSON = 2 * 1024 * 1024;
const MAX_FILE = 4 * 1024 * 1024 * 1024;

fs.mkdirSync(MEDIA, { recursive: true });
fs.mkdirSync(BACKUP, { recursive: true });

const leggi = () => JSON.parse(fs.readFileSync(DATA, 'utf8'));

function scrivi(dati) {
  // copia di sicurezza della versione precedente, poi scrittura atomica
  if (fs.existsSync(DATA)) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    fs.copyFileSync(DATA, path.join(BACKUP, `archivio-${stamp}.json`));
    const vecchi = fs.readdirSync(BACKUP).filter(f => f.endsWith('.json')).sort();
    vecchi.slice(0, Math.max(0, vecchi.length - 300)).forEach(f => fs.unlinkSync(path.join(BACKUP, f)));
  }
  const tmp = DATA + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(dati, null, 1));
  fs.renameSync(tmp, DATA);
}

const nomeSicuro = s => String(s || 'file').normalize('NFKD').replace(/[^\w.\- ]+/g, '').replace(/\s+/g, '-').replace(/^[.-]+/, '').slice(0, 120) || 'file';
const idSicuro = s => /^[a-z0-9-]{1,60}$/.test(s || '') ? s : null;

function rispondi(res, code, obj) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(obj));
}

function corpoJSON(req) {
  return new Promise((ok, ko) => {
    let n = 0; const parti = [];
    req.on('data', c => { n += c.length; if (n > MAX_JSON) { ko(new Error('troppo grande')); req.destroy(); } else parti.push(c); });
    req.on('end', () => { try { ok(JSON.parse(Buffer.concat(parti).toString('utf8'))); } catch (e) { ko(e); } });
    req.on('error', ko);
  });
}

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  try {
    if (u.pathname === '/api/archivio' && req.method === 'GET') return rispondi(res, 200, leggi());

    if (u.pathname === '/api/archivio' && req.method === 'PUT') {
      const dati = await corpoJSON(req);
      if (!dati || !Array.isArray(dati.storie) || !Array.isArray(dati.diario)) return rispondi(res, 400, { errore: 'dati non validi' });
      scrivi(dati);
      return rispondi(res, 200, { ok: true });
    }

    if (u.pathname === '/api/upload' && req.method === 'POST') {
      const id = idSicuro(u.searchParams.get('id'));
      if (!id) return rispondi(res, 400, { errore: 'storia non valida' });
      const dir = path.join(MEDIA, id);
      fs.mkdirSync(dir, { recursive: true });
      const nome = Date.now() + '-' + nomeSicuro(u.searchParams.get('name'));
      const dest = path.join(dir, nome);
      const out = fs.createWriteStream(dest);
      let n = 0, troppo = false;
      req.on('data', c => { n += c.length; if (n > MAX_FILE && !troppo) { troppo = true; req.unpipe(out); out.destroy(); fs.rmSync(dest, { force: true }); rispondi(res, 413, { errore: 'file troppo grande' }); } });
      req.pipe(out);
      out.on('finish', () => {
        if (troppo) return;
        const dati = leggi();
        const s = dati.storie.find(x => x.id === id);
        if (!s) { fs.rmSync(dest, { force: true }); return rispondi(res, 404, { errore: 'storia non trovata' }); }
        const voce = { nome: u.searchParams.get('name') || nome, url: `media/${id}/${nome}`, size: n, data: new Date().toISOString().slice(0, 10), da: (u.searchParams.get('da') || '').slice(0, 40) };
        (s.media = s.media || []).push(voce);
        scrivi(dati);
        rispondi(res, 200, voce);
      });
      out.on('error', e => rispondi(res, 500, { errore: e.message }));
      return;
    }

    if (u.pathname === '/api/media' && req.method === 'DELETE') {
      const id = idSicuro(u.searchParams.get('id'));
      const url = u.searchParams.get('url') || '';
      const dati = leggi();
      const s = id && dati.storie.find(x => x.id === id);
      if (!s || !url.startsWith(`media/${id}/`) || url.includes('..')) return rispondi(res, 400, { errore: 'richiesta non valida' });
      s.media = (s.media || []).filter(m => m.url !== url);
      fs.rmSync(path.join(ROOT, 'archivio', url), { force: true });
      scrivi(dati);
      return rispondi(res, 200, { ok: true });
    }

    rispondi(res, 404, { errore: 'non trovato' });
  } catch (e) {
    rispondi(res, 500, { errore: String(e.message || e) });
  }
}).listen(PORT, '127.0.0.1', () => console.log('archivio api su 127.0.0.1:' + PORT));
