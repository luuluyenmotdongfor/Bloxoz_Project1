# 🟦 ĐỒ ÁN 1: BLOXORZ SOLVER (CSC14003 - CƠ SỞ TRÍ TUỆ NHÂN TẠO)

> **📌 THÔNG BÁO MỚI NHẤT TỪ TRƯỞNG NHÓM (CẬP NHẬT TIẾN ĐỘ):**
> Hiện tại toàn bộ **Core Logic (kể cả cơ chế khó nhất là Split Switch tách/gộp khối)**, **Bộ 12 màn chơi chuẩn (4 cấp độ khó)**, **Script tự động chấm & vẽ biểu đồ (`benchmark.py`)**, và **Thuật toán mẫu `BFS`** đã hoàn thiện 100%.
> 
> ⚠️ **QUY TẮC GIT BẮT BUỘC:** Anh em tuyệt đối **KHÔNG push thẳng lên nhánh `main`**. Mỗi người tự tạo branch riêng cho phần việc của mình, code và chạy test kỹ bằng lệnh `python Source/benchmark.py`, sau đó push lên branch riêng và báo Trưởng nhóm (hoặc thành viên khác) kiểm tra rồi mới merge vào `main`!

---

## 1. TRẠNG THÁI HIỆN TẠI CỦA DỰ ÁN (ĐÃ XONG vs. CẦN LÀM)

| Thành phần / Đường dẫn File | Trạng thái | Chi tiết công việc |
| :--- | :---: | :--- |
| `Source/core/state.py` | ✅ **ĐÃ XONG 100%** | Định nghĩa `State` bất biến (hashable) lưu tọa độ, 4 trạng thái hướng (`STANDING`, `LYING_H`, `LYING_V`, `SPLIT`) và trạng thái cầu (`bridges_mask`). **Không sửa.** |
| `Source/core/board.py` | ✅ **ĐÃ XONG 100%** | Xử lý toàn bộ luật chơi: gạch thường, ô trống, gạch cam dễ vỡ (`Fragile`), cầu đóng/mở, và cả 3 loại công tắc (`soft`, `heavy`, `split` tách 2 khối đơn & tự động ghép lại khi đứng cạnh nhau). **Không sửa.** |
| `Source/solvers/base_solver.py` | ✅ **ĐÃ XONG 100%** | Class cha tự động đo 4 thông số: `Search Time`, `Peak Memory Usage`, `Expanded Nodes`, `Solution Length`. **Không sửa.** |
| `Source/main.py` | ✅ **ĐÃ XONG 100%** | Server Flask kết nối Web 3D. **Đã cập nhật cơ chế tự động nhận diện thuật toán** (ai code xong file solver nào là server tự nạp, không cần sửa `main.py`). |
| `Source/levels/level_01..12.json` | ✅ **ĐÃ XONG 100%** | Đã tạo đủ **12 màn chơi chuẩn** chia đều vào 4 nhóm độ khó tăng dần (từ 7 bước đến 31 bước, mở rộng >1000 nodes). Có thể dùng luôn hoặc bổ sung thêm nếu muốn. |
| `Source/validate_levels.py` | ✅ **ĐÃ XONG 100%** | Công cụ tự động kiểm tra toàn bộ file JSON map xem có hợp lệ và giải được (`SOLVABLE`) hay không. |
| `Source/benchmark.py` | ✅ **ĐÃ XONG 100%** | Script tự động chạy tất cả các thuật toán trên 12 map, kiểm tra tính đúng đắn của lời giải, xuất file `benchmark_results.csv` và vẽ 4 biểu đồ `.png` vào `Source/results/`. |
| `Source/solvers/bfs_solver.py` | ✅ **ĐÃ XONG 100%** | Thuật toán `BFSSolver` hoàn chỉnh. Dùng làm file mẫu chuẩn cho các bạn code thuật toán khác. |
| `Source/solvers/dfs_solver.py` | ❌ **CẦN LÀM** | Cài đặt `class DFSSolver(BaseSolver)` sử dụng Stack và tập `visited` tránh lặp chu trình. |
| `Source/solvers/ids_solver.py` | ❌ **CẦN LÀM** | Cài đặt `class IDSSolver(BaseSolver)` (Iterative Deepening Search) tìm kiếm lặp sâu dần. |
| `Source/solvers/ucs_solver.py` | ❌ **CẦN LÀM** | Cài đặt `class UCSSolver(BaseSolver)` dùng `heapq` với hàm Cost không đồng nhất (quy ước ở Mục 4.4). |
| `Source/solvers/astar_solver.py` | ❌ **CẦN LÀM** | Cài đặt `class AStarSolver(BaseSolver)` dùng `heapq` với hàm Heuristic đảm bảo tính Admissible (xử lý cả cổng dịch chuyển `split`). |
| `Source/gui/index.html` | 🚧 **CẦN NÂNG CẤP** | Giao diện 3D đã chạy và test được hết mọi tính năng (kể cả tách khối). Bạn phụ trách GUI cần làm đẹp thêm (xoay camera bằng chuột `OrbitControls`, vẽ viền khối, làm mượt chuyển động lăn, thêm nút bấm `Solve IDS`). |
| `Report.pdf` & `Video Demo` | ❌ **CẦN LÀM** | Viết báo cáo lý thuyết + phân tích thực nghiệm (30 điểm) và quay Video Demo up YouTube (10 điểm). |

---

## 2. HƯỚNG DẪN CHẠY TEST NHANH (BAO GỒM CẢ TEST TÁCH KHỐI SPLIT)

### Bước 1: Cài đặt thư viện
~~~bash
pip install -r requirements.txt
~~~

### Bước 2: Kiểm tra 12 màn chơi & Chạy thử Benchmark
~~~bash
python Source/validate_levels.py
python Source/benchmark.py
~~~
*(Sau khi chạy `benchmark.py`, mở thư mục `Source/results/` sẽ thấy bảng số liệu `.csv` và 4 ảnh biểu đồ `.png` được xuất tự động).*

### Bước 3: Chạy Giao diện 3D trên trình duyệt
~~~bash
python Source/main.py
~~~
Mở trình duyệt truy cập: **`http://127.0.0.1:5000`**
* **Cách test cơ chế Split Switch (Tách khối 1x1x2 thành 2 khối 1x1x1):**
  * Chọn màn **`level_10.json`**, **`level_11.json`**, hoặc **`level_12.json`** ở menu góc trái.
  * Bấm nút **`Solve BFS`** để xem AI tự động lăn vào công tắc màu tím, tách thành 2 khối vuông nhỏ (xanh đậm & xanh nhạt), điều khiển từng khối đi bấm công tắc mở cầu rồi tự ghép lại thành khối lớn về đích.
  * Nếu chơi bằng tay: Dùng phím `Mũi tên` để di chuyển, bấm phím **`Space`** để đổi qua lại giữa 2 khối nhỏ.
* **Cách tắt chương trình:** Bấm vào cửa sổ Terminal đang chạy và nhấn **`Ctrl + C`**.

---

## 3. CẤU TRÚC BỘ 12 MÀN CHƠI (4 CẤP ĐỘ KHÓ TRONG `Source/levels/`)

Bộ 12 test cases đã được thiết kế dựa trên các màn kinh điển của Bloxorz gốc (Coolmath Games) và chia thành 4 nhóm để phục vụ phần phân tích thực nghiệm trong Report:
1. **Nhóm 1 - Cơ bản (`level_01` -> `level_03`):** Chỉ gồm gạch thường (`1`), ô trống (`0`) và đích (`9`). Độ dài lời giải tối ưu từ 7 đến 31 bước.
2. **Nhóm 2 - Ô dễ vỡ Fragile Tiles (`level_04` -> `level_06`):** Có thêm gạch màu cam (`2` - đứng thẳng sẽ bị vỡ). Đặc biệt **`level_05.json`** được thiết kế có 1 đường tắt đi qua gạch cam (8 bước) và 1 đường vòng đi trên gạch cứng an toàn (16 bước) để làm nổi bật sự khác biệt giữa **BFS** và **UCS**.
3. **Nhóm 3 - Cầu & Công tắc (`level_07` -> `level_09`):** Kết hợp nhiều cầu đóng/mở (`bridges`) với công tắc tròn (`soft` switch) và công tắc chữ X (`heavy` switch).
4. **Nhóm 4 - Kết hợp & Tách khối Split Switch (`level_10` -> `level_12`):** Kết hợp đầy đủ gạch cam, cầu, công tắc `soft`/`heavy` và cổng dịch chuyển tách khối `split`.

---

## 4. "HỢP ĐỒNG CODE" & RÀNG BUỘC BẮT BUỘC CHO CÁC BẠN VIẾT THUẬT TOÁN

> **Mẹo cho thành viên nhóm:** Khi dùng Gemini Pro / ChatGPT hỗ trợ viết thuật toán của mình, **hãy copy toàn bộ Mục 4 này gửi cho AI** để code sinh ra khớp 100% với hệ thống.

### 4.1. Quy định tên File và tên Class (Để `main.py` và `benchmark.py` tự động nhận diện)
* Bạn làm **DFS**: Viết trong file `Source/solvers/dfs_solver.py` $\rightarrow$ đặt tên class là `DFSSolver(BaseSolver)`.
* Bạn làm **IDS**: Tạo file `Source/solvers/ids_solver.py` $\rightarrow$ đặt tên class là `IDSSolver(BaseSolver)`.
* Bạn làm **UCS**: Viết trong file `Source/solvers/ucs_solver.py` $\rightarrow$ đặt tên class là `UCSSolver(BaseSolver)`.
* Bạn làm **A\***: Viết trong file `Source/solvers/astar_solver.py` $\rightarrow$ đặt tên class là `AStarSolver(BaseSolver)`.

### 4.2. Ràng buộc bên trong hàm `_search(self)`
1. **Đếm số nút mở rộng:** Mỗi khi lấy (pop) một trạng thái ra khỏi `frontier` (queue/stack/heap) để duyệt các trạng thái kế tiếp, **BẮT BUỘC** phải có dòng:
   ~~~python
   self.expanded_nodes += 1
   ~~~
2. **Không dùng lệnh `print()` trong vòng lặp tìm kiếm:** Để tránh làm sai lệch thông số `Search Time`.
3. **Giá trị trả về:** Trả về `List[str]` chứa danh sách hành động (ví dụ `['RIGHT', 'DOWN', ...]`) hoặc `None` nếu không tìm thấy đường đi.

### 4.3. Các hàm và thuộc tính có sẵn từ `self.board` và `State`
* `start_state = self.board.get_initial_state()`: Lấy trạng thái bắt đầu.
* `self.board.is_goal(state)`: Trả về `True` nếu `state` đã thắng.
* `self.board.get_successors(state)`: Trả về danh sách các cặp `(action, next_state)` hợp lệ.
* Thuộc tính của `state`:
  * `state.r, state.c`: Tọa độ dòng, cột.
  * `state.orientation`: `Orientation.STANDING` (0), `Orientation.LYING_H` (1), `Orientation.LYING_V` (2), `Orientation.SPLIT` (3 - có thêm `state.r2, state.c2` và `state.active_cube`).
  * `state.get_occupied_cells()`: Trả về list các ô `[(r, c), ...]` mà khối đang chiếm giữ.
  * `State` đã có sẵn `__hash__`, `__eq__`, `__lt__` nên dùng trực tiếp được trong `set()`, `dict()`, và `heapq`.
* Thuộc tính của `self.board`:
  * `self.board.grid[r][c]`: Giá trị ô (`0`: Void, `1`: Gạch thường, `2`: Ô dễ vỡ Fragile tile, `9`: Goal).
  * `self.board.goal_pos`: Tuple `(goal_r, goal_c)` tọa độ đích.
  * `self.board.switches`: Dict `{ (r, c): switch_dict }` chứa thông tin công tắc (với `split` switch có trường `"teleport_to": [[r1, c1], [r2, c2]]`).

### 4.4. Quy ước chung về Hàm Chi Phí (Step Cost) cho bạn làm UCS và A*
Để đảm bảo tính nhất quán trong báo cáo và giữ tính **Admissible** của Heuristic trong A*, nhóm thống nhất quy ước chi phí cho 1 bước chuyển `(current_state, action, next_state)`:
* **Bước đi thông thường (trên gạch cứng hoặc đổi khối `SWITCH_CUBE`):** `cost = 1.0`.
* **Bước đi nguy hiểm (trong `next_state.get_occupied_cells()` có ít nhất 1 ô là Fragile tile, tức `self.board.grid[r][c] == 2`):** `cost = 4.0` (phạt nặng rủi ro đi lên gạch dễ vỡ).
* **Lưu ý cho bạn làm A\*:**
  * Vì chi phí bước nhỏ nhất là $\min(\text{cost}) = 1.0$, hàm Heuristic $h(n)$ dùng khoảng cách Manhattan chia 2 ($\frac{\vert{}r - r_{goal}\vert{} + \vert{}c - c_{goal}\vert{}}{2.0}$) đảm bảo không vượt quá số bước thực tế.
  * **Đặc biệt chú ý:** Với các màn có cổng dịch chuyển `split` switch (`level_10`, `11`, `12`), việc đi qua cổng dịch chuyển có thể rút ngắn khoảng cách so với đi bộ thông thường. Do đó, để giữ vững tính **Admissible**, hàm Heuristic cần lấy giá trị nhỏ nhất ($\min$) giữa khoảng cách đi trực tiếp tới đích và khoảng cách đi tới cổng `split` cộng với khoảng cách từ điểm dịch chuyển (`teleport_to`) tới đích!

---

## 5. QUY TRÌNH KIỂM TRA TRƯỚC KHI PUSH LÊN NHÁNH RIÊNG

Sau khi code xong phần của mình, các bạn bắt buộc chạy lệnh sau trên Terminal:
~~~bash
python Source/benchmark.py
~~~
Kiểm tra trên bảng kết quả in ra màn hình:
1. Cột `Solved` của thuật toán mình vừa code phải hiện **`OK`** trên tất cả 12 màn chơi (không bị `INVALID` hay `FAIL`).
2. Cột `Nodes` (`Expanded Nodes`) phải lớn hơn `0`.
3. Sau khi xác nhận chạy mượt, hãy push lên **branch riêng** của bạn và nhắn lên nhóm để merge vào `main`!