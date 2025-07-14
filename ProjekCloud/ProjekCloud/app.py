from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
import random

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        database=os.environ.get('DB_NAME', 'resepku')
    )
    return conn

# --- DB Init ---
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS resep (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(255) NOT NULL,
            deskripsi TEXT,
            bahan TEXT NOT NULL,
            langkah TEXT NOT NULL,
            sudah_dicoba TINYINT DEFAULT 0
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# --- Home: Daftar Resep ---
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM resep ORDER BY id DESC')
    resep_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', resep_list=resep_list)

# --- Tambah Resep ---
@app.route('/tambah', methods=['GET', 'POST'])
def tambah():
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        bahan = request.form['bahan']
        langkah = request.form['langkah']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO resep (nama, deskripsi, bahan, langkah) VALUES (%s, %s, %s, %s)',
                    (nama, deskripsi, bahan, langkah))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('tambah.html')

# --- Lihat Detail Resep & Checklist Belanja ---
@app.route('/resep/<int:resep_id>', methods=['GET', 'POST'])
def detail_resep(resep_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM resep WHERE id=%s', (resep_id,))
    resep = cur.fetchone()
    cur.close()
    conn.close()
    if not resep:
        return 'Resep tidak ditemukan', 404
    # Bahan dipecah per baris
    bahan_list = [b.strip() for b in resep['bahan'].split('\n') if b.strip()]
    checklist = request.form.getlist('checklist') if request.method == 'POST' else []
    return render_template('detail.html', resep=resep, bahan_list=bahan_list, checklist=checklist)

# --- Tandai Sudah Dicoba ---
@app.route('/resep/<int:resep_id>/coba', methods=['POST'])
def tandai_dicoba(resep_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE resep SET sudah_dicoba=1 WHERE id=%s', (resep_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('detail_resep', resep_id=resep_id))

# --- Hapus Resep ---
@app.route('/resep/<int:resep_id>/hapus', methods=['POST'])
def hapus_resep(resep_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM resep WHERE id=%s', (resep_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

# --- Edit Resep ---
@app.route('/resep/<int:resep_id>/edit', methods=['GET', 'POST'])
def edit_resep(resep_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM resep WHERE id=%s', (resep_id,))
    resep = cur.fetchone()
    if not resep:
        cur.close()
        conn.close()
        return 'Resep tidak ditemukan', 404
    if request.method == 'POST':
        nama = request.form['nama']
        deskripsi = request.form['deskripsi']
        bahan = request.form['bahan']
        langkah = request.form['langkah']
        cur2 = conn.cursor()
        cur2.execute('UPDATE resep SET nama=%s, deskripsi=%s, bahan=%s, langkah=%s WHERE id=%s',
                     (nama, deskripsi, bahan, langkah, resep_id))
        conn.commit()
        cur2.close()
        cur.close()
        conn.close()
        return redirect(url_for('detail_resep', resep_id=resep_id))
    cur.close()
    conn.close()
    return render_template('edit.html', resep=resep)

# --- Riwayat Masakan Dicoba ---
@app.route('/riwayat')
def riwayat():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM resep WHERE sudah_dicoba=1 ORDER BY id DESC')
    resep_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('riwayat.html', resep_list=resep_list)

@app.route('/cari', methods=['GET', 'POST'])
def cari_resep():
    hasil = []
    bahan_input = ''
    if request.method == 'POST':
        bahan_input = request.form['bahan']
        bahan_list = [b.strip().lower() for b in bahan_input.split(',') if b.strip()]
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM resep')
        resep_list = cur.fetchall()
        cur.close()
        conn.close()
        for resep in resep_list:
            bahan_resep = [b.strip().lower() for b in resep['bahan'].split('\n') if b.strip()]
            # Cek apakah semua bahan input ada di bahan resep
            if all(any(bahan in b for b in bahan_resep) for bahan in bahan_list):
                hasil.append(resep)
    return render_template('cari.html', hasil=hasil, bahan_input=bahan_input)

@app.route('/random')
def resep_random():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM resep')
    resep_list = cur.fetchall()
    cur.close()
    conn.close()
    if not resep_list:
        return render_template('random.html', resep=None)
    resep = random.choice(resep_list)
    return render_template('random.html', resep=resep)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000) 