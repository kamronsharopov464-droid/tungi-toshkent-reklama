# Telegram orqali reklama qo'yish (faqat admin @VFF_UZB).
# Admin botga rasm yoki video yuboradi, izohga muddat yozadi ("3 kun", "12 soat", "1 hafta", "muddatsiz").
# GitHub Actions bu skriptni har 10 daqiqada ishga tushiradi (.github/workflows/telegram.yml):
# yangi xabarlarni o'qiydi -> media/ ga yozadi -> ads.json yangilanadi -> o'yin hamma o'yinchilarda ko'rsatadi.
# BOT_TOKEN — omborning shifrlangan "secret" i, kodda yo'q.
import os, json, re, time, hashlib, shutil, subprocess, urllib.request, urllib.parse

TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN = 'vff_uzb'
REPO = os.environ.get('GITHUB_REPOSITORY', 'kamronsharopov464-droid/tungi-toshkent-reklama')
FAKE = os.environ.get('TT_FAKE')  # sinov: soxta xabarlar fayli (Telegram va git push ishlatilmaydi)
MAXB = 20 * 1024 * 1024
UNITS = [('soat', 3600, r'soat|час|hour|h'), ('kun', 86400, r'kun|день|дн|day|d'), ('hafta', 7 * 86400, r'hafta|недел|week|w'), ('oy', 30 * 86400, r'oy|месяц|мес|month')]
HELP = ("👋 Tungi Toshkent reklama boti.\n\n"
        "📢 Reklama qo'yish: shu yerga RASM yoki VIDEO (20 MB gacha) yuboring, izohiga muddatni yozing:\n"
        "   3 kun · 12 soat · 1 hafta · 1 oy · muddatsiz   (yozmasangiz — 1 kun)\n"
        "Reklama shahardagi 10 ta katta panelda va «O'yin boshlanmoqda» ekranida hamma o'yinchilarda chiqadi.\n\n"
        "/reklamalar — efirdagi reklamalar\n/ochir 2 — 2-reklamani o'chirish (/ochir hammasi — barchasini)\n/kanal @nom — bosh menyudagi Telegram kanal\n\n"
        "⏱ Bot har 10 daqiqada xabarlarni tekshiradi, shuning uchun javob 10–20 daqiqada keladi.")

def tg(method, **p):
    if FAKE: print('[tg]', method, (p.get('text') or '')[:70].replace('\n', ' ')); return [] if method == 'getUpdates' else {}
    with urllib.request.urlopen('https://api.telegram.org/bot' + TOKEN + '/' + method, urllib.parse.urlencode(p).encode(), timeout=60) as r:
        return json.loads(r.read())['result']

def download(file_id, dst):
    if FAKE: shutil.copy(os.environ['TT_FAKE_MEDIA'], dst); return
    f = tg('getFile', file_id=file_id)
    with urllib.request.urlopen('https://api.telegram.org/file/bot' + TOKEN + '/' + f['file_path'], timeout=120) as r, open(dst, 'wb') as o:
        shutil.copyfileobj(r, o)

def git(*a, out=False):
    r = subprocess.run(['git', *a], check=True, capture_output=True, text=True)
    return r.stdout.strip() if out else None

def load(p, d):
    try:
        with open(p, encoding='utf-8') as f: return json.load(f)
    except Exception: return d

def save(p, d):
    with open(p, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=1)

def parse_dur(t):
    t = (t or '').lower()
    if re.search(r'muddatsiz|doimiy|cheksiz', t): return 0, 'muddatsiz'
    for name, sec, rx in UNITS:
        m = re.search(r'(\d+)\s*(?:' + rx + r')\b', t)
        if m and 0 < int(m.group(1)) <= 1000: return int(m.group(1)) * sec, f"{int(m.group(1))} {name}"
    return 86400, '1 kun'

def left(u):
    if not u: return 'muddatsiz'
    s = u / 1000 - time.time()
    if s <= 0: return 'tugagan'
    return f"{int(s // 86400)} kun qoldi" if s >= 2 * 86400 else f"{int(s // 3600)} soat qoldi" if s >= 3600 else f"{max(1, int(s // 60))} daqiqa qoldi"

def media_of(m):
    if m.get('photo'): return 'img', m['photo'][-1]['file_id'], 'jpg', m['photo'][-1].get('file_size', 0)
    if m.get('video'): return 'video', m['video']['file_id'], 'mp4', m['video'].get('file_size', 0)
    if m.get('animation'): return 'video', m['animation']['file_id'], 'mp4', m['animation'].get('file_size', 0)
    d = m.get('document') or {}
    mt, ext = d.get('mime_type', ''), (d.get('file_name', '').rsplit('.', 1)[-1] or '').lower()
    if mt.startswith('image/') and ext in ('jpg', 'jpeg', 'png', 'webp'): return 'img', d['file_id'], ext, d.get('file_size', 0)
    if mt in ('video/mp4', 'video/webm') : return 'video', d['file_id'], 'webm' if 'webm' in mt else 'mp4', d.get('file_size', 0)
    return None

def main():
    st = load('state.json', {})
    ups = json.load(open(FAKE, encoding='utf-8')) if FAKE else tg('getUpdates', timeout=0, allowed_updates=json.dumps(['message']))
    if not ups: print("Yangi xabar yo'q"); return
    ads = load('ads.json', {'v': 1, 'ads': []}); ads.setdefault('ads', [])
    now = int(time.time() * 1000)
    replies, changed, last = [], False, None
    for u in ups:
        last = u['update_id']
        m = u.get('message') or {}
        fr = m.get('from') or {}
        h = hashlib.sha256(str(fr.get('id')).encode()).hexdigest()
        if st.get('admin'):
            if h != st['admin']: continue
        elif (fr.get('username') or '').lower() == ADMIN: st['admin'] = h; save('state.json', st); changed = True  # birinchi xabarda admin qotiriladi
        else: continue
        chat, text = m['chat']['id'], (m.get('caption') or m.get('text') or '').strip()
        md = media_of(m)
        if md:
            typ, fid, ext, size = md
            if size and size > MAXB: replies.append((chat, f"❌ Fayl {size // 1048576} MB — 20 MB dan oshmasin. Qisqaroq video yuboring.")); continue
            sec, label = parse_dur(text)
            aid = time.strftime('%y%m%d%H%M%S') + hashlib.sha1(fid.encode()).hexdigest()[:4]
            os.makedirs('media', exist_ok=True); path = f'media/{aid}.{ext}'
            try: download(fid, path)
            except Exception as e: replies.append((chat, f"❌ Faylni yuklab bo'lmadi ({type(e).__name__}). Qayta yuboring.")); continue
            git('add', path); git('commit', '-qm', f'Reklama {aid}')
            sha = git('rev-parse', 'HEAD', out=True)
            ads['ads'].append({'id': aid, 'type': typ, 'url': f'https://cdn.jsdelivr.net/gh/{REPO}@{sha}/{path}', 't': now, 'until': now + sec * 1000 if sec else 0})
            changed = True
            n = len([a for a in ads['ads'] if not a.get('until') or a['until'] > now])
            replies.append((chat, f"✅ Reklama qabul qilindi — {label}.\n5–10 daqiqada hamma o'yinchilarda chiqadi (shahardagi panellar va kirish ekrani).\nHozir efirda: {n} ta. Ro'yxat: /reklamalar"))
        elif re.match(r'^/(reklamalar|list)', text):
            act = [a for a in ads['ads'] if not a.get('until') or a['until'] > now]
            rows = []
            for i, a in enumerate(act):
                kind = '🖼 Rasm' if a['type'] == 'img' else '🎬 Video'
                rows.append(str(i + 1) + '. ' + kind + ' — ' + left(a.get('until')))
            msg = ("📢 Efirdagi reklamalar:\n" + "\n".join(rows) + "\n\nO'chirish: /ochir 1") if act else "Hozir efirda reklama yo'q. Rasm yoki video yuboring."
            replies.append((chat, msg))
        elif re.match(r'^/ochir', text):
            act = [a for a in ads['ads'] if not a.get('until') or a['until'] > now]
            arg = text.split(maxsplit=1)[1].strip().lower() if len(text.split()) > 1 else ''
            if arg in ('hammasi', 'all', 'barchasi'):
                ads['ads'] = []; changed = True; replies.append((chat, "🗑 Barcha reklamalar o'chirildi."))
            elif arg.isdigit() and 1 <= int(arg) <= len(act):
                rm = act[int(arg) - 1]['id']; ads['ads'] = [a for a in ads['ads'] if a['id'] != rm]; changed = True
                replies.append((chat, f"🗑 {arg}-reklama o'chirildi. Hammada 5–10 daqiqada yo'qoladi."))
            else: replies.append((chat, "Qaysi birini? Avval /reklamalar ni bosing, keyin masalan: /ochir 1"))
        elif re.match(r'^/kanal', text):
            v = text.split(maxsplit=1)[1].strip() if len(text.split()) > 1 else ''
            if re.match(r'^(@[A-Za-z0-9_]{4,32}|https://t\.me/[A-Za-z0-9_+/]{3,64})$', v): ads['tg'] = v; changed = True; replies.append((chat, f"📣 Kanal saqlandi: {v}"))
            else: replies.append((chat, "Masalan: /kanal @VFF_UZB"))
        else:
            replies.append((chat, HELP))
    if changed:
        keep = [a for a in ads['ads'] if not a.get('until') or a['until'] > now - 86400000]  # 1 kundan oldin tugaganlar tozalanadi
        live = {a['url'].rsplit('/', 1)[-1] for a in keep}
        for f in os.listdir('media') if os.path.isdir('media') else []:
            if f not in live: git('rm', '-q', f'media/{f}')
        ads['ads'] = keep; ads['updated'] = now
        save('ads.json', ads); git('add', '-A'); git('commit', '-qm', 'Reklamalar yangilandi (Telegram)')
        if not FAKE:
            for k in range(3):
                try: git('push', '-q'); break
                except subprocess.CalledProcessError:
                    if k == 2: raise
                    git('pull', '-q', '--rebase')
    for chat, t in replies:
        try: tg('sendMessage', chat_id=chat, text=t)
        except Exception as e: print('javob yuborilmadi:', type(e).__name__)
    if last is not None and not FAKE: tg('getUpdates', offset=last + 1, timeout=0)  # o'qildi deb belgilash
    print('Xabarlar:', len(ups), '| javoblar:', len(replies), '| reklamalar:', len(ads['ads']))

if __name__ == '__main__':
    main()
