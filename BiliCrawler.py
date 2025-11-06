"""
- 爬逼哩輕小說 繁體中文

這支程式用於爬取逼哩輕小說的指定小說，
並將內容（包含文字和圖片）轉換為繁體中文，最後生成 PDF 檔案。

主要功能：
1. 爬取小說目錄頁，解析出所有書卷和章節。
2. 提示用戶選擇要下載的書卷。
3. 逐章節下載內容，包括文字和圖片。
4. 使用 opencc 將簡體中文轉換為繁體中文（台灣用語）。
5. 使用 reportlab 將處理後的內容生成 PDF 檔案，每卷一個 PDF。

使用前請注意：
- 必須在程式碼同目錄下建立一個 'font' 資料夾。
- 程式會自動建立一個 'bili' 資料夾，並在其中存放爬取的資料、圖片和最終的 PDF。
"""

from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
import requests
import time
import os
from opencc import OpenCC
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import Spacer
from curl_cffi import requests
from charset_normalizer import from_bytes
import chardet

# --- 網址設定 ---
URL_PREFIX = 'https://tw.linovelib.com'
URL_CATALOG = 'https://tw.linovelib.com/novel/2025/catalog'  # 目錄頁網址
COOKIES_CATALOG = {
    'night': '0',
    '_ga': 'GA1.1.1406039415.1762417741',
    'cf_clearance': '5kioY8b7m_cMxbNMEhK9kxVKbWfRpfCH4gl_A0gk0oA-1762417740-1.2.1.1-zVJdtxoR5tDGemvEiu.bdJblqmEdJiTOZ1zeiUymHiet5rwhFxqRg6FODLhsRw_vKnibNHgZD7YdU_EVZrXAuRqgv4CLWBj5Fpz5eMSs7oBzjRUGz.2BUsPuKYiqoQa8sQZLAcvcC5S03J8cqdb6b2qG3Rb0FAUkPbesgxZSeV7kDbuOFWIDNenX8K8CZIVnaOqshietQ14pCF_dcjRp5S3FKjdaOxr7rAB9P2DejUw',
    '__gads': 'ID=d81052c5bd615a77:T=1762417740:RT=1762417740:S=ALNI_MbbBA0aELHcEMxg_ZylfVI38TeXVA',
    '__gpi': 'UID=000011af278463ca:T=1762417740:RT=1762417740:S=ALNI_MbBpHj_JV-Op203q3Cv_vMTh_nYrg',
    '__eoi': 'ID=1eb1128b1c79c0f8:T=1762417740:RT=1762417740:S=AA-AfjYWPDFcrXycAatr7eWeamYf',
    'Hm_lvt_1251eb70bc6856bd02196c68e198ee56': '1762417742',
    'HMACCOUNT': '5C95FD63AF543C63',
    '_ga_NG72YQN6TX': 'GS2.1.s1762417741$o1$g1$t1762417986$j60$l0$h0',
    'Hm_lpvt_1251eb70bc6856bd02196c68e198ee56': '1762417987',
    'FCCDCF': '%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%220d82dea0-fd26-48fa-9d8c-9c02957beed5%5C%22%2C%5B1762417740%2C966000000%5D%5D%22%5D%5D%5D',
    'FCNEC': '%5B%5B%22AKsRol98oETVWdPV7wzf4oy3yapnzLw7zD_aZHSGJvq0G362YYgUEIXSgLfldvXWS0T_qmnohwrPIBKgjqkQlH5bUbksxpdQVKs699-LyASoJWpIaY3SgppAtuSnMhPO7gO1xWXVq_dxLs8WDt-riz11Gde__OIaWQ%3D%3D%22%5D%5D',
}
HEADERS_CATALOG = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-TW,zh;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'referer': 'https://www.google.com/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    # 'cookie': 'night=0; _ga=GA1.1.1406039415.1762417741; cf_clearance=5kioY8b7m_cMxbNMEhK9kxVKbWfRpfCH4gl_A0gk0oA-1762417740-1.2.1.1-zVJdtxoR5tDGemvEiu.bdJblqmEdJiTOZ1zeiUymHiet5rwhFxqRg6FODLhsRw_vKnibNHgZD7YdU_EVZrXAuRqgv4CLWBj5Fpz5eMSs7oBzjRUGz.2BUsPuKYiqoQa8sQZLAcvcC5S03J8cqdb6b2qG3Rb0FAUkPbesgxZSeV7kDbuOFWIDNenX8K8CZIVnaOqshietQ14pCF_dcjRp5S3FKjdaOxr7rAB9P2DejUw; __gads=ID=d81052c5bd615a77:T=1762417740:RT=1762417740:S=ALNI_MbbBA0aELHcEMxg_ZylfVI38TeXVA; __gpi=UID=000011af278463ca:T=1762417740:RT=1762417740:S=ALNI_MbBpHj_JV-Op203q3Cv_vMTh_nYrg; __eoi=ID=1eb1128b1c79c0f8:T=1762417740:RT=1762417740:S=AA-AfjYWPDFcrXycAatr7eWeamYf; Hm_lvt_1251eb70bc6856bd02196c68e198ee56=1762417742; HMACCOUNT=5C95FD63AF543C63; _ga_NG72YQN6TX=GS2.1.s1762417741$o1$g1$t1762417986$j60$l0$h0; Hm_lpvt_1251eb70bc6856bd02196c68e198ee56=1762417987; FCCDCF=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%220d82dea0-fd26-48fa-9d8c-9c02957beed5%5C%22%2C%5B1762417740%2C966000000%5D%5D%22%5D%5D%5D; FCNEC=%5B%5B%22AKsRol98oETVWdPV7wzf4oy3yapnzLw7zD_aZHSGJvq0G362YYgUEIXSgLfldvXWS0T_qmnohwrPIBKgjqkQlH5bUbksxpdQVKs699-LyASoJWpIaY3SgppAtuSnMhPO7gO1xWXVq_dxLs8WDt-riz11Gde__OIaWQ%3D%3D%22%5D%5D',
}
COOKIES_PAGE = {
    'night':
    '0',
    '_ga':
    'GA1.1.858433580.1740736270',
    'Hm_lvt_1251eb70bc6856bd02196c68e198ee56':
    '1740736292',
    'HMACCOUNT':
    '8BA7214072928503',
    'cf_clearance':
    'hSIMyDbQVA5kxCW0I9bg5gi.fGVX1HgEa7B5SuYPtLQ-1740737284-1.2.1.1-DXxrnXKGpOknt3YCB0xcsKY1CywTxwzap_IxHK8TxiSSMiDUO0VWTXZtHsdr5ZOAFoKGPDAx5FT.kDdnxMq5EimgHIfVxrB1HXxfS_l1DHgM3.nGRnAGbSC1E6Hi6Rh.xTR67tSu_QET62ogqB.QZmzfVPfMiHJa1_Cz4yUpQ.E_cTl7Rrs.86MPXdE1bSXksSho8egWpSI5nUQtrXUUtFX.053CYaMxj47H4F54KsIJtHqnJyNvUlqdL65uiD.f5HGuLb9RWSWZU2NcFLzxxXRghrhjdTQNZUxvlrrFEas',
    '__gads':
    'ID=28b11837f9361c7c:T=1740736353:RT=1740737284:S=ALNI_MbeLb7vF0IR-QpiPBywKP3QgyZNjA',
    '__gpi':
    'UID=0000104e0081caf1:T=1740736353:RT=1740737284:S=ALNI_Mbbj-l5DyId6x2eRnmgDnd32aa6dA',
    '__eoi':
    'ID=96dde09a29d7d84c:T=1740736353:RT=1740737284:S=AA-AfjYSdS4zoJuD8xfQe4Bwy3B_',
    'jieqiRecentRead':
    '3095.154933.0.1.1740737288.0',
    '_ga_NG72YQN6TX':
    'GS1.1.1740736270.1.1.1740737289.0.0.0',
    'Hm_lpvt_1251eb70bc6856bd02196c68e198ee56':
    '1740737290',
    'FCNEC':
    '%5B%5B%22AKsRol8K90u22_760XILll97A0Z2PjjiAKwe_dKYM85RyT3T7KyI7_rrety0UH6lZasVeQNTWHT99Yd8oq6e-Yj8QxSgFIDtQsadgRKNooT6OMnfMpwScUiabH4ZerH8z2fsDJ-SNqfwYLFp5xXJfk2ZVlsYhrBZqA%3D%3D%22%5D%5D',
}
HEADERS_PAGE = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-TW,zh;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}
HEADERS_IMAGE = {
    'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'accept-language': 'zh-TW,zh;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'i',
    'referer': 'https://tw.linovelib.com/',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'image',
    'sec-fetch-mode': 'no-cors',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-storage-access': 'none',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
}
# --- 常量設定 ---
FONT_PATH = "font/NotoSerifTC-"  # 字型檔案路徑前綴
DATA_DIR = 'bili'  # 主要資料夾名稱
SAVE_DIR = 'bili/pic' # 圖片儲存資料夾
OUTPUT_DIRS = ['novel_text', 'pic', 'pdf_file']  # 'bili' 底下的子資料夾
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
    response = requests.get(pic_url, headers=HEADERS_IMAGE, timeout=10)
    if response.status_code != 200:
        print(f"Error: 無法下載圖片 {pic_url}，狀態碼: {response.status_code}")
        return None
    image_path = os.path.join(SAVE_DIR, f'pic_{image_index}.jpg')
    with open(image_path, 'wb') as f:
        f.write(response.content)
    time.sleep(1)  # 禮貌性延遲
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
    並將這些資訊存儲到 bili 資料夾中的 .txt 檔案。
    """
    print("正在爬取目錄頁...")
    category_page = fetch_website_content(URL_CATALOG, HEADERS_CATALOG, COOKIES_CATALOG)
    soup = BeautifulSoup(category_page.content, 'lxml')
    catalog = soup.find('div', class_='chapter-ol-catalog')
    table_data = catalog.find_all('ul', class_='volume-chapters')
    
    title_count = 0  # 累計章節 (ccss) 數量
    title_gap = []   # 儲存每個書卷 (vcss) 開始前的章節總數
    
    # 這個迴圈用來計算 'title_gap'，以便後續知道每一卷包含哪些章節
    for ul in table_data:
        for li in ul.find_all('li'):
            if li.get('class'):
                if 'chapter-bar' in li['class']:
                    # 遇到書卷 (vcss)，紀錄當前的章節總數
                    title_gap.append(title_count)
                elif 'jsChapter' in li['class'] and li.text.strip().replace(u'\xa0', ''):
                    # 遇到章節 (ccss)，章節計數 + 1
                    title_count += 1
    title_gap.append(title_count)  # 補上最後一個書卷的結尾

    # 儲存 'title_gap' 資訊
    save_important_stuff('title_gap.txt', '\n'.join(map(str, title_gap)))

    # 提取所有章節標題
    titles = [li.text.replace(' ', '') for ul in table_data for li in ul.find_all('li', class_='jsChapter') if li.a]
    save_important_stuff('title.txt', '\n'.join(titles))

    # 提取所有章節網址
    websites = [li.a['href'] for ul in table_data for li in ul.find_all('li', class_='jsChapter') if li.a]
    save_important_stuff('website.txt', '\n'.join(websites))

    # 提取所有書卷名稱
    book_names = [li.h3.text for ul in table_data for li in ul.find_all('li', class_='chapter-bar') if li.h3]
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
    輔助函數：從 'bili' 資料夾中的文件讀取所有行
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
            content = soup.find('div', {'id': 'acontent'})
            
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

image_index = 0  # 全局圖片索引，用於命名圖片檔案

def process_content(content, story):
    """
    處理單一章節的內容，將文字和圖片【依序】添加到 story 列表。
    
    :param content: 包含章節內容的 BeautifulSoup 元素
    :param story: ReportLab 的 story 列表
    """
    
    # 遍歷 content 的所有第一層子節點 (包括標籤和純文字字串)
    # 這樣才能維持圖文的原始順序
    global image_index
    for element in content.contents:
        # --- 情況 1：如果節點是「標籤」 (Tag) ---
        if isinstance(element, Tag):
            # 檢查這個標籤是否為我們定義的「圖片容器」
            if element.name == 'img':
                # 是圖片，執行圖片處理邏輯
                if element.get("src") and '/images/sloading.svg' not in element["src"]:
                    img_path = save_image(image_index, element["src"])
                    image_index += 1
                    append_image_to_story(img_path, story)
                elif element.get("data-src") and '/images/sloading.svg' not in element["data-src"]:
                    img_path = save_image(image_index, element["data-src"])
                    image_index += 1
                    append_image_to_story(img_path, story)
                else:
                    print(" 警告：找到 divimage 但無法解析圖片 src")
            
            # 如果是其他標籤 (例如 <p>, <div> 等)，包含我們想要的文字
            else:
                # 提取標籤內的所有文字
                text = element.get_text(strip=True)
                # 清理多餘的空白和特殊字元
                if text:
                    line = text.replace(' ', '').replace(u'\xa0', '')
                    if line:
                        # 將簡轉繁後的文字段落添加到 story
                        story.append(Paragraph(translate_tool.convert(line), style_normal))

        # --- 情況 2：如果節點是「純文字字串」 (NavigableString) ---
        # (這種情況可能發生於文字沒有被 <p> 標籤包住)
        elif isinstance(element, NavigableString):
            text = element.string.strip()
            # 清理多餘的空白和特殊字元
            if text:
                line = text.replace(' ', '').replace(u'\xa0', '')
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
    filename = f'{DATA_DIR}/pdf_file/{book_id}_{safe_book_name}.pdf'
    
    try:
        pdf_template = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
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