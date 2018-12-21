import urllib.request
from bs4 import BeautifulSoup

def main():
    # URL 데이터를 가져올 사이트 url 입력
    url = "https://comic.naver.com/webtoon/creation.nhn"

    # req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    ff = '마음의소리'
    fff = '쌉니다 천리마마트'
    # webtoon_list = []
    # link_list =[]
    title_link = dict()
    context = soup.find("div", class_="webtoon")
    for x in context.find_all("div",class_="thumb"):
        link = "https://comic.naver.com" + x.find("a")["href"]
        title = x.find("a")["title"]
        title_link[title] = link

    # print(title_link)
    if ff in title_link:
        print("link: ", title_link[ff])
    else:
        print("다시 한번 검색해주세요")

    if fff in title_link:
        print(title_link[fff])
    else:
        print("없습니다")
    # print(fff in title_link)
    # print(ff in title_link)
    # print(webtoon_list)
    # print(link_list)

if __name__ == "__main__":
    main()