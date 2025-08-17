import os
from PIL import Image
from PIL import UnidentifiedImageError

# Thay thế đường dẫn mẫu bằng đường dẫn thực tế tới thư mục dataset của bạn
root_dir = 'c:/Users/Admin/PycharmProjects/PythonProject/.venv3/facenet-pytorch-master/Image_dataset'
target_size = (512, 512)  # Kích thước mong muốn

print(f"Bắt đầu thay đổi kích thước ảnh trong thư mục: {root_dir}")

for subdir, _, files in os.walk(root_dir):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(subdir, file)
            try:
                # Mở ảnh và chuyển sang chế độ RGB
                img = Image.open(img_path).convert('RGB')

                # Kiểm tra xem ảnh có cần thay đổi kích thước không để tránh xử lý lại
                if img.size != target_size:
                    # Thay đổi kích thước ảnh, sử dụng LANCZOS làm bộ lọc resampling
                    # Đối với các phiên bản Pillow cũ hơn (< 9.1.0), bạn có thể cần dùng Image.LANCZOS
                    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)


                    img_resized.save(img_path)

            except FileNotFoundError:
                print(f"Lỗi: Không tìm thấy tệp ảnh {img_path}")
            except UnidentifiedImageError:
                 print(f"Lỗi: Không thể xác định định dạng tệp ảnh {img_path}")
            except Exception as e:
                print(f"Lỗi xử lý ảnh {img_path}: {e}")

print("Hoàn thành quá trình thay đổi kích thước ảnh.")
