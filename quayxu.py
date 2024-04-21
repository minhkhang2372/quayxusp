import os
import requests
import time
from datetime import datetime
import pytz
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler

# Sử dụng token trực tiếp
TOKEN = "7010785413:AAHo3-95sFfnzL7t_3OImoA1jT0ICHVCBDE"

# Định nghĩa hàm lấy dữ liệu từ API Shopee
def get_api_data(current_time_millis):
    # Tạo URL truy vấn API với thời gian hiện tại
    api_url = f"https://api.longhousee.com/api/v1/shopeexu/all_spinner?limit=20&startTime[gte]={current_time_millis}"
    
    # Gửi yêu cầu GET đến API
    response = requests.get(api_url)
    
    # Kiểm tra xem yêu cầu có thành công không
    if response.status_code == 200:
        # Lấy dữ liệu từ phản hồi của API
        data = response.json()
        return data
    else:
        # Nếu yêu cầu không thành công, in ra mã trạng thái và thông báo lỗi
        print("Failed to fetch data from API. Status code:", response.status_code)
        return None

# Định nghĩa hàm chuyển đổi link Shopee từ username
def convert_shopee_link(username):
    # URL của API chuyển đổi link
    api_url = "https://area08.000webhostapp.com/change_link/change.php"
    
    # Dữ liệu yêu cầu (POST data)
    user_cookie = "SPC_EC=.N3U0WVo5NUtqT2cyR1Z2NCWcV89jDSfBVw+TtVSFzMQKh8vytHh6wDvC87kJnBCipw+VC9ZEslAfkmW62oauHjMOyJx/dLiyfEIlaq/XYbiMQG0fBf4/MR0/Zg3vYvASeFEjBlW79KsK96kEqyDKAUr1F+mH6K8iwJP5sHq34XjBp4EZAwo98CejjztOtDU8RH3UU5/39LkSzVjTZh2rGw=="

    data = {
        "content": f"https://shopee.vn/{username}",
        "userCookie": user_cookie
    }

    # Gửi yêu cầu POST đến API chuyển đổi link
    try:
        response = requests.post(api_url, data=data)
        response.raise_for_status()  # Kiểm tra xem phản hồi có lỗi không

        # Lấy dữ liệu từ phản hồi (dữ liệu đã chuyển đổi)
        converted_data = response.text
        
        return converted_data
    
    except requests.exceptions.RequestException as e:
        print(f"Đã xảy ra lỗi. SOS: {e}")
        return None

# Định nghĩa múi giờ UTC+7
utc_plus_7 = pytz.timezone('Asia/Ho_Chi_Minh')

# Queue để lên kế hoạch các nhiệm vụ
task_queue = asyncio.Queue()

# Hàm xử lý các nhiệm vụ từ Queue
async def process_tasks():
    while True:
        # Chờ đợi nhiệm vụ được thêm vào Queue
        task = await task_queue.get()
        
        # Thực hiện nhiệm vụ
        await task

# Định nghĩa hàm xử lý lệnh /start
async def start(update: Update, context):
    await update.message.reply_text("Hello bạn, xài bot thì dùng lệnh /spin để kích hoạt nhé!")

# Định nghĩa hàm xử lý lệnh /spin
async def spin(update: Update, context):
    current_time_millis = int(time.time() * 1000)
    api_data = get_api_data(current_time_millis)
    
    if api_data and "data" in api_data and "allSpinner" in api_data["data"]:
        all_spinner = api_data["data"]["allSpinner"]
        for spinner in all_spinner:
            # Chuyển đổi thời gian từ UTC sang UTC+7
            start_time_utc = datetime.strptime(spinner["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            start_time_utc = pytz.utc.localize(start_time_utc)
            start_time_utc7 = start_time_utc.astimezone(utc_plus_7)
            start_time_str = start_time_utc7.strftime("%H:%M:%S - %d/%m/%Y")
            
            # Chuyển đổi link Shopee từ username
            shopee_link = convert_shopee_link(spinner.get('userName', 'N/A'))
            
            # Tạo nút "Vào săn xu"
            button_text = "👉 Vào LIVE Săn Xu"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, url=shopee_link)]])
            
            message = f"Tên Shop: {spinner.get('shopName', 'N/A')}\n" \
                      f"Số xu nhận: {spinner.get('maxcoin', 'N/A')}\n" \
                      f"Lượt nhận: {spinner.get('slot', 'N/A')} lượt\n" \
                      f"Bắt đầu quay lúc: {start_time_str}\n"
            
            await update.message.reply_text(message, reply_markup=keyboard)
            await asyncio.sleep(5)
    else:
        await update.message.reply_text("No spin!")

# Hàm xử lý lệnh /stop
async def stop(update: Update, context):
    await update.message.reply_text("Bot đã dừng lại!")
    # Dừng vòng lặp chính
    context.loop.stop()

# Hàm chính
def main():
    application = Application.builder().token(TOKEN).build()

    # Thêm các trình xử lý lệnh
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spin", enqueue_task))
    application.add_handler(CommandHandler("stop", stop))

    # Bắt đầu chạy bot
    application.run_polling()

async def enqueue_task(update: Update, context):
    # Thêm nhiệm vụ vào Queue
    await task_queue.put(spin(update, context))

if __name__ == "__main__":
    # Khởi tạo và chạy vòng lặp xử lý nhiệm vụ
    asyncio.run(process_tasks())
    main()
