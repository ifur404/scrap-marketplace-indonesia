import json
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup
from tqdm import tqdm

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

def savejsontext(nama,data) :
    tuliskan(nama,json.dumps(data, indent=4, sort_keys=True))

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS `tokopedia` (`id_produk` varchar(300) DEFAULT NULL,`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`produk_harga` varchar(300) NOT NULL,`produk_stock` varchar(30) DEFAULT NULL,`produk_status` varchar(2) DEFAULT NULL,`produk_terjual` varchar(30) DEFAULT NULL,`produk_ulasan` varchar(30) DEFAULT NULL,`produk_rating` varchar(30) DEFAULT NULL,`kategori_link` varchar(300) NOT NULL,`kategori_nama` varchar(300) NOT NULL,`dilihat` varchar(300) DEFAULT NULL,`produk_gambar` text,`produk_keterangan` text,`penjual` varchar(100) DEFAULT NULL,`penjual_lokasi` text,`penjual_link` varchar(300) DEFAULT NULL,`penjual_official` varchar(10) DEFAULT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()

def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def potong_tokopedia(data) :
    awal = data.find('window.__data = {')
    if awal > 1 :
        akhir = data.find('}}};')
        data = data[awal:akhir]+'}}}'
        prososes = data.replace('window.__data = ','')
        if is_json(prososes) :
            return json.loads(prososes)
        else :
            return False
    else :
        return False

# produk dalam kategori 
def produk_kategori_tokopedia(nama,link) :
    urlkuy = 'https://www.tokopedia.com'+link
    page = 0 # page kategori dimulai dari 0 karna setelah masuk lopp dia jadi 1
    while True :
        page += 1
        print("halaman "+str(page)+ " "+nama)
        link = urlkuy+'?ob=2&page='+str(page)
        print(link)
        url = with_req(link)
        if url :
            data = potong_tokopedia(url)
            if data :
                kategori_produk = data['category']['result']['data']['product']
                sukses = 0
                gagal = 0
                for x in tqdm(kategori_produk) :
                    url2 = x['url'].split("?")
                    shop = x['shop']
                    data_gambar = with_req(url2[0])
                    data_bs = BeautifulSoup(data_gambar,'html.parser')
                    if data_bs.find('div',{'itemprop' : 'description'}) :
                        produk_keterangan = data_bs.find('div',{'itemprop' : 'description'}).get_text()
                    else : 
                        produk_kategori_tokopedia = '-'
                    if data_bs.find_all('div',{'class' : 'content-img-relative'}) :
                        gambar_kumpul = []
                        for o in data_bs.find_all('div',{'class' : 'content-img-relative'}) :
                            if o.find('img') :
                                gambar_kumpul.append(o.find('img').get("src"))
                        gambar = "~".join(gambar_kumpul)
                    else :
                        gambar = '-'
                    view = with_req('https://tome.tokopedia.com/v2/provi?pid='+str(x['id']))
                    if is_json(view) :
                        view = json.loads(view)
                    else :
                        view['view'] = '-'
                    penjual = with_req('https://js.tokopedia.com/productstats/check?pid='+str(x['id'])+'&callback=show_product_stats')
                    if penjual :
                        jual = json.loads(penjual[penjual.find('{'):penjual.find('}')]+'}')
                    else :
                        jual = '-'
                    db = (x['id'],x['name'],url2[0],x['price_int'],x['stock'],x['status'],jual['success'],x['countReview'],x['rating'],'https://www.tokopedia.com/p/'+x['categoryBreadcrumb'],x['department_name'],view['data']['view'],gambar,produk_keterangan,shop['name'],shop['location'],shop['url'],shop['is_official'])
                    col = "INSERT IGNORE INTO tokopedia (id_produk,produk_nama,produk_link,produk_harga,produk_stock,produk_status,produk_terjual,produk_ulasan,produk_rating,kategori_link,kategori_nama,dilihat,produk_gambar,produk_keterangan,penjual,penjual_lokasi,penjual_link,penjual_official) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    mydb = database_setting()
                    mycursor = mydb.cursor()
                    mycursor.execute(col,db)
                    mydb.commit()
                    if mycursor.rowcount :
                        sukses += 1
                    else:
                        gagal += 1
                    mydb.close()
                print('Sukses '+str(sukses)+' || Gagal : '+str(gagal))
                print("====================================")
            else :
                print('sudah selesai mungkin')
                break
        else: 
            print('ada masalah di url yang di tuju')
            break

##### kategori ambil
def run_tokopedia() : 
    url = with_req('https://www.tokopedia.com/p')
    data = potong_tokopedia(url)
    if data :
        semua_kategori = data['allCategory']['data']['allCategoryItem']
        for x in semua_kategori :
            for u in semua_kategori[str(x)] :
                if u.get('child') :
                    for s in u['child'] :
                        produk_kategori_tokopedia(s['name'],s['url'])

    else :
        print('ulangi, jika salah terus cek kode')


buat_table_database()
run_tokopedia()
