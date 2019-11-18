import json
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import urllib.parse
from selenium import webdriver

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def tuliskan(nama,tulisan) :
	file = open(nama+'.asr', 'a')
	file.write(tulisan+"\n")
	file.close()

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE `shopee` (`nama_produk` varchar(300) DEFAULT NULL,`produk_link` varchar(300) NOT NULL,`produk_harga` varchar(300) NOT NULL,`produk_harga_min` varchar(300) NOT NULL,`produk_harga_max` varchar(300) NOT NULL,`produk_merek` varchar(30) DEFAULT NULL,`produk_stock` varchar(30) DEFAULT NULL,`produk_terjual` varchar(30) DEFAULT NULL,`produk_penilaian` varchar(30) DEFAULT NULL,`produk_like` varchar(30) DEFAULT NULL,`produk_waktu` varchar(30) DEFAULT NULL,`produk_rating_bintang` varchar(30) DEFAULT NULL,`produk_rating_jumlah` varchar(30) DEFAULT NULL,`produk_rating_satu` varchar(30) DEFAULT NULL,`produk_rating_dua` varchar(30) DEFAULT NULL,`produk_rating_tiga` varchar(30) DEFAULT NULL,`produk_rating_empat` varchar(30) DEFAULT NULL,`produk_rating_lima` varchar(30) DEFAULT NULL,`produk_model` text,`produk_kategori` text,`produk_info` text,`produk_gambar` text,`produk_keterangan` text,`penjual` varchar(30) DEFAULT NULL,`penjual_lokasi` text,`penjual_jumlah_produk` varchar(30) DEFAULT NULL,`penjual_penilaian` varchar(30) DEFAULT NULL,`penjual_respon` varchar(30) DEFAULT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")

def with_proxy(link) :
    list_proxy = open('listproxy.asr','r').read().split("\n")
    proxy = list_proxy[0]
    proxyDict = { 
                "http"  : "http://"+proxy, 
                "https" : "https://"+proxy, 
                "ftp"   : "ftp://"+proxy
                }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        }
    try:
        return requests.get(link,proxies=proxyDict,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def with_selenium(link) :
    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 7.0; PLUS Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.98 Mobile Safari/537.36')
    options.add_argument('--headless');
    driver = webdriver.Chrome(chrome_options=options)
    driver.implicitly_wait(30)
    driver.get(link)
    # data = driver.page_source
    # print(driver.status_code)
    if driver.find_elements_by_xpath("//div[@class='_3XpRHJ hairline-border-up-bottom']") :
        lokasi = [x.text for x in driver.find_elements_by_xpath("//div[@class='_3XpRHJ hairline-border-up-bottom']")][0]
    else :
        lokasi = '-'
    if driver.find_elements_by_xpath("//div[@class='A2LqCL']") : 
        penjual = [x.text for x in driver.find_elements_by_xpath("//div[@class='A2LqCL']")][0]
    else :
        penjual = '-'
    penjual_info = [x.text for x in driver.find_elements_by_xpath("//div[@class='_1Z94ro']")]
    produk = {
        'lokasi' : lokasi,
        'penjual' : penjual,
        'penjual_jumlah_produk' : penjual_info[0],
        'penjual_penilaian' : penjual_info[1],
        'penjual_respon' : penjual_info[2]
    }
    driver.quit()
    return produk

def produk(nama,itemid,shopid) :
    mydb = database_setting()
    mycursor = mydb.cursor()
    # produk_link = 'https://shopee.co.id/Xiaomi-Redmi-3s-16Gb-Gold---Garansi-Distri-1-Tahun-i.47122328.1055536318'
    # selenium_produk = with_selenium(produk_link)
    produk_link = 'https://shopee.co.id/'+re.sub("[^a-zA-Z0-9 ]","",nama).replace(' ','-')+'-i.'+str(shopid)+'.'+str(itemid)
    selenium_produk = with_selenium(produk_link)

    data_api = with_req('https://shopee.co.id/api/v2/item/get?itemid='+str(itemid)+'&shopid='+str(shopid)+'&__classic__=1')

    if data_api :
        if is_json(data_api) :
            dataya = json.loads(data_api)
            dataku = dataya['item']
            nama_produk = dataku.get('name')
            gambar = []
            for x in dataku['images'] :
                gambar.append(x)
            produk_gambar = ",".join(gambar)
            produk_keterangan = dataku.get('description')
            produk_stock = dataku.get('stock')
            produk_terjual = dataku.get('sold')
            produk_merek = dataku.get('brand')
            produk_penilaian = dataku.get('cmt_count')
            produk_like = dataku.get('liked_count')
            produk_waktu = dataku.get('ctime')
            produk_harga_min = dataku.get('price_min')
            produk_harga_max = dataku.get('price_max')
            produk_harga = dataku.get('price')
            if isinstance(produk_harga,int) :
                produk_harga = str(produk_harga)[:-5]
            if isinstance(produk_harga_min,int) :
                produk_harga_min = str(produk_harga_min)[:-5]
            if isinstance(produk_harga_max,int) :
                produk_harga_max = str(produk_harga_max)[:-5]
            produk_m = []
            for h in dataku['models'] :
                produk_m.append({'nama' : h['name'],'harga' : h['price']})
            produk_model = json.dumps(produk_m)
            produk_k = []
            for h in dataku['categories'] :
                produk_k.append(h['display_name'])
            produk_kategori = json.dumps(produk_k)
            produk_l = []
            for h in dataku['attributes'] :
                produk_l.append({h['name'] : h['value']})
            produk_info = json.dumps(produk_l)
            produk_rating_bintang = dataku['item_rating']['rating_star']
            produk_rating_jumlah = dataku['item_rating']['rating_count'][0]
            produk_rating_satu = dataku['item_rating']['rating_count'][1]
            produk_rating_dua = dataku['item_rating']['rating_count'][2]
            produk_rating_tiga = dataku['item_rating']['rating_count'][3]
            produk_rating_empat = dataku['item_rating']['rating_count'][4]
            produk_rating_lima = dataku['item_rating']['rating_count'][5]

            penjual_lokasi = selenium_produk['lokasi'] 
            penjual = selenium_produk['penjual'] 
            penjual_jumlah_produk = selenium_produk['penjual_jumlah_produk'] 
            penjual_penilaian = selenium_produk['penjual_penilaian'] 
            penjual_respon = selenium_produk['penjual_respon'] 
            if nama_produk and produk_harga :
                db = (nama_produk,produk_link,produk_harga,produk_harga_min,produk_harga_max,produk_merek,produk_stock,produk_terjual,produk_penilaian,produk_like,produk_waktu,produk_rating_bintang,produk_rating_jumlah,produk_rating_satu,produk_rating_dua,produk_rating_tiga,produk_rating_empat,produk_rating_lima,produk_model,produk_kategori,produk_info,produk_gambar,produk_keterangan,penjual,penjual_lokasi,penjual_jumlah_produk,penjual_penilaian,penjual_respon)
                col = "INSERT IGNORE INTO shopee (nama_produk,produk_link,produk_harga,produk_harga_min,produk_harga_max,produk_merek,produk_stock,produk_terjual,produk_penilaian,produk_like,produk_waktu,produk_rating_bintang,produk_rating_jumlah,produk_rating_satu,produk_rating_dua,produk_rating_tiga,produk_rating_empat,produk_rating_lima,produk_model,produk_kategori,produk_info,produk_gambar,produk_keterangan,penjual,penjual_lokasi,penjual_jumlah_produk,penjual_penilaian,penjual_respon) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                mycursor.execute(col,db)
                mydb.commit()
                if mycursor.rowcount :
                    return True
                else:
                    return False
                mydb.close()
            else :
                return False
    

def run_shopee() :
    url = with_req('https://shopee.co.id/api/v1/category_list/')
    category_list = []
    if url :
        if is_json(url) :
            for x in json.loads(url) :
                category_list.append(x['main']['catid'])
        print('Ada '+str(len(category_list))+' category utama')
        for u in category_list :
            kabaraha = 0
            while True :
                sukses = 0
                gagal = 0
                url2 = with_req('https://shopee.co.id/api/v2/search_items/?by=price&limit=100&match_id='+str(u)+'&newest='+str(kabaraha)+'&order=asc&page_type=search')
                print("page : "+str(kabaraha)+" kategori id : "+str(u))
                if url2 :
                    if is_json(url2) :
                        data = json.loads(url2)
                        if data.get('items') :
                            for o in tqdm(data['items']) :
                                if produk(o.get('name'),o.get('itemid'),o.get('shopid')) :
                                    sukses += 1
                                else :
                                    gagal +=1
                                    # tuliskan('gagalakses',o.get('name')+'||||'+str(o.get('itemid'))+'||||'+str(o.get('shopid')))
                        else :
                            print('selesai page ini')
                            break
                kabaraha += 1
                print("sukses : "+str(sukses)+" gagal : "+str(gagal))
                print("==================")

       
# buat_table_database()
run_shopee()
                    