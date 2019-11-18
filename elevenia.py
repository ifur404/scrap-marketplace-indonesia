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

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

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
    mycursor.execute("CREATE TABLE IF NOT EXISTS `elevenia` (`produk_id` varchar(300) NOT NULL,`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`harga_view` varchar(30) NOT NULL,`harga_asli` varchar(30) NOT NULL,`ulasan_jumlah` varchar(30) DEFAULT NULL,`wish_jumlah` varchar(30) DEFAULT NULL,`pertanyaan_jumlah` varchar(30) DEFAULT NULL,`produk_gambar` text,`info` text,`detail` text,`penjual_nama` varchar(300) DEFAULT NULL,`penjual_img` text,`penjual_link` varchar(300) DEFAULT NULL,`penjual_aktif` varchar(300) DEFAULT NULL,`penjual_transaksi` varchar(300) DEFAULT NULL,`penjual_kec` varchar(300) DEFAULT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()
    
def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False
        
def with_req_mobile(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 2.2) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def ambil_detail_elevenia(link) :
    print(link)
    produk_id = link[link.rfind('-')+1:]
    ## mengambil detail dari produk
    #membutuhkan link produk
    req_detail = with_req(link)
    if req_detail :
        bs_detail = BeautifulSoup(req_detail,'html.parser')
        if bs_detail.find('div',{'class' : 'storeMeta'}) : 
            img_list = []
            if bs_detail.find('ul',{'class' : 'imgNav'}) :
                for img in bs_detail.find('ul',{'class' : 'imgNav'}).find_all('li') :
                    img_list.append(img.find('a').get('href'))
            elif bs_detail.find('div',{'id' : 'mainPrdImg'}) :
                img_list.append(bs_detail.find('div',{'id' : 'mainPrdImg'}).a.get('href'))
            else :
                img_list.append('-')
            info_produk = []
            d_nama = []
            d_value = []
            data_infop = []
            if bs_detail.find('table',{'class' : 'tableDefault tableCol tableCol2 tableprdInfo'}) :
                for tr in bs_detail.find('table',{'class' : 'tableDefault tableCol tableCol2 tableprdInfo'}).find('tbody').find_all('tr') :
                    if len(tr.find_all('td')) == 1 and len(tr.find_all('th')) == 1 :
                        # info_produk.append({'name' : tr.find('th').get_text().strip(),'value' : tr.find('td').get_text().strip()})
                        pass
                    else :
                        for ye in tr.find_all('th') :
                            if ye.get_text().strip() :
                                d_nama.append(ye.get_text().strip())
                        for yu in tr.find_all('td') :
                            if yu.get_text().strip() :
                                d_value.append(yu.get_text().strip())
                        info_produk = [d_nama,d_value]
                for u in range(0,len(info_produk[1])) :
                    data_infop.append(info_produk[0][u]+' : '+info_produk[1][u])
            else :
                data_infop.append('-')
        
            req_detail_m = with_req_mobile('http://m.elevenia.co.id/product/getProductDescription.do?prdNo='+produk_id+'&reqType=text&exp=full')
            if req_detail_m :
                bs_m = BeautifulSoup(req_detail_m,'html.parser')
                if bs_m.find('div',{'class' : 'boxDetail3_1 productDetail'}) :
                    m_detail = str(bs_m.find('div',{'class' : 'boxDetail3_1 productDetail'}))
                else : 
                    m_detail = '-'
            else :
                m_detail = '-'
            if bs_detail.find('div',{'class' : 'storeMeta'}).find('a',{'class' : 'storeImg'}).find('img') :
                penjual_img = bs_detail.find('div',{'class' : 'storeMeta'}).find('a',{'class' : 'storeImg'}).find('img').get('src')
            else :
                penjual_img = '-'
            if bs_detail.find('div',{'class' : 'storeMeta'}).find('div',{'class' : 'storeWrap'}).find('a').get('href') :
                penjual_link = bs_detail.find('div',{'class' : 'storeMeta'}).find('div',{'class' : 'storeWrap'}).find('a').get('href')
            else :
                penjual_link = '-'
            if bs_detail.find('div',{'class' : 'storeMeta'}).find('div',{'class' : 'storeWrap'}).find('a').get_text() :
                penjual_nama = bs_detail.find('div',{'class' : 'storeMeta'}).find('div',{'class' : 'storeWrap'}).find('a').get_text()
            else :
                penjual_nama = '-'
            dd_data = []
            for dd in bs_detail.find('div',{'class' : 'storeStats'}).find_all('dd') :
                dd_data.append(dd.get_text().strip())
            penjual_t = dd_data[1].split('\r\n') ## Persentase jumlah pesanan yang berhasil diterima Buyer dalam 30 hari terakhir
            penjual_k = dd_data[1].split('\r\n') ## Rata-rata kecepatan Seller memproses pesanan dalam 30 hari terakhir, dihitung sejak pembayaran lunas hingga Seller menyerahkan paket ke kurir pengiriman.
            if bs_detail.find('span', {'id' : 'reviewCount'}) :
                ulasan_jumlah = bs_detail.find('span', {'id' : 'reviewCount'}).get_text()
            else :
                ulasan_jumlah = 0
            if bs_detail.find('span', {'class' : 'normPrice notranslate'}) :
                harga_asli = re.sub('[^0-9]','',bs_detail.find('span', {'class' : 'normPrice notranslate'}).get_text())
            else :
                harga_asli = '-'
            produk = {
                'nama' : bs_detail.find('h1', {'class' : 'notranslate'}).get_text(),
                'harga_view' : re.sub('[^0-9]','',bs_detail.find('span', {'class' : 'price notranslate'}).get_text()),
                'harga_asli' : harga_asli,
                'gambar' : '~'.join(img_list),
                'ulasan_jumlah' : ulasan_jumlah,
                'wish_jumlah' : re.sub('[^0-9]','',bs_detail.find('em', {'id' : 'wishCount'}).get_text()),
                'pertanyaan_jumlah' : re.sub('[^0-9]','',bs_detail.find('em', {'id' : 'allPrdQnaACnt2'}).get_text()),
                'info_p' : json.dumps(data_infop,sort_keys=True, indent=4),
                'detail_p' : m_detail,
                'penjual_img' : penjual_img,
                'penjual_nama' : penjual_nama,
                'penjual_link' : penjual_link,
                'penjual_aktif' : dd_data[0],
                'penjual_transaksi' : penjual_t[0],
                'penjual_kec' : penjual_k[0],
                }
            db = (produk_id,produk['nama'],link,produk['harga_view'],produk['harga_asli'],produk['ulasan_jumlah'],produk['wish_jumlah'],produk['pertanyaan_jumlah'],produk['gambar'],produk['info_p'],produk['detail_p'],produk['penjual_nama'],produk['penjual_img'],'http://www.elevenia.co.id'+produk['penjual_link'],produk['penjual_aktif'],produk['penjual_transaksi'],produk['penjual_kec'])
            col = "INSERT IGNORE INTO elevenia (produk_id,produk_nama,produk_link,harga_view,harga_asli,ulasan_jumlah,wish_jumlah,pertanyaan_jumlah,produk_gambar,info,detail,penjual_nama,penjual_img,penjual_link,penjual_aktif,penjual_transaksi,penjual_kec) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            mydb = database_setting()
            mycursor = mydb.cursor()
            mycursor.execute(col,db)
            mydb.commit()
            if mycursor.rowcount :
                return True
            else:
                return False
            mydb.close()
        return False
    else :
        return False

def lop_cat_elevenia(catid,catkey) :
    # mengambil link produk
    # membutuhkan 2 data yaitu key kategori dan ketegori id
    page = 0
    gagalwae = 0
    while True :
        sukses = 0
        gagal = 0
        page += 1
        link = 'http://m.elevenia.co.id/ajax/category-products.do?page='+str(page)+'&limit=15&categoryId='+str(catid)+'&categoryKey='+catkey
        req_produk = with_req_mobile(link)
        if req_produk :
            print('halaman ke : '+str(page))
            print(link)
            if is_json(req_produk) : 
                array = json.loads(req_produk)
                if array.get('count') > 0 :
                    bs = BeautifulSoup(array['docs'],'html.parser')
                    for li in tqdm(bs('li')) :
                        if li.a.get('href') :
                            if ambil_detail_elevenia(li.a.get('href').replace('/m.','/www.')) :
                                sukses += 1
                            else :
                                gagal += 1
                else :
                    print('Kategori ini sudah selesai')
                    print('====================================')
                    break
            else :
                gagalwae += 1
                if gagalwae > 3 :
                    break
                print('bukan json harus di cek')
                print('====================================')        
        print('Sukses :'+str(sukses)+' || Gagal : '+str(gagal))
        print("================================================")
        

def cari_id(link) :
    data = with_req(link)
    if data :
        bs_idkat = BeautifulSoup(data,'html.parser')
        if bs_idkat.find('input',{'name' : 'sCtgrNo'}) :
            catid = bs_idkat.find('input',{'name' : 'sCtgrNo'}).get('value')
            catkey = link[link.find('ctg-')+4:]
            if catkey and catid :
                lop_cat_elevenia(catid,catkey)
    else :
        return False


def run_elevenia() :
    data = with_req('http://www.elevenia.co.id/sitemap-category.xml')
    if data :
        bs_data = BeautifulSoup(data,'lxml')
        hitung = 0
        for i in bs_data.find_all('loc') :
            hitung += 1
            print("kategori "+str(hitung)+" Of "+str(len(bs_data.find_all('loc'))))
            cari_id(i.get_text())
    else :
        print('masalah jaringan')

buat_table_database()
run_elevenia()