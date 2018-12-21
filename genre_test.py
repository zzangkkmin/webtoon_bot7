import urllib.request
from bs4 import BeautifulSoup
import time

def detail_crawling(url):
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    details = []
    for text in soup.find_all("div", class_="detail"):
        for d in text.find_all("p"):
            detail = str(d).replace("<p>", "").replace("<br/>", " ").replace("</p>", "").replace("&lt;", "<").replace(
                "&gt;", ">")
            details.append(detail)
    return detail
    # return u'\n'.join(details)
def main():
    # URL 데이터를 가져올 사이트 url 입력
    order_option = ["update","ViewCount","StarScore"]
    genre = ["episode", "omnibus", "story", "daily", "comic", "fantasy", "action", "drama","pure","sensibility","thrill","historical","sports"]
    url = "https://comic.naver.com/webtoon/genre.nhn?genre=" + genre[0]

    #if) 순서옵션이 존재할 경우
    url = url + "&order=" + order_option[0]
    print(url)
    # req = urllib.request.Request(url)
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    webtoon_list = []
    context = soup.find("ul", class_="img_list")
    for x in context.find_all("li"):
        link = "https://comic.naver.com" + x.find("a")["href"]
        title = x.find("a")["title"]
        author = x.find("dd", class_="desc").get_text().strip()
        detail = detail_crawling(link)
        finished = x.find("img", class_="finish")
        if finished != None:
            finished= finished["alt"]
        # print(finished)

        webtoon_info = dict()

        rate = x.find_all("div", class_="rating_type")
        for r in rate:
            score = r.find("strong").get_text()

        webtoon_info["title"] = title
        webtoon_info["author"] = author
        webtoon_info["score"] = score
        webtoon_info["detail"] = detail
        webtoon_info["finished"] = finished
        webtoon_list.append(webtoon_info)
    print(webtoon_list)


if __name__ == "__main__":
    main()
