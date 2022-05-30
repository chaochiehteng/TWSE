import os, cv2, requests, urllib3
import numpy as np
from bs4 import BeautifulSoup
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#圖片預處理
WIDTH = 200
HEIGHT = 60
CROP_LEFT = 10
CROP_TOP = 10
CROP_BOTTON = 10

def preprocessing(from_filename, to_filename):
    if not os.path.isfile(from_filename):
        return
    img = cv2.imread(from_filename)
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 30, 30, 7, 21)
    
    kernel = np.ones((4,4), np.uint8) 
    erosion = cv2.erode(denoised, kernel, iterations=1)
    burred = cv2.GaussianBlur(erosion, (5, 5), 0)
    
    edged = cv2.Canny(burred, 30, 150)
    dilation = cv2.dilate(edged, kernel, iterations=1) 
    
    crop_img = dilation[CROP_TOP:HEIGHT - CROP_BOTTON, CROP_LEFT:WIDTH]

    cv2.imwrite(to_filename, crop_img)
    return

#CNN
def one_hot_decoding(prediction, allowedChars):
    text = ''
    for predict in prediction:
        value = np.argmax(predict[0])
        text += allowedChars[value]
    return text


#輸入證券商text 輸出合併的結果
def deal_with_dealer(text):
    text = re.sub(r"\s+", "", text)
    return text
    
    
    text = text.split(' ')[-2:]
    text1 = text[0]
    text2 = text[-1]
    b = text2.split('\u3000')
    text2 = ''.join(b)
    final_text = text1 + text2
    return final_text

#輸入只含數字的html標籤 輸出合併的結果(int)
def deal_with_number(text):
    text = text.split(' ')[-1]
    text = int(text)
    return text
#輸入只含浮點數的html標籤 輸出合併的結果(int)
def deal_with_float(text):
    text = text.split(' ')[-1]
    text = text.replace(',', '')
    text = float(text)
    return text

#輸入只含數字及逗號的字串，處理成int之後輸出
def deal_with_str(text):
    text = text.replace(',', '')
    text = int(text)
    return text

def find_twse_day():
    url = 'https://bsr.twse.com.tw/bshtm/bsWelcome.aspx'
    pages = requests.get(url, verify = False)
    soup = BeautifulSoup(pages.text, 'html.parser')
    date = soup.select_one('#Label_Date')
    date = date.text.replace('/', '-')
    return date
    