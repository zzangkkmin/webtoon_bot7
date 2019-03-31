import json
# import os
# import re
import urllib.request
import datetime
import random
# import csv

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxp-503773686820-505524094661-510626696903-0a41749399898b1902ee2424b705c930"
slack_client_id = "503773686820.508540083143"
slack_client_secret = "e6b52f65c372a6167d400d73d7b3e6ea"
slack_verification = "UwOM1Lv0i8AmqMslilS124so"
sc = SlackClient(slack_token)

his_dict = {}

#img 가져오기
def img_crawling(url):
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    comic_info = soup.find("div", class_="comicinfo")
    src = comic_info.find("div", class_="thumb").find("img")["src"]

    return src

# 신규 웹툰 카테고리(요일)
def category_day_crawling(url):
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    spot = soup.find("ul", class_="category_tab")
    category_tab = spot.find_all("li")

    category = []
    for lst in category_tab:
        if lst["class"][0] == 'on':
            category.append(lst.find("a").get_text())
            break

    return u'\n'.join(category)

# 신규 웹툰(추천)
def _crawl_new_recom_webtoon():
    url = "https://comic.naver.com/webtoon/weekday.nhn"
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    spot = soup.find("div", class_="webtoon_spot2")
    banner = spot.find("h3").get_text()

    tit_recom = spot.find_all("strong")
    tlst = []
    for lst in tit_recom:
        tlst.append(lst["title"])

    hyp_recom = spot.find_all("a")
    hlst = []
    for lst in hyp_recom:
        if "/list.nhn" in lst["href"]:
            hlst.append(lst["href"])

    slst = []
    dlst = []
    for l in hlst:
        link = "https://comic.naver.com" + l
        dlst.append(category_day_crawling(link))
        slst.append(img_crawling(link))

    aut_recom = spot.find_all("p", class_="author2")
    alst = []
    for lst in aut_recom:
        alst.append(lst.find("a")["title"])

    lst_new_recom = []
    for i in range(len(tlst)):
        R = str(hex(random.randrange(0, 256)))[2:]
        G = str(hex(random.randrange(0, 256)))[2:]
        B = str(hex(random.randrange(0, 256)))[2:]

        # slack message builder 형식에 맞춰서 dictionary 생성
        tmp = {}
        tmp["color"] = '#' + R + G + B
        tmp["title"] = tlst[i]
        tmp["title_link"] = "https://comic.naver.com" + hlst[i]
        tmp["text"] = "{} | ".format(alst[i]) + "{}".format(dlst[i])
        tmp["thumb_url"] = slst[i]

        lst_new_recom.append(tmp)

    return (banner, lst_new_recom)


# 오늘의 웹툰(추천)
def _crawl_today_recom_webtoon():
    week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    r = datetime.datetime.today().weekday()

    url = "https://comic.naver.com/webtoon/weekdayList.nhn?week=" + week[r]
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    spot = soup.find("div", class_="webtoon_spot")

    sub_tit = spot.find("h3").get_text()
    banner = sub_tit[:8] + " " + sub_tit[8:]

    tit_recom = spot.find_all("div", class_="thumb")
    tlst = []
    for lst in tit_recom:
        tlst.append(lst.find("a")["title"])

    hyp_recom = spot.find_all("a")
    hlst = []
    for lst in hyp_recom:
        if "/list.nhn" in lst["href"]:
            hlst.append(lst["href"])

    aut_recom = spot.find_all("dd", class_="desc")
    alst = []
    for lst in aut_recom:
        alst.append(lst.find("p").find("a")["title"])

    rat_recom = spot.find_all("div", class_="rating_type2")
    rlst = []
    for lst in rat_recom:
        rlst.append(lst.find("strong").get_text())

    slst = []
    for l in hlst:
        link = "https://comic.naver.com" + l
        slst.append(img_crawling(link))

    lst_today_recom = []
    for i in range(len(tlst)):
        R = str(hex(random.randrange(0, 256)))[2:]
        G = str(hex(random.randrange(0, 256)))[2:]
        B = str(hex(random.randrange(0, 256)))[2:]

        # slack message builder 형식에 맞춰서 dictionary 생성
        tmp = {}
        tmp["color"] = '#' + R + G + B
        tmp["title"] = tlst[i]
        tmp["title_link"] = "https://comic.naver.com" + hlst[i]
        tmp["text"] = "[{}] | {}".format(alst[i], rlst[i])
        tmp["thumb_url"] = slst[i]

        lst_today_recom.append(tmp)

    return (banner, lst_today_recom)

# 조회 옵션
def order_options(i):
    options = ["Update", "ViewCount", "StarScore", "TitleName"]
    url = "order=" + options[i]
    return url

# 해당 웹툰 페이지에서 detail 크롤링
def detail_crawling(url):
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    details = []
    for text in soup.find_all("div", class_="detail"):
        for d in text.find_all("p"):
            detail = str(d).replace("<p>", "").replace("\n", "").replace("</p>", "").replace("&lt;", "<").replace("&gt;", ">").replace("\r", "").replace("<br/>", "\n")
            details.append(detail)

    return u'\n'.join(details)

# 요일 웹툰(Top 3)
def _crawl_week_top_ten_webtoon(i,  order):
    week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    o_url = "&" + order_options(order)
    url = "https://comic.naver.com/webtoon/weekdayList.nhn?week=" + week[i] + o_url
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    spot = soup.find("ul", class_="img_list")
    banner = soup.find("div", class_="view_type").find("h3").get_text() + " Top 3"
    order_str = ['업데이트순', '조회순', '별점순', '제목순']
    banner += " (" + order_str[order] + ")\n"

    tit_recom = spot.find_all("div", class_="thumb")
    tlst = []
    hlst = []
    for i in range(3):
        tlst.append(tit_recom[i].find("a")["title"])
        hlst.append(tit_recom[i].find("a")["href"])

    aut_recom = spot.find_all("dd", class_="desc")
    alst = []
    for i in range(3):
        alst.append(aut_recom[i].find("a").get_text())

    rat_recom = spot.find_all("div", class_="rating_type")
    rlst = []
    for i in range(3):
        rlst.append(rat_recom[i].find("strong").get_text())

    slst = []
    dlst = []
    for l in hlst:
        link = "https://comic.naver.com" + l
        dlst.append(detail_crawling(link))
        slst.append(img_crawling(link))

    lst_week_top_ten = []
    for i in range(3):
        R = str(hex(random.randrange(0, 256)))[2:]
        G = str(hex(random.randrange(0, 256)))[2:]
        B = str(hex(random.randrange(0, 256)))[2:]

        # slack message builder 형식에 맞춰서 dictionary 생성
        tmp = {}
        tmp["color"] = '#' + R + G + B
        tmp["title"] = tlst[i]
        tmp["title_link"] = "https://comic.naver.com" + hlst[i]
        tmp["text"] = "{} | {}\n".format(alst[i], rlst[i]) + "{}".format(dlst[i])
        tmp["thumb_url"] = slst[i]

        lst_week_top_ten.append(tmp)

    return (banner, lst_week_top_ten)

#장르별 웹툰(Top 3)
def _crawl_genre_top_ten_webtoon(i, order):
    genre = ["episode", "omnibus", "story", "daily", "comic", "fantasy", "action", "drama", "pure", "sensibility",
             "thrill", "historical", "sports"]

    o_url = order_options(order)
    url = "https://comic.naver.com/webtoon/genre.nhn?" + o_url + "&genre=" + genre[i]

    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    banner_tmp = soup.find("div", class_="view_type").find("h3").get_text()
    banner_split = banner_tmp.split()
    banner = banner_split[0] + " 웹툰"
    order_str = ['업데이트순', '조회순', '별점순', '제목순']
    banner += " Top 3" + " (" + order_str[order] + ")\n"

    spot = soup.find("ul", class_="img_list")
    tit_recom = spot.find_all("div", class_="thumb")
    flst = []  # 완결여부 리스트
    tlst = []
    hlst = []
    for i in range(3):
        tlst.append(tit_recom[i].find("a")["title"])
        hlst.append(tit_recom[i].find("a")["href"])
        fin = tit_recom[i].find("img", class_="finish")
        if fin != None:
            flst.append(fin["alt"])
        else:
            flst.append("")

    aut_recom = spot.find_all("dd", class_="desc")
    alst = []
    for i in range(3):
        alst.append(aut_recom[i].find("a").get_text())

    rat_recom = spot.find_all("div", class_="rating_type")
    rlst = []
    for i in range(3):
        rlst.append(rat_recom[i].find("strong").get_text())

    slst = []
    dlst = []
    for l in hlst:
        link = "https://comic.naver.com" + l
        dlst.append(detail_crawling(link))
        slst.append(img_crawling(link))

    lst_genre_top_ten = []
    for i in range(3):
        R = str(hex(random.randrange(0, 256)))[2:]
        G = str(hex(random.randrange(0, 256)))[2:]
        B = str(hex(random.randrange(0, 256)))[2:]

        # slack message builder 형식에 맞춰서 dictionary 생성
        tmp = {}
        tmp["color"] = '#' + R + G + B
        tmp["title"] = tlst[i]
        tmp["title_link"] = "https://comic.naver.com" + hlst[i]
        if flst[i] != "":
            tmp["text"] = "{} | {} | {}\n".format(alst[i], rlst[i], flst[i]) + "{}".format(dlst[i])
        else:
            tmp["text"] = "{} | {}\n".format(alst[i], rlst[i]) + "{}".format(dlst[i])
        tmp["thumb_url"] = slst[i]

        lst_genre_top_ten.append(tmp)

    return (banner, lst_genre_top_ten)

#완결 웹툰(Top 3)
def _crawl_fin_top_ten_webtoon(order):
    o_url = "?" + order_options(order)
    url = "https://comic.naver.com/webtoon/finish.nhn" +o_url
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    spot = soup.find("ul", class_="img_list")
    banner = soup.find("div", class_="view_type").find("h3").get_text() + " Top 3"
    order_str = ['업데이트순', '조회순', '별점순', '제목순']
    banner += " (" + order_str[order] + ")\n"

    tit_recom = spot.find_all("div", class_="thumb")
    tlst = []
    hlst = []
    for i in range(3):
        tlst.append(tit_recom[i].find("a")["title"])
        hlst.append(tit_recom[i].find("a")["href"])

    aut_recom = spot.find_all("dd", class_="desc")
    alst = []
    for i in range(3):
        alst.append(aut_recom[i].find("a").get_text())

    rat_recom = spot.find_all("div", class_="rating_type")
    rlst = []
    for i in range(3):
        rlst.append(rat_recom[i].find("strong").get_text())

    slst = []
    dlst = []
    for l in hlst:
        link = "https://comic.naver.com" + l
        dlst.append(detail_crawling(link))
        slst.append(img_crawling(link))

    lst_fin_top_ten = []
    for i in range(3):
        R = str(hex(random.randrange(0, 256)))[2:]
        G = str(hex(random.randrange(0, 256)))[2:]
        B = str(hex(random.randrange(0, 256)))[2:]

        # slack message builder 형식에 맞춰서 dictionary 생성
        tmp = {}
        tmp["color"] = '#' + R + G + B
        tmp["title"] = tlst[i]
        tmp["title_link"] = "https://comic.naver.com" + hlst[i]
        tmp["text"] = "{} | {}\n".format(alst[i], rlst[i]) + "{}".format(dlst[i])
        tmp["thumb_url"] = slst[i]

        lst_fin_top_ten.append(tmp)

    return (banner, lst_fin_top_ten)


#전체 웹툰 검색
def _crawl_info_webtoon():
    url = "https://comic.naver.com/webtoon/creation.nhn"
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    tit_link = {}
    context = soup.find("div", class_="webtoon")
    for x in context.find_all("div", class_="thumb"):
        link = "https://comic.naver.com" + x.find("a")["href"]
        tit = x.find("a")["title"]
        tit_link[tit] = link

    return tit_link

#특정 웹툰 검색
def _crawl_specific_webtoon(title):
    info = _crawl_info_webtoon()

    hyper = ""
    if title in info:
        hyper = info[title]

    sourcecode = urllib.request.urlopen(hyper).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    comic_info = soup.find("div", class_="comicinfo")
    src = comic_info.find("div", class_="thumb").find("img")["src"]

    R = str(hex(random.randrange(0, 256)))[2:]
    G = str(hex(random.randrange(0, 256)))[2:]
    B = str(hex(random.randrange(0, 256)))[2:]

    # slack message builder 형식에 맞춰서 dictionary 생성
    tmp = {}
    tmp["color"] = '#' + R + G + B
    banner = "해당 웹툰 검색 결과입니다.\n"
    if hyper == "":
        tmp["title"] = "'" + title + "'" + " 웹툰은 존재하지 않습니다."
        tmp["title_link"] = hyper
        tmp["text"] = "정확한 명칭으로 검색해주세요"
    else:
        tmp["title"] = title
        tmp["title_link"] = hyper
        tmp["text"] = ""
        tmp["image_url"] = src

    lst_spec_toon = []
    lst_spec_toon.append(tmp)

    return (banner, lst_spec_toon)

#특정 키워드 검색
def _crawl_specific_key_webtoon(keyword):
    info = _crawl_info_webtoon()

    tlst = []
    hlst = []
    for tit in list(info.keys()):
        if keyword in tit:
            tlst.append(tit)
            hlst.append(info[tit])

    lst_key_toon = []
    for i in range(len(tlst)):
        R = str(hex(random.randrange(0, 256)))[2:]
        G = str(hex(random.randrange(0, 256)))[2:]
        B = str(hex(random.randrange(0, 256)))[2:]

        # slack message builder 형식에 맞춰서 dictionary 생성
        tmp = {}
        tmp["color"] = '#' + R + G + B
        tmp["title"] = tlst[i]
        tmp["title_link"] = hlst[i]
        tmp["text"] = ""

        lst_key_toon.append(tmp)

    if len(lst_key_toon) == 0:
        return u"해당 키워드는 검색 결과가 없습니다.\n"
    else:
        return ("해당 키워드 검색 결과입니다.\n", lst_key_toon)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        week_str = "월화수목금토일"
        week = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
        genre_str = "에피소드옴니버스스토리일상개그판타지액션드라마순정감성스릴러시대극스포츠"
        genre = {'에피소드': 0, '옴니버스': 1, '스토리': 2, '일상': 3, '개그': 4, '판타지': 5, '액션': 6,
                 '드라마': 7, '순정': 8, '감성': 9, '스릴러': 10, '시대극': 11, '스포츠': 12}
        order_g = {'업데이트순': 0, '조회순': 1, '별점순': 2}
        order = {'업데이트순': 0, '조회순': 1, '별점순': 2, '제목순': 3}

        guide = []
        with open('guide.txt', 'r') as file:
            for line in file:
                guide.append(line)

        split_text = text.split()
        if len(split_text) == 1:
            keywords = u'\n'.join(guide)
        else:
            if "오늘" in text:
                keywords = _crawl_today_recom_webtoon()
            elif "신규" in text:
                keywords = _crawl_new_recom_webtoon()
            elif split_text[1][0] in week_str: #요일
                day = split_text[1][0]
                o = "조회순"
                if split_text[3] != o:
                    o = split_text[3]
                keywords = _crawl_week_top_ten_webtoon(week[day], order[o])
            elif split_text[1] in genre_str: #장르
                g = split_text[1]
                o = "조회순"
                if split_text[3] != o:
                    o = split_text[3]
                keywords = _crawl_genre_top_ten_webtoon(genre[g], order_g[o])
            elif "완결" in text: #완결
                o = "업데이트순"
                if split_text[3] != o:
                    o = split_text[3]
                keywords = _crawl_fin_top_ten_webtoon(order[o])
            elif "키워드" in text: #키워드
                keywords = _crawl_specific_key_webtoon(split_text[2])
            elif "검색" in text: #검색
                txt = ""
                for i in range(2, len(split_text)):
                    txt += split_text[i]
                    if i < len(split_text) - 1:
                        txt += " "
                keywords = _crawl_specific_webtoon(txt)
            else: #그 외 입력
                keywords = u'\n'.join(guide)

        if type(keywords) is tuple: # keywords의 타입이 튜플이면 hypertext형태로 출력하도록 api_call 인자 전달
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords[0],  # pretext
                attachments=keywords[1]  # dictionary list
            )
        else: # 그 외의 경우에는 일반적으로 처리
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )
        print("완료")
        return make_response("App mention message has been sent", 200, )


    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        #
        #
        #
        #
        #
        #
        #
        #
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
