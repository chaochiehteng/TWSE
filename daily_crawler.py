import os, cv2, urllib3
import shioaji as sj
from matplotlib import lines
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from datetime import datetime
import requests, shutil, time, csv, re
from bs4 import BeautifulSoup
from keras.models import load_model
from keras.utils  import np_utils
from keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard
import numpy as np
import pandas as pd
from datetime import timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from tool import preprocessing, one_hot_decoding, deal_with_dealer, deal_with_number, deal_with_float, deal_with_str

print('model loading...')
model = load_model("twse_cap_model.hdf5")
print('loading completed')

allowedChars = 'ACDEFGHJKLNPQRTUVXYZ2346789'
CAPTCHA_IMG = "captcha.jpg"
PROCESSED_IMG = "preprocessing.jpg"

#登入永豐api
api = sj.Shioaji()
YOUR_PERSON_ID = ''
YOUR_PASSWORD = ''
accounts = api.login(YOUR_PERSON_ID, YOUR_PASSWORD)
api.activate_ca(
    ca_path="",
    ca_passwd="",
    person_id="",
)
#抓取所有上市上櫃股票清單(listed, OTC)
listed_stock_url = 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=1&issuetype=1&industry_code=&Page=1&chklike=Y'
time.sleep(1)
OTC_stock_url = 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=2&issuetype=4&industry_code=&Page=1&chklike=Y'
def stock_list_crawler(type, url):
    pages = requests.get(url)
    data = pd.read_html(pages.text)
    data = data[0]
    data = data.drop(columns = [1, 5, 8], axis = 1, inplace = False)
    data.columns = ['編號', '有價證券代號', '有價證券名稱', '市場別', '產業別', '上市上櫃日', '備註']
    data = data.drop(0, axis = 0, inplace = False)
    data = data.set_index('編號')

    try:
        path = './data/' + today
        if not os.path.isdir(path):
            os.mkdir(path)
        if type == 'listed':
            filename = '上市股票清單'
        elif type == 'OTC':
            filename = '上櫃股票清單'
        else:
            print('type error')
        data.to_csv('./data/' + today + '/' + today + '_' + filename + '.csv')
        print(today, filename, '儲存成功')
    except:
        print(today, filename, 'save error')
    return data

#找出最後交易日 輸入到today
def find_twse_day():
    url = 'https://bsr.twse.com.tw/bshtm/bsWelcome.aspx'
    pages = requests.get(url, verify = False)
    soup = BeautifulSoup(pages.text, 'html.parser')
    date = soup.select_one('#Label_Date')
    date = date.text.replace('/', '-')
    return date
today = find_twse_day()

#goodinfo抓取當日漲停股票
def daily_stock_price_record():
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'}
    url = 'https://goodinfo.tw/tw/StockList.asp?MARKET_CAT=智慧選股&INDUSTRY_CAT=漲停股'
    pages = requests.get(url, headers = headers)
    pages.encoding = "utf-8"
    soup = BeautifulSoup(pages.text, 'html.parser')
    data = soup.select_one("#txtStockListData")
    num = data.find('td', {'style': 'color:#FF8040;font-weight:bold;word-break:break-all;'}).text
    num = [int(s) for s in re.findall(r'-?\d+\.?\d*', num)]
    number = num[0]
    daily_stock_price_record_df = pd.DataFrame(columns = 
                ['代碼', '名稱', '交易市場', '成交價', '漲跌價', '漲跌幅', '成交張數', '成交額(百萬)', '昨收', 'Open', 'High', 'Low', '振幅(%)', '可否當沖'])
    stock_info_list = data.find_all('nobr')
    for n in range(number):
        r = '#row' + str(n)
        stock_info = data.select_one(r).find_all('nobr')
        code = stock_info[0].text
        name = stock_info[1].text
        ex = stock_info[2].text
        price = stock_info[4].text
        limit_amount = stock_info[5].text
        limit_percent = stock_info[6].text
        unit = stock_info[7].text
        amount = stock_info[8].text
        yesterday = stock_info[9].text
        Open = stock_info[10].text
        High =  stock_info[11].text
        Low = stock_info[12].text
        wave = stock_info[13].text
        contract = api.Contracts.Stocks[code]
        daytrade = contract.day_trade.value
        daily_stock_price_record_df.loc[n] = [code, name, ex, price, limit_amount, limit_percent, unit, amount, yesterday, Open, High, Low, wave, daytrade]
                
    try:
        path = './data/' + today
        if not os.path.isdir(path):
            os.mkdir(path)
        daily_stock_price_record_df.to_csv('./data/' + today + '/' + today + '_' + '漲停個股清單' + '.csv')
        print(today, '漲停個股清單', '儲存成功')
    except:
        print(today, '漲停個股清單', 'save_error')
    return daily_stock_price_record_df

#輸入股票名稱 抓取買賣日報 存成CSV檔
def get_chip_csv(stock_name):
    #存入股票名稱
    resp = requests.get("https://bsr.twse.com.tw/bshtm/bsMenu.aspx", verify = False)
    soup = BeautifulSoup(resp.text, 'html.parser')
    img_tags = soup.select("#Panel_bshtm img")
    src = img_tags[0].get('src')
    rs = requests.session()
    resp = rs.get("https://bsr.twse.com.tw/bshtm/" + src, stream=True, verify = False)
    if resp.status_code == 200:
        with open(CAPTCHA_IMG, 'wb') as f:
            resp.raw.decode_content = True
            shutil.copyfileobj(resp.raw, f)
    
    preprocessing(CAPTCHA_IMG, PROCESSED_IMG)
    train_data = np.stack([np.array(cv2.imread(PROCESSED_IMG))/255.0])
    prediction = model.predict(train_data)
    predict_captcha = one_hot_decoding(prediction, allowedChars)

    payload = {}
    acceptable_input = ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION', 'RadioButton_Normal',
                    'TextBox_Stkno', 'CaptchaControl1', 'btnOK']
    inputs = soup.select("input")
    for elem in inputs:
        if elem.get("name") in acceptable_input:
            if elem.get("value") != None:
                payload[elem.get("name")] = elem.get("value")
            else:
                payload[elem.get("name")] = ""
                
    payload['TextBox_Stkno'] = stock_name
    payload['CaptchaControl1'] = predict_captcha
    resp1 = rs.post("https://bsr.twse.com.tw/bshtm/bsMenu.aspx", data=payload, verify = False)
    if '驗證碼錯誤!' in resp1.text:
        print('驗證碼錯誤, predict_captcha: ' + predict_captcha)
        return 0
    elif '驗證碼已逾期!' in resp1.text:
        print('驗證碼已逾期, predict_captcha: ' + predict_captcha)
        return 0
    elif '查無資料' in resp1.text:
        print('股票:', stock_name, '查無資料')
        return 1
    elif 'HyperLink_DownloadCSV' in resp1.text:
        print("驗證碼通過！", predict_captcha)
        response = rs.get('https://bsr.twse.com.tw/bshtm/bsContent.aspx?v=t', verify = False)
        print('資料處理中....')
        #亦可直接用pd.read_html(response.text)，但實測發現速度較慢
        good_soup = BeautifulSoup(response.text, 'html.parser')
        column_list = good_soup.find_all('td', {'class': 'column_value_center'})
        V = 0
        #減1因為最後一個不是數字
        #抓出總共有幾筆資料
        for count in range(len(column_list)-1):
            number = column_list[count].text
            number = number.split(' ')[-1]
            num = int(number)
            if num > V:
                V = num
        crazy_df = pd.DataFrame(columns = ['序', '證券商', '成交單價', '買進股數', '賣出股數'], index = range(V))
        list = good_soup.find_all('tr', {'class': ['column_value_price_3', 'column_value_price_2']})
        river = good_soup.find_all('tr', {'class': 'column_value_price_3'})
        
        for num in range(V):
            useful = list[num].find_all('td')
            index = deal_with_number(useful[0].text)
            dealer = deal_with_dealer(useful[1].text)
            price = deal_with_float(useful[2].text)
            buy_shares = deal_with_str(useful[3].text)
            sell_shares =deal_with_str(useful[4].text)
            ind = index-1
            crazy_df.loc[ind] = [index, dealer, price, buy_shares, sell_shares]
        crazy_df = crazy_df.set_index('序')
        c = 1
        crazy_df.loc[1, '分界'] = c
        for i in range(1, len(crazy_df)):
            n = crazy_df.iloc[i]['證券商']
            n = re.sub("[\u4e00-\u9fa5\,\。]", "", n)
            l =  crazy_df.iloc[i-1]['證券商']
            l = re.sub("[\u4e00-\u9fa5\,\。]", "", l)
            if n == l:
                crazy_df.loc[i+1, '分界'] = c
            else:
                c = c+1
                crazy_df.loc[i+1, '分界'] = c

        try:
            path = './data/' + today
            if not os.path.isdir(path):
                os.mkdir(path)
            crazy_df.to_csv('./data/' + today + '/' + stock_name + '_' + today + '.csv')
            print(today, stock_name, '儲存成功')
        except:
            print(today, stock_name, 'save error')
        time.sleep(1)
        return 1
#上市上櫃股票清單
listed = stock_list_crawler('listed', listed_stock_url)
stock_list_crawler('OTC', OTC_stock_url)
#漲停股票清單
list_df = daily_stock_price_record()

#爬取買賣日報表，並以line notify通知
token = ''
headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
mes = today + '買賣日報表' +' ' + '下載開始'
params = {"message": mes}
r = requests.post("https://notify-api.line.me/api/notify",
    headers=headers, params=params)

def crawl():
    for n in  range(len(listed)): 
        stock_name = listed.iloc[n]['有價證券代號']
        i = 0
        while i == 0:
            try:
                i = get_chip_csv(stock_name)
                print('已完成' + str(n+1) +'/' + str(len(listed)))
            except:
                mes = today + ' ' + '下載中斷' +' ' + '已完成' + str(n+1) +'/' + str(len(listed))
                print(mes)
                params = {"message": mes}
                r = requests.post("https://notify-api.line.me/api/notify",
                    headers=headers, params=params)
                return 1
    mes = today + ' ' + '下載完畢' + ' ' + '已完成' + str(len(listed)) + '/' + str(len(listed))
    params = {"message": mes}
    r = requests.post("https://notify-api.line.me/api/notify",
        headers=headers, params=params)
    return 0

de = crawl()