import json,requests,time,re,mysql.connector,os
from tqdm import tqdm
from bs4 import BeautifulSoup

def is_json(myjson):
    try:
        json.loads(myjson)
    except :
        return False
    return True

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

def savejsontext(nama,data) :
    tuliskan(nama,json.dumps(data, indent=4, sort_keys=True))

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS `blibli` (`produk_id` varchar(300) NOT NULL,`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`harga_view` varchar(30) NOT NULL,`harga_diskon` varchar(30) NOT NULL,`harga_asli` varchar(30) NOT NULL,`brand_nama` varchar(300) DEFAULT NULL,`brand_logo` varchar(300) DEFAULT NULL,`produk_garansi` varchar(300) DEFAULT NULL,`produk_ulasan` text,`produk_gambar` text,`keterangan` text,`keterangan_unik` text,`penjual` text,`penjual_poin` varchar(300) DEFAULT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    
def with_req_jadul(link) :
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except :
        return False
        
def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except :
        return False

def ambil_produk(id_unik) :
    #### ambil produk #########
    data_produk = with_re_jadulq('https://www.blibli.com/backend/product/products/'+id_unik+'/_summary')
    data_penjual = with_re_jadulq('https://www.blibli.com/backend/product/products/'+id_unik+'/_info')
    if data_produk and data_penjual :
        #=======================json===================
        if is_json(data_produk) and is_json(data_penjual) :
            pr = json.loads(data_produk)['data']
            pe = json.loads(data_penjual)['data']
            info = {
            'nama' : pe['merchant']['name'],
            'rating' : pe['merchant'].get('rating'),
            'location' : pe['merchant']['location'],
            'url' : pe['merchant']['url'],
            'luarnegri' : pe['merchant'].get('international'),
            }
            img_list = []
            for g in pr['images'] :
                img_list.append(g['full'])
            produk = {
            'nama' : pr['name'],
            'harga_view' : int(pe['price'].get('offered')),
            'harga_diskon' : pe['price'].get('discount'),
            'harga_asli' : int(pe['price'].get('listed')),
            'url' : pr['url'],
            'merek' : pr['brand'].get('name'),
            'merek_logo' : pr['brand'].get('logo'),
            'garansi' : pr['warranty'],
            'loyalpoin' : pe.get('loyaltyPoint'),
            'keterangan' : pr.get('description'),
            'keterangan_daripenjual' : pr.get('uniqueSellingPoint'),
            'gambar' : '~'.join(img_list),
            'ulasan' : json.dumps(pr['review']), #array
            'kategori' : json.dumps(pr['categories']), # array
            'sertifikasi' : json.dumps(pr['specifications']), #array
            'penjual' : json.dumps(info), # array
            }
            db = (id_unik,produk['nama'],produk['url'],produk['harga_view'],produk['harga_diskon'],produk['harga_asli'],produk['merek'],produk['merek_logo'],produk['garansi'],produk['ulasan'],produk['gambar'],produk['keterangan'],produk['keterangan_daripenjual'],produk['penjual'],produk['loyalpoin'])
            col = "INSERT IGNORE INTO blibli (produk_id,produk_nama,produk_link,harga_view,harga_diskon,harga_asli,brand_nama,brand_logo,produk_garansi,produk_ulasan,produk_gambar,keterangan,keterangan_unik,penjual,penjual_poin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
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
            tuliskan_jika('gagal_blokir',id_unik)
        #     return False
        #     print('ini bukan json')

        # # ================ xml =========================
        #     bs_produk = BeautifulSoup(data_produk,'lxml')
        #     bs_penjual = BeautifulSoup(data_penjual,'lxml')

        #     produk_data = bs_produk.find("data")
        #     penjual_data = bs_penjual.find("data")
        #     print(data_penjual)
        #     print("===================")
        #     print(data_produk)
        #     kategori_list = []
        #     for kategori in produk_data.find('categories').find_all('categories') :
        #         kategori_list.append({'url' : kategori.find('url').get_text(),'label' : kategori.find('label').get_text()})
        #     sertifikasi_list = []
        #     for s in produk_data.find('specifications').find_all('specifications') :
        #         sertifikasi_list.append({'nama' : s.find('name').get_text(),'nilai' : s.find('value').get_text()})
        #     warna_list = []
        #     if penjual_data.find('allattributes').find('warna').find('values').find_all('values') :
        #         for o in penjual_data.find('allattributes').find('warna').find('values').find_all('values') :
        #             warna_list.append(o.get_text())
        #         warna = "~".join(warna_list)
        #     else :
        #         warna = '-'
        #     penjual = {
        #         'nama' : penjual_data.find('merchant').find('name').get_text(),
        #         'rating' : penjual_data.find('merchant').find('rating').get_text(),
        #         'location' : penjual_data.find('merchant').find('location').get_text(),
        #         'url' : penjual_data.find('merchant').find('url').get_text(),
        #         'luarnegri' : penjual_data.find('merchant').find('international').get_text()
        #         }
        #     print(penjual)
        #     produk = {
        #         'nama' : produk_data.find('name').get_text(),
        #         'harga_view' : penjual_data.find('price').find('offered').get_text(),
        #         'harga_diskon' : penjual_data.find('price').find('discount').get_text(),
        #         'harga_asli' : penjual_data.find('price').find('listed').get_text(),
        #         'url' : produk_data.find('url').get_text(),
        #         'merek' : produk_data.find('brand').find('name').get_text(),
        #         'merek_logo' : produk_data.find('brand').find('logo').get_text(),
        #         'ulasan_rating' : produk_data.find('review').find('rating').get_text(),
        #         'ulasan_jumlah' : produk_data.find('review').find('count').get_text(),
        #         'garansi' : produk_data.find('warranty').get_text(),
        #         'kembalian' : penjual_data.find('services').find('services').get_text(),
        #         'loyalpoin' : penjual_data.find('loyaltypoint').get_text(),
        #         'keterangan' : produk_data.find('description').get_text(),
        #         'keterangan_daripenjual' : produk_data.find('uniquesellingpoint').get_text(),
        #         'kategori' : json.dumps(kategori_list, indent=4, sort_keys=True),
        #         'sertifikasi' : json.dumps(sertifikasi_list, indent=4, sort_keys=True),
        #         'warna' : warna,
        #         'penjual' : penjual,
        #     }
        #     print(produk)
    else :
        print('masalah jaringan')
        return False

def cari_id(id_kategori) :
    ####### ambil semua data produk dari kategori ############
    start = 0
    while True :
        sukses = 0
        gagal = 0
        link = 'https://www.blibli.com/backend/search/products?start='+str(start)+'&category='+id_kategori+'&sort=3'
        data_produk = with_req(link)
        if data_produk :
            array = json.loads(data_produk)
            if array['data'].get('products') :
                print("Kategori "+id_kategori+" || start "+str(start))
                for x in tqdm(array['data']['products']) :
                    if ambil_produk(x['formattedId']) :
                        sukses += 1
                    else :
                        gagal += 1
                    # print(x['formattedId'])
            else :
                print('Kategori in sudah selesai')
                print("========================")
                break
            start += len(array['data'].get('products'))
            print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
            print("==============")
    
def run_blibli() :
    ### ambil semua category ###########
    data_kategori = with_re_jadulq('https://www.blibli.com/getCategoryStructures')
    bs_ka = BeautifulSoup(data_kategori,'lxml')
    for x in bs_ka.find_all('c') :
        if '-' in x.get_text() :
            cari_id(x.get_text())

buat_table_database()
run_blibli()
