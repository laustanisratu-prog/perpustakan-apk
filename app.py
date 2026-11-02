from flask import Flask, request, redirect, session, render_template_string, send_file
import sqlite3, os
from datetime import datetime, timedelta
from io import BytesIO
import random

app = Flask(__name__)
app.secret_key = 'perpus_final_2026'
DB = 'perpustakaan.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS anggota (nim TEXT PRIMARY KEY, nama TEXT, prodi TEXT, telp TEXT, status TEXT DEFAULT 'Aktif')")
    c.execute("CREATE TABLE IF NOT EXISTS buku (id INTEGER PRIMARY KEY, judul TEXT, pengarang TEXT, kategori TEXT, no_panggil TEXT, stok INTEGER, total INTEGER, jenis TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS peminjaman (id INTEGER PRIMARY KEY, nim TEXT, buku_id INTEGER, tgl_pinjam TEXT, tgl_kembali TEXT, tgl_dikembalikan TEXT, status TEXT, denda INTEGER DEFAULT 0, catatan TEXT DEFAULT '')")
    c.execute("CREATE TABLE IF NOT EXISTS usulan (id INTEGER PRIMARY KEY, nim TEXT, judul TEXT, pengarang TEXT, alasan TEXT, status TEXT DEFAULT 'Menunggu')")
    c.execute("CREATE TABLE IF NOT EXISTS karya (id INTEGER PRIMARY KEY, nim TEXT, judul TEXT, tahun TEXT, file_name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS bukutamu (id INTEGER PRIMARY KEY, nim TEXT, tujuan TEXT, tgl TEXT)")
    
    if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
        c.executemany("INSERT INTO users (username,password,role) VALUES (?,?,?)", [
            ('admin','admin','admin'),
            ('kepala','kepala','kepala'),
            ('2023001','mhs','mahasiswa'),
            ('11257061','deni','mahasiswa'),
        ])
    if c.execute("SELECT COUNT(*) FROM anggota").fetchone()[0]==0:
        c.executemany("INSERT INTO anggota VALUES (?,?,?,?,?)", [
            ('11257061','deni','informatika','08123456789','Aktif'),
            ('2023001','Budi Santoso','Informatika','08123456789','Aktif'),
            ('2023002','Siti Aminah','Sistem Informasi','08234567890','Aktif'),
        ])
    if c.execute("SELECT COUNT(*) FROM buku").fetchone()[0]==0:
        c.executemany("INSERT INTO buku (judul,pengarang,kategori,no_panggil,stok,total,jenis) VALUES (?,?,?,?,?,?,?)", [
            ('Python Dasar','Andi Wijaya','Pemrograman','005.133 PYT',10,10,'Buku'),
            ('Jurnal AI Terapan 2024','Tim Dosen','AI','001.5 JUR',15,15,'Jurnal'),
            ('E-Book Basis Data','Eko Kurniawan','Database','005.74 EBO',100,100,'E-Book'),
            ('Repositori Skripsi Informatika 2023','Mahasiswa','Tugas Akhir','001.6 SKR',20,20,'Digital'),
        ])
    conn.commit(); conn.close()

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
*{font-family:'Poppins',sans-serif} body{background:#f6f8ff;margin:0}
.navbar{background:white;padding:14px 28px;display:flex;gap:20px;align-items:center;box-shadow:0 4px 20px rgba(0,0,0,.06);position:sticky;top:0;z-index:99}
.navbar a{color:#636e72;text-decoration:none;font-weight:600;padding:8px 16px;border-radius:20px;transition:.2s}
.navbar a:hover,.active{background:#6c5ce7;color:white!important}
.container{padding:28px;max-width:1250px;margin:auto}
.card{padding:22px;border-radius:20px;color:white;display:flex;justify-content:space-between;align-items:center;box-shadow:0 10px 25px rgba(0,0,0,.1);transition:.3s}
.card:hover{transform:translateY(-4px)} .c1{background:linear-gradient(135deg,#6c5ce7,#a29bfe)} .c2{background:linear-gradient(135deg,#00b894,#55efc4)} .c3{background:linear-gradient(135deg,#fdcb6e,#ffeaa7);color:#2d3436} .c4{background:linear-gradient(135deg,#e17055,#fab1a0)}
.box{background:white;padding:24px;border-radius:18px;box-shadow:0 8px 30px rgba(0,0,0,.05);margin-bottom:20px}
table{width:100%;border-collapse:separate;border-spacing:0;background:white;border-radius:16px;overflow:hidden;box-shadow:0 5px 20px rgba(0,0,0,.04)}
th{background:#f8f9ff;color:#6c5ce7;padding:14px;text-align:left} td{padding:13px;border-top:1px solid #f1f2f6}
.btn{padding:8px 16px;border-radius:20px;border:none;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;font-size:13px}
.btn-p{background:#6c5ce7;color:white} .btn-g{background:#00b894;color:white} .btn-r{background:#ff7675;color:white}
input,select,textarea{padding:11px 14px;border-radius:12px;border:1.5px solid #dfe6e9;width:100%;box-sizing:border-box;margin:6px 0;outline:none}
input:focus{border-color:#6c5ce7}
.badge{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}
</style>
"""

def base_nav(role):
    menu = f"""
    <div class="navbar"><div style="font-weight:800;color:#6c5ce7">📚 SIM PERPUS v3</div>
    <a href="/dashboard">Dashboard</a><a href="/opac">OPAC Katalog</a>
    """
    if role in ('admin','kepala'): menu+= '<a href="/anggota">Data Anggota</a><a href="/sirkulasi">Sirkulasi</a><a href="/laporan">Pelaporan</a>'
    menu+= '<a href="/pengadaan">Pengadaan & Upload</a><a href="/digital">Digital Library</a><a href="/bukutamu">Buku Tamu</a>'
    menu+= f'<span style="margin-left:auto">👤 {session.get("user")} ({role})</span><a href="/logout" style="background:#ffeaa7">Logout</a></div><div class="container">'
    return STYLE + menu

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form['username']; p=request.form['password']
        conn=get_db(); user=conn.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone(); conn.close()
        if user: session['user']=u; session['role']=user['role']; return redirect('/dashboard')
    return render_template_string(STYLE + """
    <div style="min-height:100vh;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;justify-content:center;align-items:center">
    <div class="box" style="width:380px;text-align:center"><div style="font-size:50px">🎓</div><h2>Login SIM Perpus</h2>
    <p style="color:#888;font-size:13px">admin/admin | kepala/kepala | 2023001/mhs | 11257061/deni</p>
    <form method="post"><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required><button class="btn btn-p" style="width:100%;padding:12px;margin-top:10px">Masuk</button></form>
    </div></div>""")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    conn=get_db()
    jb=conn.execute("SELECT COUNT(*) FROM buku").fetchone()[0]; st=conn.execute("SELECT SUM(stok) FROM buku").fetchone()[0] or 0
    ag=conn.execute("SELECT COUNT(*) FROM anggota").fetchone()[0]; pj=conn.execute("SELECT COUNT(*) FROM peminjaman WHERE status='dipinjam'").fetchone()[0]
    tamu=conn.execute("SELECT COUNT(*) FROM bukutamu WHERE date(tgl)=date('now')").fetchone()[0]
    denda_total=conn.execute("SELECT SUM(denda) FROM peminjaman").fetchone()[0] or 0
    conn.close()
    return render_template_string(base_nav(session['role']) + f"""
    <h2>Halo, {session['user']} 👋</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px">
        <div class="card c1"><div>📚 Koleksi<br><b>{jb} Jenis / {st} Stok</b></div>📖</div>
        <div class="card c2"><div>👨‍🎓 Anggota<br><b>{ag} Mahasiswa</b></div>🎓</div>
        <div class="card c3"><div>⏳ Dipinjam<br><b>{pj} Transaksi</b></div>🔥</div>
        <div class="card c4"><div>📝 Kunjungan Hari Ini<br><b>{tamu} Orang</b> | Denda Rp {denda_total}</div>📊</div>
    </div>
    <div class="box" style="margin-top:20px"><b>✅ 6 Modul Lengkap Aktif</b> : Data Anggota + OPAC + Sirkulasi + Pengadaan/Digitalisasi + Digital Library + Buku Tamu & Pelaporan</div></div>
    """)

@app.route('/opac')
def opac():
    if 'user' not in session: return redirect('/login')
    q=request.args.get('q',''); jenis=request.args.get('jenis','')
    conn=get_db()
    sql="SELECT * FROM buku WHERE (judul LIKE ? OR kategori LIKE ?)"
    params=[f"%{q}%",f"%{q}%"]
    if jenis: sql+=" AND jenis=?"; params.append(jenis)
    buku=conn.execute(sql, params).fetchall(); conn.close()
    return render_template_string(base_nav(session['role']) + """
    <h2>🔍 OPAC - Katalog Pencarian Mandiri</h2>
    <div class="box"><form><div style="display:flex;gap:10px"><input name="q" value="{{q}}" placeholder="Cari judul, kategori..."><select name="jenis"><option value="">Semua Jenis</option><option value="Buku">Buku</option><option value="Jurnal">Jurnal</option><option value="E-Book">E-Book</option><option value="Digital">Digital</option></select><button class="btn btn-p">Cari</button></div></form></div>
    <div class="box"><table><tr><th>No Panggil</th><th>Judul</th><th>Jenis</th><th>Stok</th></tr>
    {% for b in buku %}<tr><td><span class="badge" style="background:#f0f4ff;color:#6c5ce7">{{b['no_panggil']}}</span></td><td><b>{{b['judul']}}</b><br><small style="color:#888">{{b['pengarang']}} - {{b['kategori']}}</small></td><td>{{b['jenis']}}</td><td>{{b['stok']}}</td></tr>{% endfor %}</table></div></div>
    """, buku=buku, q=q)

@app.route('/sirkulasi')
def sirkulasi():
    if 'user' not in session: return redirect('/login')
    conn=get_db()
    for p in conn.execute("SELECT * FROM peminjaman WHERE status='dipinjam'").fetchall():
        tgl_kembali=datetime.strptime(p['tgl_kembali'],'%Y-%m-%d')
        if datetime.now() > tgl_kembali:
            hari=(datetime.now()-tgl_kembali).days
            denda=hari*1000
            conn.execute("UPDATE peminjaman SET denda=? WHERE id=?",(denda,p['id']))
    conn.commit()
    pinjam=conn.execute("SELECT peminjaman.*, buku.judul, anggota.nama FROM peminjaman JOIN buku ON peminjaman.buku_id=buku.id JOIN anggota ON peminjaman.nim=anggota.nim ORDER BY id DESC").fetchall()
    buku=conn.execute("SELECT * FROM buku WHERE stok>0").fetchall(); ag=conn.execute("SELECT * FROM anggota WHERE status='Aktif'").fetchall(); conn.close()
    return render_template_string(base_nav(session['role']) + """
<h2>🔄 Modul Sirkulasi Transaksi</h2>
<div class="box"><h3>Pinjam + Catatan Target Membaca</h3>
<form action="/pinjam" method="post" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
<select name="nim">{% for a in ag %}<option value="{{a['nim']}}">{{a['nim']}} - {{a['nama']}}</option>{% endfor %}</select>
<select name="buku_id">{% for b in buku %}<option value="{{b['id']}}">{{b['judul']}} ({{b['stok']}})</option>{% endfor %}</select>
<textarea name="catatan" placeholder="Target baca..." style="grid-column:span 2"></textarea>
<button class="btn btn-p" style="grid-column:span 2">Pinjam</button></form></div>
<div class="box"><table><tr><th>NIM</th><th>Buku</th><th>Tgl Kembali</th><th>Denda</th><th>Catatan</th><th>Aksi</th></tr>
{% for p in pinjam %}<tr><td>{{p['nim']}}<br><small>{{p['nama']}}</small></td><td>{{p['judul']}}</td><td>{{p['tgl_kembali']}}</td><td>Rp {{p['denda']}}</td><td>{{p['catatan']}}</td>
<td>{% if p['status']=='dipinjam' %}<a class="btn btn-g" href="/kembali/{{p['id']}}">Kembali</a> <a class="btn btn-p" href="/perpanjang/{{p['id']}}">Perpanjang</a> <a class="btn btn-r" href="/rusak/{{p['id']}}">Rusak/Hilang</a>{% else %}✅ {{p['status']}}{% endif %}</td></tr>{% endfor %}</table></div></div>
""", pinjam=pinjam, buku=buku, ag=ag)
@app.route('/pinjam', methods=['POST'])
def pinjam():
    conn=get_db(); conn.execute("UPDATE buku SET stok=stok-1 WHERE id=?",(request.form['buku_id'],))
    conn.execute("INSERT INTO peminjaman (nim,buku_id,tgl_pinjam,tgl_kembali,status,catatan) VALUES (?,?,?,?,?,?)",
                 (request.form['nim'],request.form['buku_id'],datetime.now().strftime('%Y-%m-%d'),(datetime.now()+timedelta(days=7)).strftime('%Y-%m-%d'),'dipinjam',request.form['catatan'])); conn.commit(); conn.close(); return redirect('/sirkulasi')

@app.route('/kembali/<int:id>')
def kembali(id):
    conn=get_db(); p=conn.execute("SELECT * FROM peminjaman WHERE id=?",(id,)).fetchone()
    if p: conn.execute("UPDATE buku SET stok=stok+1 WHERE id=?",(p['buku_id'],)); conn.execute("UPDATE peminjaman SET status='kembali', tgl_dikembalikan=? WHERE id=?",(datetime.now().strftime('%Y-%m-%d'),id))
    conn.commit(); conn.close(); return redirect('/sirkulasi')

@app.route('/rusak/<int:id>')
def rusak(id):
    conn=get_db()
    p=conn.execute("SELECT * FROM peminjaman WHERE id=?",(id,)).fetchone()
    if p:
        # Buku rusak = stok gak balik, kena denda 50rb
        conn.execute("UPDATE peminjaman SET status='rusak', denda=50000, tgl_dikembalikan=? WHERE id=?",(datetime.now().strftime('%Y-%m-%d'),id))
        # gak usah tambah stok, karena buku rusak
    conn.commit(); conn.close()
    return redirect('/sirkulasi')

@app.route('/perpanjang/<int:id>')
def perpanjang(id):
    conn=get_db(); p=conn.execute("SELECT * FROM peminjaman WHERE id=?",(id,)).fetchone()
    if p: new_tgl=(datetime.strptime(p['tgl_kembali'],'%Y-%m-%d')+timedelta(days=7)).strftime('%Y-%m-%d'); conn.execute("UPDATE peminjaman SET tgl_kembali=? WHERE id=?",(new_tgl,id)); conn.commit()
    conn.close(); return redirect('/sirkulasi')

@app.route('/anggota', methods=['GET','POST'])
def anggota():
    if 'user' not in session: return redirect('/login')
    conn=get_db()
    if request.method=='POST':
        try: conn.execute("INSERT INTO anggota VALUES (?,?,?,?,?)",(request.form['nim'],request.form['nama'],request.form['prodi'],request.form['telp'],'Aktif')); conn.execute("INSERT OR IGNORE INTO users VALUES (NULL,?,?,'mahasiswa')",(request.form['nim'],request.form['nim'])); conn.commit()
        except: pass
    ag=conn.execute("SELECT * FROM anggota").fetchall(); conn.close()
    return render_template_string(base_nav(session['role']) + """
    <h2>👨‍🎓 Modul Data Anggota + Cetak Kartu</h2>
    <div class="box"><form method="post" style="display:flex;gap:8px;flex-wrap:wrap"><input name="nim" placeholder="NIM" required style="width:120px"><input name="nama" placeholder="Nama" required style="width:180px"><input name="prodi" placeholder="Prodi" required style="width:150px"><input name="telp" placeholder="No HP" required style="width:130px"><button class="btn btn-p">Tambah Anggota</button></form></div>
    <div class="box"><table><tr><th>NIM</th><th>Nama</th><th>Prodi</th><th>Telp</th><th>Status</th><th>Kartu</th></tr>
    {% for a in ag %}<tr><td>{{a['nim']}}</td><td>{{a['nama']}}</td><td>{{a['prodi']}}</td><td>{{a['telp']}}</td><td><span class="badge" style="background:#00b894;color:white">{{a['status']}}</span></td><td><a class="btn btn-p" href="/cetak_kartu/{{a['nim']}}">🪪 Cetak Kartu Estetik</a></td></tr>{% endfor %}</table></div></div>
    """, ag=ag)

# ==== KARTU ESTETIK VERSI PERTAMA YANG BAGUSAN ====
@app.route('/cetak_kartu/<nim>')
def cetak_kartu(nim):
    conn=get_db(); a=conn.execute("SELECT * FROM anggota WHERE nim=?",(nim,)).fetchone(); conn.close()
    return render_template_string("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');
    *{font-family:'Poppins',sans-serif}
    body{background:#f0f2ff;display:flex;justify-content:center;padding:30px;margin:0}
    @media print { body{background:white} .no-print{display:none} }
    .card{width:360px;height:220px;background:linear-gradient(135deg,#6c5ce7,#a29bfe);border-radius:18px;color:white;padding:18px;position:relative;box-shadow:0 15px 35px rgba(108,92,231,.4)}
    .card-header{font-weight:800;font-size:12px;letter-spacing:1px;opacity:.9;border-bottom:1px solid rgba(255,255,255,.3);padding-bottom:8px;margin-bottom:12px}
    .card-body{display:flex;gap:14px}
    .photo{width:75px;height:90px;background:white;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:40px;color:#6c5ce7}
    .info{font-size:12px;line-height:1.6}
    .barcode{position:absolute;bottom:14px;right:18px;background:white;color:#2d3436;padding:4px 10px;border-radius:6px;font-size:10px;font-weight:700}
    </style>
    <div>
    <div class="card">
        <div class="card-header">KARTU ANGGOTA PERPUSTAKAAN - UNIVERSITAS</div>
        <div class="card-body">
            <div class="photo">👤</div>
            <div class="info">
                <div style="font-size:15px;font-weight:800">{{a['nama'].upper()}}</div>
                NIM: {{a['nim']}}<br>
                Prodi: {{a['prodi']}}<br>
                Status: <span style="background:#00b894;padding:2px 8px;border-radius:10px;font-size:10px">{{a['status']}}</span><br>
                <small>Berlaku s/d 2027</small>
            </div>
        </div>
        <div class="barcode">|| ||| {{a['nim']}} |||</div>
    </div>
    <div style="text-align:center;margin-top:18px"><button onclick="window.print()" style="padding:10px 22px;border-radius:20px;border:none;background:#6c5ce7;color:white;font-weight:700;cursor:pointer">🖨️ Print Kartu Estetik</button>
    <br><br><a href="/anggota" style="color:#636e72;text-decoration:none;font-size:13px">← Kembali</a></div>
    </div>
    """, a=a)

@app.route('/pengadaan', methods=['GET','POST'])
def pengadaan():
    if 'user' not in session: return redirect('/login')
    conn=get_db()
    if request.method=='POST':
        if 'judul_usul' in request.form: conn.execute("INSERT INTO usulan (nim,judul,pengarang,alasan) VALUES (?,?,?,?)",(session['user'],request.form['judul_usul'],request.form['pengarang'],request.form['alasan']))
        else: conn.execute("INSERT INTO karya (nim,judul,tahun,file_name) VALUES (?,?,?,?)",(session['user'],request.form['judul_karya'],request.form['tahun'],request.form['file_name']))
        conn.commit()
    usulan=conn.execute("SELECT * FROM usulan ORDER BY id DESC").fetchall(); karya=conn.execute("SELECT * FROM karya ORDER BY id DESC").fetchall(); conn.close()
    return render_template_string(base_nav(session['role']) + """
    <h2>📦 Pengadaan & Digitalisasi</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div class="box"><h3>📝 Usulan Buku Baru</h3><form method="post"><input name="judul_usul" placeholder="Judul Buku" required><input name="pengarang" placeholder="Pengarang" required><textarea name="alasan" placeholder="Alasan usulan..." required></textarea><button class="btn btn-p" style="width:100%">Kirim Usulan</button></form></div>
    <div class="box"><h3>📤 Self-Upload Karya Ilmiah / TA</h3><form method="post"><input name="judul_karya" placeholder="Judul TA / Skripsi" required><input name="tahun" placeholder="Tahun" required><input name="file_name" placeholder="skripsi_budi.pdf" required><button class="btn btn-g" style="width:100%">Upload Karya</button></form></div>
    </div>
    <div class="box"><h3>📋 Daftar Usulan</h3><table><tr><th>NIM</th><th>Judul</th><th>Status</th>{% if session['role']!='mahasiswa' %}<th>Verifikasi</th>{% endif %}</tr>
    {% for u in usulan %}<tr><td>{{u['nim']}}</td><td>{{u['judul']}}</td><td><span class="badge" style="background:#fdcb6e">{{u['status']}}</span></td>{% if session['role']!='mahasiswa' %}<td><a class="btn btn-g" href="/verif_usulan/{{u['id']}}">Setujui</a></td>{% endif %}</tr>{% endfor %}</table></div>
    <div class="box"><h3>📚 Koleksi Karya Terupload</h3><table><tr><th>NIM</th><th>Judul</th><th>Tahun</th><th>File</th></tr>{% for k in karya %}<tr><td>{{k['nim']}}</td><td>{{k['judul']}}</td><td>{{k['tahun']}}</td><td>{{k['file_name']}}</td></tr>{% endfor %}</table></div></div>
    """, usulan=usulan, karya=karya)

@app.route('/setujui_usulan/<int:id>')
def setujui_usulan(id):
    conn=get_db()
    u = conn.execute("SELECT * FROM usulan WHERE id=?",(id,)).fetchone()
    if u:
        judul = u['judul'].replace('stok 20','').replace('stok','').strip() # bersihin jadi 'algoritma'
        # Tambah ke OPAC sebagai buku baru dengan stok 20
        conn.execute("INSERT INTO buku (judul, pengarang, kategori, stok, no_panggil) VALUES (?,?,?,?,?)",
                     (judul.title(), u['nim'], 'Pemrograman', 20, f'005.{id} ALG'))
        conn.execute("UPDATE usulan SET status='Disetujui' WHERE id=?",(id,))
    conn.commit(); conn.close()
    return redirect('/opac') # biar abis klik langsung ke OPAC

@app.route('/verif_usulan/<int:id>')
@app.route('/verifikasi/<int:id>')
@app.route('/setujui/<int:id>')
@app.route('/setujui_usulan/<int:id>')
def verif_usulan(id):
    conn=get_db()
    u = conn.execute("SELECT * FROM usulan WHERE id=?",(id,)).fetchone()
    if u:
        judul_bersih = u['judul'].lower().replace('stok 20','').replace('stok','').strip().title()
        if judul_bersih == "":
            judul_bersih = "Algoritma"
        
        # Langsung masukin ke OPAC dengan stok 20
        cek = conn.execute("SELECT * FROM buku WHERE judul LIKE ?", ('%'+judul_bersih+'%',)).fetchone()
        if cek:
            conn.execute("UPDATE buku SET stok = stok + 20 WHERE id=?", (cek['id'],))
        else:
            conn.execute("INSERT INTO buku (judul, pengarang, kategori, stok, no_panggil) VALUES (?,?,?,?,?)",
                         (judul_bersih, u['nim'], 'Pemrograman', 20, f'005.{id} ALG'))
        
        conn.execute("UPDATE usulan SET status='Disetujui' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/opac')

@app.route('/digital')
def digital():
    if 'user' not in session: return redirect('/login')
    conn=get_db(); ebook=conn.execute("SELECT * FROM buku WHERE jenis IN ('E-Book','Digital','Jurnal')").fetchall(); conn.close()
    return render_template_string(base_nav(session['role']) + """
    <h2>💻 Perpustakaan Digital</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px">
    {% for b in ebook %}
    <div class="box" style="text-align:center"><div style="font-size:45px">📘</div>
    <b>{{b['judul']}}</b><br><small style="color:#888">{{b['jenis']}} | {{b['no_panggil']}} | Stok: {{b['stok']}}</small><br><br>
    <a class="btn btn-p" href="/baca/{{b['id']}}">📖 Baca Online</a> 
    <a class="btn btn-g" href="/download/{{b['id']}}">⬇️ Download</a>
    <a class="btn btn-r" href="/hapus_buku/{{b['id']}}" style="margin-top:8px" onclick="return confirm('Hapus buku ini?')">🗑️ Hapus</a>
    </div>{% endfor %}
    </div>
    <div class="box" style="margin-top:20px"><h3>➕ Tambah Buku / Jurnal / E-Book Baru</h3>
    <form action="/tambah_buku" method="post" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
    <input name="judul" placeholder="Judul Buku" required><input name="pengarang" placeholder="Pengarang" required>
    <input name="kategori" placeholder="Kategori: Pemrograman/AI/Database" required><input name="no_panggil" placeholder="No Panggil: 005.133 PYT" required>
    <select name="jenis"><option value="Buku">Buku</option><option value="Jurnal">Jurnal</option><option value="E-Book">E-Book</option><option value="Digital">Digital</option></select>
    <input name="stok" type="number" placeholder="Jumlah Stok" required>
    <button class="btn btn-p" style="grid-column:span 2">📚 Tambah Koleksi</button>
    </form>
    <small style="color:#888">Ini buat nambah buku, nambah stok, sama ngatur kerusakan (tinggal edit stok jadi 0)</small>
    </div></div>
    """, ebook=ebook)

@app.route('/baca/<int:id>')
def baca(id):
    conn=get_db(); b=conn.execute("SELECT * FROM buku WHERE id=?",(id,)).fetchone(); conn.close()
    return render_template_string(STYLE + """
    <div style="padding:30px;max-width:900px;margin:auto;background:white;min-height:100vh">
    <a href="/digital" class="btn btn-p">← Kembali</a>
    <h2>📖 Sedang Membaca: {{b['judul']}}</h2>
    <p style="color:#888">{{b['pengarang']}} | {{b['jenis']}} | {{b['no_panggil']}}</p>
    <div style="background:#f8f9ff;border:2px dashed #6c5ce7;border-radius:16px;padding:40px;text-align:center;margin-top:20px">
        <div style="font-size:60px">📄</div>
        <h3>Preview PDF - {{b['judul']}}</h3>
        <p style="color:#888">Ini adalah simulasi viewer PDF.<br>Di skripsi asli nanti bisa dihubungkan ke file PDF beneran di folder /static/pdf/</p>
        <div style="background:white;padding:20px;text-align:left;border-radius:12px;margin-top:15px;font-size:13px;line-height:1.8;color:#2d3436">
        <b>BAB I PENDAHULUAN</b><br>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ini isi dari {{b['judul']}}...<br><br>
        <b>BAB II LANDASAN TEORI</b><br>
        {{b['kategori']}} merupakan salah satu bidang yang berkembang pesat...
        </div>
        <br><a href="/download/{{b['id']}}" class="btn btn-g">⬇️ Download Full PDF</a>
    </div></div>
    """, b=b)

@app.route('/download/<int:id>')
def download(id):
    conn=get_db(); b=conn.execute("SELECT * FROM buku WHERE id=?",(id,)).fetchone(); conn.close()
    # bikin file PDF dummy biar bisa ke-download
    from io import BytesIO
    from flask import send_file
    pdf_content = f"Judul: {b['judul']}\nPengarang: {b['pengarang']}\nJenis: {b['jenis']}\nIni adalah file dummy untuk demo skripsi.".encode()
    return send_file(BytesIO(pdf_content), as_attachment=True, download_name=f"{b['judul']}.pdf")

@app.route('/tambah_buku', methods=['POST'])
def tambah_buku():
    conn=get_db()
    conn.execute("INSERT INTO buku (judul,pengarang,kategori,no_panggil,stok,total,jenis) VALUES (?,?,?,?,?,?,?)",
                 (request.form['judul'],request.form['pengarang'],request.form['kategori'],request.form['no_panggil'],int(request.form['stok']),int(request.form['stok']),request.form['jenis']))
    conn.commit(); conn.close()
    return redirect('/digital')

@app.route('/hapus_buku/<int:id>')
def hapus_buku(id):
    conn=get_db(); conn.execute("DELETE FROM buku WHERE id=?",(id,)); conn.commit(); conn.close()
    return redirect('/digital')

@app.route('/bukutamu', methods=['GET','POST'])
def bukutamu():
    if 'user' not in session: return redirect('/login')
    conn=get_db()
    if request.method=='POST': conn.execute("INSERT INTO bukutamu (nim,tujuan,tgl) VALUES (?,?,?)",(request.form['nim'],request.form['tujuan'],datetime.now().strftime('%Y-%m-%d %H:%M:%S'))); conn.commit()
    tamu=conn.execute("SELECT bukutamu.*, anggota.nama FROM bukutamu JOIN anggota ON bukutamu.nim=anggota.nim ORDER BY id DESC LIMIT 50").fetchall()
    anggota_list=conn.execute("SELECT * FROM anggota").fetchall(); conn.close()
    return render_template_string(base_nav(session['role']) + """
    <h2>📝 Buku Tamu & Kunjungan Digital</h2>
    <div class="box"><form method="post" style="display:flex;gap:10px"><input name="nim" list="daftar-nim" autocomplete="off" placeholder="Scan NIM / Ketik NIM" required style="width:200px"><datalist id="daftar-nim">{% for a in anggota_list %}<option value="{{a['nim']}}">{{a['nama']}} - {{a['nim']}}</option>{% endfor %}</datalist><input name="tujuan" placeholder="Tujuan: Baca, Pinjam, dll" required><button class="btn btn-p">✅ Check-In Kunjungan</button></form><small style="color:#888">Udah fix, gak muncul 34668276 lagi</small></div>
    <div class="box"><table><tr><th>Waktu</th><th>NIM - Nama</th><th>Tujuan</th></tr>{% for t in tamu %}<tr><td>{{t['tgl']}}</td><td>{{t['nim']}} - {{t['nama']}}</td><td>{{t['tujuan']}}</td></tr>{% endfor %}</table></div></div>
    """, tamu=tamu, anggota_list=anggota_list)

@app.route('/laporan')
def laporan():
    if session.get('role') not in ('admin','kepala'): return redirect('/dashboard')
    conn=get_db()
    lap_buku=conn.execute("SELECT * FROM buku").fetchall()
    lap_pinjam=conn.execute("SELECT peminjaman.*, anggota.nama, buku.judul FROM peminjaman JOIN anggota ON peminjaman.nim=anggota.nim JOIN buku ON peminjaman.buku_id=buku.id").fetchall()
    lap_tamu=conn.execute("SELECT date(tgl) as tgl, COUNT(*) as jml FROM bukutamu GROUP BY date(tgl) ORDER BY tgl DESC").fetchall()
    conn.close()
    return render_template_string(base_nav(session['role']) + """
    <h2>📊 Dasbor Laporan Real-Time</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div class="box"><h3>📈 Laporan Kunjungan Harian</h3><table><tr><th>Tanggal</th><th>Jumlah</th></tr>{% for l in lap_tamu %}<tr><td>{{l['tgl']}}</td><td>{{l['jml']}} orang</td></tr>{% endfor %}</table><br><button class="btn btn-p" onclick="window.print()">🖨️ Cetak</button></div>
    <div class="box"><h3>📦 Laporan Inventaris</h3><table><tr><th>Judul</th><th>Stok</th><th>No Panggil</th></tr>{% for b in lap_buku %}<tr><td>{{b['judul']}}</td><td>{{b['stok']}}/{{b['total']}}</td><td>{{b['no_panggil']}}</td></tr>{% endfor %}</table><br><button class="btn btn-p" onclick="window.print()">🖨️ Cetak</button></div>
    </div>
    <div class="box"><h3>🔄 Laporan Sirkulasi & Denda</h3><table><tr><th>NIM</th><th>Buku</th><th>Status</th><th>Denda</th></tr>{% for p in lap_pinjam %}<tr><td>{{p['nim']}}</td><td>{{p['judul']}}</td><td>{{p['status']}}</td><td>Rp {{p['denda']}}</td></tr>{% endfor %}</table><br><button class="btn btn-g" onclick="window.print()">🖨️ Cetak Rekap</button></div></div>
    """, lap_buku=lap_buku, lap_pinjam=lap_pinjam, lap_tamu=lap_tamu)

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

# TAMBAH BUKU MANUAL BUAT ADMIN
# TAMBAH BUKU MANUAL BUAT ADMIN
@app.route('/tambah_buku', methods=['GET','POST'])
def tambah_buku_manual():   # <-- GANTI NAMA INI, tadinya tambah_buku
    if request.method == 'POST':
        conn=get_db()
        conn.execute("INSERT INTO buku (no_panggil, judul, pengarang, kategori, jenis, stok) VALUES (?,?,?,?,?,?)",
                     (request.form['no_panggil'],
                      request.form['judul'],
                      request.form['pengarang'],
                      request.form['kategori'],
                      request.form['jenis'],
                      int(request.form['stok'])))
        conn.commit(); conn.close()
        return redirect('/opac')
    
    # Form simpelnya
    return """
    <div style='max-width:500px;margin:50px auto;font-family:sans-serif'>
    <h2>+ Tambah Buku Baru</h2>
    <form method=POST>
        No Panggil: <input name=no_panggil value='005.1 ALG' style='width:100%;padding:8px;margin:5px 0'><br>
        Judul: <input name=judul placeholder='ex: Algoritma' required style='width:100%;padding:8px;margin:5px 0'><br>
        Pengarang: <input name=pengarang placeholder='ex: Eko Kurniawan' required style='width:100%;padding:8px;margin:5px 0'><br>
        Kategori: <input name=kategori value='Pemrograman' style='width:100%;padding:8px;margin:5px 0'><br>
        Jenis: 
        <select name=jenis style='width:100%;padding:8px;margin:5px 0'>
            <option>Buku</option><option>Jurnal</option><option>Skripsi</option><option>E-Book</option>
        </select><br>
        Stok: <input type=number name=stok value='20' required style='width:100%;padding:8px;margin:5px 0'><br>
        <button type=submit style='background:blue;color:white;padding:10px 20px;width:100%;border:none;border-radius:5px;margin-top:10px'>Simpan ke OPAC</button>
    </form>
    <a href='/opac'>Kembali ke OPAC</a>
    </div>
    """

if __name__=='__main__':
    init_db(); app.run(debug=True)