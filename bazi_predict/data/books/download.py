import os
import requests
from urllib.parse import quote

# Directory
SAVE_DIR = "bazi_predict/data/books"
os.makedirs(SAVE_DIR, exist_ok=True)

# Books Layout: Name -> Raw URL
# Note: GitHub Raw URLs often need precise encoding
BOOKS = {
    "渊海子平.txt": "https://raw.githubusercontent.com/Jeremyzjj/books/master/国学/八字- 渊海子平.txt",
    "三命通会.txt": "https://raw.githubusercontent.com/kvnbox/classic-texts/master/三命通会.txt", 
    # Fallback to a different repo if mymmsc is not straight forward
}

# Alternative known good sources or use a proxy if needed.
# Let's try to construct the Jeremyzjj link carefully.
# https://github.com/Jeremyzjj/books/blob/master/国学/八字- 渊海子平.txt
# Raw: https://raw.githubusercontent.com/Jeremyzjj/books/master/国学/八字-%20渊海子平.txt

def download_file(filename, url):
    print(f"Downloading {filename} from {url}...")
    try:
        # Auto-encode the path part if requests doesn't handle it (requests usually handles it well)
        # But for 'raw.githubusercontent', we need to be careful with spaces.
        
        resp = requests.get(url)
        if resp.status_code == 200:
            path = os.path.join(SAVE_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"Success: Saved to {path} ({len(resp.text)} chars)")
        else:
            print(f"Failed: {resp.status_code}")
            # Fallback: Create a sample file so the app doesn't crash
            create_sample(filename)
    except Exception as e:
        print(f"Error: {e}")
        create_sample(filename)

def create_sample(filename):
    print(f"Creating sample for {filename}")
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("此为《" + filename.replace('.txt','') + "》的试读样本。\n由于网络原因，完整版下载失败，请手动替换此文件。\n\n第一章 论五行生克\n五行者，金木水火土也...")

if __name__ == "__main__":
    # URL 1: Yuan Hai Zi Ping
    # Encode only the path parts that are non-ascii? Requests might do it.
    # We'll try the direct string first.
    url1 = "https://raw.githubusercontent.com/Jeremyzjj/books/master/%E5%9B%BD%E5%AD%A6/%E5%85%AB%E5%AD%97-%20%E6%B8%8A%E6%B5%B7%E5%AD%90%E5%B9%B3.txt"
    download_file("渊海子平.txt", url1)
    
    # URL 2: San Ming Tong Hui
    # Try a different one if mymmsc failed. 
    # Let's try a standard classical text repo
    url2 = "https://raw.githubusercontent.com/garychowcmu/daodejing/master/sanmingtonghui.txt" 
    # That was a guess. Let's use the one we tried but properly encoded.
    # mymmsc/books/master/三命通会.txt
    url2_real = "https://raw.githubusercontent.com/mymmsc/books/master/%E4%B8%89%E5%91%BD%E9%80%9A%E4%BC%9A.txt"
    download_file("三命通会.txt", url2_real)
