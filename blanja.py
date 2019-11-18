import json
import requests
import time
import re
import mysql.connector
from tqdm import tqdm
from bs4 import BeautifulSoup

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def hargatoint(harga) :
    return re.sub('[^0-9]','',harga)

def tuliskan(nama,tulisan) :
	file = open(nama+'.asr', 'a')
	file.write(tulisan+"\n")
	file.close()

def savejsontext(nama,data) :
    tuliskan(nama,json.dumps(data, indent=4, sort_keys=True))

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS `blanja` (`produk_id` varchar(300) NOT NULL,`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`produk_skor` varchar(30) NOT NULL,`harga_view` varchar(30) NOT NULL,`harga_label` varchar(30) NOT NULL,`produk_kondisi` varchar(30) NOT NULL,`produk_terjual` varchar(30) NOT NULL,`produk_stock` varchar(30) NOT NULL,`ulasan_jumlah` varchar(30) NOT NULL,`ulasan_rating` varchar(30) NOT NULL,`produk_gambar` text,`deskripsi` text,`spestifikasi` text,`penjual_nama` varchar(300) DEFAULT NULL,`penjual_url` varchar(300) DEFAULT NULL,`penjual_rating_barang` varchar(300) DEFAULT NULL,`penjual_rating_pengiriman` varchar(300) DEFAULT NULL,`penjual_rating_layanan` varchar(300) DEFAULT NULL,`penjual_alamat` varchar(300) DEFAULT NULL,`penjual_online` varchar(300) DEFAULT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()
    
def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def with_post_tambahan(link,page) :
    headers = {
        'Host' : 'item.blanja.com',
        'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept' : '*/*',
        'Accept-Language' : 'en-US,en;q=0.5',
        'Accept-Encoding' : 'gzip, deflate, br',
        'Referer' : 'https://www.blanja.com/',
        'Origin' : 'https://www.blanja.com',
        'Connection' : 'keep-alive',
        'Pragma' : 'no-cache',
        }
    data = {
        'pageNo' : str(page)
    }
    try:
        return requests.post(link,headers=headers,timeout=10,verify=True,data=data).text   
    except requests.exceptions.RequestException as e:
        return False

def blanja_produk(link) :
    data = with_req(link)
    if data :
        bs_data = BeautifulSoup(data,'html.parser')
        if bs_data.find('h1',{'class' : 'title fSize-18 fWeight-bold mb10'}) :
            produk_id = link[link.rfind('-')+1:]
            img_list = []
            for img in bs_data.find('ul',{'class' : 'showcase-thumbnail mt20'}).find_all('img') : 
                img_list.append(img.get('src').replace('//','https://').replace('_56x56.jpg',''))
            item_score = data[data.find('var pageData = ') : data.find("}';")].replace("var pageData = '","")+'}'
            if is_json(item_score) :
                array = json.loads(item_score)
                barang_score = array.get('itemScore')
            else :
                barang_score = '-'
            if bs_data.find('p',{'id' : 'listPrice'}) :
                harga_label = hargatoint(bs_data.find('p',{'id' : 'listPrice'}).span.get_text())
            else :
                harga_label = '-'
            if  bs_data.find('div',{'class' : 'fLeft mt10 lHeight-16 fColor-red fWeight-bold'}) :
                kondisi = bs_data.find('div',{'class' : 'fLeft mt10 lHeight-16 fColor-red fWeight-bold'}).get_text().strip()
            else :
                kondisi = '-'
            if bs_data.find('div',{'class' : 'fLeft fSize-32 fWeight-bold fColor-softblack'}) :
                ulasan_rating = bs_data.find('div',{'class' : 'fLeft fSize-32 fWeight-bold fColor-softblack'})
            else :
                ulasan_rating = '-'
            cat_list = []
            for cat in bs_data.find_all('span',{'class' : 'catLink'}) :
                if cat.find('a').get_text() == 'Home' :
                    pass
                else :
                    cat_list.append({'url' : cat.find('a').get('href'),'nama' : cat.find('a').get_text()})
            if bs_data.find('input',{'id' : 'quantityItems'}) :
                stock = bs_data.find('input',{'id' : 'quantityItems'}).get('value')
            else : 
                stock = '-'
            produk = {
                'nama' : bs_data.find('h1',{'class' : 'title fSize-18 fWeight-bold mb10'}).get_text(),
                'gambar' : '~'.join(img_list),
                'harga' : hargatoint(bs_data.find('span',{'class' : 'lHeight-24 fSize-18 fWeight-bold'}).get_text().strip()),
                'terjual' : hargatoint(bs_data.find('p',{'class' : 'fRight fWeight-bold'}).get_text()),
                'jumlah_ulasan' : hargatoint(bs_data.find('a',{'id' : 'toFeedback'}).get_text()),
                'deskripsi' : bs_data.find('input',{'id' : 'temple'}).get('value'),
                'spestifikasi' : bs_data.find('li',{'class' : 'p30','tag' : 'specification'}).get_text(),
            }
            kum_rat = []
            for rat in bs_data.find_all('span',{'class' : 'fRight ml5 fSize-12'}) :
                kum_rat.append(re.sub('[^0-9]','',rat.get_text()))
            penjual = {
                'nama' : bs_data.find('h2',{'class' : 'fLeft'}).get_text(),
                'url' : bs_data.find('a',{'class' : 'fSize-16 fWeight-bold fColor-softblack tDecoration-none'}).get('href'),
                'rating_barang' : kum_rat[0],
                'rating_pengiriman' : kum_rat[1],
                'rating_layanan' : kum_rat[2],
                'online' : bs_data.find('p',{'class' : 'fColor-softblack fSize-12'}).get_text(),
                'alamat' : bs_data.find('p',{'class' : 'fColor-softblack mt10 fSize-12'}).get_text(),
            }
            db = (produk_id,produk['nama'],link,barang_score,produk['harga'],harga_label,kondisi,produk['terjual'],stock,produk['jumlah_ulasan'],ulasan_rating,produk['gambar'],produk['deskripsi'],produk['spestifikasi'],penjual['nama'],penjual['url'],penjual['rating_barang'],penjual['rating_pengiriman'],penjual['rating_layanan'],penjual['alamat'],penjual['online'])
            col = "INSERT IGNORE INTO blanja (produk_id,produk_nama,produk_link,produk_skor,harga_view,harga_label,produk_kondisi,produk_terjual,produk_stock,ulasan_jumlah,ulasan_rating,produk_gambar,deskripsi,spestifikasi,penjual_nama,penjual_url,penjual_rating_barang,penjual_rating_pengiriman,penjual_rating_layanan,penjual_alamat,penjual_online) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            mydb = database_setting()
            mycursor = mydb.cursor()
            mycursor.execute(col,db)
            mydb.commit()
            if mycursor.rowcount :
                return True
            else:
                return False
            mydb.close()
        else :
            print(link)
            tuliskan('error.log',link)
            # print('dia kill saya')
            return False
    else :
        print(link)
        tuliskan('blokir',link)
        print('aaaaaaaaaaaaaaaaa')
        return False

# def with_post_tambahan2(link,link_asli,page) :
#     headers = {
#         'Host' : 'item.blanja.com',
#         'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',
#         'Accept' : '*/*',
#         'Accept-Language' : 'en-US,en;q=0.5',
#         'Accept-Encoding' : 'gzip, deflate, br',
#         'Referer' : link_asli,
#         'Origin' : 'https://www.blanja.com',
#         'Connection' : 'keep-alive',
#         'Pragma' : 'no-cache',
#         }
#     data = {
#         'pageNo' : str(page)
#     }
#     try:
#         return requests.post(link,headers=headers,timeout=10,verify=True,data=data).text   
#     except requests.exceptions.RequestException as e:
#         return False

# def get_category(link,link_asli) :
#     page = 0
#     while True :
#         page += 1
#         data = with_post_tambahan(link,link_asli,page)
#         bs_data = BeautifulSoup(data,'html.parser')
#         for x in bs_data.find_all('div',{'class' : 'product-box'}) :
#             print(x.a.get('href'))
#         if bs_data.find('span',{'class' : 'recnum'}).get('data') == page :
#             break

def run_blanja() :
    page = 0
    gagalwae = 0
    off = 0
    while True :
        page += 1
        sukses = 0
        gagal = 0
        print('Halaman ke '+str(page)+' Of '+str(off))
        data = with_post_tambahan('https://item.blanja.com/items/a/search?&order=salesprice_asc',page)
        if data :
            bs_data = BeautifulSoup(data,'html.parser')
            if bs_data.find_all('div',{'class' : 'product-box'}) :
                for x in tqdm(bs_data.find_all('div',{'class' : 'product-box'})) :
                    if blanja_produk(x.a.get('href')) :
                        sukses += 1
                    else :
                        gagal += 1
                print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
                print('===============================')
                if bs_data.find('span',{'class' : 'recnum'}).get('data') == page :
                    print('Sudah Semua')
                    print('===============================')
                    break
                off = bs_data.find('span',{'class' : 'recnum'}).get('data')
            else :
                print('aku tidak tau salahnya dimana')
        else :
            if gagalwae < 3 :
                page -= 1    
            else :
                gagalwae = 0        
            

# def get_category_link(link) :
#     data = with_req(link)
#     if data :
#         bs_data = BeautifulSoup(data,'html.parser')

# def get_kategori() :
#     data = with_req('https://item.blanja.com/navigation/backendCategory?device=PC')
#     if data :
#         if is_json(data) :
#             array = json.loads(data)
#             # print(array['mappingLvlCategory'])
#             for o in range(1,array['lengthLvl']+1) :
#                 for i in array['mappingLvlCategory'][str(o)] :
#                     if i['lvlCategory'] == 1 :
#                         link = 'https://m.blanja.com/katalog/c/'+i['menuDisplay']+'/'+i['urlKey']
#                         get_category_link(link)
#         else :
#             return False
#     else :
#         return False
    
# print(get_kategori())
# get_category_link('https://www.blanja.com/katalog/c/fas/fashion')
# get_category('https://item.blanja.com/items/a/search?&order=salesprice_asc')
# get_category('https://item.blanja.com/items/a/search?oneNav=20000101,20000103,20000105&order=salesprice_asc')
# print(with_post_ambil('https://www.blanja.com/katalog/p/fas/tas-keren-testing-18670178'))

buat_table_database()
run_blanja()