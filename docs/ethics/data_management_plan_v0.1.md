# Quản lý và giả danh hóa dữ liệu người tham gia — bản nháp v0.1

> **Ghi chú nội bộ (không đưa vào bản nộp).** Bản nháp chưa được phê duyệt và chưa triển khai.
> Phần dưới đường kẻ là đúng nội dung bản nộp; bản Word được dựng từ file này. Ô `[...]` chờ
> thầy, đơn vị hoặc hội đồng.
>
> - Huy soạn 2026-10-21 dựa trên [khung đạo đức v0.1 mục 5](ethics_outline_v0.1.md) và
>   [chính sách dữ liệu](../DATA_POLICY.md). Cập nhật 2026-10-29: rút lui, phiếu giấy có danh tính,
>   gán mã ngẫu nhiên, thời hạn lưu; 2026-10-30: danh sách mã tới `SUB035` theo trần tuyển 35.
> - Ngoại lệ của quy tắc "raw bất biến": xóa theo yêu cầu rút lui (thêm 2026-10-26) và tiêu hủy khi
>   hết hạn lưu (thêm 2026-10-29), đều có nhật ký; xem thêm [quy ước dữ liệu](../quy_uoc_du_lieu.md)
>   mục 1.
> - 2026-10-31, sau rà soát cuối (đề xuất, chờ thầy/đơn vị): thêm mục 1 (đơn vị chịu trách nhiệm,
>   căn cứ pháp lý: Luật 91/2025/QH15 và Nghị định 356/2025/NĐ-CP thay Nghị định 13/2023/NĐ-CP từ
>   2026-01-01; Nghị định 356 Điều 19 yêu cầu hồ sơ đánh giá tác động, nộp trong 60 ngày kể từ khi
>   bắt đầu xử lý; không thấy điều khoản miễn trừ cho nghiên cứu khoa học; tra cứu 2026-10-31
>   trên bản sao văn bản ở luatvietnam.vn và ketoananpha.vn, chưa đối chiếu bản gốc), mã hóa toàn ổ cho mọi thiết bị lưu dữ liệu (trước đây chỉ bảng liên kết), mục 5
>   (người đăng ký nhưng không tham gia hoặc không đủ điều kiện), hạn 30 ngày cho việc xóa kể cả bản
>   sao lưu, sau mốc khóa không dùng dữ liệu cho mục đích mới, thời hạn lưu tính từ công bố **đầu
>   tiên**, sự cố dữ liệu ngoài Git, điều kiện cho mục 10 của phiếu đồng thuận, giới tính trong
>   phiếu sàng lọc.
> - 2026-10-31, sau vòng phản biện thứ hai (đã đối chiếu Nghị định 356/2025/NĐ-CP trên
>   luatvietnam.vn: Điều 5 xác nhận yêu cầu trong 02 ngày làm việc, xóa trong 20 ngày, 30 ngày khi có
>   bên xử lý hay bên thứ ba, gia hạn một lần tối đa 20 ngày; Điều 29 báo chủ thể dữ liệu trong 72 giờ
>   khi lộ dữ liệu vị trí hoặc sinh trắc học, báo cơ quan chuyên trách theo Điều 28, lưu hồ sơ vi phạm
>   ít nhất 05 năm kể từ khi khắc phục): xóa trong 20 ngày thay cho 30 ngày; báo người tham gia trong 72
>   giờ, không còn điều kiện "nếu có nguy cơ lộ danh tính"; ngoại lệ lưu hồ sơ sự cố 05 năm; trần tiêu
>   hủy 05 năm kể từ khi kết thúc đề tài (đề xuất, chờ thầy); giảng viên hướng dẫn không mở bảng liên
>   kết; giữ liên lạc tối đa 30 ngày để hỏi thăm sau sự cố; bỏ câu "không thực hiện được" sau mốc khóa,
>   thay bằng đề nghị giữ lại kèm ô chờ căn cứ pháp lý và phương án dự phòng (xóa và chạy lại).
> - Đề xuất của nhóm, chờ thầy/hội đồng: thời hạn lưu, nơi lưu, người quản lý (đề xuất Huy, dự
>   phòng Linh), mốc khóa dữ liệu. Mốc khóa hiện gắn với cổng G4 (Tuần 20, tuần 2027-01-28 đến
>   2027-02-03); nếu đề tài kéo dài theo [đề xuất Tuần 7](../meetings/week_07_de_xuat_sua_protocol_va_ho_so.md)
>   mục 2.1 thì đổi thành 2027-06-04. Không chọn ngày công bố làm mốc khóa, vì ngày này không biết
>   trước nên không cam kết được với người tham gia.
> - Chi tiết kỹ thuật (thư mục `data/raw/<subject>/<session>/<recording>/`, logger
>   `packet-logger-v3`, manifest SHA-256) ở [quy ước dữ liệu](../quy_uoc_du_lieu.md) và
>   [hướng dẫn logger](../protocol/packet_logger.md).

---

## 1. Trách nhiệm và căn cứ

- Đơn vị chịu trách nhiệm dữ liệu: [đơn vị chủ trì]. Người quản lý dữ liệu: [họ tên]; người dự
  phòng: [họ tên].
- Bên kiểm soát dữ liệu là [đơn vị chủ trì]; bên xử lý dữ liệu là nhóm nghiên cứu.
- Thông tin sức khỏe và dữ liệu sinh trắc học là dữ liệu cá nhân nhạy cảm theo Luật Bảo vệ dữ liệu
  cá nhân số 91/2025/QH15 và Nghị định 356/2025/NĐ-CP (cùng hiệu lực từ 01/01/2026). Nhóm chỉ xử lý
  các dữ liệu này cho mục đích nghiên cứu đã nêu trong bản thông tin, trên cơ sở sự đồng ý bằng văn
  bản của người tham gia. Mỗi mục đích có ô đồng ý riêng trong phiếu đồng thuận, các ô để trống sẵn,
  và người tham gia được báo rõ đây là dữ liệu nhạy cảm.
- Hồ sơ đánh giá tác động xử lý dữ liệu cá nhân theo Nghị định 356/2025/NĐ-CP: [đơn vị chủ trì xác
  nhận việc lập và nộp hồ sơ, người phụ trách].

## 2. Dữ liệu thu thập và nơi tạo ra

<!-- cols: 34,38,28 -->
| Loại | Tạo ở đâu | Có định danh? |
| --- | --- | --- |
| Phiếu đồng thuận có chữ ký | Giấy | Có (họ tên, chữ ký, mã nghiên cứu) |
| Bảng liên kết danh tính với mã nghiên cứu | File được mã hóa, trên máy của người quản lý dữ liệu | Có |
| Thông tin liên lạc để hẹn lịch | Lưu cùng chỗ với bảng liên kết, không đưa vào dữ liệu nghiên cứu | Có; xóa khi người đó xong buổi cuối hoặc rút lui, hoặc theo mục 5; giữ thêm tối đa 30 ngày để hỏi thăm sau sự cố nếu người đó đồng ý ở mục 9 của phiếu đồng thuận |
| Phiếu sàng lọc | Giấy, chỉ ghi mã nghiên cứu | Không trực tiếp; có tuổi, giới tính, tay thuận và các câu trả lời về sức khỏe |
| Tín hiệu PPG, điện tim, chuyển động và mốc thời gian | Phần mềm ghi trên máy tính xách tay (qua USB) | Không trực tiếp; dạng sóng là dữ liệu sinh trắc nên không phải ẩn danh tuyệt đối |
| Số đo huyết áp (tâm thu, tâm trương, mạch) và thời điểm đo | Phiếu ghi buổi đo, theo mã lượt đo | Không trực tiếp |
| Thông tin kỹ thuật của buổi đo (cấu hình thiết bị, vị trí đeo, nhiệt độ phòng) | Phần mềm ghi và phiếu ghi buổi đo | Không |
| Nhật ký sự cố, nhật ký rút lui | Biểu mẫu, chỉ ghi mã | Không trực tiếp |

Nhóm không thu mã sinh viên, số căn cước, ngày sinh đầy đủ, ảnh, video, ghi âm hay vị trí GPS. Họ
tên chỉ có trên phiếu đồng thuận giấy và trong bảng liên kết; thông tin liên lạc lưu cùng bảng liên
kết. Dữ liệu nghiên cứu, tức mọi thứ chỉ mang mã nghiên cứu, không chứa họ tên, số điện thoại hay
email.

## 3. Giả danh hóa

- Mã người tham gia có dạng `SUB001` và được gán ngẫu nhiên. Trước khi tuyển, người quản lý dữ liệu
  tạo danh sách `SUB001`–`SUB035` theo thứ tự xáo trộn bằng một số khởi tạo (seed) giữ kín, cất cùng
  bảng liên kết. Mỗi người đăng ký nhận mã kế tiếp trong danh sách, nên không suy ra được mã từ thứ
  tự đăng ký hay từ danh tính. Mã buổi đo (`S001`…) và mã lượt đo (`E01`…) không chứa thông tin cá
  nhân.
- Đây là **giả danh hóa**, không phải ẩn danh: bảng liên kết vẫn tồn tại, và dạng sóng cùng thông
  tin kỹ thuật vẫn có rủi ro bị tái nhận diện.
- Có hai nơi nối danh tính với mã:
  - bảng liên kết: được mã hóa bằng [công cụ, ví dụ AES-256], lưu trên thiết bị riêng không đồng bộ
    lên dịch vụ đám mây, và chỉ người quản lý dữ liệu (và người dự phòng) mở được;
  - phiếu đồng thuận giấy, có họ tên và mã. Người tham gia cần mã để rút lui, nên mã vẫn được ghi
    trên phiếu. Phiếu được cất trong tủ có khóa, ở bìa riêng.
- Phiếu sàng lọc giấy (dữ liệu sức khỏe theo mã) được cất ở bìa khác, không cùng bìa với phiếu đồng
  thuận, để thông tin sức khỏe và họ tên không nằm chung một chỗ.
- Tuổi được lưu theo năm; không lưu ngày sinh.

## 4. Lưu trữ, bảo mật và quyền truy cập

- Dữ liệu gốc từ thiết bị không bị sửa, ghi đè hay xóa để làm sạch kết quả. Mỗi lần ghi có tệp kê
  khai kèm mã băm SHA-256 tạo ngay lúc ghi. Chỉ có hai ngoại lệ, đều có nhật ký: xóa theo yêu cầu
  rút lui (mục 6) và tiêu hủy khi hết hạn lưu (mục 7). Dữ liệu dẫn xuất có số phiên bản và truy
  ngược được về dữ liệu gốc, cấu hình và phiên bản mã nguồn đã dùng.
- Nơi lưu: [thiết bị lưu trữ của phòng thí nghiệm]. Mọi máy tính và ổ đĩa chứa dữ liệu nghiên cứu
  đều được mã hóa toàn ổ [công cụ, ví dụ BitLocker] và có mật khẩu đăng nhập riêng. Bản sao lưu:
  [nơi, tần suất], cũng được mã hóa. Dữ liệu không được đồng bộ lên dịch vụ đám mây công cộng.
- Phiếu giấy được cất trong tủ có khóa tại [phòng], phiếu đồng thuận và phiếu sàng lọc ở hai bìa
  riêng.
- Quyền truy cập: dữ liệu nghiên cứu (chỉ mang mã) do các thành viên nhóm nghiên cứu có tên trong hồ
  sơ và giảng viên hướng dẫn truy cập; bảng liên kết chỉ người quản lý dữ liệu và người dự phòng mở
  được, giảng viên hướng dẫn không được mở. Thành viên hội đồng đạo đức hoặc cơ quan có thẩm quyền
  được xem hồ sơ, kể cả phiếu có họ tên, khi giám sát nghiên cứu. Không chia sẻ dữ liệu ra ngoài khi
  chưa có chấp thuận (mục 9).
- Kho mã nguồn của nhóm chỉ chứa mã và tài liệu, **không bao giờ** chứa dữ liệu người tham gia, bảng
  liên kết, phiếu đã scan hay tệp đánh dấu tay trên dữ liệu người. Các thư mục dữ liệu bị loại khỏi
  kho mã nguồn bằng cấu hình, và mỗi lần cập nhật kho đều được kiểm tra trước khi đưa lên.

## 5. Người đăng ký nhưng không tham gia hoặc không đủ điều kiện

- Thông tin liên lạc do người quan tâm tự cung cấp khi đăng ký chỉ dùng để gửi bản thông tin và hẹn
  buổi đầu. Nếu người đó không tham gia, thông tin này được xóa trong vòng 30 ngày.
- Người đã ký đồng thuận nhưng không đủ điều kiện ở phiếu sàng lọc: nhóm không ghi tín hiệu của
  người đó; phiếu sàng lọc (chỉ mang mã) được giữ để báo cáo số liệu tổng hợp và được tiêu hủy cùng
  dữ liệu nghiên cứu (mục 7); thông tin liên lạc được xóa trong vòng 30 ngày; phiếu đồng thuận được
  giữ làm hồ sơ.

## 6. Rút lui và xóa

- Khi một người rút lui, nhóm ngừng thu dữ liệu của người đó. Người rút lui chọn xóa hay giữ dữ liệu
  đã thu. Lựa chọn này được ghi vào nhật ký rút lui, gồm mã, ngày, lựa chọn và người ghi, không kèm
  danh tính.
- Nếu người đó chọn xóa và yêu cầu đến trước mốc khóa dữ liệu, nhóm xác nhận đã nhận yêu cầu trong
  02 ngày làm việc, và trong vòng 20 ngày (Nghị định 356/2025/NĐ-CP, Điều 5):
  - xóa dữ liệu gốc, dữ liệu dẫn xuất, các bản xuất, dòng tương ứng trong bảng liên kết và thông
    tin liên lạc, kể cả trên bản sao lưu. Nếu sau này phải phục hồi từ một bản sao lưu cũ thì dùng
    nhật ký xóa để xóa lại trước khi dùng dữ liệu;
  - hủy phiếu sàng lọc giấy;
  - giữ phiếu đồng thuận làm hồ sơ về việc đồng thuận;
  - ghi lại thao tác xóa (mã, ngày, người làm).
- Mốc khóa dữ liệu là bản chụp dữ liệu (kèm mã băm SHA-256) được khóa trước lần phân tích chính đầu
  tiên, vào ngày [ngày khóa dữ liệu]. Ngày này được ghi trong bản thông tin (mục 9) ngay từ khi
  tuyển, nên người tham gia biết trước.
- Sau mốc khóa, dữ liệu đã nằm trong bộ dữ liệu phân tích đã khóa. Nhóm đề nghị giữ dữ liệu này cho
  các phân tích đã định trước, vì các phân tích (đánh giá chéo bỏ từng người) dùng chung toàn bộ bộ
  dữ liệu [căn cứ pháp lý cho việc giữ lại sau mốc khóa: chờ đơn vị chủ trì xác nhận; nếu không có
  căn cứ thì nhóm xóa theo yêu cầu và chạy lại các phân tích không có dữ liệu của người đó]. Kết quả
  đã công bố ở dạng tổng hợp không thể rút lại. Nhóm vẫn ngừng thu thêm dữ liệu, xóa thông tin liên
  lạc, và không dùng dữ liệu của người đó cho mục đích mới nào khác.
- Khi nhóm dừng sự tham gia của một người (bản thông tin mục 9), dữ liệu đã thu được xử lý như dữ
  liệu của người đã đồng ý, và người đó vẫn có quyền yêu cầu xóa trước mốc khóa.

## 7. Thời hạn lưu và tiêu hủy

- Thời hạn lưu theo quy định lưu trữ của trường/hội đồng [quy định áp dụng]. Nếu không có quy định,
  dữ liệu được giữ 03 năm rồi tiêu hủy. Thời hạn này tính từ mốc muộn hơn trong hai mốc: ngày kết
  thúc đề tài và ngày có công bố đầu tiên dùng dữ liệu này. Nếu không có công bố thì tính từ ngày
  kết thúc đề tài, nên mốc luôn là một ngày cụ thể và không bị kéo dài bởi các công bố sau. Khi áp
  dụng thời hạn 03 năm này, dữ liệu được tiêu hủy không muộn hơn 05 năm kể từ ngày kết thúc đề tài.
- Ngoại lệ: hồ sơ sự cố dữ liệu (mục 8) được giữ ít nhất 05 năm kể từ ngày khắc phục xong sự cố
  (Nghị định 356/2025/NĐ-CP, Điều 29), kể cả khi dữ liệu nghiên cứu đã tiêu hủy; hồ sơ này chỉ mang
  mã và không chứa tín hiệu.
- Cách tiêu hủy: xóa an toàn theo loại thiết bị lưu trữ, hủy phiếu giấy bằng máy hủy và lập biên bản
  tiêu hủy.

## 8. Sự cố dữ liệu

Sự cố gồm: mất hoặc bị lấy cắp máy tính hay ổ đĩa có dữ liệu; người không có quyền truy cập được dữ
liệu; gửi nhầm dữ liệu; đưa nhầm dữ liệu lên kho mã nguồn hay nơi công khai. Khi phát hiện:

1. Dừng ngay việc đồng bộ và cập nhật kho mã nguồn; báo cho nhóm và giảng viên hướng dẫn.
2. Thu hồi quyền truy cập và đổi mật khẩu liên quan; nếu dữ liệu đã lên kho mã nguồn thì gỡ khỏi
   toàn bộ lịch sử của kho, không chỉ xóa tệp.
3. Đánh giá phạm vi: dữ liệu nào, của bao nhiêu người, có nguy cơ lộ danh tính hay không.
4. Báo người tham gia bị ảnh hưởng trong vòng 72 giờ kể từ khi phát hiện, nếu sự cố liên quan tới
   dữ liệu sức khỏe hoặc sinh trắc học của họ (Nghị định 356/2025/NĐ-CP, Điều 29); nếu không báo riêng
   được thì thông báo theo cách mà quy định cho phép.
5. Đơn vị chủ trì báo cơ quan chuyên trách bảo vệ dữ liệu cá nhân theo Điều 28 và 29 của Nghị định
   356/2025/NĐ-CP; nhóm báo hội đồng đạo đức theo thời hạn của hội đồng [thời hạn, kênh báo].
6. Lập và lưu hồ sơ sự cố theo mục 7.

## 9. Chia sẻ, công bố và sử dụng sau

- Chỉ công bố số liệu tổng hợp, không nhận ra được từng người.
- Dữ liệu không được chia sẻ ra ngoài nhóm nghiên cứu. Việc chia sẻ dữ liệu đã giả danh hóa ra ngoài
  (ví dụ lên kho dữ liệu khoa học) không thuộc hồ sơ này; nếu muốn làm thì phải có đồng thuận riêng
  của người tham gia và chấp thuận của hội đồng.
- Nếu mục 10 của phiếu đồng thuận được giữ [chờ thầy/hội đồng], dữ liệu của người đã đồng ý ở mục
  đó có thể được chính nhóm dùng trong nghiên cứu tiếp theo về ước lượng huyết áp từ tín hiệu PPG và
  điện tim, với cùng cách lưu trữ, cùng người được truy cập và cùng thời hạn lưu như kế hoạch này.
  Mỗi nghiên cứu tiếp theo dùng dữ liệu này phải có chấp thuận của hội đồng đạo đức. Người tham gia
  có thể rút lại sự đồng ý ở mục 10 bất cứ lúc nào; khi đó dữ liệu của họ không được dùng cho nghiên
  cứu mới nào nữa.
