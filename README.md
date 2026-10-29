# 🟦 ĐỒ ÁN 1: BLOXORZ SOLVER (CSC14003 - CƠ SỞ TRÍ TUỆ NHÂN TẠO)

> **📌 LƯU Ý QUAN TRỌNG DÀNH CHO THÀNH VIÊN NHÓM & CÔNG CỤ AI (GEMINI PRO / CHATGPT):**
>
> 1. File `README.md` này đã **tóm tắt toàn bộ đề bài PDF của thầy, bảng giải đáp Q&A, luật chơi chi tiết, kiến trúc code có sẵn và hướng dẫn từng nhiệm vụ**. Anh em chưa kịp đọc file PDF của thầy chỉ cần đọc kỹ file này từ trên xuống dưới là nắm được 100% yêu cầu.
>
> 2. Nếu bạn dùng AI (Gemini / ChatGPT) để hỗ trợ viết code hoặc viết báo cáo, **hãy copy toàn bộ nội dung file `README.md` này gửi cho AI trước** để AI hiểu chính xác các hàm có sẵn của nhóm, tuyệt đối không tự ý sửa các file trong `Source/core/`.
>
> 3. **QUY TẮC GIT BẮT BUỘC:** Anh em **KHÔNG push thẳng lên nhánh `main`**. Mỗi người tự tạo branch riêng cho phần việc của mình, code và test kỹ bằng lệnh `python Source/benchmark.py`, sau đó push lên branch đó rồi báo Trưởng nhóm (hoặc thành viên khác) kiểm tra và merge vào `main`!

---

## 1. TÓM TẮT ĐỀ BÀI PDF & GIẢI ĐÁP Q&A CỦA THẦY (CHO ANH EM CHƯA ĐỌC ĐỀ)

### 1.1. Luật chơi Bloxorz (Cần nắm rõ để hiểu thuật toán & đi vấn đáp)

* **Mục tiêu:** Điều khiển một khối hình hộp chữ nhật kích thước `1x1x2` lăn trên bàn cờ sao cho khối **rơi thẳng đứng (STANDING)** vào đúng ô lỗ đích (`Goal hole`). Nếu khối chỉ nằm ngang qua lỗ đích thì chưa thắng; nếu bất kỳ phần nào của khối lăn ra ngoài bàn cờ hoặc đè lên ô trống (`Void`) thì thua.

* **3 Trạng thái hướng của khối `1x1x2` (Orientation):**

  * `STANDING (0)`: Đứng thẳng trên 1 ô `(r, c)`.

  * `LYING_H (1)`: Nằm ngang chiếm 2 ô `(r, c)` và `(r, c+1)`.

  * `LYING_V (2)`: Nằm dọc chiếm 2 ô `(r, c)` và `(r+1, c)`.

* **Các ô đặc biệt (Advanced Tiles - Bắt buộc cả Game và Solver phải xử lý được):**

  * **Ô dễ vỡ (`Fragile tile` - màu cam, mã `2`):** Chỉ chịu được sức nặng khi khối **nằm ngang hoặc nằm dọc**. Nếu khối **đứng thẳng (`STANDING`)** trên ô màu cam, gạch sẽ vỡ và khối rơi xuống vực (nước đi không hợp lệ).

  * **Cầu (`Bridges`):** Các ô cầu có thể Đóng hoặc Mở, được điều khiển bởi công tắc (`Switch`). Khi cầu đóng, nó giống như ô trống (`Void`); khi cầu mở, nó giống gạch thường (`Floor tile`). **Lưu ý sống còn:** Trạng thái tìm kiếm (`State`) bắt buộc phải lưu cả trạng thái Đóng/Mở của mọi cây cầu trên bản đồ!

  * **3 loại Công tắc (`Switches`):**

    1. **Soft switch (Hình tròn/bát giác):** Kích hoạt khi bất kỳ phần nào của khối chạm vào (dù đứng hay nằm).

    2. **Heavy switch (Hình chữ X):** Chỉ kích hoạt khi khối `1x1x2` **đứng thẳng (`STANDING`)** đè toàn bộ trọng lượng lên nó (nằm đè lên không kích hoạt được).

    3. **Split switch (Dấu ngoặc đơn `()` - màu tím):** Chỉ kích hoạt khi khối **đứng thẳng** trên nó. Nó sẽ dịch chuyển tức thời (`teleport`) khối tới 2 vị trí định trước và **tách khối thành 2 khối lập phương đơn `1x1x1` (`SPLIT`)**. Người chơi điều khiển từng khối đơn một (bấm phím `Space` để đổi khối điều khiển). Khi 2 khối đơn di chuyển đến 2 ô kề cạnh nhau, chúng **tự động ghép lại** thành khối `1x1x2` ban đầu. Khối đơn `1x1x1` bấm được Soft switch nhưng **không bấm được Heavy switch** và **không thể tự rơi xuống lỗ đích để thắng**.

  * **Hành vi công tắc:** Có thể là `toggle` (mỗi lần chạm sẽ đảo trạng thái Đóng <-> Mở của cầu) hoặc `permanent` (chuyển cầu sang trạng thái cố định).

### 1.2. Cơ cấu 100 điểm của Đồ án

1. **Reimplement the Game & GUI (20 điểm):**

   * Core mechanics (10 điểm): Bàn cờ cơ bản, lăn khối 4 hướng, kiểm tra rơi/thắng.

   * Advanced tiles (10 điểm): Ô dễ vỡ, cầu và đủ 3 loại công tắc (Soft, Heavy, Split).

2. **4 Thuật toán tìm kiếm bằng Python (40 điểm - mỗi thuật toán 10 điểm):**

   * **BFS Solver (10đ):** Tìm kiếm theo chiều rộng.

   * **DFS / IDS Solver (10đ):** Tìm kiếm theo chiều sâu (có kiểm soát lặp trạng thái) hoặc Lặp sâu dần (Iterative Deepening Search).

   * **UCS Solver (10đ):** Tìm kiếm chi phí cực tiểu. **Lưu ý:** Nếu mọi bước đi đều có `cost = 1` thì UCS biến thành BFS; do đó bắt buộc phải tự thiết kế hàm chi phí không đồng nhất (Non-uniform cost function) và giải thích lý do trong báo cáo.

   * **A* Solver (10đ):** Tìm kiếm A* với hàm Heuristic ước lượng khoảng cách tới đích. Phải giải thích cách thiết kế và chứng minh tính **Admissible** (không đánh giá quá cao chi phí thực tế) / **Consistent** tương ứng với hàm Cost đã chọn.

3. **Báo cáo PDF - Report (30 điểm):**

   * **Phân công công việc & % Hoàn thành:** Điểm cá nhân = Điểm nhóm x % Hoàn thành của thành viên đó.

   * **Mô tả thuật toán (10đ):** Giải thích chi tiết BFS, DFS/IDS, UCS, A* và cách mô hình hóa bài toán (State representation, Actions, Transition model, Goal test, Cost function, Heuristics, tránh lặp trạng thái).

   * **Thực nghiệm - Experiments (20đ):** Chạy thử nghiệm trên bộ test cases chia theo độ khó tăng dần. Đo đủ 4 thông số: **Search Time**, **Peak Memory Usage**, **Expanded Nodes**, **Solution Length**. Trình bày bằng **Bảng số liệu (Tables)**, **Biểu đồ (Charts/Plots)** và nhận xét ưu/nhược điểm của từng thuật toán.

   * **References & Appendix:** Trích dẫn mọi nguồn tham khảo (link GitHub, tài liệu) và **ghi lại cách nhóm sử dụng AI (LLMs) kèm các câu Prompts đã dùng**.

4. **Video Demo YouTube (10 điểm):**

   * Quay giao diện GUI 3D (5đ) và quá trình chơi thủ công + bấm nút chạy các Solver tự lăn về đích (5đ), có **phụ đề hoặc thuyết minh** (Tiếng Việt hoặc Tiếng Anh), up lên YouTube ở chế độ Public và dán link vào báo cáo.

### 1.3. Tổng hợp 7 câu trả lời của Thầy trong bảng Q&A

1. **Test case dùng nguồn có sẵn trên mạng được không?** $\rightarrow$ Được.

2. **Số lượng test case tối thiểu là bao nhiêu?** $\rightarrow$ Tối thiểu **10 test cases** (Repo hiện có **20 màn chơi** thuộc 5 nhóm).

3. **Báo cáo viết bằng tiếng Anh hay tiếng Việt?** $\rightarrow$ Tùy nhóm, nhưng **phải thống nhất 1 ngôn ngữ**, tránh nửa Anh nửa Việt.

4. **Khi bấm nút Solve thì GUI hiện đáp án thế nào?** $\rightarrow$ **GUI tự động cho khối sắt lăn từng bước đến đích luôn.**

5. **Có được dùng Source Code game có sẵn không?** $\rightarrow$ Được (nhớ trích dẫn/cite đầy đủ trong báo cáo).

6. **Tiêu chí của GUI là gì?** $\rightarrow$ **Phải là 3D.**

7. **GUI code bằng ngôn ngữ khác được không?** $\rightarrow$ Được (ví dụ JavaScript/Three.js), chỉ cần **riêng phần thuật toán bắt buộc viết bằng Python**.

**⚠️ Cảnh báo từ đề bài:** Giảng viên có quyền gọi **vấn đáp ngẫu nhiên (oral interviews)** để kiểm tra kiến thức thực sự của từng thành viên về dự án. Mọi hành vi đạo văn hoặc gian lận sẽ bị 0 điểm toàn bộ môn học.

---

## 2. TRẠNG THÁI HIỆN TẠI CỦA DỰ ÁN (NHỮNG GÌ ĐÃ XONG vs. CẦN LÀM TIẾP)

Repo hiện có **Bộ khung lõi (`core/`)**, **20 màn chơi**, **5 solver BFS, DFS, IDS, UCS, A*** và **Giao diện Web 3D**. Bản sửa và benchmark phục vụ report cần được nhóm chạy kiểm tra trước khi chốt số liệu.

| Đường dẫn File | Trạng thái | Mô tả chi tiết |
| :--- | :---: | :--- |
| `Source/core/state.py` | **ĐÃ CÀI ĐẶT** | `State` có hàm băm; lưu tọa độ, hướng, trạng thái cầu và khối đang điều khiển. Không thay đổi thuộc tính của một state khi nó đã nằm trong `visited` hoặc được dùng làm khóa. |
| `Source/core/board.py` | ✅ **ĐÃ XONG 100%** | Đọc file JSON map, kiểm tra nước đi hợp lệ (rơi xuống Void, vỡ gạch cam Fragile, cầu đóng), xử lý đủ 3 công tắc (`soft`, `heavy`, `split` tách/gộp khối). **Tuyệt đối không sửa.** |
| `Source/solvers/base_solver.py` | **ĐÃ CÀI ĐẶT** | Đo phần `solve()` bằng `tracemalloc`, đơn vị KiB; giới hạn mặc định 30 giây và 500.000 node. Benchmark report đo thêm phần khởi tạo solver. |
| `Source/main.py` | ✅ **ĐÃ XONG 100%** | Server Flask kết nối Python với GUI 3D. **Đã cài cơ chế tự động nạp thuật toán**: hễ ai code xong file solver nào là server tự nhận diện, không cần sửa `main.py`. |
| `Source/levels/` | **20 MAP** | Level 01–12 và 13–20 (`_split`). Ba nền công tắc ở map 14–16 đã đổi thành gạch thường; vẫn cần kiểm tra khả năng tiếp cận và kích hoạt. |
| `Source/validate_levels.py` | **ĐÃ CÀI ĐẶT** | Tìm lời giải bằng BFS; phân biệt trạng thái giới hạn với vô nghiệm và chấp nhận lời giải 0 bước. |
| `Source/benchmark.py` | **BẢN CŨ** | Script một lần chạy; dữ liệu cũ không có thông tin máy và không đo phần khởi tạo heuristic của A*. |
| `Source/benchmark_report.py` | **CHỜ CHẠY** | Kiểm tra nhỏ, replay lời giải, chạy lặp, đối chiếu BFS–IDS và UCS–A*, xuất CSV/JSON/LaTeX/biểu đồ vào thư mục riêng. |
| `Source/solvers/bfs_solver.py` | **ĐÃ CÀI ĐẶT** | Queue, `visited`, đường đi lưu trong frontier; tối ưu số hành động. |
| `Source/solvers/dfs_solver.py` | **ĐÃ CÀI ĐẶT** | Stack, `visited`; trả `None` khi hết frontier mà không tới đích. |
| `Source/solvers/ids_solver.py` | **ĐÃ CÀI ĐẶT** | Lặp sâu dần, `MAX_DEPTH = 100`, `path_states` và `best_depth`; có trạng thái `DEPTH_LIMIT`. |
| `Source/solvers/ucs_solver.py` | **ĐÃ CÀI ĐẶT** | `heapq`, `visited`, dùng chung `get_step_cost` với A*. |
| `Source/solvers/astar_solver.py` | **ĐÃ CÀI ĐẶT** | Gọi `Heuristic.__call__` trong `search_utils.py`; xem Mục 5.4. |
| `Source/gui/index.html` | **ĐÃ CÀI ĐẶT** | Có đủ 5 nút Solve, OrbitControls, Split/ghép khối và hoạt ảnh; nhóm kiểm tra trực tiếp trên GUI. |
| `Report.pdf` & `Video Demo` | **CẦN CHỐT** | Cập nhật kết quả benchmark thực tế, giải thích đúng heuristic đang dùng và bổ sung link video. |

---

## 3. HƯỚNG DẪN CÀI ĐẶT, CHẠY THỬ (TEST SPLIT SWITCH) & TẮT SERVER

Ngay sau khi clone dự án về máy, mọi thành viên làm theo đúng các bước sau:

### Bước 1: Cài đặt thư viện

Mở Terminal trong VS Code (`Ctrl + ~`) tại thư mục gốc và chạy:

~~~bash

pip install -r requirements.txt

~~~

### Bước 2: Kiểm tra và chạy benchmark trên 20 map

~~~bash

python Source/benchmark_report.py --check-only

python Source/benchmark_report.py --repeats 3 --time-limit 10 --node-limit 250000 --machine-label "Lenovo Legion 5 R7000 2024"

~~~

Chỉ chạy benchmark khi kiểm tra nhanh không có `FAIL`. `LIMIT` trong kiểm tra heuristic nghĩa là chưa duyệt hết đồ thị, chưa kết luận phần còn lại. Mỗi lần chạy lưu vào `Source/results/report_<thời gian>/`: `benchmark_raw.csv`, `benchmark_results.csv`, `machine_info.json`, `checks.json`, `solutions.jsonl`, 5 biểu đồ `.png`, `bfs.jpg` và hai đoạn bảng `.tex`.

Thời gian chính trong report là `total_time_sec` (khởi tạo solver + `solve()`); `search_time_sec` giữ riêng phép đo cũ. Bộ nhớ là đỉnh cấp phát Python trong cùng phạm vi, đơn vị KiB. Các phép đo bật `tracemalloc`, không dùng GPU. Giới hạn thời gian áp dụng cho `solve()`; thời gian khởi tạo được đo thêm. Chỉ lấy trung vị và vẽ những trường hợp thành công đủ số lần, không có lỗi đối chiếu; các trường hợp bị giới hạn vẫn được lưu với trạng thái tương ứng.

### Bước 3: Khởi chạy Giao diện Game 3D

~~~bash

python Source/main.py

~~~

Khi Terminal hiện dòng `🚀 Khởi chạy Bloxorz 3D tại địa chỉ: http://127.0.0.1:5000`, mở trình duyệt (Chrome/Edge) vào: **`http://127.0.0.1:5000`**.

* **Cách chơi bằng tay:** Dùng 4 phím mũi tên `Lên`, `Xuống`, `Trái`, `Phải` để lăn khối sắt.

* **Cách test nút Solve tự động:** Bấm nút **`Solve BFS`** ở góc trái, khối sắt sẽ tự động lăn từ đầu đến đích và hiện đủ 4 thông số đo đạc.

* **Cách test cơ chế Tách khối (`Split Switch`):**

  * Ở ô chọn màn chơi góc trái, chọn **`level_10.json`**, **`level_11.json`**, hoặc **`level_12.json`**.

  * Bấm **`Solve BFS`** (hoặc tự lăn khối đứng thẳng vào ô công tắc màu tím) để xem khối `1x1x2` tách thành 2 khối nhỏ `1x1x1` (xanh đậm & xanh nhạt), bấm phím **`Space`** để đổi khối điều khiển, đi bấm công tắc mở cầu và tự ghép lại khi đứng cạnh nhau!

### Bước 4: Cách tắt chương trình

Để dừng server đang chạy, bấm chuột vào cửa sổ **Terminal** trong VS Code và nhấn tổ hợp phím **`Ctrl + C`**.

---

## 4. CHI TIẾT BỘ 20 MÀN CHƠI TEST CASES (`Source/levels/`)

Bộ map dùng nguồn tham khảo **Damien Clarke, Bloxorz, Coolmath Games & StrategyWiki Walkthrough** và các màn mở rộng của nhóm, chia thành **5 nhóm cấu trúc**. Độ khó thực tế cần nhận xét từ kết quả đo:

1. **Nhóm 1 - Cơ bản (`level_01` $\rightarrow$ `level_03`):** Chỉ gồm gạch thường (`1`), ô trống (`0`) và lỗ đích (`9`). Gồm Stage 1 gốc (7 bước), Stage 3 gốc (20 bước) và Stage 6 Labyrinth (31 bước).

2. **Nhóm 2 - Ô dễ vỡ Fragile Tiles (`level_04` $\rightarrow$ `level_06`):** Có thêm các ô gạch màu cam (`2` - đứng thẳng sẽ bị vỡ).

   * `level_05.json` có ô Fragile. Không mặc định rằng BFS đi 8 bước còn UCS đi 16 bước; so sánh số hành động và chi phí từ kết quả benchmark thực tế.

3. **Nhóm 3 - Cầu & Công tắc (`level_07` $\rightarrow$ `level_09`):** Gồm Stage 2 gốc và các màn mở rộng kết hợp nhiều cầu (`bridges`) với công tắc tròn (`soft` switch) và công tắc chữ X (`heavy` switch).

4. **Nhóm 4 - Kết hợp & Tách khối Split Switch (`level_10` $\rightarrow$ `level_12`):** Kết hợp gạch Fragile, cầu, công tắc và cổng dịch chuyển tách khối.

5. **Nhóm 5 - Split mở rộng (`level_13_split` $\rightarrow$ `level_20_split`):** Gồm các cấu hình Split, cầu và công tắc phức tạp hơn. Có lời giải chưa chứng minh mọi công tắc đều đã được kiểm thử; xem danh sách công tắc đã kích hoạt trong `checks.json` và `solutions.jsonl`.

---

## 5. ĐẶC TẢ KỸ THUẬT ("HỢP ĐỒNG CODE" CHO NGƯỜI CODE & AI)

Để code của 5 thành viên ghép vào nhau chạy khớp 100%, mọi người bắt buộc tuân thủ các quy định sau:

### 5.1. Quy định đặt tên File và tên Class

* Thuật toán **BFS**: `Source/solvers/bfs_solver.py` $\rightarrow$ `class BFSSolver(BaseSolver)` **(Đã có sẵn)**

* Thuật toán **DFS**: `Source/solvers/dfs_solver.py` $\rightarrow$ `class DFSSolver(BaseSolver)`

* Thuật toán **IDS**: `Source/solvers/ids_solver.py` $\rightarrow$ `class IDSSolver(BaseSolver)`

* Thuật toán **UCS**: `Source/solvers/ucs_solver.py` $\rightarrow$ `class UCSSolver(BaseSolver)`

* Thuật toán **A\***: `Source/solvers/astar_solver.py` $\rightarrow$ `class AStarSolver(BaseSolver)`

### 5.2. Cấu trúc đối tượng `State` (`Source/core/state.py`) & `Board` (`Source/core/board.py`)

* **Thuộc tính của `state`:**

  * `state.r`, `state.c`: Tọa độ dòng, cột của khối (nếu `LYING_H` thì chiếm `(r, c)` và `(r, c+1)`; nếu `LYING_V` thì chiếm `(r, c)` và `(r+1, c)`).

  * `state.orientation`: `Orientation.STANDING` (0), `Orientation.LYING_H` (1), `Orientation.LYING_V` (2), `Orientation.SPLIT` (3 - khi tách đôi sẽ có thêm tọa độ khối thứ hai ở `state.r2, state.c2` và khối đang chọn `state.active_cube`).

  * `state.bridges_mask`: Tuple kiểu `bool` lưu trạng thái Đóng/Mở của các cây cầu.

  * `state.get_occupied_cells()`: Trả về danh sách các ô `[(r, c), ...]` mà khối đang đè lên.

  * `State` đã được cài sẵn `__hash__`, `__eq__`, và `__lt__`, nên có thể bỏ trực tiếp vào `visited = set()`, `dict()`, hoặc `heapq.heappush()`.

* **Các hàm có sẵn của `self.board`:**

  * `self.board.get_initial_state() -> State`: Lấy trạng thái xuất phát.

  * `self.board.is_goal(state: State) -> bool`: Trả về `True` nếu khối đã đứng thẳng tại ô đích.

  * `self.board.get_successors(state: State) -> List[Tuple[str, State]]`: Trả về danh sách các cặp `(action, next_state)` hợp lệ (`action` gồm `'UP'`, `'DOWN'`, `'LEFT'`, `'RIGHT'`, `'SWITCH_CUBE'`).

  * `self.board.grid[r][c]`: Ma trận bản đồ (`0`: Void, `1`: Gạch thường, `2`: Ô dễ vỡ Fragile tile, `9`: Đích Goal).

  * `self.board.goal_pos`: Tuple `(goal_r, goal_c)` tọa độ đích.

  * `self.board.switches`: Dictionary `{ (r, c): switch_dict }` lưu các công tắc trên bản đồ (công tắc `split` có thuộc tính `"teleport_to": [[tr1, tc1], [tr2, tc2]]`).

### 5.3. Khuôn mẫu `BaseSolver` & 3 Ràng buộc bắt buộc trong `_search(self)`

~~~python

from typing import List, Optional

from solvers.base_solver import BaseSolver

class TenThuatToanSolver(BaseSolver):

    def _search(self) -> Optional[List[str]]:

        # RÀNG BUỘC 1: Mỗi lần gọi board.get_successors trong tìm kiếm,

        # BẮT BUỘC phải cộng biến đếm:

        #     self.expanded_nodes += 1

        # RÀNG BUỘC 2: KHÔNG dùng lệnh print() trong vòng lặp để không làm chậm Search Time.

        # RÀNG BUỘC 3: Trả về list các bước đi (VD: ['RIGHT', 'DOWN', ...]) hoặc None nếu vô nghiệm.

        pass

~~~

### 5.4. Quy ước chung về Hàm Chi Phí (Step Cost) cho bạn làm UCS và bạn làm A*

UCS và A* hiện cùng gọi `get_step_cost(board, next_state)` trong `Source/solvers/search_utils.py`:

* **Chi phí nguyên:** `10 + 20*has_fragile + 20*is_split + closed_bridges`, tính trên trạng thái sau bước đi. Mỗi điều kiện Fragile/Split nhận 0 hoặc 1; `closed_bridges` là số cầu chưa cho đi qua.

* **Chi phí trong bảng report:** chia tổng chi phí nguyên cho 10. Bước thường không có cầu đóng là 1; chỉ chạm Fragile là 3. `SWITCH_CUBE` vẫn chịu khoản phạt Split. Đây là các ưu tiên do nhóm đặt ra, không phải xác suất gạch vỡ.

* **Heuristic đang chạy:** `Heuristic.__init__` dùng Dijkstra ngược trên toàn bộ lưới chữ nhật, bỏ qua ô trống và các ràng buộc khối/cầu/Fragile. Cạnh giữa hai ô kề có trọng số 5; cạnh dịch chuyển có trọng số 0. `__call__` trả khoảng cách nhỏ nhất trong các ô khối đang chiếm.

  1. Mỗi bước thật có chi phí ít nhất 10. Mỗi ô của trạng thái kế tiếp có thể được nối từ một ô của trạng thái trước bằng đường trên lưới nới lỏng có chi phí không quá 10, kể cả bước vào cổng rồi dịch chuyển. Vì vậy `h(s) <= cost(s,a,s') + h(s')`, và tại đích `h = 0`.

  2. `merge_to_goal`, `mahattan_heuristic` và `get_heuristic` bên dưới là mã thử nghiệm, chưa được A* gọi. Chúng còn lỗi lấy tọa độ và khởi tạo dữ liệu; chưa dùng làm kết quả thực nghiệm hoặc tuyên bố heuristic thứ hai đã hoàn thiện.

---

## 6. HƯỚNG DẪN TỪNG NHIỆM VỤ & PROMPT MẪU ĐỂ COPY DÁN VÀO AI

Các prompt dưới đây là mẫu từ giai đoạn đầu. Những thông số hoặc nhận xét khác với Mục 5.4 không mô tả bản code hiện tại; giữ lại để đối chiếu lịch sử sử dụng AI.

### 🔹 NHIỆM VỤ A: Cài đặt DFS (`Source/solvers/dfs_solver.py`)

* 💡 **Prompt mẫu copy dán vào Gemini Pro / ChatGPT:**

  > **"Tôi đang làm đồ án Bloxorz Solver bằng Python. Đây là đặc tả kỹ thuật của nhóm tôi: [Dán toàn bộ Mục 5 của README vào đây]. Hãy viết code hoàn chỉnh cho file `Source/solvers/dfs_solver.py` với `class DFSSolver(BaseSolver)` sử dụng ngăn xếp (stack) và tập `visited` để tránh lặp chu trình. Đảm bảo tăng `self.expanded_nodes += 1` mỗi khi pop một trạng thái ra khỏi stack. Sau đó, hãy viết cho tôi 1 trang giải thích chi tiết thuật toán DFS trong bài toán Bloxorz (mã giả, độ phức tạp thời gian/không gian, tại sao DFS tìm ra đường đi rất dài và không tối ưu) để tôi đưa vào Report và đi vấn đáp."**

### 🔹 NHIỆM VỤ B: Cài đặt IDS (`Source/solvers/ids_solver.py`)

* 💡 **Prompt mẫu copy dán vào Gemini Pro / ChatGPT:**

  > **"Tôi đang làm đồ án Bloxorz Solver bằng Python. Đây là đặc tả kỹ thuật của nhóm tôi: [Dán toàn bộ Mục 5 của README vào đây]. Hãy viết code hoàn chỉnh cho file `Source/solvers/ids_solver.py` với `class IDSSolver(BaseSolver)` cài đặt thuật toán Iterative Deepening Search (lặp sâu dần với `max_depth = 50`). Lưu ý: trong mỗi vòng lặp giới hạn độ sâu `limit`, hãy dùng dictionary `best_depth = {start_state: 0}` để cắt tỉa các trạng thái bị lặp lại ở độ sâu lớn hơn hoặc bằng độ sâu đã thăm nhằm giúp IDS chạy nhanh trên bản đồ có chu trình mà không mất tính tối ưu. Sau đó viết giải thích lý thuyết so sánh IDS với BFS và DFS để tôi đưa vào Report."**

### 🔹 NHIỆM VỤ C: Cài đặt UCS (`Source/solvers/ucs_solver.py`)

* 💡 **Prompt mẫu copy dán vào Gemini Pro / ChatGPT:**

  > **"Tôi đang làm đồ án Bloxorz Solver bằng Python. Đây là đặc tả kỹ thuật của nhóm tôi: [Dán toàn bộ Mục 5 của README vào đây]. Hãy viết code hoàn chỉnh cho file `Source/solvers/ucs_solver.py` với `class UCSSolver(BaseSolver)` sử dụng `heapq` và hàm chi phí không đồng nhất đúng như Mục 5.4 (bước thường = 1.0, bước có ô đè lên Fragile tile `self.board.grid[r][c] == 2` thì cost = 4.0). Sau đó, hãy viết phần giải thích lý thuyết hàm Cost này và phân tích tại sao trên màn `level_05.json` thuật toán BFS lại đi đường tắt qua gạch cam còn UCS lại chọn đường vòng qua gạch cứng an toàn để tôi đưa vào Report."**

### 🔹 NHIỆM VỤ D: Cài đặt A* (`Source/solvers/astar_solver.py`)

* 💡 **Prompt mẫu copy dán vào Gemini Pro / ChatGPT:**

  > **"Tôi đang làm đồ án Bloxorz Solver bằng Python. Đây là đặc tả kỹ thuật của nhóm tôi: [Dán toàn bộ Mục 5 của README vào đây]. Hãy viết code hoàn chỉnh cho file `Source/solvers/astar_solver.py` với `class AStarSolver(BaseSolver)` sử dụng `heapq`. Hãy thiết kế hàm `heuristic(self, state)` thật chặt chẽ theo đúng Mục 5.4: sử dụng khoảng cách Manhattan chia 2, xử lý cả trường hợp `Orientation.SPLIT` và trường hợp bản đồ có công tắc dịch chuyển `split` switch (lấy min giữa đi thẳng và đi qua cổng teleport). Kèm theo đó, hãy viết chứng minh toán học tại sao hàm Heuristic này đảm bảo tính Admissible và Consistent để tôi đưa vào Report."**

### 🔹 NHIỆM VỤ E: Nâng cấp Giao diện 3D (`Source/gui/index.html`) & Quay Video Demo

* 💡 **Prompt mẫu copy dán vào Gemini Pro / ChatGPT:**

  > **"Đây là file `Source/gui/index.html` hiện tại của nhóm tôi: [Dán toàn bộ code file Source/gui/index.html vào đây]. Hãy giữ nguyên toàn bộ các hàm gọi API backend Flask (`/api/levels`, `/api/level/<filename>`, `/api/move`, `/api/solve`), nhưng nâng cấp giao diện Three.js giúp tôi: (1) Thêm nút bấm `Solve IDS` gọi `runSolver('ids')`, (2) Thêm đường viền đen sắc nét `THREE.EdgesGeometry` cho từng ô gạch và khối sắt 3D để nhìn rõ khối như game gốc, (3) Tích hợp `OrbitControls` qua link CDN để dùng chuột xoay/zoom bản đồ 3D tự do, (4) Vẽ công tắc `heavy` hình chữ X màu vàng và `soft` hình trụ tròn nổi bật trên mặt gạch."**

---

## 7. QUY TRÌNH LÀM VIỆC TRÊN GIT & CHUẨN BỊ BÁO CÁO

1. **Tạo nhánh riêng (Feature Branch) và kiểm tra trước khi push:**

   * Tạo nhánh riêng: `git checkout -b feature/ten-phan-viec`

   * Sau khi code xong, chạy kiểm tra bằng `python Source/benchmark_report.py --check-only`, rồi chạy benchmark report trên cùng phiên bản source.

   * Kiểm tra trạng thái, lời giải và đối chiếu trong `checks.json`. `TIME_LIMIT`, `NODE_LIMIT`, `DEPTH_LIMIT` không chứng minh vô nghiệm; lời giải 0 bước có thể có `Expanded Nodes = 0`. Không sửa source trong lúc đo.

   * Đẩy lên nhánh riêng (`git push origin feature/ten-phan-viec`) rồi nhắn lên nhóm để kiểm tra và merge vào `main`.

2. **Lưu lại Prompt AI cho phần Appendix:**

   * Đề bài bắt buộc trong mục **Appendix** của báo cáo phải liệt kê các câu Prompt nhóm đã dùng khi làm việc với AI. Mỗi anh em nhớ lưu lại 2–3 câu prompt mình đã hỏi AI kèm tóm tắt kết quả vào file báo cáo chung của nhóm nhé!

## Sơ đồ luồng hoạt động của chương trình

```mermaid
flowchart LR
    subgraph Client_Entry ["1. Giao diện & Điều phối"]
        GUI["💻 gui/index.html<br/>(Three.js 3D Web)"]
        API["⚙️ main.py<br/>(Flask API Server)"]
        BENCH["📊 benchmark.py<br/>(Thực nghiệm độc lập)"]
    end

    subgraph Solvers_Layer ["2. Bộ não Thuật toán (solvers/)"]
        BASE["📐 base_solver.py<br/>(Khuôn mẫu chung)"]
        ALGOS["🔍 Các thuật toán con:<br/>• bfs_solver.py<br/>• dfs_solver.py<br/>• ids_solver.py<br/>• ucs_solver.py<br/>• astar_solver.py"]
        BASE --> ALGOS
    end

    subgraph Core_Layer ["3. Luật chơi & Vật lý (core/)"]
        BOARD["🗺️ board.py<br/>(Bản đồ, Công tắc, Cầu, Tách khối)"]
        STATE["🧊 state.py<br/>(Tọa độ khối, Trạng thái cầu, Hash)"]
        BOARD <--> STATE
    end

    %% Luồng Web Solve
    GUI -- "(1) POST /api/solve<br/>{level, algo}" --> API
    API -- "(2) Khởi tạo Board, Solver &<br/>gọi solver.solve()" --> Solvers_Layer
    Solvers_Layer -- "(5) Kết quả: path ['UP', 'RIGHT'...],<br/>time, nodes, memory" --> API
    API -- "(6) Trả JSON về Web<br/>-> Dựng animation 3D lăn về đích" --> GUI

    %% Luồng Giao tiếp Solver - Core
    Solvers_Layer -- "(3) Chỉ gọi 3 hàm:<br/>• get_initial_state()<br/>• is_goal(state)<br/>• get_successors(state)" --> BOARD
    BOARD -- "(4) Trả về các nước đi hợp lệ:<br/>List (action, next_state)" --> Solvers_Layer

    %% Luồng Benchmark
    BENCH -. "(Chạy ngầm hàng loạt<br/>không qua Web/Flask)" .-> Solvers_Layer
    BENCH -. "Đọc màn chơi" .-> BOARD
    BENCH --> CSV["📈 File .csv & Biểu đồ"]
```
