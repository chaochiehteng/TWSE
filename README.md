# TWSE證交所買賣日報每日爬蟲

## 簡介
本專案發想於我目前正在修習的課程 [人工智慧/機器學習的財務應用]，課程教授許多機器學習應用在財務分析的方式。  
此專案的目的為，以證交所每日公布之上市股票買賣日報表的券商分點資料，研究特定隔日沖分點的操作手法，希望從隔日沖標的tick資料與隔日沖分點的交易明細找出特定券商分點的操作手法，最終以機器學習的模型，建立一個預測特定隔日沖券商分點動向的模型。  

目前上傳的檔案只包含每日爬取資料的程式，希望等到資料數累積夠多再來建立模型。

## Code
* `daily_crawler.py`  
是進行爬蟲的主程式，執行之後會完成以下幾個工作:  
  * 1.爬取最新的上市上櫃股票清單  
  * 2.至Goodinfo爬取當日漲停股票  
  * 3.至證交所買賣日報表網站爬取所有上市股票的券商買賣日報表  
  * 4.任務完成後透過line notify傳送line訊息通知  

* `summarise_csv.py`  
在爬取所有券商買賣日報表之後，可以用summarise_csv.py來統計出當天漲停的股票當中買超、買進股數或是賣出股數的分點券商排行  


## 參考資料
1. https://www.youtube.com/watch?v=KESG8I9C3oA&ab_channel=%E5%A4%A7%E6%95%B8%E8%BB%9F%E9%AB%94%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8
2. https://www.youtube.com/watch?v=zmHVG6c_kFo&ab_channel=%E5%A4%A7%E6%95%B8%E8%BB%9F%E9%AB%94%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8
3. https://github.com/maxmilian/twse_bshtm_captcha
