import json
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup
from tqdm import tqdm

def is_json(myjson):
    try :
        json.loads(myjson)
    except :
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
    mycursor.execute("CREATE TABLE IF NOT EXISTS `jdid` (`produk_id` varchar(300) NOT NULL,`produk_nama` varchar(300) NOT NULL,`produk_link` varchar(300) NOT NULL,`produk_harga` varchar(30) NOT NULL,`produk_milik` varchar(30) DEFAULT NULL,`produk_berat` varchar(30) DEFAULT NULL,`garansi_priode` varchar(30) DEFAULT NULL,`ulasan_total` varchar(30) DEFAULT NULL,`bintang_satu` varchar(30) DEFAULT NULL,`bintang_dua` varchar(30) DEFAULT NULL,`bintang_tiga` varchar(30) DEFAULT NULL,`bintang_empat` varchar(30) DEFAULT NULL,`bintang_lima` varchar(30) DEFAULT NULL,`kategori_link` varchar(300) NOT NULL,`kategori_nama` varchar(300) NOT NULL,`produk_gambar` text,`produk_keterangan` text,`produk_rank` text,`penjual_alamat` text,`penjual_nama` varchar(100),PRIMARY KEY (`produk_link`)) ENGINE=InnoDB DEFAULT CHARSET=latin1;")
    mydb.close()
    
def with_req(link) :
    headers = {
        'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'no-cache',
        }
    try:
        return requests.get(link,headers=headers,timeout=10,verify=True).text   
    except requests.exceptions.RequestException as e:
        return False

# def potong(data) :
#     awal = data.find('window.__data = {')
#     if awal > 1 :
#         akhir = data.find('}}};')
#         data = data[awal:akhir]+'}}}'
#         prososes = data.replace('window.__data = ','')
#         if is_json(prososes) :
#             return json.loads(prososes)
#         else :
#             return False
#     else :
#         return False

def potong_produk_m_jdid(data) :
    if data.find('<script>var pageModel=') > 1 :
        awal = data.find('<script>var pageModel=')
        akhir = data.find('};</script>')
        data = data[awal:akhir]+'}'
        prososes = data.replace('<script>var pageModel=','')
        if is_json(prososes) :
            return json.loads(prososes)
        else :
            return False
    else :
        return False

def potong_produk_d_jdid(data) :
    if data.find('additional: ') > 1 :
        awal = data.find('additional: ')
        akhir = data.find(']},')
        data = data[awal:akhir]+']}}'
        prososes = data.replace('additional: ','')
        if is_json(prososes) :
            return json.loads(prososes)
        else :
            return False
    else :
        return False

# def kategori() :
#     data = with_req('https://www.jd.id/')
#     awal = data.find('HOMEDATAFORFLOOR["floorLayout"] = [')
#     kategori = []
#     if awal > 1 :
#         akhir = data.find('];',awal+1)
#         data = '['+data[awal:akhir].replace('HOMEDATAFORFLOOR["floorLayout"] = [','')+']'
#         if is_json(data) :
#             array = json.loads(data)
#             for x in array :
#                 for kiri in x['modules']['left'][4]['params']['data'] :
#                     kategori.append({'nama' : kiri['hotWords'],'url' : kiri['url']})          

#                 for kanan in x['modules']['right'][1]['params']['data'] :
#                     kategori.append({'nama' : kanan['hotWords'],'url' : kanan['url']})
#     for k in kategori :
#         # if '.html' in k['url']
#         #     tuliskan('kategori_html',k['url'])
#         # else if 'keywords' in k['url'] :
#         #     tuliskan('kategori_keywords',k['url']) 
#         # else if 'sale.jd' in k['url'] :
#         #     tuliskan('kategori_sale')
#         if '/category/' in k['url'] :
#             tuliskan('kategori_bener',k['url'])
        
    # savejsontext('kategorilist',kategori)
    # return kategori


def scrap_jdid(link,kategori_link) :
    mydb = database_setting()
    mycursor = mydb.cursor()
    data = with_req(link.replace('www.','m.'))
    data_d = with_req(link)
    if data_d and data :
        d_produk = potong_produk_d_jdid(data_d)
        if d_produk is False :
            return False
        produk = potong_produk_m_jdid(data)
        if produk is False :
            return False
        produk_keterangan = d_produk.get('description')
        produk_rank = json.dumps(d_produk['vender']['venderRank'],indent=4, sort_keys=True)
        penjual_alamat = produk['city'].get('area_id')
        penjual_nama = produk['wareVO'].get('salerName')
        produk_nama = produk['wareVO']['title']
        produk_merek = produk.get('brandName')
        produk_gambar = "~".join(produk['skuPicList']) # https://img10.jd.id/Indonesia/
        produk_harga = produk['skuVO']['costPrice']['amount']
        produk_berat = produk['skuVO']['weight']
        kategori_nama = produk['pageParam'].get('categoryName')
        produk_milik = produk['wareVO'].get('propertyRight')
        garansi_priode = produk['wareVO'].get('warrantyPeriod') #https://m.jd.id/ware/warranty?code=5
        wareid = produk['wareVO']['wareId']
        review = with_req('https://m.jd.id/wareDetail/comment?dataType=JSON&wareId='+str(wareid)+'&pageSize=10&pageIndex=1')
        if is_json(review) :
            produk_review = json.loads(review)
            ulasan_total = produk_review.get('totalItem')
            if produk_review.get('commentCountVO') :
                bintang_satu = produk_review['commentCountVO'].get('oneStar')
                bintang_dua = produk_review['commentCountVO'].get('twoStar')
                bintang_tiga = produk_review['commentCountVO'].get('threeStar')
                bintang_empat = produk_review['commentCountVO'].get('fourStar')
                bintang_lima = produk_review['commentCountVO'].get('fiveStar')
            else :
                bintang_satu = '0'
                bintang_dua = '0'
                bintang_tiga = '0'
                bintang_empat = '0'
                bintang_lima = '0'
        else :
                bintang_satu = '0'
                bintang_dua = '0'
                bintang_tiga = '0'
                bintang_empat = '0'
                bintang_lima = '0'
        db = (wareid,produk_nama,link,produk_harga,produk_milik,produk_berat,garansi_priode,ulasan_total,bintang_satu,bintang_dua,bintang_tiga,bintang_empat,bintang_lima,kategori_link,kategori_nama,produk_gambar,produk_keterangan,produk_rank,penjual_alamat,penjual_nama)
        col = "INSERT IGNORE INTO jdid (produk_id,produk_nama,produk_link,produk_harga,produk_milik,produk_berat,garansi_priode,ulasan_total,bintang_satu,bintang_dua,bintang_tiga,bintang_empat,bintang_lima,kategori_link,kategori_nama,produk_gambar,produk_keterangan,produk_rank,penjual_alamat,penjual_nama) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mycursor.execute(col,db)
        mydb.commit()
        if mycursor.rowcount :
            return True
        else:
            return False
        mydb.close()
    else :
        return False

def kumpul_produk_jdid(linknya) :
    page = 0
    gagalwae = 0
    while True :
        sukses = 0
        gagal = 0
        page += 1
        link = linknya+'?searchtype=sh&sortType=sort_lowprice_asc&pageSize=10&page='+str(page)
        print(link)
        url = with_req(link)
        if url :
            bs = BeautifulSoup(url,'html.parser')
            if 'not match' in bs.title.string :
                print('halaman tidak ada list. lanjut kategorinnya')
                print("=============================================")
                break
            else :
                for x in tqdm(bs.find_all('div',{'class' : 'p-pic'})) :
                    if x.a :
                        link = x.a.get('href').replace('//www','https://www')
                        if scrap_jdid(link,linknya) :
                            sukses += 1
                        else :
                            gagal += 1
                print('Sukses : '+str(sukses)+' || Gagal '+str(gagal))
                print("============================================")
            gagalwae = 0
        else :
            gagalwae += 1
            if gagalwae == 3 :
                break

def run_jdid() :
    data = with_req('https://www.jd.id/map/sitemap.html')
    bs = BeautifulSoup(data,'html.parser')
    sitemap = bs.find('div',{'id' : 'sitemap'})
    for x in sitemap.find_all('a',{'target' : '_blank'}) :
        if '/category/' in x.get('href') :
            if x.get('href') :
                kumpul_produk_jdid(x.get("href").replace('//www','https://www'))

buat_table_database()
run_jdid()
