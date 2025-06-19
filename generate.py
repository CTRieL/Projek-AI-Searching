class GenerateFurniturePosition:
    def __init__(self, room_rows, room_cols, furnitures):
        from testing import AreaCalculator
        self.room_rows = room_rows
        self.room_cols = room_cols
        self.furnitures = furnitures
        self.room = [[0 for _ in range(room_cols)] for _ in range(room_rows)]
        self.placements = []  # hasil penempatan
        self.best_area = 0
        self.area_calc = AreaCalculator()

    def can_place(self, matrix, top, left):
        f_rows, f_cols = len(matrix), len(matrix[0])
        if top + f_rows > self.room_rows or left + f_cols > self.room_cols:
            return False
        for i in range(f_rows):
            for j in range(f_cols):
                if matrix[i][j] and self.room[top + i][left + j]:
                    return False
        return True

    def place(self, matrix, top, left, value):
        f_rows, f_cols = len(matrix), len(matrix[0])
        for i in range(f_rows):
            for j in range(f_cols):
                if matrix[i][j]:
                    self.room[top + i][left + j] = value

    def get_unique_rotations(self, matrix):
        import numpy as np
        mats = []
        mat_np = np.array(matrix)
        for k in range(4):
            rot = np.rot90(mat_np, k).tolist()
            if rot not in mats:
                mats.append(rot)
        return mats

    def sort_furnitures(self):
        self.furnitures.sort(
            key=lambda f: sum(sum(row) for row in f['matrix']),
            reverse=True
        )

    def furnitures_have_access(self):
        from collections import deque

        n, m = self.room_rows, self.room_cols
        visited = [[False]*m for _ in range(n)]
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]

        # 1. Temukan semua komponen area kosong dan identifikasi yang paling luas
        largest_region = set()
        largest_size = 0

        for i in range(n):
            for j in range(m):
                if self.room[i][j] == 0 and not visited[i][j]:
                    # BFS/kumpulkan komponen kosong ini
                    q = deque([(i,j)])
                    visited[i][j] = True
                    region_cells = [(i,j)]
                    while q:
                        y, x = q.popleft()
                        for dy, dx in dirs:
                            ny, nx = y+dy, x+dx
                            if 0 <= ny < n and 0 <= nx < m:
                                if self.room[ny][nx] == 0 and not visited[ny][nx]:
                                    visited[ny][nx] = True
                                    q.append((ny, nx))
                                    region_cells.append((ny, nx))
                    size = len(region_cells)
                    if size > largest_size:
                        largest_size = size
                        largest_region = set(region_cells)

        # Jika tidak ada area kosong sama sekali, berarti tidak ada akses ke mana-mana.
        # Bisa dianggap gagal, kecuali kalau definisi lain. Di sini anggap gagal:
        if largest_size == 0:
            return False

        # 2. Untuk setiap komponen furnitur, cek adjacency ke largest_region
        visited_furn = [[False]*m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                if self.room[i][j] != 0 and not visited_furn[i][j]:
                    furn_id = self.room[i][j]
                    # BFS kumpulkan semua sel furnitur dengan id ini
                    q = deque([(i,j)])
                    visited_furn[i][j] = True
                    furn_cells = [(i,j)]
                    while q:
                        y, x = q.popleft()
                        for dy, dx in dirs:
                            ny, nx = y+dy, x+dx
                            if 0 <= ny < n and 0 <= nx < m:
                                if self.room[ny][nx] == furn_id and not visited_furn[ny][nx]:
                                    visited_furn[ny][nx] = True
                                    q.append((ny, nx))
                                    furn_cells.append((ny, nx))
                    # Cek apakah salah satu sel furnitur berdampingan dengan area kosong terbesar
                    has_access = False
                    for (y, x) in furn_cells:
                        for dy, dx in dirs:
                            ny, nx = y+dy, x+dx
                            if 0 <= ny < n and 0 <= nx < m:
                                if (ny, nx) in largest_region:
                                    has_access = True
                                    break
                        if has_access:
                            break
                    if not has_access:
                        return False  # kelompok furnitur ini terkunci
        return True

    def count_filled_sides(self, room):
        n, m = self.room_rows, self.room_cols
        sides = 0
        # Atas
        if any(room[0][j] != 0 for j in range(m)):
            sides += 1
        # Bawah
        if any(room[n-1][j] != 0 for j in range(m)):
            sides += 1
        # Kiri
        if any(room[i][0] != 0 for i in range(n)):
            sides += 1
        # Kanan
        if any(room[i][m-1] != 0 for i in range(n)):
            sides += 1
        return sides

    def total_luas_furnitur_sisa(self, idx):
        # Hitung total luas semua furnitur yang belum ditempatkan
        return sum(sum(sum(row) for row in self.furnitures[i]['matrix']) for i in range(idx, len(self.furnitures)))

    def count_long_side_touching(self):
        # Menghitung jumlah furnitur yang sisi panjangnya (bukan lebar) menyentuh dinding kos
        n, m = self.room_rows, self.room_cols
        count = 0
        for idx, furn in enumerate(self.furnitures):
            id_val = furn['id'] if 'id' in furn else idx + 1
            mat = furn['matrix']
            f_rows, f_cols = len(mat), len(mat[0])
            # Sisi panjang
            if f_rows == f_cols:
                continue  # skip persegi
            is_long_row = f_rows > f_cols
            # Cari semua sel milik furnitur ini
            cells = [(i, j) for i in range(n) for j in range(m) if self.room[i][j] == id_val]
            if not cells:
                continue
            # Cek apakah ada baris/kolom di dinding yang penuh oleh id_val sesuai orientasi panjang
            touches = False
            if is_long_row:
                # Sisi panjang vertikal (cek baris 0 atau n-1)
                min_row = min(i for i, _ in cells)
                max_row = max(i for i, _ in cells)
                if min_row == 0 or max_row == n-1:
                    touches = True
            else:
                # Sisi panjang horizontal (cek kolom 0 atau m-1)
                min_col = min(j for _, j in cells)
                max_col = max(j for _, j in cells)
                if min_col == 0 or max_col == m-1:
                    touches = True
            if touches:
                count += 1
        return count

    def brute_force(self, idx=0):
        if idx == 0:
            self.sort_furnitures()
            self.room = [[0]*self.room_cols for _ in range(self.room_rows)]
            self.best_score = -1
            self.placements = []
        area_kosong = sum(cell == 0 for row in self.room for cell in row)
        luas_sisa = self.total_luas_furnitur_sisa(idx)
        if area_kosong < luas_sisa:
            return
        matrix_snapshot = [row[:] for row in self.room]
        # Hitung score kombinasi saat ini
        score_tuple = self.area_calc.score_layout(matrix_snapshot, self.furnitures, self.count_filled_sides)
        # Pastikan tuple memiliki minimal 5 elemen (isi 0 jika kurang)
        score_tuple = tuple(list(score_tuple) + [0]*(5-len(score_tuple)))
        score, area_score, side_score, long_side_score, max_area = score_tuple[:5]
        # Prune jika score saat ini < best_score
        if score < self.best_score:
            return
        if idx == len(self.furnitures):
            if score > self.best_score:
                self.best_score = score
                self.placements = [[row[:] for row in self.room]]
            elif score == self.best_score:
                self.placements.append([row[:] for row in self.room])
            return
        furn = self.furnitures[idx]
        for rot_matrix in self.get_unique_rotations(furn['matrix']):
            f_rows, f_cols = len(rot_matrix), len(rot_matrix[0])
            for i in range(self.room_rows - f_rows + 1):
                for j in range(self.room_cols - f_cols + 1):
                    if self.can_place(rot_matrix, i, j):
                        # Gunakan id unik jika ada, jika tidak fallback ke idx+1
                        value = furn['id'] if 'id' in furn else idx+1
                        self.place(rot_matrix, i, j, value)
                        if self.furnitures_have_access():
                            self.brute_force(idx+1)
                        self.place(rot_matrix, i, j, 0)

    def generate(self):
        self.placements = []
        self.brute_force()
        return self.placements