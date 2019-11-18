import json
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup
import os
from tqdm import tqdm

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

if not os.path.exists('kategori.asr'):
    os.mknod('kategori.asr')

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

def hapus_data() :
    data = ['listproxy.asr','kategori.asr']
    for namafile in tqdm(data) :
        if os.path.exists(namafile):
            os.remove(namafile)
            print("sudah di hapus "+namafile) 
        else:
            print("tidak ada "+namafile)

def hapus_database() :
    data = ['listproxy.asr','kategori.asr']
    for namafile in tqdm(data) :
        if os.path.exists(namafile):
            os.remove(namafile)
            print("sudah di hapus "+namafile) 
        else:
            print("tidak ada "+namafile) 

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    ##buat table kategori produk
    mycursor.execute("CREATE TABLE `kategori` (`link` varchar(300) NOT NULL,`nama_kategori` text NOT NULL,PRIMARY KEY (`link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mycursor.execute("CREATE TABLE `produk` (`id_produk` int(11) DEFAULT NULL,`link` varchar(250) NOT NULL,`nama_produk` text,`gambar_produk` text,`harga_produk` varchar(15) DEFAULT NULL,`merk` varchar(20) DEFAULT NULL,`rating` varchar(10) DEFAULT NULL,`penjual` varchar(30) DEFAULT NULL,`lokasi` varchar(20) DEFAULT NULL,`keterangan` text,`kategori_produk` varchar(300) DEFAULT NULL, PRIMARY KEY (`link`), KEY `kategori_produk` (`kategori_produk`), CONSTRAINT `produk_ibfk_1` FOREIGN KEY (`kategori_produk`) REFERENCES `kategori` (`link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()

def hapus_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    ##hapus table kategori dan produk
    mycursor.execute("DROP TABLE `produk`; DROP TABLE `kategori`;",multi=True)     
    mydb.close()


def simpan_produk(id_produk,link,nama_produk,gambar_produk,harga_produk,merk,rating,penjual,lokasi,keterangan,kategori_produk) :
    mydb = database_setting()
    mycursor = mydb.cursor()
    db = (id_produk,link,nama_produk,gambar_produk,harga_produk,merk,rating,penjual,lokasi,keterangan,kategori_produk)
    col = "INSERT IGNORE INTO produk (id_produk,link,nama_produk,gambar_produk,harga_produk,merk,rating,penjual,lokasi,keterangan,kategori_produk) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    mycursor.execute(col,db)
    mydb.commit()
    if mycursor.rowcount :
        return True
    else:
        return False
    mydb.close()

def simpan_category(link,nama) :
    mydb = database_setting()
    mycursor = mydb.cursor()
    db = (link,nama)
    col = "INSERT IGNORE INTO kategori (link,nama_kategori) VALUES (%s,%s)"
    mycursor.execute(col,db)
    mydb.commit()
    if mycursor.rowcount :
        return True
    else:
        return False
    mydb.close()

def with_proxy(link) :
    # list_proxy = open('listproxy.asr','r').read().split("\n")
    # proxy = list_proxy[0]
    # proxyDict = { 
    #             "http"  : "http://"+proxy, 
    #             "https" : "https://"+proxy, 
    #             "ftp"   : "ftp://"+proxy
    #             }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False
    
def lazada_category() :
    berhasil = 0
    gagal = 0
    url = requests.get('https://lazada.co.id').text
    data = BeautifulSoup(url,'html.parser')
    data_kumpul = []
    arrow = data.find_all('li',{'class' : 'sub-item-remove-arrow'})
    for x in arrow :
        parse = x.find('a')
        data_kumpul.append(parse.get('href').replace('//','https://')+"|||"+parse.get_text().strip())

    category = data.find('div',{'class' : 'lzd-home-page-category'})
    for x in category.find_all('li', class_='lzd-site-menu-grand-item') : 
        data_kumpul.append(x.a.get('href').replace('//','https://')+"|||"+x.a.get_text().strip())

    sub_kategori = data.find_all('li',{'class' : 'lzd-site-menu-grand-item'})
    for x in sub_kategori :
        parse = x.find('a')
        data_kumpul.append(parse.get('href').replace('//','https://')+"|||"+parse.get_text().strip())
    
    for list_data in tqdm(data_kumpul) :
        bagi = list_data.split('|||')
        linknya = bagi[0]
        textnya = bagi[1]
        if linknya in open('kategori.asr','r').read() :
            pass
            # print('sudah ada')
        else:
            tuliskan('kategori',linknya)
            # print('di tambahkan')
        if simpan_category(linknya,textnya) :
            # print('sukses')
            berhasil += 1
        else: 
            gagal += 1
    print('Berhasil di tambahkan : '+str(berhasil))
    print('Gagal di tambahkan : '+str(gagal))

def check_termurah(link) :
    url = with_proxy(link+'?sort=priceasc')
    awal = url.find('<script>window.pageData=')
    if awal > 1 :
        akhir = url.find('}}</script>')
        data = url[awal:akhir]+'}}'
        prososes = data.replace('<script>window.pageData=','')
        if is_json(prososes) :
            array = json.loads(prososes)
            return re.sub("[^0-9]", "",array['mods']['listItems'][0]['priceShow'])

def check_termahal(link) :
    url = with_proxy(link+'?sort=pricedesc')
    awal = url.find('<script>window.pageData=')
    if awal > 1 :
        akhir = url.find('}}</script>')
        data = url[awal:akhir]+'}}'
        prososes = data.replace('<script>window.pageData=','')
        if is_json(prososes) :
            array = json.loads(prososes)
            return re.sub("[^0-9]", "",array['mods']['listItems'][0]['priceShow'])  

def lazada_produk(link) :
    with_proxy('https://lazada.co.id')
    termurah = check_termurah(link)
    termahal = check_termahal(link)
    gambarku = []
    keterangannya = []
    if termahal and termurah :
        hargalop = 0
        i = 0
        while True :
            berhasil = 0
            gagal = 0
            i += 1
            if hargalop == 0 :
                hargalop = int(termurah)
            linknya = link+'?sort=priceasc&price='+str(hargalop)+'-'   
            print(linknya)
            url = with_proxy(linknya)
            awal = url.find('<script>window.pageData=')
            if awal > 1 :
                akhir = url.find('}}</script>')
                data = url[awal:akhir]+'}}'
                prososes = data.replace('<script>window.pageData=','')
                if is_json(prososes) :
                    array = json.loads(prososes)
                    jumlah_produk = array['mainInfo']['dataLayer']['page']['resultNr']
                    print('## Ada '+str(jumlah_produk)+' total produk')
                    ## list produk
                    produk = array['mods']['listItems']
                    ## harga terakhir dari page yang di ekses
                    hargalopbak = int(re.sub("[^0-9]", "",array['mods']['listItems'][1-len(produk)]['priceShow']))
                    if hargalop == hargalopbak :
                        hargalop += 1
                    else :
                        hargalop = hargalopbak
                    for x in produk :
                        for u in x['thumbs'] :
                            if u.get('image') :
                                gambarku.append(u.get('image'))
                        gambar_produk = '~'.join(gambarku)
                        id_produk = x.get('itemId')
                        link2 = x.get('productUrl').replace('//www','https://www')
                        nama_produk = x.get('name')
                        harga_produk = re.sub("[^0-9]", "",x.get('priceShow'))
                        merk = x.get('brandName')
                        rating = x.get('ratingScore')
                        penjual = x.get('sellerName')
                        lokasi = x.get('location')
                        for u in x.get('description') :
                            keterangannya.append(u)
                        keterangan = "\n".join(keterangannya)
                        kategori_produk = link
                        ## untuk simpan ke mysql database
                        if simpan_produk(id_produk,link2,nama_produk,gambar_produk,harga_produk,merk,rating,penjual,lokasi,keterangan,kategori_produk) :
                            berhasil += 1
                        else :
                            gagal += 1
                        gambarku = []
                        keterangannya = []

            else : 
                print('gagal ambil mungkin kena catcha')
                break
            if int(hargalop) >= int(termahal) :
                break
            print('Produk Berhasil di simpan : '+str(berhasil))
            print('Produk Gagal di simpan : '+str(gagal))
            print('====================')
    else :
        print('ada masalah di proxy')

def simpan_proxy(name) :
    data = requests.get('https://www.sslproxies.org/').text
    bs = BeautifulSoup(data,'html.parser')
    data = []
    table = bs.find('table')
    table_body = table.find('tbody')

    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])

    proxy = []
    for x in data :
        proxy.append(x[0]+":"+x[1])
    if proxy :
        print('simpan')
        tulisan = "\n".join(proxy)
        file = open(name+'.asr', 'w')
        file.write(tulisan)
        file.close()
    else: 
        print('gagal cek manual')

def ambil_proxy() :
    ## listproxy adalah nama filenya
    simpan_proxy('listproxy')

def run_kategori() :
    ## jalankan scraping kategori
    lazada_category()

def run_produk() :
    list_kategori = open('kategori.asr','r').read().split("\n")
    ##satu persatu
    # category = list_kategori[0]
    # lazada_produk(category)

    ##looping 
    for kategori in list_kategori :
        lazada_produk(kategori)




##############################################
### langkah - langkah 1 ###
# membuat mysql table kategori dan produk beserta colums
# buat_table_database()

### langkah - langkah 2 (opsional) #### 
# ambil list proxy ssl di https://www.sslproxies.org/
# menghasilkan file ouput listproxy.asr yang nantinya akan di gunakan jika ada blokir captcha
# ambil_proxy()

### langkah - langkah 2 ####
# scraping kategori
# menghasilkan file ouput kategori.asr 
# dan menyimpan di database dengan table kategori
# run_kategori()

### langkah - langkah 3 #### 
# scraping kategori yang ada di list kategori.asr
# kemudian simpan di database dengan table produk
# run_produk()

## Configuration ##
# untuk hapus semua file log kategori dan listproxy
# hapus_data()

# untuk hapus table produk dan kategori
# hapus_table_database()

################################################