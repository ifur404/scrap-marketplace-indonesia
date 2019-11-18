import json,requests,os,time,re,mysql.connector
from tqdm import tqdm
from bs4 import BeautifulSoup


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
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

def savejsontext(nama,data) :
    tuliskan(nama,json.dumps(data, indent=4, sort_keys=True))

def database_setting() :
    return mysql.connector.connect(host="localhost",user="",passwd="",database="")

def buat_table_database() :
    mydb = database_setting()
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS `jualo` (`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`harga` varchar(30) NOT NULL,`dilihat` varchar(30) NOT NULL,`produk_kondisi` varchar(30) NOT NULL,`produk_gambar` text,`deskripsi` text,`spestifikasi` text,`penjual_nama` varchar(300) DEFAULT NULL,`penjual_url` varchar(300) DEFAULT NULL,`penjual_telepon` varchar(300) DEFAULT NULL,`penjual_alamat` varchar(300) DEFAULT NULL,`penjual_verif` varchar(300) DEFAULT NULL,`penjual_online` varchar(300) DEFAULT NULL,PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()
    
def with_req(link) :
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

def toint(harga) :
    return re.sub('[^0-9]','',harga)

def nomer_telpon_jualo(url) :
    slug = url.split('/iklan-')
    url = with_req('https://www.jualo.com/show_phone_numbers_ad?ad_slug='+slug[1])
    if url :
        return str(url[url.find('alt="')+5:url.find('"',url.find('alt="')+5)])
    else :
        return '-'

def ambil_gambar_jualo(data) :
    awal = data.find('var image_arr = ')
    if awal > 1:
        gambar = json.loads(data[awal:data.find('];',awal+1)].replace('var image_arr = ','')+']')
    return "~".join(gambar)

def jualo_detail(link) :
    data = with_req(link)
    if data :
        bs_data = BeautifulSoup(data,'html.parser')
        if bs_data.find('h1',{'class' : 'product-name'}) :
            info_anu = []
            for x in bs_data.find_all('div',{'class' : 'product-info__list'}) :
                info_anu.append(x.get_text().strip())
            spesifikasi_list = []
            for u in bs_data.find_all('div',{'class' : 'specification__list'}) :
                if u.find('div',{'class' : 'title'}) and  u.find('div',{'class' : 'col-7 pad-0'}) :
                    nama = u.find('div',{'class' : 'title'}).get_text().strip()
                    value =  u.find('div',{'class' : 'col-7 pad-0'}).get_text().strip()
                    spesifikasi_list.append({nama : value})
            if bs_data.find('span',{'class' : 'product-price-value'}) :
                harga = toint(bs_data.find('span',{'class' : 'product-price-value'}).get_text())
            else :
                harga = '-'
            barang = {
                'nama' : bs_data.find('h1',{'class' : 'product-name'}) .get_text(),
                'kondisi' : info_anu[0],
                'lokasi' : info_anu[1],
                'dilihat' : toint(info_anu[2]),
                'spesifikasi' : json.dumps(spesifikasi_list),
                'deskripsi' : bs_data.find('div',{'id' : 'tabDescription'}).get_text(),
                'gambar' : ambil_gambar_jualo(data),
            }
            online_t = bs_data.find('div',{'class' : 'user-contact-list'}).get_text().strip().split('Terakhir dilihat\n\n')
            if bs_data.find('div',{'class' : 'verified'}) :
                verif = bs_data.find('div',{'class' : 'verified'}).get_text().strip()
            elif bs_data.find('div',{'class' : 'unverified'}) :
                verif = bs_data.find('div',{'class' : 'unverified'}).get_text().strip()
            else :
                verif = '-'
            if len(online_t) > 1 :
                status_online = online_t[1]
            else :
                status_online = '-'
            penjual = {
                'nama' : bs_data.find('div',{'class' : 'user__name'}).a.get_text(),
                'link' : bs_data.find('div',{'class' : 'user__name'}).a.get('href'),
                'nomer_telpon' : nomer_telpo_jualon(link),
                'lokasi' : bs_data.find('div',{'class' : 'user__location'}).get_text().strip(),
                'online' : status_online,
            }
            db = (barang['nama'],link,harga,barang['dilihat'],barang['kondisi'],barang['gambar'],barang['deskripsi'],barang['spesifikasi'],penjual['nama'],penjual['link'],penjual['nomer_telpon'],penjual['lokasi'],verif,penjual['online'])
            col = "INSERT IGNORE INTO jualo (produk_nama,produk_link,harga,dilihat,produk_kondisi,produk_gambar,deskripsi,spestifikasi,penjual_nama,penjual_url,penjual_telepon,penjual_alamat,penjual_verif,penjual_online) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            mydb = database_setting()
            mycursor = mydb.cursor()
            mycursor.execute(col,db)
            mydb.commit()
            if mycursor.rowcount :
                return True
            else:
                tuliskan_jika('sudah',link)
                return False
            mydb.close()
        else :
            tuliskan_jika('judul_tidak_ada',link)
            return False
    else :
        tuliskan_jika('dilock',link)
        return False


def run_jualo() :
    data = with_req('https://www.jualo.com/semua/termurah')
    print('halaman ke 1')
    if data :
        sukses = 0
        gagal = 0
        bs_data = BeautifulSoup(data,'html.parser')
        for u in tqdm(bs_data.find_all('div',{'class' : 'product-item'})) :
            if jualo_detail(u.a.get('href')) :
                sukses += 1
            else :
                gagal += 1
        print('Sukses : '+str(sukses)+' || Gagal '+str(gagal))        
        print("=========================================")
        halaman = bs_data.find('span',{'class' : 'orange'}).get_text().strip()
        for x in range(2,int(halaman)) : # dimulai dari 2 karna yang pertama sudah kan di atas
            data2 = with_req('https://www.jualo.com/semua/termurah/?page='+str(x))
            print('halaman ke '+str(x)+' dari '+str(halaman))
            gagal = 0
            sukses = 0
            if data2 :
                bs_data2 = BeautifulSoup(data2,'html.parser')
                for u in tqdm(bs_data2.find_all('div',{'class' : 'product-item'})) :
                    if jualo_detail(u.a.get('href')) :
                        sukses += 1
                    else :
                        gagal += 1
                print('Sukses : '+str(sukses)+' || Gagal '+str(gagal))
                print("=========================================")
            else :
                print('gagal di ambil')
    else :
        print('ulangi')
    
buat_table_database()
run_jualo()