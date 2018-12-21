import urllib.request
from bs4 import BeautifulSoup
import time

def detail_crawling(url):
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    details = []
    text = soup.find("div", class_="detail")
    for d in text.find_all("p"):
        detail = str(d).replace("<p>", "").replace("<br/>", " ").replace("</p>", "").replace("&lt;", "<").replace("&gt;", ">")
        details.append(detail)
    return detail
    # return u'\n'.join(details)
def main():
    # URL 데이터를 가져올 사이트 url 입력
    # genre = ["episode", "omnibus", "story", "daily", "comic", "fantasy", "action", "drama","pure","sensibility","thrill","historical","sports"]
    order_option = ["update", "ViewCount", "StarScore", "TitleName"]
    url = "https://comic.naver.com/webtoon/finish.nhn"

    # if j != -1:
    # url = url + "?order=" + order_option[1]

    # req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    webtoon_list = []
    context = soup.find("ul", class_="img_list")
    count = 0
    for x in context.find_all("li"):
        link = "https://comic.naver.com" + x.find("a")["href"]
        title = x.find("a")["title"]
        author = x.find("dd", class_="desc").get_text().strip()
        detail = detail_crawling(link)

        webtoon_info = dict()
        rate = x.find_all("div", class_="rating_type")
        for r in rate:
            score = r.find("strong").get_text()

        webtoon_info["title"] = title
        webtoon_info["author"] = author
        webtoon_info["score"] = score
        webtoon_info["detail"] = detail
        webtoon_list.append(webtoon_info)
        if count == 9:
            break
        else:
            count = count + 1
    for xx in webtoon_list:
        print(xx)
    # print(webtoon_list)


if __name__ == "__main__":
    main()
