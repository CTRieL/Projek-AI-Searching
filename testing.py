class AreaCalculator:
    def __init__(self):
        self.maxAreaOfAllCombinations = 0
        self.maxAreaCoords = []  # koordinat (y,x) area maksimal

    def getMaxArea(self, arr, row):
        stack = []
        res = 0
        n = len(arr)
        coords = []

        for i in range(n):
            while stack and arr[stack[-1]] >= arr[i]:
                tp = stack.pop()
                width = i if not stack else i - stack[-1] - 1
                height = arr[tp]
                area = height * width
                if area > res:
                    res = area
                    coords = [(row - k, j) for k in range(height) for j in range(i - width, i)]
            stack.append(i)

        while stack:
            tp = stack.pop()
            width = n if not stack else n - stack[-1] - 1
            height = arr[tp]
            area = height * width
            if area > res:
                res = area
                coords = [(row - k, j) for k in range(height) for j in range(n - width, n)]

        return res, coords

    def maxArea(self, matrix):
        # matrix: numpy array, 1 for empty, 0 for obstacle
        if matrix.size == 0:
            return 0

        n, m = matrix.shape
        arr = [0] * m
        ans = 0
        coords_of_max = []

        for i in range(n):
            for j in range(m):
                if matrix[i][j] == 1:
                    arr[j] += 1
                else:
                    arr[j] = 0

            area, coords = self.getMaxArea(arr, i)
            if area > ans:
                ans = area
                coords_of_max = coords

        self.maxAreaCoords = coords_of_max
        self.maxAreaOfAllCombinations = max(self.maxAreaOfAllCombinations, ans)
        return ans

    def highlightMaxArea(self, matrix):
        for y, x in self.maxAreaCoords:
            if 0 <= y < len(matrix) and 0 <= x < len(matrix[0]):
                matrix[y][x] = 2

    def resetMaxArea(self):
        self.maxAreaOfAllCombinations = 0
        self.maxAreaCoords = []

    def test_layout(self, matrix):
        """
        syarat
        1) Temukan area kosong persegi panjang terbesar,
        2) Cek setiap furnitur punya akses ke area itu.
        Mengembalikan: (max_area, coords_max_area, access_ok)
        """
        import numpy as np
        # ubah ke binary: 1=empty, 0=furniture
        bin_matrix = np.where(np.array(matrix)==0, 1, 0)
        max_area = self.maxArea(bin_matrix)
        coords = list(self.maxAreaCoords)
        # cek akses berdasarkan matriks asli (0=empty,1=furniture)
        return max_area, coords

    def score_layout(self, matrix, furnitures, count_filled_sides_func):
        # matrix: grid, furnitures: list of dict, count_filled_sides_func: fungsi hitung sisi
        import numpy as np
        if not matrix or not matrix[0]:
            return 0, 0, 0, 0
        n = len(matrix)
        m = len(matrix[0])
        # Area kosong terbesar
        bin_matrix = np.where(np.array(matrix)==0, 1, 0)
        max_area = self.maxArea(bin_matrix)
        area_score = max_area / (n * m) if n * m > 0 else 0
        # Skor sisi
        filled_sides = count_filled_sides_func(matrix)
        if filled_sides == 4:
            side_score = 0
        else:
            side_score = filled_sides / 3 if filled_sides > 0 else 0
        # Skor bonus sisi panjang menyentuh dinding
        long_side_touch = 0
        for idx, furn in enumerate(furnitures):
            id_val = idx + 1
            mat = furn['matrix']
            f_rows, f_cols = len(mat), len(mat[0])
            if f_rows == f_cols:
                continue  # skip persegi
            is_long_row = f_rows > f_cols
            cells = [(i, j) for i in range(n) for j in range(m) if matrix[i][j] == id_val]
            if not cells:
                continue
            touches = False
            if is_long_row:
                min_row = min(i for i, _ in cells)
                max_row = max(i for i, _ in cells)
                if min_row == 0 or max_row == n-1:
                    touches = True
            else:
                min_col = min(j for _, j in cells)
                max_col = max(j for _, j in cells)
                if min_col == 0 or max_col == m-1:
                    touches = True
            if touches:
                long_side_touch += 1
        long_side_score = long_side_touch / len(furnitures) if furnitures else 0
        score = 0.1 * area_score + 0.4 * side_score + 0.5 * long_side_score
        return score, area_score, side_score, long_side_score, max_area