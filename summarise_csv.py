import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)
pd.set_option('display.width', 1000)

#找出最後交易日 輸入到today
def find_twse_day():
    url = 'https://bsr.twse.com.tw/bshtm/bsWelcome.aspx'
    pages = requests.get(url, verify = False)
    soup = BeautifulSoup(pages.text, 'html.parser')
    date = soup.select_one('#Label_Date')
    date = date.text.replace('/', '-')
    return date
today = find_twse_day()
path = './data/' + today + '/' + today + '_漲停個股清單.csv'
df = pd.read_csv(path)


def buy_summary(stock_name):
    route = './data/' + today + '/' + stock_name + '_' + today + '.csv'
    data = pd.read_csv(route)
    grouped = data.groupby('分界')
    for i in range(int(data.iloc[-1]['分界'])):
        globals()[stock_name + '_' + str(i+1)] = grouped.get_group(i+1)

    buy = pd.DataFrame(columns = ['分點名稱', '買進股數'])
    for i in range(int(data.iloc[-1]['分界'])):
        name = globals()[stock_name + '_' + str(i+1)].iloc[0]['證券商']
        share = globals()[stock_name + '_' + str(i+1)]['買進股數'].sum()
        buy.loc[i] = [name, share]
    buy = buy.sort_values('買進股數', ascending=False)
    buy['排名'] = range(1, len(buy)+1)
    buy = buy.set_index('排名')
    return buy.head()

def sell_summay(stock_name):
    route = './data/' + today + '/' + stock_name + '_' + today + '.csv'
    data = pd.read_csv(route)
    grouped = data.groupby('分界')
    for i in range(int(data.iloc[-1]['分界'])):
        globals()[stock_name + '_' + str(i+1)] = grouped.get_group(i+1)

    sell = pd.DataFrame(columns = ['分點名稱', '賣出股數'])
    for i in range(int(data.iloc[-1]['分界'])):
        name = globals()[stock_name + '_' + str(i+1)].iloc[0]['證券商']
        share = globals()[stock_name + '_' + str(i+1)]['賣出股數'].sum()
        sell.loc[i] = [name, share]
    sell = sell.sort_values('賣出股數', ascending=False)
    sell['排名'] = range(1, len(sell)+1)
    sell = sell.set_index('排名')
    return sell.head()

def buy_sell_summay(stock_name):
    route = './data/' + today + '/' + stock_name + '_' + today + '.csv'
    data = pd.read_csv(route)
    grouped = data.groupby('分界')
    for i in range(int(data.iloc[-1]['分界'])):
        globals()[stock_name + '_' + str(i+1)] = grouped.get_group(i+1)

    buy_sell = pd.DataFrame(columns = ['分點名稱', '買超股數'])
    for i in range(int(data.iloc[-1]['分界'])):
        name = globals()[stock_name + '_' + str(i+1)].iloc[0]['證券商']
        share = globals()[stock_name + '_' + str(i+1)]['買進股數'].sum()-globals()[stock_name + '_' + str(i+1)]['賣出股數'].sum()
        buy_sell.loc[i] = [name, share]
    buy_sell = buy_sell.sort_values('買超股數', ascending=False)
    buy_sell['排名'] = range(1, len(buy_sell)+1)
    buy_sell = buy_sell.set_index('排名')
    
    try:
        path = './data/' + today
        if not os.path.isdir(path):
            os.mkdir(path)
        #若要用style(df.to_excel)
        buy_sell.to_csv('./data/' + today + '/' + stock_name + '_' + today + '買超分點報表' + '.csv')
        print(today, stock_name, '買超分點報表' + '儲存成功')
    except:
        print(today, stock_name, '買超分點報表' + 'save error')
    return buy_sell

d = df.loc[df['交易市場']== '市']
for n in range(len(d)):
    stock_name = str(d.iloc[n]['代碼'])
    a = buy_sell_summay(stock_name)
    b = df[df['代碼'] == int(stock_name)]['名稱']
    print(stock_name, b.iloc[0])
    print(a.head())