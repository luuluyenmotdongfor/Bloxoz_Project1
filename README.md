$readme = @'
# 🟦 ĐỒ ÁN 1: BLOXORZ SOLVER (CSC14003 - CƠ SỞ TRÍ TUỆ NHÂN TẠO)

> **LƯU Ý DÀNH CHO THÀNH VIÊN NHÓM & CÔNG CỤ AI (GEMINI / CHATGPT):**
> File `README.md` này là tài liệu đặc tả kỹ thuật và phân công công việc chính thức của nhóm. Nếu bạn sử dụng AI để hỗ trợ viết code hoặc viết báo cáo, **hãy copy toàn bộ nội dung file này gửi cho AI trước** để AI hiểu chính xác kiến trúc code có sẵn của nhóm, tuyệt đối không tự ý sửa đổi các file trong thư mục `Source/core/`.

---

## 1. TỔNG QUAN YÊU CẦU & TIÊU CHÍ CHẤM ĐIỂM (TỪ ĐỀ BÀI & Q&A CỦA THẦY)

* **Trọng tâm đồ án (100 điểm):**
  * **Game & GUI 3D (20 điểm):** 10 điểm Core mechanics (gạch thường, ô trống, lỗ đích, lăn khối 3 trạng thái) + 10 điểm Advanced tiles (ô dễ vỡ Fragile tile, cầu Bridges, 3 loại công tắc Soft/Heavy/Split switch). Thầy yêu cầu **GUI phải là 3D** và **khi bấm nút Solve thì khối sắt tự động lăn đến đích**.
  * **4 Thuật toán tìm kiếm (40 điểm):** BFS (10đ), DFS hoặc IDS (10đ), UCS (10đ), A* (10đ) bắt buộc cài đặt bằng **Python**.
  * **Báo cáo Report (30 điểm):** Phân công nhiệm vụ (% hoàn thành), mô tả thuật toán & mô hình hóa bài toán (10đ), chạy thực nghiệm trên **tối thiểu 10 test cases** chia theo độ khó, lập bảng và vẽ biểu đồ so sánh 4 thông số: *Search Time, Peak Memory Usage, Expanded Nodes, Solution Length* (20đ). Báo cáo thống nhất 1 ngôn ngữ (100% Tiếng Việt hoặc 100% Tiếng Anh).
  * **Video Demo YouTube (10 điểm):** Quay giao diện 3D, chơi thủ công và chạy các Solver có phụ đề/thuyết minh.
* **Quy định sử dụng AI & Vấn đáp:** Được phép dùng AI và dùng source/test case có sẵn nhưng **phải trích dẫn (cite) nguồn và lưu lại các câu Prompt đã dùng vào phần Appendix (Phụ lục) của báo cáo**. Giảng viên có quyền gọi vấn đáp ngẫu nhiên để kiểm tra hiểu biết về thuật toán.

---

## 2. TRẠNG THÁI HIỆN TẠI CỦA DỰ ÁN (ĐÃ LÀM XONG vs. CẦN LÀM TIẾP)

Trưởng nhóm đã xây dựng xong toàn bộ **Bộ khung lõi (Core Logic)**, **Khung đo đạc thuật toán**, **Thuật toán mẫu BFS**, và **Giao diện Web 3D cơ bản**. Dưới đây là trạng thái từng file:

| Đường dẫn File | Trạng thái | Mô tả chi tiết |
| :--- | :---: | :--- |
| `Source/core/state.py` | ✅ **ĐÃ XONG 100%** | Định nghĩa class `State` bất biến (hashable) lưu tọa độ, hướng khối (`STANDING`, `LYING_H`, `LYING_V`, `SPLIT`) và trạng thái đóng/mở của toàn bộ cầu (`bridges_mask`). **Không cần sửa.** |
| `Source/core/board.py` | ✅ **ĐÃ XONG 100%** | Đọc file JSON map, kiểm tra nước đi hợp lệ (rơi xuống Void, vỡ gạch cam Fragile, cầu đóng), xử lý đủ 3 công tắc (Soft, Heavy, Split tách/gộp khối). **Không cần sửa.** |
| `Source/solvers/base_solver.py` | ✅ **ĐÃ XONG 100%** | Class cha tự động bấm giờ (`Search Time`), đo đỉnh bộ nhớ (`Peak Memory` bằng `tracemalloc`), đếm `Expanded Nodes` và `Solution Length`. **Không cần sửa.** |
| `Source/solvers/bfs_solver.py` | ✅ **ĐÃ XONG 100%** | Thuật toán BFS hoàn chỉnh. Dùng làm code mẫu chuẩn cho các thuật toán còn lại. |
| `Source/main.py` | 🔄 **XONG 80%** | Server Flask kết nối Python với GUI 3D. Đã nối sẵn BFS. Khi code xong DFS, UCS, A* chỉ cần bỏ dấu `#` ở dòng import là chạy. |
| `Source/gui/index.html` | 🚧 **CẦN NÂNG CẤP** | Giao diện 3D (`Three.js`) đã chạy được: vẽ bản đồ, chơi bằng phím mũi tên, bấm `Solve BFS` tự lăn khối về đích. **Cần làm đẹp thêm** (vẽ viền khối, xoay camera bằng chuột, hiệu ứng lăn mượt). |
| `Source/levels/` | 🚧 **CẦN BỔ SUNG** | Mới chỉ có `level_01.json` để test. **Cần tạo đủ tối thiểu 10–12 file JSON map** chia làm 4 nhóm độ khó. |
| `Source/solvers/dfs_solver.py` | ❌ **ĐANG TRỐNG** | Cần viết thuật toán `DFSSolver` (hoặc `IDSSolver`) kế thừa từ `BaseSolver`. |
| `Source/solvers/ucs_solver.py` | ❌ **ĐANG TRỐNG** | Cần viết thuật toán `UCSSolver` + Thiết kế hàm chi phí (Cost function) không đồng nhất. |
| `Source/solvers/astar_solver.py` | ❌ **ĐANG TRỐNG** | Cần viết thuật toán `AStarSolver` + Thiết kế hàm Heuristic đảm bảo tính Admissible. |
| `Source/benchmark.py` | ❌ **ĐANG TRỐNG** | Cần viết script tự động chạy cả 4 thuật toán trên toàn bộ 10+ map để xuất bảng số liệu & vẽ biểu đồ `matplotlib` đưa vào Report. |

---

## 3. HƯỚNG DẪN CHẠY TEST THỬ & CÁCH TẮT CHƯƠNG TRÌNH

Ngay sau khi tải dự án về máy, mọi thành viên hãy làm theo 3 bước sau để kiểm tra bộ khung:

### Bước 1: Cài đặt thư viện
Mở Terminal trong VS Code (`Ctrl + ~`) tại thư mục gốc và chạy:
~~~bash
pip install -r requirements.txt
~~~

### Bước 2: Khởi chạy chương trình
~~~bash
python Source/main.py
~~~
Khi Terminal hiện dòng `🚀 Khởi chạy Bloxorz 3D tại địa chỉ: [http://127.0.0.1:5000](http://127.0.0.1:5000)`, hãy mở trình duyệt (Chrome/Edge) truy cập vào: **`[http://127.0.0.1:5000](http://127.0.0.1:5000)`**.
* **Test chơi bằng tay:** Bấm các phím mũi tên `Lên`, `Xuống`, `Trái`, `Phải` để lăn khối sắt.
* **Test thuật toán mẫu:** Bấm nút **`Solve BFS`** ở góc trái, quan sát thông số đo đạc hiện ra và khối sắt tự động lăn qua công tắc, mở cầu, đi qua gạch cam về đích.

### Bước 3: Cách tắt chương trình
Để dừng server đang chạy, bấm chuột vào cửa sổ **Terminal** trong VS Code và nhấn tổ hợp phím **`Ctrl + C`**.

---

## 4. ĐẶC TẢ KỸ THUẬT ("HỢP ĐỒNG CODE" DÀNH CHO NGƯỜI CODE & AI)

Để code của các thành viên ghép vào nhau chạy ngay lập tức, mọi người cần tuân thủ cấu trúc các hàm có sẵn sau:

### 4.1. Cấu trúc đối tượng `State` (`Source/core/state.py`)
Mỗi trạng thái `state` có các thuộc tính:
* `state.r`, `state.c`: Tọa độ dòng, cột của khối (nếu nằm ngang thì chiếm `(r, c)` và `(r, c+1)`; nếu nằm dọc thì chiếm `(r, c)` và `(r+1, c)`).
* `state.orientation`: Kiểu `Orientation` gồm:
  * `Orientation.STANDING` (0): Đứng thẳng tại 1 ô.
  * `Orientation.LYING_H` (1): Nằm ngang.
  * `Orientation.LYING_V` (2): Nằm dọc.
  * `Orientation.SPLIT` (3): Bị tách làm 2 khối đơn 1x1x1 tại `(r, c)` và `(r2, c2)`.
* `state.bridges_mask`: Một `tuple` các giá trị `bool` biểu diễn trạng thái Đóng (`False`) / Mở (`True`) của từng cây cầu.
* `state.get_occupied_cells()`: Trả về danh sách các tọa độ `[(r, c), ...]` mà khối đang đè lên.
* **Lưu ý:** `State` đã được cài sẵn `__hash__`, `__eq__`, và `__lt__`, nên có thể bỏ trực tiếp vào `visited = set()` hoặc `heapq.heappush(frontier, (cost, state, path))`.

### 4.2. Các hàm có sẵn của `Board` (`Source/core/board.py`)
Khi viết thuật toán trong `solvers/`, biến `self.board` cung cấp sẵn:
* `self.board.get_initial_state() -> State`: Trả về trạng thái xuất phát của màn chơi.
* `self.board.is_goal(state: State) -> bool`: Kiểm tra trạng thái hiện tại đã thắng chưa (đứng thẳng tại ô đích).
* `self.board.get_successors(state: State) -> List[Tuple[str, State]]`: Trả về danh sách các cặp `(action, next_state)` hợp lệ. Trong đó `action` là một trong các chuỗi: `'UP'`, `'DOWN'`, `'LEFT'`, `'RIGHT'`, hoặc `'SWITCH_CUBE'`.
* Các thuộc tính hỗ trợ tính Cost và Heuristic:
  * `self.board.grid`: Ma trận 2 chiều của bản đồ (`0`: Void, `1`: Gạch thường, `2`: Ô dễ vỡ Fragile tile, `9`: Đích Goal).
  * `self.board.goal_pos`: Tuple `(goal_r, goal_c)` tọa độ ô đích.
  * `self.board.switches`: Dictionary `{ (r, c): switch_info_dict }` lưu các công tắc trên bản đồ.

### 4.3. Khuôn mẫu `BaseSolver` (`Source/solvers/base_solver.py`)
Mọi thuật toán đều phải kế thừa `BaseSolver` và định nghĩa hàm `_search(self)`:
~~~python
from typing import List, Optional
from solvers.base_solver import BaseSolver

class TenThuatToanSolver(BaseSolver):
    def _search(self) -> Optional[List[str]]:
        # 1. Lấy trạng thái đầu: start_state = self.board.get_initial_state()
        # 2. Mỗi khi lấy 1 trạng thái ra khỏi frontier để mở rộng, BẮT BUỘC gọi:
        #       self.expanded_nodes += 1
        # 3. Trả về danh sách các bước đi (VD: ['RIGHT', 'DOWN', ...]) hoặc None nếu vô nghiệm.
        pass
~~~

---

## 5. HƯỚNG DẪN CHI TIẾT CHO TỪNG NHIỆM VỤ (KÈM PROMPT AI)

### 🔹 NHIỆM VỤ 1: Cài đặt DFS (hoặc IDS) và UCS (`dfs_solver.py` & `ucs_solver.py`)
* **File cần làm:** `Source/solvers/dfs_solver.py` (class `DFSSolver`) và `Source/solvers/ucs_solver.py` (class `UCSSolver`).
* **Yêu cầu cốt lõi từ đề bài:**
  * **DFS:** Phải dùng tập `visited` để tránh bị kẹt trong chu trình lặp vô tận (cycles), hoặc có thể cài đặt Iterative Deepening Search (IDS).
  * **UCS:** Nếu mọi bước đi đều có cost = 1 thì UCS sẽ biến thành BFS. Vì vậy bắt buộc phải thiết kế một **hàm chi phí không đồng nhất (non-uniform cost function)** hợp lý (ví dụ: di chuyển bình thường tốn cost = 2; di chuyển đè lên ô dễ vỡ `grid[r][c] == 2` tốn cost = 5 vì nguy hiểm; kích hoạt công tắc tốn cost = 1...) và giải thích rõ trong báo cáo.
* **Cách test sau khi code xong:** Mở `Source/main.py`, xóa dấu `#` ở dòng `from solvers.dfs_solver import DFSSolver`, `from solvers.ucs_solver import UCSSolver` và trong `solver_map`, sau đó chạy `python Source/main.py` rồi bấm nút `Solve DFS` / `Solve UCS` trên web.
* 💡 **Prompt mẫu để bạn copy dán vào Gemini Pro / ChatGPT:**
  > *"Tôi đang làm đồ án Bloxorz Solver bằng Python. Đây là nội dung README đặc tả cấu trúc `State`, `Board`, và `BaseSolver` của nhóm tôi: [Dán mục 4 của README vào đây]. Hãy viết giúp tôi code hoàn chỉnh cho file `Source/solvers/dfs_solver.py` (class `DFSSolver`) và `Source/solvers/ucs_solver.py` (class `UCSSolver` sử dụng `heapq` với hàm chi phí không đồng nhất: bước thường cost = 2, đè lên ô dễ vỡ Fragile tile có `grid[r][c] == 2` thì cost = 5, bước đổi khối `SWITCH_CUBE` cost = 1). Đồng thời viết giải thích lý thuyết toán học của hàm Cost này để tôi đưa vào Report."*

---

### 🔹 NHIỆM VỤ 2: Cài đặt A* (`astar_solver.py`) & Chạy thực nghiệm (`benchmark.py`)
* **File cần làm:** `Source/solvers/astar_solver.py` (class `AStarSolver`) và `Source/benchmark.py`.
* **Yêu cầu cốt lõi từ đề bài:**
  * Thiết kế hàm `heuristic(state)` ước lượng khoảng cách đến `self.board.goal_pos`.
  * Đảm bảo tính **Admissible** (không bao giờ ước lượng vượt quá chi phí thực tế) tương ứng với hàm Cost đã chọn. Chú ý xử lý trường hợp bản đồ có cổng dịch chuyển (`split` switch) và trạng thái khối đang nằm cần ít nhất 1 bước để dựng đứng.
  * Viết `Source/benchmark.py` tự động chạy cả 4 thuật toán (`BFS`, `DFS`, `UCS`, `A*`) qua tất cả các file `.json` trong `Source/levels/`, in bảng kết quả (Time, Memory, Expanded Nodes, Length) và dùng `matplotlib` vẽ biểu đồ cột/đường so sánh lưu thành ảnh `.png` để chèn vào Report.

---

### 🔹 NHIỆM VỤ 3: Thiết kế 10+ Test Cases (`levels/`) & Nâng cấp GUI 3D (`gui/index.html`)
* **Phần 1 - Tạo bộ Map Test Cases (Tối thiểu 10–12 màn chơi):**
  * Tạo các file `level_01.json` đến `level_12.json` trong `Source/levels/`.
  * Có thể lấy bản đồ từ game Bloxorz gốc trên Coolmath Games hoặc trên GitHub (nhớ lưu link nguồn để trích dẫn vào báo cáo).
  * Chia rõ thành **4 nhóm độ khó tăng dần** để phân tích trong báo cáo:
    1. `level_01` -> `level_03` (Easy): Chỉ có gạch thường (`1`), ô trống (`0`) và đích (`9`).
    2. `level_04` -> `level_06` (Medium - Fragile): Có thêm các ô dễ vỡ màu cam (`2`).
    3. `level_07` -> `level_09` (Hard - Bridges & Switches): Có cầu đóng/mở và công tắc `soft`, `heavy`.
    4. `level_10` -> `level_12` (Expert - Combined & Split): Kết hợp đủ loại gạch và có công tắc `split` tách khối.
* **Phần 2 - Làm đẹp GUI 3D (`Source/gui/index.html`):**
  * Giữ nguyên các hàm gọi API (`/api/levels`, `/api/level/<filename>`, `/api/move`, `/api/solve`), nâng cấp phần hiển thị `Three.js`:
    * Vẽ đường viền đen (`THREE.EdgesGeometry`) cho từng viên gạch và khối sắt để nhìn rõ khối 3D như game gốc.
    * Thêm `THREE.OrbitControls` để người dùng có thể dùng chuột xoay/zoom bản đồ 3D.
    * Phân biệt rõ hình dáng 3 loại công tắc trên mặt gạch: Hình trụ tròn cho `soft`, chữ X cho `heavy`, và vòng tròn/dấu ngoặc cho `split`.
* 💡 **Prompt mẫu để bạn copy dán vào Gemini Pro / ChatGPT:**
  > *"Đây là file `Source/gui/index.html` hiện tại của nhóm tôi: [Dán code index.html vào]. Hãy giữ nguyên toàn bộ logic gọi API backend Flask, nhưng nâng cấp đồ họa Three.js giúp tôi: (1) Thêm viền đen `EdgesGeometry` cho từng ô gạch và khối chữ nhật để nhìn sắc nét, (2) Tích hợp `OrbitControls` qua CDN để xoay góc nhìn 3D bằng chuột, (3) Vẽ công tắc `heavy` hình chữ X và `soft` hình tròn nổi bật trên mặt gạch, (4) Làm hiệu ứng nội suy mượt mà khi khối di chuyển giữa các trạng thái."*

---

## 6. QUY TẮC LÀM VIỆC NHÓM & CHUẨN BỊ BÁO CÁO (REPORT)

1. **Không sửa trực tiếp vào `Source/core/`:** Mọi logic luật chơi đã chuẩn hóa ở `core/`. Nếu phát hiện bug, hãy nhắn cho Trưởng nhóm kiểm tra.
2. **Ghi chép lại Prompt AI:** Mỗi thành viên khi dùng Gemini/ChatGPT hỗ trợ code phần của mình hãy **lưu lại 2–3 câu prompt tiêu biểu** vào một file nháp để cuối kỳ tổng hợp vào mục **Appendix (Phụ lục)** của báo cáo (bắt buộc theo yêu cầu đề bài trang 7).
3. **Viết thuyết minh thuật toán của mình:** Ai code thuật toán nào thì chuẩn bị luôn 1–2 trang giải thích thuật toán đó (cách hoạt động, hàm Cost / Heuristic, ưu nhược điểm khi chạy thực nghiệm) để ghép vào phần **Algorithm Description (10 điểm)** và sẵn sàng trả lời khi thầy gọi vấn đáp.
'@
Set-Content -Path "README.md" -Value $readme -Encoding UTF8
Write-Host "Đã ghi xong file README.md chuẩn định dạng 100%!" -ForegroundColor Green