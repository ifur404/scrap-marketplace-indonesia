import json
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import urllib.parse

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True

def toint(data) :
    return re.sub('[^0-9]','',data)

def tuliskan(nama,tulisan) :
	file = open(nama+'.asr', 'a')
	file.write(tulisan+"\n")
	file.close()

def tuliskan_jika(nama,tulisan) :
    if not os.path.exists(nama+'.asr'):
        os.mknod(nama+'.asr')
    if tulisan in open(nama+'.asr','r').read() :
        pass
    else :
        file = open(nama+'.asr', 'a')
        file.write(tulisan+"\n")
        file.close()

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS `bukalapak` (`link` varchar(250) NOT NULL,`nama_produk` text,`harga_produk`varchar(15) DEFAULT NULL,`gambar_produk`varchar(300) DEFAULT NULL,`rating_baik` varchar(10) DEFAULT NULL,`rating_buruk` varchar(10) DEFAULT NULL,`rating_value` varchar(10) DEFAULT NULL,`jumlah_ulasan` varchar(10) DEFAULT NULL,`nama_penjual` varchar(30) DEFAULT NULL,`penjual_info` text DEFAULT NULL, `lokasi` varchar(20) DEFAULT NULL,`keterangan` text,`kategori_link` varchar(300) DEFAULT NULL,`kondisi` varchar(300) DEFAULT NULL,`terjual` varchar(300) DEFAULT NULL,`dilihat` varchar(300) DEFAULT NULL,`difavoritkan` varchar(300) DEFAULT NULL,`diperbarui` varchar(300) DEFAULT NULL,`berat` varchar(300) DEFAULT NULL,`stock` varchar(300) DEFAULT NULL,`kategori_nama` varchar(300) DEFAULT NULL,PRIMARY KEY (`link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()

def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException:
        return False

def produk_bukalapak(link) :
    print(link)
    mydb = database_setting()
    mycursor = mydb.cursor()
    cari_awal = '{"@context":"http://schema.org","@type":"http://schema.org/Product"'
    cari_akhir = '}}\n</script>'
    url = with_req(link)
    if url :
        data = BeautifulSoup(url,'html.parser')
        if data.find('span',{'class' : 'c-user-identification-location__txt qa-seller-location'}) :
            lokasi = data.find('span',{'class' : 'c-user-identification-location__txt qa-seller-location'}).get_text().strip()
        else :
            lokasi = '-'
        gambar = data.find_all('a',{'class' : 'js-product-image-gallery__thumbnail c-product-image-gallery__thumbnail'})
        gambarnya = []
        for x in gambar :
            if x.get('data-bg-image-url') :
                gambarnya.append(x.get('data-bg-image-url'))
        kondisi = data.find('meta',{'name' : 'twitter:data2'}).get('content')
        if data.find('dd',{'class' : 'c-deflist__value qa-pd-sold-value'}) :
            terjual = data.find('dd',{'class' : 'c-deflist__value qa-pd-sold-value'}).get_text().strip()
        else : 
            terjual = '-'
        if data.find('dd',{'class' : 'c-deflist__value qa-pd-seen-value js-product-seen-value'}) :
            dilihat = data.find('dd',{'class' : 'c-deflist__value qa-pd-seen-value js-product-seen-value'}).get_text().strip()
        else :
            dilihat = '-'
        if data.find('dd',{'class' : 'c-deflist__value qa-pd-favorited-value'}) :
            difavoritkan = data.find('dd',{'class' : 'c-deflist__value qa-pd-favorited-value'}).get_text().strip()
        else :
            difavoritkan = '-'
        if data.find('dd',{'class' : 'c-deflist__value qa-pd-updated-value'}) :
            diperbarui = data.find('dd',{'class' : 'c-deflist__value qa-pd-updated-value'}).get_text().strip()
        else :
            diperbarui = '-'
        berat = data.find('dd',{'class' : 'c-deflist__value qa-pd-weight-value qa-pd-weight'}).get_text().strip()
        if data.find('div',{'class' : 'u-txt--small qa-pd-stock'}) :
            stock = toint(data.find('div',{'class' : 'u-txt--small qa-pd-stock'}).get_text())
        else :
            stock = '-'
        info_penjual = []
        if  data.find('table',{'class' : 'c-table c-table--tight'}) :
            allrows = data.find('table',{'class' : 'c-table c-table--tight'}).tbody.findAll('tr')
            for row in allrows:
                info_penjual.append([])
                allcols = row.findAll('td')
                for col in allcols:
                    thestrings = [str(s) for s in col.findAll(text=True)]
                    thetext = ''.join(thestrings)
                    info_penjual[-1].append(thetext)
            penjual_info = json.dumps(info_penjual)
        else :
            penjual_info = '-'
        awal = url.find(cari_awal)
        akhir = url.find(cari_akhir)
        data = url[awal:akhir]+'}}'
        rating_buruk = '-'
        rating_baik = '-'
        rating_value = '-'
        jumlah_ulasan = '-'
        if is_json(data) :
            produk = json.loads(data)
            array1 = produk['offers']
            if produk.get('aggregateRating') :
                array2 = produk['aggregateRating']
                rating_buruk = array2.get('worstRating')
                rating_baik = array2.get('bestRating')
                rating_value = array2.get('ratingValue')
                jumlah_ulasan = array2.get('reviewCount')
            array3 = produk['offers']['seller']
            if gambarnya :
                gambar_produk = '~'.join(gambarnya)
            else :
                gambar_produk = produk.get('image')
            nama_produk = produk.get('name')
            link = produk.get('url').replace('m.bukal','www.bukal')
            harga_produk = array1.get('price') 
            nama_penjual = array3.get('name')
            keterangan = produk.get('description').replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
            kategori_link = link[0:link.rfind('/')].replace('/p/','/c/')
            kategori_nama = produk.get('category')
            db = (link,nama_produk,harga_produk,gambar_produk,rating_baik,rating_buruk,rating_value,jumlah_ulasan,nama_penjual,penjual_info,lokasi,keterangan,kategori_link,kategori_nama,kondisi,terjual,dilihat,difavoritkan,diperbarui,berat,stock)
            col = "INSERT IGNORE INTO bukalapak (link,nama_produk,harga_produk,gambar_produk,rating_baik,rating_buruk,rating_value,jumlah_ulasan,nama_penjual,penjual_info,lokasi,keterangan,kategori_link,kategori_nama,kondisi,terjual,dilihat,difavoritkan,diperbarui,berat,stock) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            mycursor.execute(col,db)
            mydb.commit()
            if mycursor.rowcount :
                return True
            else:
                return False
            mydb.close()


def bukalapak_list_produk(link) :
    bukalapak = 'https://bukalapak.com'
    url = with_req(link)
    data = BeautifulSoup(url,'html.parser')
    jumlah_page = int(data.find('span',{'class' : 'last-page'}).get_text())
    print('halaman 1 dari '+str(jumlah_page))
    sukses = 0
    gagal = 0
    for x in tqdm(data.find_all('a',{'class' : 'product-media__link js-tracker-product-link'})) :
        if produk_bukalapak(bukalapak+''+x.get('href')) :
            sukses += 1
        else :
            gagal += 1
    print('sukses : '+str(sukses))
    print('gagal : '+str(gagal))
    print('==========================')
    i = 2 # dimulai dari 2 karna page pertama yang atas 
    while i <= jumlah_page :
        sukses = 0
        gagal = 0
        print('halaman '+str(i)+' dari '+str(jumlah_page))
        url2 = with_req(link+'&page='+str(i))
        if url2 :
            data2 = BeautifulSoup(url2,'html.parser')
            for u in tqdm(data2.find_all('a',{'class' : 'product-media__link js-tracker-product-link'})) :
                    if produk_bukalapak(bukalapak+''+u.get('href')) :
                        sukses += 1
                    else :
                        gagal += 1
            print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
            print('==========================')
            i += 1

def run_bukalapak() :
    url = with_req('https://www.bukalapak.com/c?from=navbar_icon')
    data = BeautifulSoup(url,'html.parser')
    for x in data.find_all('a',{'class' : 'c-list-ui__link'}) :
        if x.get('href') :
            if '/c/' in x.get('href') :
                linksay = 'https://www.bukalapak.com'+x.get('href').replace('?from=category_all&section=category_list','?utf8=%E2%9C%93&search[keywords]=&search[sort_by]=price%3Aasc')
                print('Kategori : '+x.get_text())
                bukalapak_list_produk(linksay)

buat_table_database()
run_bukalapak()

