import math
import uuid
from flask import Flask, render_template, request, redirect, url_for, session
from functools import reduce
from generate import GenerateFurniturePosition
from testing import AreaCalculator

app = Flask(__name__)
app.secret_key = 'furnitur_secret_key'

def compute_grid(kost_length, kost_width, furnitures, max_grid=8):
    """
    kost_length, kost_width: ukuran kos dalam meter (int atau float, tapi di sini diasumsikan int atau float yang mewakili meter utuh atau desimal).
    furnitures: list of dict, setiap dict punya 'length' dan 'width' dalam meter (angka int atau float).
    max_grid: batas maksimal grid per dimensi (default 10).
    
    Mengembalikan:
      - rows, cols: ukuran grid ruangan dalam sel (int),
      - furn_grid: list dict furnitur dengan 'length','width' sebagai ukuran dalam sel integer, dan 'matrix' dibangun ulang,
      - cell_meter: ukuran sel dalam meter (float).
    Jika tidak ditemukan skala exact yang menghasilkan grid ≤ max_grid, akan fallback dengan cell_meter minimal agar grid ≤ max_grid (approximate).
    """
    # Ambil ukuran kos (meter)
    L = float(kost_length)
    W = float(kost_width)
    # Pertama coba exact: cari gcd integer untuk ukuran meter utuh jika semua integer.
    # Jika L,W dan furn lengths/lebar adalah integer: lakukan gcd.
    # Jika tidak integer, kita fallback langsung ke approximate.
    # Cek apakah semua ukuran adalah integer (misal 5.0 dianggap integer).
    def is_int_val(x):
        # Cek float mewakili integer
        return abs(x - round(x)) < 1e-9

    all_int = is_int_val(L) and is_int_val(W) and all(is_int_val(f['length']) and is_int_val(f['width']) for f in furnitures)
    cell_meter = None
    rows = cols = None

    if all_int:
        # Hitung gcd dari semua dimensi (integer)
        dims = [int(round(L)), int(round(W))]
        for f in furnitures:
            dims.append(int(round(f['length'])))
            dims.append(int(round(f['width'])))
        # gcd_all_int: gcd dari semua dims
        gcd_all = reduce(math.gcd, dims)
        # Coba pakai cell_meter = gcd_all
        cm = float(gcd_all)  # dalam meter
        # Hitung grid size
        r = int(round(L / cm))
        c = int(round(W / cm))
        # Pastikan tepat integer: karena pembagian ints oleh gcd_all harus integer
        # Cek ≤ max_grid
        if r <= max_grid and c <= max_grid:
            cell_meter = cm
            rows, cols = r, c
        else:
            # Jika r atau c > max_grid, fallback approximate:
            # Cari cell_meter minimal agar grid ≤ max_grid:
            # cell_meter >= L/max_grid dan >= W/max_grid
            cm_req = max(L / max_grid, W / max_grid)
            # Bulatkan ke atas ke angka meter utuh (atau desimal? Karena kita pakai meter utuh di input).
            # Misal L=8, max_grid=10: 8/10=0.8 → ceil ke 1 meter sel: grid 8x8 still >10? 8<=10 OK.
            # Untuk L=20, max_grid=10: 20/10=2 → cm=2m: grid 10x...
            # Kita round up ke integer meter: cell_meter = ceil(cm_req)
            cell_meter = float(math.ceil(cm_req))
            # Hitung rows, cols
            rows = math.ceil(L / cell_meter)
            cols = math.ceil(W / cell_meter)
            # rows,cols kini ≤ max_grid guaranteed by cara hitung cm_req
    else:
        # Jika ada ukuran desimal, langsung fallback approximate:
        # Tentukan cell_meter minimal agar grid ≤ max_grid:
        cm_req = max(L / max_grid, W / max_grid)
        # Kita pilih cell_meter = cm_req (float), tapi untuk mempermudah konversi ke sel integer, kita gunakan cell_meter sebagai float.
        # Atau bulatkan ke 0.1, 0.01? Di sini kita gunakan cell_meter = cm_req tanpa pembulatan, lalu lakukan ceil untuk sel furnitur.
        # Namun cell_meter terlalu kecil (desimal) bisa menghasilkan banyak sel; tetapi karena cm_req = L/max_grid jadi rows <= max_grid.
        cell_meter = cm_req
        rows = math.ceil(L / cell_meter)
        cols = math.ceil(W / cell_meter)
        # Hasil rows,cols <= max_grid
    # Pastikan cell_meter, rows, cols telah di-set
    if cell_meter is None or rows is None or cols is None:
        # Sebagai fallback aman: 1 meter per sel
        cell_meter = 1.0
        rows = math.ceil(L / cell_meter)
        cols = math.ceil(W / cell_meter)
        # Jika masih > max_grid, kita tetap biarkan; UI nanti beri peringatan
    # Konversi furnitures ke grid
    furn_grid = []
    for f in furnitures:
        fl = float(f['length'])
        fw = float(f['width'])
        # Hitung ukuran sel furnitur: ceil
        fr = max(1, int(math.ceil(fl / cell_meter)))
        fc = max(1, int(math.ceil(fw / cell_meter)))
        furn_item = {
            'id': f.get('id'),  # Pastikan id ikut diteruskan ke grid generator
            'name': f.get('name', ''),
            'length': fr,
            'width': fc,
            'matrix': [[1 for _ in range(fc)] for _ in range(fr)]
        }
        furn_grid.append(furn_item)
    return rows, cols, cell_meter, furn_grid

@app.route('/', methods=['GET', 'POST'])
def input_furniture():
    if 'furnitures' not in session:
        session['furnitures'] = []
        
    # default kos: bisa sebagai integer meter
    if 'kost_length' not in session or not session.get('kost_length'):
        session['kost_length'] = 300
    if 'kost_width' not in session or not session.get('kost_width'):
        session['kost_width'] = 300
    # default grid & ukuran terakhir
    if 'rows' not in session or 'cols' not in session:
        # awalnya grid sesuai ukuran kos default
        session['rows'] = int(session['kost_length'])
        session['cols'] = int(session['kost_width'])
    if 'grid' not in session:
        session['grid'] = [[0 for _ in range(session['cols'])] for _ in range(session['rows'])]
    if 'grid_scale' not in session:
        session['grid_scale'] = 100  # default 1 sel = 100 cm (1m)

    best_alternatives = []
    best_alternatives_scores = []
    if request.method == 'POST':
        # 1. Cek input ukuran kos (form input kos) tanpa furnitur
        if 'kost_length' in request.form and 'kost_width' in request.form \
           and not ('name' in request.form and 'length' in request.form and 'width' in request.form):
            # Ambil ukuran meter (integer string)
            length_val = request.form.get('kost_length')
            width_val  = request.form.get('kost_width')
            # Simpan sebagai integer (atau float jika perlu)
            try:
                kl = int(length_val) if length_val else 1.0
            except:
                kl = 1.0
            try:
                kw = int(width_val) if width_val else 1.0
            except:
                kw = 1.0
            # Simpan ke session
            session['kost_length'] = kl
            session['kost_width']  = kw
            # Reset furnitures karena ukuran kos berubah
            session['furnitures'] = []
            # Reset grid sesuai meter awal (sementara)
            # Kita tentukan rows,cols dan grid saat generate nanti
            session['rows'] = int(max(1, round(kl)))
            session['cols'] = int(max(1, round(kw)))
            session['grid'] = [[0 for _ in range(session['cols'])] for _ in range(session['rows'])]
            session['grid_scale'] = 100  # default fallback
            session.modified = True

        # 2. Input furnitur (tanpa generate langsung)
        elif 'name' in request.form and 'length' in request.form and 'width' in request.form:
            name = request.form.get('name', '').strip()
            length_val = request.form.get('length','')
            width_val  = request.form.get('width','')
            try:
                fl = float(length_val) if length_val else 1.0
            except:
                fl = 1.0
            try:
                fw = float(width_val) if width_val else 1.0
            except:
                fw = 1.0
            if name:
                furn = {
                    'id': uuid.uuid4().hex,  # Tambahkan id unik
                    'name': name,
                    'length': fl,
                    'width': fw,
                    'matrix': [[1 for _ in range(max(1, round(fw)))] for _ in range(max(1, round(fl)))]
                }
                session['furnitures'].append(furn)
                session.modified = True

        # 3. Setelah possible update di atas, lakukan generate grid dan tata letak
        #    (Tanpa cek tombol generate khusus, seperti di kode-mu sekarang: setiap POST akan update grid jika furnitures ada)
        if session['furnitures']:
            # Hitung grid berdasarkan meter-to-grid
            kl = session['kost_length']
            kw = session['kost_width']
            furnitures = session['furnitures']
            rows, cols, cell_meter, furn_grid = compute_grid(kl, kw, furnitures, max_grid=10)
            # Simpan rows, cols, dan skala grid
            session['rows'] = rows
            session['cols'] = cols
            # grid_scale dalam cm: cell_meter (m) * 100
            try:
                session['grid_scale'] = int(round(cell_meter * 100))
            except:
                session['grid_scale'] = cell_meter * 100
            # Generate layout
            gen = GenerateFurniturePosition(rows, cols, furn_grid)
            results, results_scores = gen.generate()
            if results:
                session['grid'] = results[0]
                # Hitung skor untuk layout terpilih
                area_calc = AreaCalculator()
                scoring = area_calc.score_layout(session['grid'], furn_grid, gen.count_filled_sides)
                session['scoring'] = scoring
                best_alternatives = results[1:4] if len(results) > 1 else []
                best_alternatives_scores = results_scores[1:4] if len(results_scores) > 1 else []
            else:
                session['grid'] = [[0 for _ in range(cols)] for _ in range(rows)]
                session['scoring'] = None
                best_alternatives = []
                best_alternatives_scores = []
        else:
            # Tanpa furnitur: reset grid sesuai ukuran kos (meter dibulatkan)
            session['rows'] = int(max(1, round(session['kost_length'])))
            session['cols'] = int(max(1, round(session['kost_width'])))
            session['grid'] = [[0 for _ in range(session['cols'])] for _ in range(session['rows'])]
            session['grid_scale'] = 100
            session['scoring'] = None
            best_alternatives = []
            best_alternatives_scores = []
        session['best_alternatives'] = best_alternatives
        session['best_alternatives_scores'] = best_alternatives_scores
        return redirect(url_for('input_furniture'))

    # GET: render template, pakai rows, cols dari session
    best_alternatives = session.get('best_alternatives', [])
    best_alternatives_scores = session.get('best_alternatives_scores', [])
    best_alternatives_zipped = list(zip(best_alternatives, best_alternatives_scores))
    return render_template('index.html',
                           furnitures=session.get('furnitures', []),
                           grid=session.get('grid', [[0]*session.get('cols',6) for _ in range(session.get('rows',6))]),
                           rows=int(session.get('rows',6)),
                           cols=int(session.get('cols',6)),
                           kost_length=session.get('kost_length',300),
                           kost_width=session.get('kost_width',300),
                           grid_scale=session.get('grid_scale',100),
                           scoring=session.get('scoring', None),
                           best_alternatives_zipped=best_alternatives_zipped,
                           calc_time=session.get('calc_time', None)
    )


@app.route('/reset', methods=['POST'])
def reset():
    session['furnitures'] = []
    session['kost_length'] = 300
    session['kost_width'] = 300
    session['rows'] = 5
    session['cols'] = 5
    session['grid_scale'] = 100
    session['grid'] = [[0]*5 for _ in range(5)]
    session['scoring'] = None
    return redirect(url_for('input_furniture'))

@app.route('/delete_furniture/<int:index>', methods=['POST'])
def delete_furniture(index):
    if 'furnitures' in session and 0 <= index < len(session['furnitures']):
        session['furnitures'].pop(index)
        session.modified = True
        furnitures = session.get('furnitures', [])
        if furnitures:
            kl = session['kost_length']
            kw = session['kost_width']
            rows, cols, cell_meter, furn_grid = compute_grid(kl, kw, furnitures, max_grid=10)
            session['rows'] = rows
            session['cols'] = cols
            session['grid_scale'] = int(round(cell_meter*100))
            gen = GenerateFurniturePosition(rows, cols, furn_grid)
            results = gen.generate()
            if results:
                session['grid'] = results[0]
            else:
                session['grid'] = [[0]*cols for _ in range(rows)]
        else:
            # Tidak ada furnitur: reset grid meter-bulat
            session['rows'] = int(max(1, round(session['kost_length'])))
            session['cols'] = int(max(1, round(session['kost_width'])))
            session['grid'] = [[0]*session['cols'] for _ in range(session['rows'])]
            session['grid_scale'] = 100
    return redirect(url_for('input_furniture'))


if __name__ == '__main__':
    app.run(debug=True)