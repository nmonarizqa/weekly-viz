'''
Ini adalah script untuk mengubah pdf lampiran hasil CPNS jadi csv
Caveat: kalo langsung prosess 20rb halaman, agak keselek di tengah, jadi mending di-iterate beberapa halaman
Saya yakin ada cara yang lebih elegan. Feel free to give me any suggestions

Cara run 
python export_data_to_csv.py index_halaman_start index_halaman_end

Misal
python export_data_to_csv.py 0 100
'''

import pdfplumber
import pandas as pd
import datetime as dt
import sys

def check_for_detail_tables(page):
    '''
    Fungsi untuk mengecek keberadaan tabel perorangan
    Input: page (ex: pdf.pages[0])
    Output: 
        - found (binary, iya tidaknya sebuah halaman punya tabel perorangan)
        - df_returned (tabel perorangan jika ada)
    '''
    found = False
    df_returned = pd.DataFrame()
    for table in page.extract_tables():
        df = pd.DataFrame(table)
        if (df.shape[1] == 11) & (df.shape[0]>16):
            found = True
            df_returned = df
    return found, df_returned

def check_for_jabatan(page):
    '''
    Fungsi untuk mengecek keberadaan informasi lowongan
    Input: page (ex: pdf.pages[0])
    Output: 
        - dicitionary berisi informasi lowongan
    '''
    if "Lokasi Formasi :" in page.extract_text():
        text = page.extract_text()
        pendidikan = page.extract_tables()[1][0][1]
        jabatan_strings = text.split("Jabatan : ")[1].split("Lokasi")[0]
        lokasi_front = ""
        jabatan = jabatan_strings.split("\n")[0]

        if len(jabatan_strings.split("\n")) > 1:
            lokasi_front = " ".join(jabatan_strings.split("\n")[1:])
        lokasi_string = text.split("Lokasi Formasi : ")[1].split("Jenis")[0]
        if len(lokasi_string.split("\n")) > 2:
            lokasi_back = " ".join(lokasi_string.split("\n")[1:])
        else:
            lokasi_back = lokasi_string.split(" - ")[1]

        return {
            "kode_jabatan": jabatan.split(" - ")[0],
            "jabatan": jabatan.split(" - ")[1],
            "kode_lokasi": lokasi_string.split(" - ")[0],
            "lokasi_formasi": lokasi_front+lokasi_back,
            "jenis_formasi": text.split("Jenis Formasi : ")[1].split("\n")[0],
            "pendidikan": pendidikan
        }
    else:
        return {}

def get_info_from_table(df_):
    '''
    Fungsi untuk mengekstrak informasi dari tabel perorangan 
    Input: df_ (dataframe tabel perorangan)
    Output: 
        - dicitionary berisi informasi perorangan yang telah diekstrak
    '''
    skd = df_.iloc[7:10,[1,3]]
    skb = df_.iloc[13:,[1,3,4,5,6]]

    skd_dict = skd.set_index(1)[3].to_dict()
    skb_dict = skb.set_index(1)[3].to_dict()

    bobot_skb = skb.set_index(1)[5]
    bobot_skb.index = ["bobot_"+x for x in bobot_skb.index]
    bobot_skb = bobot_skb.to_dict()

    final_skb = skb.set_index(1)[6]
    final_skb.index = ["final_"+x for x in final_skb.index]
    final_skb = final_skb.to_dict()

    base_data =  {
        "no_peserta": df_.iloc[1,1],
        "kode_pendidikan": df_.iloc[1,2],
        "tanggal_lahir": df_.iloc[1,8],
        "ipk": df_.iloc[1,10],
        "keterangan": df_.iloc[7,10],
        "total_skd": df_.iloc[7,5],
        "total_skd_skala_100": df_.iloc[7,7],
        "total_skd_dengan_bobot": df_.iloc[7,8],
        "total_skd": df_.iloc[13,7],
        "total_skb_dengan_bobot": df_.iloc[13,8],
        "total_nilai_akhir": df_.iloc[7,9]
    }

    return {**base_data, **skd_dict, **skb_dict, **bobot_skb, **final_skb}

def split_df(df_):
    '''
    Fungsi untuk split tabel perorangan. Kadang ada satu halaman dengan lebih dari satu tabel.
    Input: df_ (dataframe tabel perorangan)
    Output: 
        - list berisi beberapa dataframe untuk tiap individu
    '''
    dfs = []
    header_indexes = list(df_[df_[1]=="No Peserta"].index)
    header_indexes.append(len(df_))
    for i in range(len(header_indexes)-1):
        splitted_df = df_.iloc[header_indexes[i]: header_indexes[i+1], :]
        splitted_df.index = range(len(splitted_df))
        dfs.append(splitted_df)
    return dfs

if __name__ == "__main__":
    start_index = int(sys.argv[1])
    end_index = int(sys.argv[2])
    export_filename = "cpns_"+str(start_index)+"_"+str(end_index)+".csv"
    pdf = pdfplumber.open('4b. Pengumuman Hasil SKB.pdf')

    # start iterating
    result = []
    last_jabatan = {}

    start_time = dt.datetime.now()
    for i in range(start_index, end_index):
        pg = pdf.pages[i]

        # jika halaman tsb ada info tentang lowongan, simpan
        current_jabatan = check_for_jabatan(pg)
        if current_jabatan != {}:
            last_jabatan = current_jabatan
        
        is_detail_found, detail_df = check_for_detail_tables(pg)
        # jika ketemu ada tabel perorangan
        if is_detail_found:
            splitted_df = split_df(detail_df)
            for df_ in splitted_df:
                details = get_info_from_table(df_)
                if current_jabatan == {}:
                    # kalo ada info lowongan di halaman yang sama, pakai info lowongan tsb
                    details.update(last_jabatan)
                else:
                    # kalo ga, pake info lowongan terakhir
                    details.update(current_jabatan)
                    last_jabatan = current_jabatan
                result.append(details)

        # untuk logging
        if i%100 == 99:
            curr_time = dt.datetime.now()
            print("Done for "+str(i), curr_time-start_time)
            start_time = dt.datetime.now()

    res = pd.DataFrame(result)
    res.to_csv(export_filename)

        





