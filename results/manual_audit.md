# Nhật ký Ingestion & Kết quả Chấm tay (Manual Audit)

## 1. Nhật ký Làm sạch Dữ liệu (Ingestion & Cleaning Log)
- **Tài liệu nguồn**: `data/art_of_war.pdf` (*Sun Tzu on the Art of War*, bản dịch tiếng Anh của Lionel Giles, 1910; bản in của Allandale Online Publishing, 2000).
- **Tổng số trang vật lý trong PDF**: 66 trang (đánh số từ 1 đến 66).
- **Số trang bị loại bỏ**: **4/66 trang (6.06%)**, bao gồm:
  - **Trang 1**: Trang bìa và thông tin xuất bản (*Allandale Online Publishing*, ISBN `1-903328-03-9`), không chứa nội dung học thuật của 13 chương.
  - **Trang 2**: Trang trắng hoàn toàn (`0` ký tự).
  - **Trang 3**: Trang mục lục (*Contents: Chapters I–XIII*), chỉ chứa danh sách tên chương và số trang dẫn chiếu.
  - **Trang 66**: Trang trắng hoàn toàn cuối sách (`0` ký tự).
- **Số trang hợp lệ đưa vào Chunking & Indexing**: **62 trang** (từ trang 4 đến trang 65).
- **Quy tắc chuẩn hóa văn bản (`clean_text`)**:
  1. Xóa dòng tiêu đề chương/sách lặp lại ở đầu trang (Running headers dạng `Sun Tzu on the Art of War` hoặc số La Mã kèm tên chương ở đầu mỗi trang).
  2. Xóa số trang đơn lẻ ở cuối trang (Page footers).
  3. Gộp các từ bị ngắt gạch nối cuối dòng (`-\n`) và chuẩn hóa khoảng trắng đa dòng thành một khoảng trắng đơn để tránh đứt từ khi tính embedding.

---

## 2. Chấm tay Hạng mục 1: Chunk Coherence (10 vị trí cố định)
- **Quy tắc lấy mẫu**: Chọn cố định 10 trang đầu tiên có nội dung chính (từ **Trang 4 đến Trang 13**) và kiểm tra chunk đầu tiên (`_000`) của mỗi trang trên cả 3 chiến lược A, B, C.
- **Thang điểm** (theo `BENCHMARK.md` mục 5.1):
  - `2`: Chunk trọn ý, không đứt câu ở đầu hoặc cuối chunk.
  - `1`: Đứt nhẹ ở ranh giới nhưng vẫn đọc hiểu được ý chính.
  - `0`: Đứt ngang câu/danh sách làm mất nghĩa hoặc gộp hỗn tạp nhiều phần không liên quan.

| Vị trí | Trang PDF | Chunk ID (Strategy A) | Điểm A (0-2) | Nhận xét Strategy A (`fixed_size=450, overlap=50`) | Chunk ID (Strategy B & C) | Điểm B (0-2) | Điểm C (0-2) | Nhận xét Strategy B & C (`by_paragraph, max_size=600`) |
| :---: | :---: | :--- | :---: | :--- | :--- | :---: | :---: | :--- |
| 1 | Trang 4 | `art-of-war-1910_p004_fixed_000` | **0** | Cắt ngang điều 4 tại `"4. Th"`, làm đứt lìa danh sách 5 yếu tố cốt lõi sang chunk sau (`q01` trượt top-3). | `art-of-war-1910_p004_para_000` | **2** | **2** | Giữ trọn vẹn điều 1 đến điều 4 (475 ký tự), kết thúc đúng dấu chấm câu cuối điều 4. |
| 2 | Trang 5 | `art-of-war-1910_p005_fixed_000` | **1** | Cắt ngang điều 11 tại `"according to the"`, làm đứt vế sau của câu giải thích. | `art-of-war-1910_p005_para_000` | **2** | **2** | Giữ nguyên vẹn các câu hỏi so sánh ở điều 13 và kết thúc trọn câu tại điều 14 (544 ký tự). |
| 3 | Trang 6 | `art-of-war-1910_p006_fixed_000` | **1** | Cắt ngang điều 20 tại `"Wait"`, tách rời câu mệnh lệnh chiến thuật ở đầu điều 20. | `art-of-war-1910_p006_para_000` | **2** | **2** | Giữ trọn điều 15 đến điều 19 (466 ký tự), kết thúc trọn vẹn tại `"Hold out baits to entice the enemy. Feign disorder, and crush him."` |
| 4 | Trang 7 | `art-of-war-1910_p007_fixed_000` | **1** | Cắt ngang cuối câu điều 1 chương II tại `"which will only be"`, thiếu mệnh đề kết thúc. | `art-of-war-1910_p007_para_000` | **2** | **2** | Giữ nguyên vẹn toàn bộ điều 1 chương *Waging War* (478 ký tự), đầy đủ thông số 100,000 quân và 1,000 lượng bạc/ngày. |
| 5 | Trang 8 | `art-of-war-1910_p008_fixed_000` | **1** | Cắt ngang giữa từ ở điều 4 (`"ar"` trong `"arrows"`), gây đứt từ ở cuối chunk. | `art-of-war-1910_p008_para_000` | **2** | **2** | Giữ trọn điều 2 và điều 3 chương II (510 ký tự), không cắt ngang từ hay câu. |
| 6 | Trang 9 | `art-of-war-1910_p009_fixed_000` | **1** | Cắt ngang điều 9 tại `"Bring war material with"`, đứt câu giữa chừng. | `art-of-war-1910_p009_para_000` | **2** | **2** | Giữ trọn vẹn điều 7 và điều 8 chương II (270 ký tự), kết thúc đúng dấu chấm câu. |
| 7 | Trang 10 | `art-of-war-1910_p010_fixed_000` | **1** | Cắt ngang từ `"pl"` (trong `"plains of Chung-shan"`), làm đứt câu so sánh chi phí vận lương. | `art-of-war-1910_p010_para_000` | **2** | **2** | Giữ trọn vẹn điều 13 và điều 14 chương II (564 ký tự), bảo toàn toàn bộ các tỷ lệ quy đổi lương thảo. |
| 8 | Trang 11 | `art-of-war-1910_p011_fixed_000` | **2** | Ngẫu nhiên kết thúc vừa khít cuối câu đầu của điều 3 (`"...next best is toPrevent the junction of the enemy's forces."`). | `art-of-war-1910_p011_para_000` | **2** | **2** | Giữ trọn vẹn điều 1 và điều 2 chương III *Attack by Stratagem* (420 ký tự). |
| 9 | Trang 12 | `art-of-war-1910_p012_fixed_000` | **1** | Cắt ngang câu ở điều 8 tại `"if equally matched, we"`, thiếu vế hành động. | `art-of-war-1910_p012_para_000` | **1** | **1** | Đầu trang 12 có câu tiếp nối từ cuối trang 11 chuyển sang trước khi vào điều 6–7, nhưng kết thúc cuối chunk trọn vẹn tại hết điều 7 (410 ký tự). |
| 10 | Trang 13 | `art-of-war-1910_p013_fixed_000` | **2** | Kết thúc ngay sau câu dẫn điều 12 (`"12. Now there are three ways in which a ruler can bring misfortune upon his army:—"`). | `art-of-war-1910_p013_para_000` | **2** | **2** | Giữ trọn vẹn phần kết điều 10 và toàn bộ điều 11 chương III (482 ký tự). |
| **Tổng** | **10 vị trí** | **Strategy A** | **11/20** | **TB: 1.10 / 2.00 (55.0%)** | **Strategy B & C** | **19/20** | **19/20** | **TB: 1.90 / 2.00 (95.0%)** |

---

## 3. Chấm tay Hạng mục 2: Metadata Usefulness & Filter Compliance (Tập Test)
- **Quy tắc kiểm tra** (theo `BENCHMARK.md` mục 5.2):
  1. Kiểm tra toàn bộ **15 bản ghi kết quả** của tập `test` (`5 câu × top-3`) ở Strategy C xem các trường metadata (`doc_id`, `page`, `section`, `title`, `year`, `offset_start`, `offset_end`) có khớp chính xác với vị trí thực tế trong file PDF gốc hay không.
  2. Kiểm tra **Filter Compliance**: Với các câu có trường `filter` (`q20` ở tập `test` và `q13`, `q14`, `q15` ở tập `dev`), kiểm tra xem cả 3 kết quả top-3 có thuộc đúng chương (`section`) được yêu cầu hay không.

### 3.1. Kiểm tra 15 bản ghi Top-3 tập Test trên Strategy C
| Câu hỏi | Rank | Chunk ID | `doc_id` | `page` | `section` | Khớp PDF gốc? | Đạt / Không đạt |
| :---: | :---: | :--- | :--- | :---: | :--- | :---: | :---: |
| `q16` | 1 | `art-of-war-1910_p013_para_000` | `art-of-war-1910` | 13 | `Attack by Stratagem` | Khớp chính xác trang 13, chương III | **Đạt (1/1)** |
| `q16` | 2 | `art-of-war-1910_p028_para_000` | `art-of-war-1910` | 28 | `Maneuvering` | Khớp chính xác trang 28, chương VII | **Đạt (1/1)** |
| `q16` | 3 | `art-of-war-1910_p020_para_001` | `art-of-war-1910` | 20 | `Energy` | Khớp chính xác trang 20, chương V | **Đạt (1/1)** |
| `q17` | 1 | `art-of-war-1910_p026_para_001` | `art-of-war-1910` | 26 | `Weak Points and Strong` | Khớp chính xác trang 26, chương VI | **Đạt (1/1)** |
| `q17` | 2 | `art-of-war-1910_p053_para_000` | `art-of-war-1910` | 53 | `The Nine Situations` | Khớp chính xác trang 53, chương XI | **Đạt (1/1)** |
| `q17` | 3 | `art-of-war-1910_p005_para_001` | `art-of-war-1910` | 5 | `Laying Plans` | Khớp chính xác trang 5, chương I | **Đạt (1/1)** |
| `q18` | 1 | `art-of-war-1910_p039_para_000` | `art-of-war-1910` | 39 | `The Army on the March` | Khớp chính xác trang 39, chương IX | **Đạt (1/1)** |
| `q18` | 2 | `art-of-war-1910_p030_para_000` | `art-of-war-1910` | 30 | `Maneuvering` | Khớp chính xác trang 30, chương VII | **Đạt (1/1)** |
| `q18` | 3 | `art-of-war-1910_p056_para_000` | `art-of-war-1910` | 56 | `The Nine Situations` | Khớp chính xác trang 56, chương XI | **Đạt (1/1)** |
| `q19` | 1 | `art-of-war-1910_p053_para_001` | `art-of-war-1910` | 53 | `The Nine Situations` | Khớp chính xác trang 53, chương XI | **Đạt (1/1)** |
| `q19` | 2 | `art-of-war-1910_p041_para_001` | `art-of-war-1910` | 41 | `The Army on the March` | Khớp chính xác trang 41, chương IX | **Đạt (1/1)** |
| `q19` | 3 | `art-of-war-1910_p011_para_000` | `art-of-war-1910` | 11 | `Attack by Stratagem` | Khớp chính xác trang 11, chương III | **Đạt (1/1)** |
| `q20` | 1 | `art-of-war-1910_p063_para_000` | `art-of-war-1910` | 63 | `The Use of Spies` | Khớp chính xác trang 63, chương XIII | **Đạt (1/1)** |
| `q20` | 2 | `art-of-war-1910_p063_para_001` | `art-of-war-1910` | 63 | `The Use of Spies` | Khớp chính xác trang 63, chương XIII | **Đạt (1/1)** |
| `q20` | 3 | `art-of-war-1910_p065_para_000` | `art-of-war-1910` | 65 | `The Use of Spies` | Khớp chính xác trang 65, chương XIII | **Đạt (1/1)** |

- **Độ chính xác Metadata (Metadata Accuracy)**: **15/15 (100%)** bản ghi ở Strategy B và C có `doc_id`, `page`, `section` khớp tuyệt đối với PDF gốc (Strategy A chỉ có `doc_id` và `page`, thiếu `section` nên chỉ đạt cấp cơ bản).

### 3.2. So sánh Filter Compliance (Tuân thủ bộ lọc `section` trên cả 3 kết quả Top-3)
| Câu hỏi | Split | Bộ lọc yêu cầu (`filter`) | Top-3 Sections ở Strategy A & B (Không lọc) | Top-3 Sections ở Strategy C (Có lọc SQL) | Tuân thủ A & B | Tuân thủ C |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: |
| `q13` | `dev` | `{"section": "Maneuvering"}` | 1. `Maneuvering` (p.28)<br>2. `The Nine Situations` (p.54)<br>3. `The Nine Situations` (p.55) | 1. `Maneuvering` (p.28)<br>2. `Maneuvering` (p.32)<br>3. `Maneuvering` (p.28) | **Không đạt** (Lẫn 2/3 chunk chương XI) | **Đạt (3/3)** |
| `q14` | `dev` | `{"section": "Terrain"}` | 1. `Terrain` (p.45)<br>2. `Laying Plans` (p.6)<br>3. `The Nine Situations` (p.54) | 1. `Terrain` (p.45)<br>2. `Terrain` (p.46)<br>3. `Terrain` (p.46) | **Không đạt** (Lẫn 2/3 chunk chương I, XI) | **Đạt (3/3)** |
| `q15` | `dev` | `{"section": "The Nine Situations"}` | 1. `The Nine Situations` (p.49)<br>2. `Laying Plans` (p.4)<br>3. `Terrain` (p.45) | 1. `The Nine Situations` (p.49)<br>2. `The Nine Situations` (p.55)<br>3. `The Nine Situations` (p.50) | **Không đạt** (Lẫn 2/3 chunk chương I, X) | **Đạt (3/3)** |
| `q20` | `test` | `{"section": "The Use of Spies"}` | 1. `The Use of Spies` (p.63)<br>2. `The Use of Spies` (p.63)<br>3. `The Use of Spies` (p.65) | 1. `The Use of Spies` (p.63)<br>2. `The Use of Spies` (p.63)<br>3. `The Use of Spies` (p.65) | **Đạt (3/3)** | **Đạt (3/3)** |
| **Tổng** | **4 câu** | **Tỷ lệ câu tuân thủ tuyệt đối 100% Top-3** | — | — | **Dev: 0/3 (0%)**<br>**Test: 1/1 (100%)** | **Dev: 3/3 (100%)**<br>**Test: 1/1 (100%)** |

---

## 4. Chấm tay Hạng mục 3: Grounding Quality (5 câu tập Test `q16`–`q20`)
- **Thang điểm** (theo `BENCHMARK.md` mục 5.3):
  - `2`: Top-3 chứa đầy đủ bằng chứng để trả lời chính xác và trọn vẹn câu hỏi.
  - `1`: Top-3 có thông tin liên quan đúng chủ đề/trang đích nhưng thiếu một phần chi tiết cụ thể trong câu hỏi.
  - `0`: Top-3 không chứa thông tin trả lời được câu hỏi.

| Câu hỏi | Nội dung câu hỏi (Test Split) | Điểm A (0-2) | Điểm B (0-2) | Điểm C (0-2) | Giải thích chi tiết dựa trên `traces_A.json`, `traces_B.json`, `traces_C.json` |
| :---: | :--- | :---: | :---: | :---: | :--- |
| `q16` | *What is the rule of war regarding how to deal with an enemy force when our forces are ten to the enemy's one, five to one, and twice as numerous?* | **2** | **2** | **2** | Cả A (`p013_fixed_001` ở Rank 1) và B, C (`p013_para_000` ở Rank 1) đều trả về trọn vẹn điều 11 chương III trang 13 chứa đủ 3 tỷ lệ: 10 chọi 1 thì bao vây, 5 chọi 1 thì tấn công, gấp đôi thì chia quân. |
| `q17` | *How does Sun Tzu compare military tactics to water, and what should a military force avoid and strike according to this analogy?* | **2** | **1** | **1** | Ở Strategy A, `p026_fixed_001` (Rank 1) chứa cả điều 29–31 trang 26 (*"avoid what is strong and to strike at what is weak"*). Ở Strategy B & C, Rank 1 trả về `p026_para_001` (trang 26) chứa điều 31–33 giải thích quy luật dòng nước biến hóa theo địa hình/kẻ địch, nhưng thiếu câu điều 29–30 nằm ở chunk `p026_para_000` ngay trước đó -> đạt 1/2 điểm (có liên quan trực tiếp đúng ẩn dụ nước ở trang 26 nhưng thiếu vế tránh mạnh đánh yếu). |
| `q18` | *In The Army on the March, what does it mean when a general's soldiers are standing leaning on their spears, and what does it mean when birds gather on a spot?* | **2** | **2** | **2** | Cả A (`p039_fixed_000` ở Rank 1) và B, C (`p039_para_000` ở Rank 1) đều chứa đầy đủ điều 24 (chim tụ tập là doanh trại địch đã bỏ trống) và điều 28 (lính chống giáo đứng là đang đói lả) ở trang 39. |
| `q19` | *Why does Sun Tzu compare a skillful tactician to the shuai-jan, a snake found in the Ch'ang mountains?* | **2** | **2** | **2** | Cả A (`p053_fixed_001` ở Rank 1) và B, C (`p053_para_001` ở Rank 1) đều chứa nguyên vẹn điều 29 chương XI trang 53 mô tả rắn Thường Sơn (*shuai-jan*): đánh vào đầu thì đuôi ứng cứu, đánh vào đuôi thì đầu ứng cứu, đánh vào giữa thì cả đầu lẫn đuôi cùng ứng cứu. |
| `q20` | *In The Use of Spies, how does Sun Tzu define 'local spies', 'inward spies', and 'converted spies'?* (Filter: `section = The Use of Spies`) | **2** | **2** | **2** | Cả A (`p063_fixed_001` ở Rank 1) và B, C (`p063_para_000` ở Rank 1 và `p063_para_001` ở Rank 2) đều chứa đầy đủ định nghĩa điều 8, 9, 10, 11 chương XIII trang 63 về *local spies*, *inward spies* và *converted spies*. |
| **Tổng** | **5 câu tập Test (Thang 10)** | **10/10** | **9/10** | **9/10** | **TB Strategy A: 2.00/2.00 · TB Strategy B & C: 1.80/2.00** |