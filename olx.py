import json,requests,os,time,re,mysql.connector
from tqdm import tqdm
from bs4 import BeautifulSoup

def is_json(myjson):
    try:
        json.loads(myjson)
    except :
        return False
    return True

def hargatoint(harga) :
    return re.sub('[^0-9]','',harga)

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
    mycursor.execute("CREATE TABLE IF NOT EXISTS `olx` (`produk_id` varchar(100) NOT NULL,`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`harga` varchar(30) NOT NULL,`dilihat` varchar(30) NOT NULL,`lokasi` varchar(30) NOT NULL,`gambar` text,`deskripsi` text,`spestifikasi` text,`penjual_nama` varchar(300) DEFAULT NULL,`penjual_url` varchar(300) DEFAULT NULL,`penjual_telepon` varchar(300) DEFAULT NULL,`penjual_verif` varchar(300) DEFAULT NULL,`penjual_gabung` varchar(300) DEFAULT NULL,kategori_nama varchar(300) NOT NULL,kategori_link varchar(300) NOT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()
    
def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def with_req_telpon(link,ref) :
    headers = {
        'Host' : 'm.olx.co.id',
        'User-Agent' : 'Mozilla/5.0 (Linux; Android 7.0; PLUS Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.98 Mobile Safari/537.36',
        'Accept' : '*/*',
        'Accept-Language' : 'en-US,en;q=0.5',
        'Accept-Encoding' : 'gzip, deflate, br',
        'Referer' : ref,
        'X-Requested-With' : 'XMLHttpRequest',
        'Connection' : 'keep-alive',
        'Pragma' : 'no-cache',
        'Cache-Control' : 'no-cache',
        'TE' : 'Trailers',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def toint(harga) :
    return re.sub('[^0-9]','',harga)

def jumlah_page_olx(bs_data) :
    page_ye = bs_data.find_all('a',{'class' : 'block br3 brc8 large tdnone lheight24'})
    return toint(page_ye[len(page_ye)-1].get_text())

def nomer_telpon(id,ref) :
    url = with_req_telpon('https://m.olx.co.id/adcontact/getcontact/?id='+str(id)+'&type=sms',ref)
    if is_json(url) :
        array = json.loads(url)
        if array.get('status') == 'success' :
            return array['data'].get('value')
        else :
            return '-'
    else :
        return '-'

def olx_detail(link,catname,catlink) :
    print(link)
    data = with_req(link)
    bs_data = BeautifulSoup(data,'html.parser')
    if bs_data.find('h1',{'itemprop' : 'name'}) and bs_data.find('span',{'itemprop' : 'price'}) :
        dilihat = bs_data.find_all('div',{'class' : 'pdingtop10'})
        gambar_list = []
        for x in bs_data.find_all('li',{'class' : 'fleft'}) :
            gambar_list.append(x.a.get('href'))
        barang = {
            'nama' : bs_data.find('h1',{'itemprop' : 'name'}).get_text().strip(),
            'harga' : toint(bs_data.find('span',{'itemprop' : 'price'}).get_text()),
            'lokasi' : bs_data.find('strong',{'class' : 'c2b small'}).a.get_text().strip(),
            'id' : bs_data.find('span',{'class' : 'rel inlblk'}).get_text().strip(),
            'spesifikasi' : str(bs_data.find('ul',{'class' : 'spesifikasi'})),
            'description' : bs_data.find('span',{'itemprop' : 'description'}).get_text(),
            'dilihat' : toint(dilihat[1].get_text()),
            'gambar' : "~".join(gambar_list),
        }
        if bs_data.find('text',{'class' : 'badge_phonever_text'}) :
            verif = bs_data.find('text',{'class' : 'badge_phonever_text'}).get_text()
        else :
            verif = 'Tidak'
        if bs_data.find('span',{'class' : 'block color-5 brkword xx-large'}) :
            penjual = {
                'nama' : bs_data.find('span',{'class' : 'block color-5 brkword xx-large'}).get_text(),
                'gabung' : bs_data.find('span',{'class' : 'block color-5 normal margintop5 sinceline'}).get_text(),
                'url' : bs_data.find('a',{'data-event' : 'np_click_lister_profile'}).get('href'),
                'nomer' : nomer_telpon(barang['id'],link.replace('www.','m.'))
            }
        else :
            penjual = {
                'nama' : '-',
                'gabung' : '-',
                'url' : '-',
                'nomer' : '-',
            }
        db = (barang['id'],barang['nama'],link,barang['harga'],barang['dilihat'],barang['lokasi'],barang['gambar'],barang['description'],barang['spesifikasi'],penjual['nama'],penjual['url'],penjual['nomer'],verif,penjual['gabung'],catlink,catname)
        col = "INSERT IGNORE INTO olx (produk_id,produk_nama,produk_link,harga,dilihat,lokasi,gambar,deskripsi,spestifikasi,penjual_nama,penjual_url,penjual_telepon,penjual_verif,penjual_gabung,kategori_nama,kategori_link) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
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
        tuliskan_jika('linkerror',link)
        return False

def sub_kat2(bs_data):
    # sub kategori
    if bs_data.find('li',{'class' : 'visible'}) :
        for x in bs_data.find_all('li',{'class' : 'visible'}) :
            nama_sub = x.a.get_text().strip()
            link_sub = x.a.get('href')
            print('Halaman dari sub kategori : '+nama_sub)
            data = with_req(link_sub)
            if data :
                bs_data = BeautifulSoup(data,'html.parser')
                print('Halaman 1')
                print(link_sub)
                sukses = 0
                gagal = 0
                for u in tqdm(bs_data.find_all('a',{'class' : 'marginright5 link linkWithHash detailsLink'})) :
                    if olx_detail(u.get('href')[: u.get('href').find('html')+4],link_sub,nama_sub) :
                        sukses += 1
                    else :
                        gagal += 1
                print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
                print('=========================')
                
                jumlah_halaman = jumlah_page_olx(bs_data)
                for i in range(2,int(jumlah_halaman)+1) :
                    data = with_req(link_sub+'?page='+str(i))
                    if data :
                        bs_data = BeautifulSoup(data,'html.parser')
                        print('Halaman '+str(i)+' of '+str(jumlah_halaman))
                        print(link_sub+'?page='+str(i))
                        sukses = 0
                        gagal = 0
                        for u in tqdm(bs_data.find_all('a',{'class' : 'marginright5 link linkWithHash detailsLink'})) :
                            if olx_detail(u.get('href')[: u.get('href').find('html')+4],link_sub,nama_sub) :
                                sukses += 1
                            else :
                                gagal += 1
                        print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
                        print('=========================')

def sub_kat(bs_data):
    # sub kategori
    if bs_data.find('li',{'class' : 'visible'}) :
        for x in bs_data.find_all('li',{'class' : 'visible'}) :
            nama_sub = x.a.get_text().strip()
            link_sub = x.a.get('href')
            print('Halaman dari sub kategori : '+nama_sub)
            data = with_req(link_sub)
            if data :
                bs_data = BeautifulSoup(data,'html.parser')
                print('Halaman 1')
                print(link_sub)
                sukses = 0
                gagal = 0
                for u in tqdm(bs_data.find_all('a',{'class' : 'marginright5 link linkWithHash detailsLink'})) :
                    if olx_detail(u.get('href')[: u.get('href').find('html')+4],link_sub,nama_sub) :
                        sukses += 1
                    else :
                        gagal += 1
                print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
                print('=========================')
                
                jumlah_halaman = jumlah_page_olx(bs_data)
                for i in range(2,int(jumlah_halaman)+1) :
                    data = with_req(link_sub+'?page='+str(i))
                    if data :
                        bs_data = BeautifulSoup(data,'html.parser')
                        print('Halaman '+str(i)+' of '+str(jumlah_halaman))
                        print(link_sub+'?page='+str(i))
                        sukses = 0
                        gagal = 0
                        for u in tqdm(bs_data.find_all('a',{'class' : 'marginright5 link linkWithHash detailsLink'})) :
                            if olx_detail(u.get('href')[: u.get('href').find('html')+4],link_sub,nama_sub) :
                                sukses += 1
                            else :
                                gagal += 1
                        print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
                        print('=========================')
                sub_kat2(bs_data)

def kategori_olx(link,catname) :
    data = with_req(link)
    if data :
        bs_data = BeautifulSoup(data,'html.parser')
        print('Halaman 1')
        print(link)
        sukses = 0
        gagal = 0
        for u in tqdm(bs_data.find_all('a',{'class' : 'marginright5 link linkWithHash detailsLink'})) :
            if olx_detail(u.get('href')[: u.get('href').find('html')+4],link,catname) :
                sukses += 1
            else :
                gagal += 1
        print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
        print('=========================')
        
        jumlah_halaman = jumlah_page_olx(bs_data)
        for i in range(2,int(jumlah_halaman)+1) :
            data = with_req(link+'?page='+str(i))
            if data :
                bs_data = BeautifulSoup(data,'html.parser')
                print('Halaman '+str(i)+' of '+str(jumlah_halaman))
                print(link+'?page='+str(i))
                sukses = 0
                gagal = 0
                for u in tqdm(bs_data.find_all('a',{'class' : 'marginright5 link linkWithHash detailsLink'})) :
                    if olx_detail(u.get('href')[: u.get('href').find('html')+4],link,catname) :
                        sukses += 1
                    else :
                        gagal += 1
                print('Sukses : '+str(sukses)+' || Gagal : '+str(gagal))
                print('=========================')
        sub_kat(bs_data)
    else :
        print('ga bisa di ambil')
    
def run_olx() :
    data = with_req('https://www.olx.co.id')
    if data :
        bs_data = BeautifulSoup(data,'html.parser')
        for x in bs_data.find_all('a',{'class' : 'tdnone'}) :
            if '/kategori/' in x.get('href') and x.find('span',{'class' : 'link block'}) :
                kategori_olx(x.get('href').replace('/kategori/','/'),x.get_text().strip())
    else :
        print('coba lagi')

buat_table_database()
run_olx()
