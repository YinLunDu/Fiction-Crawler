"""
- 爬輕小說文庫 繁體中文

這支程式用於爬取輕小說文庫 (wenku8.net) 的指定小說，
並將內容（包含文字和圖片）轉換為繁體中文，最後生成 PDF 檔案。

主要功能：
1. 爬取小說目錄頁，解析出所有書卷和章節。
2. 提示用戶選擇要下載的書卷。
3. 逐章節下載內容，包括文字和圖片。
4. 使用 opencc 將簡體中文轉換為繁體中文（台灣用語）。
5. 使用 reportlab 將處理後的內容生成 PDF 檔案，每卷一個 PDF。

依賴套件：
- beautifulsoup4
- requests
- opencc-python-reimplemented
- reportlab
- lxml

使用前請注意：
- 必須在程式碼同目錄下建立一個 'font' 資料夾。
- 'font' 資料夾中需要有 'NotoSansTC-Regular.ttf' 和 'NotoSansTC-Bold.ttf' 字型檔案。
- 程式會自動建立一個 'wenku' 資料夾，並在其中存放爬取的資料、圖片和最終的 PDF。
"""

from bs4 import BeautifulSoup
import requests
import time
import os
from opencc import OpenCC
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Spacer
from curl_cffi import requests
from charset_normalizer import from_bytes
import chardet
# --- 網址設定 ---
URL_PREFIX = 'https://www.wenku8.net/novel/3/3057/'  # 輕小說文庫預設網址
COOKIES_CATALOG = {
    'cf_clearance': 'AmevgZ63B6GWUY0mvSOZKGIvNzWjoaPHMMq67EreZxg-1762308485-1.2.1.1-DzK0h18xU6DrKhneoL.Qvd5BgNqPwxam68U9ihWH4sdDo4j4x9RZp7lhcIP3ZckiKuGHOydJTMdFVsk4Ul74hzf8t9DtqkbkqoyVCfXcUhooWCdc8UOtH4A1CEY.kTOiLFJ71cqgI0H7kxtuUhDaSVfJq97z_uZskVWxrgenLgX6qq0NnWg6f20QcPL8sEaPKzggCd_VFby9u51qOne_pW1Vu2gY1FBuB1xwcwZIlgQ',
}
HEADERS_CATALOG = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'accept-language': 'zh-TW,zh;q=0.9',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
}
COOKIES_PAGE = {
    'Hm_lvt_b74ae3cad0d17bb613b120c400dcef59': '1762310863',
    'Hm_lpvt_b74ae3cad0d17bb613b120c400dcef59': '1762310863',
    'HMACCOUNT': '50D1DFF5E9DACAF8',
    'Hm_lvt_d72896ddbf8d27c750e3b365ea2fc902': '1762310863',
    'Hm_lpvt_d72896ddbf8d27c750e3b365ea2fc902': '1762310863',
    'cf_clearance': 'B30NU39Tr4eIVFnEen.h_Kfff41NNAwxnOUo_QHR1U8-1762310862-1.2.1.1-CwLnciiYNgoo7dFSDkuqCpnGDuIjo47_K4ydmnohNKanQaVCKQgpPJ0m6nBc.RlwqazKQBMrGficGavAILUvc_ls8pwoa9a7OBDNyiiSKswqIPWAFu5HRpG68Pnm7CFllnhqz8OpBDMjXjgNSWM_yPRpK0v4wJCDDU3rpxC5wK3Sj0OV4ZtaDnBOzrRt.sx7X9EvJUylVd80UthATYWUp48dyH3gHS_53t69VF5pwdk',
    '_clck': '12b30wd%5E2%5Eg0r%5E0%5E2135',
    '_clsk': '1tkid78%5E1762310864450%5E1%5E1%5Ea.clarity.ms%2Fcollect',
}
HEADERS_PAGE = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    # 'cookie': 'Hm_lvt_b74ae3cad0d17bb613b120c400dcef59=1762310863; Hm_lpvt_b74ae3cad0d17bb613b120c400dcef59=1762310863; HMACCOUNT=50D1DFF5E9DACAF8; Hm_lvt_d72896ddbf8d27c750e3b365ea2fc902=1762310863; Hm_lpvt_d72896ddbf8d27c750e3b365ea2fc902=1762310863; cf_clearance=B30NU39Tr4eIVFnEen.h_Kfff41NNAwxnOUo_QHR1U8-1762310862-1.2.1.1-CwLnciiYNgoo7dFSDkuqCpnGDuIjo47_K4ydmnohNKanQaVCKQgpPJ0m6nBc.RlwqazKQBMrGficGavAILUvc_ls8pwoa9a7OBDNyiiSKswqIPWAFu5HRpG68Pnm7CFllnhqz8OpBDMjXjgNSWM_yPRpK0v4wJCDDU3rpxC5wK3Sj0OV4ZtaDnBOzrRt.sx7X9EvJUylVd80UthATYWUp48dyH3gHS_53t69VF5pwdk; _clck=12b30wd%5E2%5Eg0r%5E0%5E2135; _clsk=1tkid78%5E1762310864450%5E1%5E1%5Ea.clarity.ms%2Fcollect',
}

# --- 常量設定 ---
FONT_PATH = "font/NotoSansTC-"  # 字型檔案路徑前綴
DATA_DIR = 'wenku'  # 主要資料夾名稱
OUTPUT_DIRS = ['novel_text', 'pic', 'pdf_file']  # 'wenku' 底下的子資料夾
PAGE_WIDTH, PAGE_HEIGHT = A4  # PDF 頁面大小
translate_tool = OpenCC('s2twp')  # 簡中轉繁中 (s2twp: 簡轉繁，包含用語轉換)

# --- 字型與 PDF 樣式設定 ---
pdfmetrics.registerFont(TTFont('notoR', f"{FONT_PATH}Regular.ttf"))
pdfmetrics.registerFont(TTFont('notoB', f"{FONT_PATH}Bold.ttf"))
styles = getSampleStyleSheet()
style_normal = ParagraphStyle('styleNormal', fontName='notoR', fontSize=10, leading=20)  # 一般內文樣式
style_title = ParagraphStyle('styleTitle', fontName='notoB', fontSize=13, alignment=1)  # 章節標題樣式

def fetch_website_content(url, _headers, _cookies):
    """
    輔助函數：獲取指定 URL 的網頁內容
    """
    response = requests.get(url, headers=_headers, cookies=_cookies, impersonate='chrome110')
    encoding = chardet.detect(response.content)['encoding']
    best = from_bytes(response.content).best()
    response.encoding = best.encoding if best.encoding else 'utf-8'
    if response.status_code != 200:
        print(f"Error: 無法訪問 {url}，狀態碼: {response.status_code}")
        return None
    return response

def save_image(image_index, pic_url):
    """
    輔助函數：下載並儲存圖片
    
    :param image_index: 圖片的索引編號 (用於命名)
    :param pic_url: 圖片的 URL
    :return: 儲存的圖片路徑
    """
    response = requests.get(pic_url, headers=HEADERS_PAGE, cookies=COOKIES_PAGE)
    image_path = f'wenku/pic/pic_{image_index}.jpg'
    with open(image_path, 'wb') as f:
        f.write(response.content)
    time.sleep(0.5)  # 禮貌性延遲
    return image_path

def append_image_to_story(image_path, story):
    """
    輔助函數：將圖片添加到 PDF 故事流 (story list)
    並處理圖片過大的問題。
    
    :param image_path: 圖片的本地路徑
    :param story: ReportLab 的 story 列表
    """
    try:
        img = Image(image_path)
        img_width, img_height = img.wrap(0, 0)
        
        # 檢查圖片是否超出頁面大小，如果超出則按比例縮放
        if img_width > PAGE_WIDTH or img_height > PAGE_HEIGHT:
            # 計算縮放比例，+1 確保圖片邊緣有留白
            scale_factor = max(img_width / PAGE_WIDTH, img_height / PAGE_HEIGHT) + 1
            img.drawWidth = img_width / scale_factor
            img.drawHeight = img_height / scale_factor
            
        story.append(img)
        story.append(PageBreak())  # 插入圖片後換頁
    except Exception as e:
        print(f"Error: {e} - 無法處理圖片: {image_path}")

def find_names_and_urls():
    """
    爬取目錄頁，獲取所有書卷名、章節名、章節網址
    並將這些資訊存儲到 wenku 資料夾中的 .txt 檔案。
    """
    print("正在爬取目錄頁...")
    category_page = fetch_website_content(URL_PREFIX, HEADERS_CATALOG, COOKIES_CATALOG)
    soup = BeautifulSoup(category_page.content, 'lxml')
    catalog = soup.find('table', class_='css')
    table_data = catalog.find_all('td')

    title_count = 0  # 累計章節 (ccss) 數量
    title_gap = []   # 儲存每個書卷 (vcss) 開始前的章節總數
    
    # 這個迴圈用來計算 'title_gap'，以便後續知道每一卷包含哪些章節
    for info in table_data:
        if info.get('class'):
            if 'vcss' in info['class']:
                # 遇到書卷 (vcss)，紀錄當前的章節總數
                title_gap.append(title_count)
            elif 'ccss' in info['class'] and info.text.strip().replace(u'\xa0', ''):
                # 遇到章節 (ccss)，章節計數+1
                title_count += 1
    title_gap.append(title_count)  # 補上最後一個書卷的結尾

    # 儲存 'title_gap' 資訊
    save_important_stuff('title_gap.txt', '\n'.join(map(str, title_gap)))

    # 提取所有章節標題
    titles = [title.text.replace(' ', '') for title in catalog.find_all('td', class_='ccss') if title.a]
    save_important_stuff('title.txt', '\n'.join(titles))

    # 提取所有章節網址
    websites = [title.a['href'] for title in catalog.find_all('td', class_='ccss') if title.a]
    save_important_stuff('website.txt', '\n'.join(websites))

    # 提取所有書卷名稱
    book_names = [book.text for book in catalog.find_all('td', class_='vcss')]
    save_important_stuff('book_name.txt', '\n'.join(book_names))
    print("目錄頁爬取完畢，資料已儲存。")

def save_important_stuff(filename, content):
    """
    輔助函數：將爬取到的元資料 (metadata) 內容寫入文件
    """
    with open(os.path.join(DATA_DIR, filename), 'w', encoding='utf-8') as f:
        f.write(content)

def prompt_user_to_choose():
    """
    顯示書目列表並提示用戶選擇要下載的卷。
    
    :return: 一個包含用戶選擇的書卷索引 (int) 的列表
    """
    book_names = load_from_file('book_name.txt')
    chosen_indices = []
    
    print("\n--- 書目列表 ---")
    for i, name in enumerate(book_names):
        print(f"[{i}] {name.strip()}")
    print(f"[{len(book_names)}] 我全都要")
    print("------------------")
    
    user_selection = list(map(int, input("請輸入想要的書目 (數字用空格隔開): ").split()))
    
    if len(book_names) in user_selection:
        # 如果用戶選擇了 "我全都要"
        chosen_indices = list(range(len(book_names)))
    else:
        # 否則，只添加用戶選擇的索引
        chosen_indices = user_selection
        
    print(f"已選擇: {[book_names[i].strip() for i in chosen_indices]}")
    return chosen_indices

def load_from_file(filename):
    """
    輔助函數：從 'wenku' 資料夾中的文件讀取所有行
    """
    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
        return f.readlines()

def download_content(chosen_books):
    """
    根據用戶選擇的書卷索引 (chosen_books)，下載對應的小說內容。
    
    :param chosen_books: 由 prompt_user_to_choose() 回傳的索引列表
    """
    titles = load_from_file('title.txt')
    book_names = load_from_file('book_name.txt')
    title_gaps = list(map(int, load_from_file('title_gap.txt')))
    websites = load_from_file('website.txt')
    
    story = []  # 用於 ReportLab 生成 PDF 的內容列表
    
    # 遍歷用戶選擇的每一本書 (書卷)
    for book_id in chosen_books:
        book_name = book_names[book_id].strip()
        print(f"\n--- 正在下載: {book_name} ---")
        
        # 根據 title_gaps 確定這本書的章節範圍
        start_title_index = title_gaps[book_id]
        end_title_index = title_gaps[book_id + 1]
        
        for title_id in range(start_title_index, end_title_index):
            url = URL_PREFIX + websites[title_id].strip()
            page_content = fetch_website_content(url, HEADERS_PAGE, COOKIES_PAGE)
            soup = BeautifulSoup(page_content.content, 'lxml')
            content = soup.find('div', {'id': 'content'})
            
            if content:
                cur_title = f'<< {translate_tool.convert(titles[title_id].strip())} >>'
                print(f"  正在處理章節: {cur_title}")
                
                # 添加標題和間距到 story
                story.append(Spacer(1, 0.2 * inch))
                story.append(Paragraph(f'{translate_tool.convert(cur_title)}\n', style_title))
                story.append(Spacer(1, 0.3 * inch))
                
                # 處理該章節的內文 (文字和圖片)
                process_content(content, story)
            
            time.sleep(4)  # 尊重伺服器，延遲 4 秒
        
        # 該書卷的所有章節都處理完畢，生成 PDF
        generate_pdf(story, book_name, book_id)
        story.clear()  # 清空 story 列表，準備下一本書
        print(f"--- {book_name} 下載並生成 PDF 完畢 ---")

def process_content(content, story):
    """
    處理單一章節的內容，將文字和圖片添加到 story 列表。
    
    :param content: 包含章節內容的 BeautifulSoup 元素
    :param story: ReportLab 的 story 列表
    """
    pics = content.find_all('div', class_='divimage')
    image_index = 0  # 圖片索引
    
    if pics:
        # 如果該章節有插圖
        for pic in pics:
            if pic.a and pic.a.get("href"):
                img_path = save_image(image_index, pic.a["href"])
                image_index += 1
                append_image_to_story(img_path, story)
            else:
                print("  警告：找到 divimage 但無法解析圖片 href")
    else:
        # 如果該章節沒有插圖 (純文字)
        for element in content:
            # 排除網站的廣告/簽名行
            if 'http://www.wenku8.com' not in element.text:
                # 清理多餘的空白和特殊字元
                line = element.text.strip().replace(' ', '').replace(u'\xa0', '')
                if line:
                    # 將簡轉繁後的文字段落添加到 story
                    story.append(Paragraph(translate_tool.convert(line), style_normal))

def generate_pdf(story, book_name, book_id):
    """
    使用 ReportLab 將 story 列表的內容生成 PDF 檔案。
    
    :param story: 包含 Paragraph 和 Image 物件的列表
    :param book_name: 書卷名稱 (用於 PDF 命名)
    :param book_id: 書卷 ID (用於 PDF 命名)
    """
    # 轉換書名為繁體
    safe_book_name = translate_tool.convert(book_name)
    # 避免檔案名稱中包含非法字元 (簡易處理)
    safe_book_name = safe_book_name.replace('/', '_').replace('\\', '_').replace(':', '_')
    filename = f'wenku/pdf_file/{book_id}_{safe_book_name}.pdf'
    
    try:
        pdf_template = SimpleDocTemplate(filename, pagesize=A4)
        pdf_template.build(story)
    except Exception as e:
        print(f"生成 PDF {filename} 時發生錯誤: {e}")

def delete_folder(folder_path):
    """
    輔助函數：刪除指定資料夾及其內容
    """
    if os.path.exists(folder_path):
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(folder_path)

def main():
    """
    主執行函數
    """
    delete_folder(DATA_DIR)  # 刪除舊的資料夾以確保乾淨的環境
    
    print("建立資料夾結構...")
    # 建立必要的資料夾
    os.makedirs(DATA_DIR, exist_ok=True)
    for directory in OUTPUT_DIRS:
        os.makedirs(os.path.join(DATA_DIR, directory), exist_ok=True)

    # 1. 爬取目錄頁並儲存資訊
    find_names_and_urls()
    
    # 2. 提示用戶選擇書目
    chosen_books = prompt_user_to_choose()
    
    # 3. 根據用戶選擇下載內容並生成 PDF
    download_content(chosen_books)
    
    print("\n全部任務完成！")

if __name__ == "__main__":
    main()