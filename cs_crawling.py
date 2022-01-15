import os
import platform
import re
import time

import sqlalchemy
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

import models
from models import EventItems

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

options = webdriver.ChromeOptions()
if platform.system() != 'Windows':
    options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
options.add_argument(f'user-agent={user_agent}')

path = 'chromedriver_win32.exe' if platform.system() == 'Windows' else os.path.abspath("chromedriver")

CU_URL = "http://cu.bgfretail.com/event/plus.do?category=event&depth2=1&sf=N"
GS25_URL = "http://gs25.gsretail.com/gscvs/ko/products/event-goods#"
SEVEN_ELEVEN_URL = "https://www.7-eleven.co.kr/product/presentList.asp"
MINISTOP_URL = "https://www.ministop.co.kr/MiniStopHomePage/page/event/plus1.do"
EMART24_URL = "https://www.emart24.co.kr/product/eventProduct.asp"


# 리스트에서 처음 10개랑 마지막 10개 상품 추출
# 총 20개가 안 되면...
def extract_first10_last10(ret_str_list, event_items, dum_event_items=None):
    if len(event_items) < 20:

        if len(event_items) == 1:
            # 제일 처음 1개
            ret_str_list.append('<h3><b>처음 1개</b></h3>\n')
            ret_str_list.append(f'1: {event_items[0]}\n')
            if dum_event_items is not None:
                ret_str_list.append(f'(덤) 1: {dum_event_items[0]}\n')

            ret_str_list.append('.\n.\n.\n')

            # 마지막 1개
            ret_str_list.append('<h3><b>마지막 1개</b></h3>\n')
            ret_str_list.append(f'1: {event_items[0]}\n')
            if dum_event_items is not None:
                ret_str_list.append(f'(덤) 1: {dum_event_items[0]}\n')
            return

        if len(event_items) // 2 == 0:  # 짝수 개면 딱 반반씩
            mid_offset = len(event_items) // 2
            ret_str_list.append(f'<h3><b>처음 {mid_offset}개</b></h3>\n')
            for i in range(0, mid_offset):
                ret_str_list.append(f'{i}: {event_items[i]}\n')
                if dum_event_items is not None:
                    ret_str_list.append(f'(덤) {i}: {dum_event_items[i]}\n')

            ret_str_list.append('.\n.\n.\n')

            ret_str_list.append(f'<h3><b>마지막 {mid_offset}개</b></h3>\n')
            for i in range(mid_offset, len(event_items)):
                ret_str_list.append(f'{i}: {event_items[i]}\n')
                if dum_event_items is not None:
                    ret_str_list.append(f'(덤) {i}: {dum_event_items[i]}\n')

        else:  # 홀수 개면 가운데 한 개 빼고 나누면 됨
            mid_offset = len(event_items) // 2
            ret_str_list.append(f'<h3><b>처음 {mid_offset}개</b></h3>\n')
            for i in range(0, mid_offset):
                ret_str_list.append(f'{i}: {event_items[i]}\n')
                if dum_event_items is not None:
                    ret_str_list.append(f'(덤) {i}: {dum_event_items[i]}\n')

            ret_str_list.append('.\n.\n.\n')

            ret_str_list.append(f'<h3><b>마지막 {mid_offset}개</b></h3>\n')
            for i in range(mid_offset + 1, len(event_items)):
                ret_str_list.append(f'{i}: {event_items[i]}\n')
                if dum_event_items is not None:
                    ret_str_list.append(f'(덤) {i}: {dum_event_items[i]}\n')
    else:
        ret_str_list.append('<h3><b>처음 10개</b></h3>\n')
        for i in range(0, 10):
            ret_str_list.append(f'{i}: {event_items[i]}\n')
            if dum_event_items is not None:
                ret_str_list.append(f'(덤) {i}: {dum_event_items[i]}\n')

        ret_str_list.append('.\n.\n.\n')

        ret_str_list.append('<h3><b>마지막 10개</b></h3>\n')
        for i in range(len(event_items) - 10, len(event_items)):
            ret_str_list.append(f'{i}: {event_items[i]}\n')
            if dum_event_items is not None:
                ret_str_list.append(f'(덤) {i}: {dum_event_items[i]}\n')

    ret_str_list.append('\n\n<h4><b>----------------------------------------------------------------------------------</b></h4>\n')


def cu_crawling(cs, ret_dict):
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(CU_URL)
    print(driver.title)
    ret_str_list = [f'<h1><b><{cs} 행사 상품 목록></b></h1>\n\n']

    def cu_plus_event_item_crawling(page_event_type):
        # 1+1 | 2+1 페이지로 이동
        driver.execute_script('goDepth(\'23\');') if page_event_type == '1+1' else driver.execute_script(
            'goDepth(\'24\');')
        time.sleep(3)

        nonlocal ret_str_list
        event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        # 스크롤 맨 아래까지 내리기
        last_height = driver.execute_script('return document.body.scrollHeight')
        PAUSE_TIME = 2
        scroll_num = 0
        try:
            while True:
                # scroll down to bottom
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                load_more_button = driver.find_element(By.CSS_SELECTOR, 'div.prodListBtn')

                # load more page
                if load_more_button is not None:
                    driver.execute_script('nextPage(1);')
                    if PAUSE_TIME <= 20:
                        PAUSE_TIME += 1.5
                    print(f'{cs} one_or_two_plus_one scrolling: {scroll_num}')
                    scroll_num += 1
                    print('PAUSE_TIME =', PAUSE_TIME)
                    time.sleep(2) if page_event_type == '1+1' else time.sleep(PAUSE_TIME)

                # calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script('return document.body.scrollHeight')
                if new_height == last_height:
                    print('new_height == last_height')
                    break
                last_height = new_height
        except NoSuchElementException as noSuchElementException:  # 모두 스크롤이 됐을 때, element 체크하는 method가 없음
            print(f'{cs} 1+1 스크롤 완료: {noSuchElementException.msg}') if page_event_type == '1+1' else print(
                f'{cs} 2+1 스크롤 완료: {noSuchElementException.msg}')

        # start crawling
        try:
            prod_list = driver.find_elements(By.CSS_SELECTOR, '#contents > div.relCon > div.prodListWrap > ul > li')

            for prod in prod_list:
                title = prod.find_element(By.CSS_SELECTOR, 'p.prodName').text
                img_url = prod.find_element(By.CSS_SELECTOR, 'div.photo > a > img').get_attribute('src')
                price = int(prod.find_element(By.CSS_SELECTOR, 'p.prodPrice').text[:-1].replace(',', ''))
                discounted_price = round(price / 2) if page_event_type == '1+1' else round(price / 3)
                event_type = prod.find_element(By.CSS_SELECTOR, 'ul > li').text

                event_item = EventItems(item_name=title, item_price=price, item_actual_price=discounted_price, depth=0,
                                        image_url=img_url, category=None, cs_brand=cs, event_type=event_type)
                session.add(event_item)
                session.commit()
                event_items.append(event_item)

                print(f'{cs} event_item = {event_item}')

            print(f'{cs} 1+1 행사 제품 개수: {len(event_items)}') if page_event_type == '1+1' else print(
                f'{cs} 2+1 행사 제품 개수: {len(event_items)}')

            ret_str_list.append(
                f'\n<h3><b>{cs} 1+1 행사 제품 개수: {len(event_items)}</b></h3>\n') if page_event_type == '1+1' else ret_str_list.append(
                f'\n<h3><b>{cs} 2+1 행사 제품 개수: {len(event_items)}</b></h3>\n')

            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)

        except NoSuchElementException as noSuchElementException:
            print(noSuchElementException.msg)
        except StaleElementReferenceException as staleElementReferenceException:
            print(staleElementReferenceException.msg)
        except:
            session.rollback()
            raise
        finally:
            session.close()

    cu_plus_event_item_crawling("1+1")
    cu_plus_event_item_crawling("2+1")
    ret_str_list.append(
        f'\n<h3><b>============================={cs} End=============================</b></h3>\n\n')
    ret_dict[cs] = ''.join(ret_str_list)
    driver.quit()


def gs25_crawling(cs, ret_dict):
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(GS25_URL)
    print(driver.title)

    ret_str_list = [f'<h1><b><{cs} 행사 상품 목록></b></h1>\n']
    time.sleep(1)

    def gs25_plus_event_item_crawling(page_event_type):  # 1+1, 2+1 데이터 크롤링 (덤증정 행사상품은 가져오는 데이터가 약간 상이하므로 따로 진행)
        one_or_two_to_one_button = driver.find_element(By.ID, page_event_type)
        one_or_two_to_one_button.click()
        now_index = 0 if page_event_type == 'ONE_TO_ONE' else 1

        nonlocal ret_str_list
        event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        time.sleep(1)

        try:
            while True:  # 한 페이지에 있는 이벤트 아이템 리스트 가져오기( 한 페이지에 8개 있음. 나중에 바뀔 수도 있음)
                prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.eventtab > div.tblwrap.mt50 > ul.prod_list')[
                    now_index].find_elements(By.CSS_SELECTOR, 'li')

                for prod in prod_list:
                    title = prod.find_element(By.CSS_SELECTOR, 'div.prod_box > p.tit').text
                    img_url = prod.find_element(By.CSS_SELECTOR, 'div.prod_box > p.img > img').get_attribute('src')
                    price = int(
                        prod.find_element(By.CSS_SELECTOR, 'div.prod_box > p.price > span.cost').text[:-1].replace(',',
                                                                                                                   ''))
                    discounted_price = round(price / 2) if page_event_type == '1+1' else round(price / 3)
                    event_type = prod.find_element(By.CSS_SELECTOR,
                                                   f'div.prod_box > div.flag_box.{page_event_type} > p.flg01').text

                    # Save in DB
                    event_item = EventItems(item_name=title, item_price=price, item_actual_price=discounted_price,
                                            depth=0, image_url=img_url, category=None, cs_brand=cs,
                                            event_type=event_type)
                    session.add(event_item)
                    session.commit()
                    event_items.append(event_item)
                    print(f'{cs} 1+1 event_item = {event_item}') if page_event_type == 'ONE_TO_ONE' else print(
                        f'{cs} 2+1 event_item = {event_item}'
                    )

                if len(prod_list) < 8:
                    break

                driver.execute_script("goodsPageController.moveControl(1)")
                time.sleep(0.5)

            print(f'{cs} 1+1 행사 제품 개수 = {len(event_items)}') if page_event_type == 'ONE_TO_ONE' else print(
                f'{cs} 2+1 행사 제품 개수 = {len(event_items)}')
            ret_str_list.append(
                f'\n<h3><b>{cs} 1+1 행사 제품 개수: {len(event_items)}</b></h3>\n') if page_event_type == '1+1' else ret_str_list.append(
                f'\n<h3><b>{cs} 2+1 행사 제품 개수: {len(event_items)}</b></h3>\n')

            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)

        except NoSuchElementException as noSuchElementException:
            print(noSuchElementException.msg)
        except StaleElementReferenceException as staleElementReferenceException:
            print(staleElementReferenceException.msg)
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def gs25_gift_event_item_crawling():  # 덤증정 행사 데이터 크롤링
        gift_button = driver.find_element(By.ID, "GIFT")
        gift_button.click()

        nonlocal ret_str_list
        event_items = []
        dum_event_items = []

        actions = ActionChains(driver)

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        time.sleep(1)

        try:
            while True:  # 한 페이지에 있는 이벤트 아이템 리스트 가져오기( 한 페이지에 8개 있음. 나중에 바뀔 수도 있음)
                prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.eventtab > div.tblwrap.mt50 > ul.prod_list')[
                    2].find_elements(By.CSS_SELECTOR, 'li')

                for prod in prod_list:  # 파이썬은 함수 스코프 언어라서, try, while, for, if-else에서 선언된 변수는 스코프를 갖지 않는다.
                    title = prod.find_element(By.CSS_SELECTOR, 'div.prod_box > p.tit').text
                    img_url = prod.find_element(By.CSS_SELECTOR, 'div.prod_box > p.img > img').get_attribute('src')
                    price = int(
                        prod.find_element(By.CSS_SELECTOR, 'div.prod_box > p.price > span.cost').text[:-1].replace(',',
                                                                                                                   ''))
                    event_type = prod.find_element(By.CSS_SELECTOR, 'div.flag_box.GIFT > p.flg01 > span').text

                    actions.move_to_element(prod).perform()  # 해당 아이템에 대한 mouse over

                    dum_title = prod.find_element(By.CSS_SELECTOR,
                                                  'div.prod_box > div.dum_box > div.dum_txt > p.name').text
                    dum_img_url = prod.find_element(By.CSS_SELECTOR,
                                                    'div.prod_box > div.dum_box > div.dum_prd > p.img > img').get_attribute(
                        'src')
                    dum_price = prod.find_element(By.CSS_SELECTOR,
                                                  'div.prod_box > div.dum_box > div.dum_txt > p.price').text[
                                :-1].replace(',', '')

                    # Save in DB
                    event_item = EventItems(item_name=title, item_price=price, item_actual_price=None, depth=0,
                                            image_url=img_url, category=None, cs_brand=cs, event_type=event_type)
                    session.add(event_item)
                    session.flush()  # 일단 DB에 들어가야 ID가 나온다.
                    # refresh updates given object in the session with its state in the DB
                    session.refresh(event_item)

                    event_item.bundle_id = event_item.event_item_id

                    # 덤 증정 상품 정보(depth = 1)
                    dum_event_item = EventItems(item_name=dum_title, item_price=dum_price, item_actual_price=None,
                                                depth=1, bundle_id=event_item.event_item_id, image_url=dum_img_url,
                                                category=None, cs_brand=cs, event_type=event_type)
                    session.add(dum_event_item)
                    session.commit()

                    event_items.append(event_item)
                    dum_event_items.append(dum_event_item)

                    print(f'{cs} event_item = {event_item}')
                    print(f'{cs} dum_event_item = {dum_event_item}')

                if len(prod_list) < 8:
                    break

                driver.execute_script("goodsPageController.moveControl(1)")
                time.sleep(2)

            print(f'{cs} 덤증정 행사 상품 개수: {len(dum_event_items)}')
            ret_str_list.append(f'\n<h3><b>{cs} 덤 증정 행사 상품 개수: {len(dum_event_items)}</b></h3>\n')
            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items, dum_event_items=dum_event_items)

        except NoSuchElementException as noSuchElementException:
            print(noSuchElementException.msg)
        except StaleElementReferenceException as staleElementReferenceException:
            print(staleElementReferenceException.msg)
        except:
            session.rollback()
            raise
        finally:
            session.close()

    gs25_plus_event_item_crawling('ONE_TO_ONE')
    gs25_plus_event_item_crawling('TWO_TO_ONE')
    gs25_gift_event_item_crawling()  # 덤증정(파라미터 원래 없음)

    ret_str_list.append(
        f'\n<h3><b>============================={cs} End=============================</b></h3>\n\n')
    ret_dict[cs] = ''.join(ret_str_list)

    driver.quit()  # 크롬에서 열려있는 모든 탭 종료


def seven_eleven_crawling(cs, ret_dict):
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(SEVEN_ELEVEN_URL)
    print(driver.title)

    ret_str_list = [f'<h1><b><{cs} 행사 상품 목록></b><h1>\n']

    ONE_PLUS_ONE = 1
    TWO_PLUS_ONE = 2
    GIFT = 3
    DISCOUNT = 4

    def seven_eleven_plus_and_discount_event_item_crawling(page_type):
        # 1+1 | 2+1 | 할인행사 페이지로 이동
        if page_type == ONE_PLUS_ONE:
            driver.execute_script(f'fncTab(\'{ONE_PLUS_ONE}\');')
        elif page_type == TWO_PLUS_ONE:
            driver.execute_script(f'fncTab(\'{TWO_PLUS_ONE}\');')
        else:
            driver.execute_script(f'fncTab(\'{DISCOUNT}\');')
        time.sleep(1.5)

        event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        scroll_num = 0
        # 스크롤 맨 아래까지 내리기
        last_height = driver.execute_script('return document.body.scrollHeight')
        try:
            while True:
                # scroll down to bottom
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                load_more_button = driver.find_element(By.CSS_SELECTOR,
                                                       'div.conSection > div.img_list > #listUl > li.btn_more')

                # load more page
                if load_more_button is not None:
                    driver.execute_script(f'fncMore({page_type});')  # load more JS function
                    scroll_num += 1
                    print(f'{cs} (page_type: {page_type}) scrolling: {scroll_num}')
                    time.sleep(2.5)

                # calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script('return document.body.scrollHeight')
                if new_height == last_height:
                    print('new_height == last_height')
                    break
                last_height = new_height
        except NoSuchElementException as noSuchElementException:  # 모두 스크롤이 됐을 때, element 체크하는 method가 없음
            print(f'{cs} (page_type: {page_type}) 스크롤({scroll_num}) 완료: {noSuchElementException.msg}')

        # start crawling
        try:
            prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.conSection > div.img_list > #listUl > li')
            for prod in prod_list:  # 맨 처음과 맨 마지막 아이템은 아이템이 아니므로 예외에 걸리고, 나머지 그 사이에 있는 아이템만 가져옴
                try:
                    title = prod.find_element(By.CSS_SELECTOR,
                                              'div.pic_product > div.infowrap > div.name').text  # 맨 처음과 마지막에 예외 발생할 수 있음
                    img_url = prod.find_element(By.CSS_SELECTOR, 'div.pic_product > img').get_attribute('src')
                    price = int(
                        prod.find_element(By.CSS_SELECTOR, 'div.pic_product > div.infowrap > div.price').text.replace(
                            ',',
                            ''))
                    if page_type == ONE_PLUS_ONE:
                        discounted_price = round(price / 2)
                    elif page_type == TWO_PLUS_ONE:
                        discounted_price = round(price / 3)
                    else:
                        discounted_price = price  # 세븐일레븐은 할인되기 전 원래 가격 제공 안 함.
                    event_type = '가격할인' if page_type == DISCOUNT else prod.find_element(By.CSS_SELECTOR, 'ul > li').text

                    event_item = EventItems(item_name=title, item_price=price, item_actual_price=discounted_price,
                                            depth=0, image_url=img_url, category=None, cs_brand=cs,
                                            event_type=event_type)
                    session.add(event_item)
                    session.commit()
                    event_items.append(event_item)

                    print(f'{cs} event_item = {event_item}')

                except NoSuchElementException as noSuchElementException:
                    print(noSuchElementException.msg)
                except StaleElementReferenceException as staleElementReferenceException:
                    print(staleElementReferenceException.msg)

            if page_type == ONE_PLUS_ONE:
                print(f'{cs} 1+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 1+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
            elif page_type == TWO_PLUS_ONE:
                print(f'{cs} 2+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 2+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
            else:
                print(f'{cs} 할인 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 할인 행사 제품 개수: {len(event_items)}</b></h3>\n')

            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)

        except:
            session.rollback()
            raise
        finally:
            session.close()

    def seven_eleven_gift_event_item_crawling(page_type):  # Seven-Eleven 덤증정 상품 크롤링
        # 증정행사 페이지로 이동
        driver.execute_script(f'fncTab(\'{GIFT}\');')
        time.sleep(1.5)

        event_items = []
        dum_event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        scroll_num = 0
        # 스크롤 맨 아래까지 내리기
        last_height = driver.execute_script('return document.body.scrollHeight')
        try:
            while True:
                # scroll down to bottom
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                load_more_button = driver.find_element(By.CSS_SELECTOR,
                                                       'div.conSection > div.img_list > #listUl > li.btn_more')

                # load more page
                if load_more_button is not None:
                    driver.execute_script(f'fncMore({page_type});')
                    scroll_num += 1
                    print(f'seven_eleven(page_type: {page_type}) scrolling: {scroll_num}')
                    time.sleep(2)

                # calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script('return document.body.scrollHeight')
                if new_height == last_height:
                    print('new_height == last_height')
                    break
                last_height = new_height
        except NoSuchElementException as noSuchElementException:  # 모두 스크롤이 됐을 때, element 체크하는 method가 없음
            print(f'1+1 스크롤({scroll_num}) 완료: {noSuchElementException.msg}') if page_type == ONE_PLUS_ONE else print(
                f'2+1 스크롤 완료({scroll_num}): {noSuchElementException.msg}')

        # start crawling
        try:
            prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.conSection > div.img_list > #listUl > li')
            for prod in prod_list:  # 맨 처음과 맨 마지막 아이템은 아이템이 아니므로 예외에 걸리고, 나머지 그 사이에 있는 아이템만 가져옴
                try:
                    title = prod.find_element(By.CSS_SELECTOR,
                                              'a.btn_product_01 > div.pic_product > div.infowrap > div.name').text
                    img_url = prod.find_element(By.CSS_SELECTOR,
                                                'a.btn_product_01 > div.pic_product > img').get_attribute(
                        'src')
                    price = int(prod.find_element(By.CSS_SELECTOR,
                                                  'a.btn_product_01 > div.pic_product > div.infowrap > div.price').text.replace(
                        ',', ''))
                    event_type = '덤증정'

                    dum_title = prod.find_element(By.CSS_SELECTOR,
                                                  'a.btn_product_02 > div.pic_product > div.infowrap > div.name').text
                    dum_img_url = prod.find_element(By.CSS_SELECTOR,
                                                    'a.btn_product_02 > div.pic_product > img').get_attribute('src')
                    dum_price = int(prod.find_element(By.CSS_SELECTOR,
                                                      'a.btn_product_02 > div.pic_product > div.infowrap > div.price').text.replace(
                        ',', ''))

                    # 행사 상품 + 덤증정 아이템 같이 저장해야 함
                    event_item = EventItems(item_name=title, item_price=price, item_actual_price=None, depth=0,
                                            image_url=img_url, category=None, cs_brand=cs, event_type=event_type)

                    session.add(event_item)
                    session.flush()
                    session.refresh(event_item)

                    event_item.bundle_id = event_item.event_item_id

                    # 덤 증정 상품 정보(depth = 1)
                    dum_event_item = EventItems(item_name=dum_title, item_price=dum_price, item_actual_price=None,
                                                depth=1, bundle_id=event_item.event_item_id, image_url=dum_img_url,
                                                category=None, cs_brand=cs, event_type=event_type)
                    session.add(dum_event_item)
                    session.commit()

                    event_items.append(event_item)
                    dum_event_items.append(dum_event_item)

                    print(f'{cs} 덤 증정 행사 event_item = {event_item}, dum_event_item = {dum_event_item}')

                except NoSuchElementException as noSuchElementException:
                    print(noSuchElementException.msg)
                except StaleElementReferenceException as staleElementReferenceException:
                    print(staleElementReferenceException.msg)

            print(f'{cs} 덤 증정 행사 제품 개수: {len(event_items)}')
            ret_str_list.append(f'\n<h3><b>{cs} 덤 증정 행사 제품 개수: {len(event_items)}</b></h3>')
            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items, dum_event_items=dum_event_items)

        except:
            session.rollback()
            raise
        finally:
            session.close()

    seven_eleven_plus_and_discount_event_item_crawling(ONE_PLUS_ONE)
    seven_eleven_plus_and_discount_event_item_crawling(TWO_PLUS_ONE)
    seven_eleven_gift_event_item_crawling(GIFT)
    seven_eleven_plus_and_discount_event_item_crawling(DISCOUNT)

    ret_str_list.append(
        f'\n<h3><b>============================={cs} End=============================</b></h3>')
    ret_dict[cs] = ''.join(ret_str_list)
    driver.quit()


def ministop_crawling(cs, ret_dict):
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(MINISTOP_URL)
    print(driver.title)

    ret_str_list = [f'<h1><b><{cs} 행사 상품 목록></b></h1>\n']

    ONE_PLUS_ONE_HREF = 'https://www.ministop.co.kr/MiniStopHomePage/page/event/plus1.do'
    TWO_PLUS_ONE_HREF = 'https://www.ministop.co.kr/MiniStopHomePage/page/event/plus2.do'
    GIFT_HREF = 'https://www.ministop.co.kr/MiniStopHomePage/page/event/add.do'
    DISCOUNT_HREF = 'https://www.ministop.co.kr/MiniStopHomePage/page/event/sale.do'

    def ministop_plus_and_discount_event_item_crawling(page_type):
        # 1+1 | 2+1 | 할인행사 페이지로 이동
        if page_type == ONE_PLUS_ONE_HREF:
            driver.get(ONE_PLUS_ONE_HREF)
        elif page_type == TWO_PLUS_ONE_HREF:
            driver.get(TWO_PLUS_ONE_HREF)
        else:
            driver.get(DISCOUNT_HREF)
        time.sleep(1)

        event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        scroll_num = 0
        # 스크롤 맨 아래까지 내리기
        last_height = driver.execute_script('return document.body.scrollHeight')
        try:
            while True:
                # scroll down to bottom
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                load_more_button = driver.find_element(By.CSS_SELECTOR,
                                                       'div.inner.wrap.service1 > div.event_plus_list > div.pr_btns > a.pr_more')

                # load more page
                if load_more_button is not None:
                    load_more_button.click()
                    scroll_num += 1
                    print(f'{cs} (page_type: {page_type}) scrolling: {scroll_num}')
                    time.sleep(1)

                # calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script('return document.body.scrollHeight')
                if new_height == last_height:
                    print('new_height == last_height')
                    print(f'{cs} (page_type: {page_type}) 스크롤({scroll_num}) 완료')
                    break
                last_height = new_height
        except NoSuchElementException as noSuchElementException:  # 모두 스크롤이 됐을 때, element 체크하는 method가 없음
            print(f'ministop(page_type: {page_type}) 스크롤({scroll_num}) 완료: {noSuchElementException.msg}')

        # start crawling
        try:
            prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.inner.wrap.service1 > div.event_plus_list > ul > li')
            for prod in prod_list:
                title = prod.find_element(By.CSS_SELECTOR, 'a > img').get_attribute('alt')
                img_url = prod.find_element(By.CSS_SELECTOR, 'a > img').get_attribute('src')
                origin_price = int(prod.find_elements(By.CSS_SELECTOR, 'a > p > strong')[0].text[:-1].replace(',', '')) \
                    if page_type == DISCOUNT_HREF else int(
                    prod.find_element(By.CSS_SELECTOR, 'a > p > strong').text.replace(',', ''))
                discounted_price = int(prod.find_elements(By.CSS_SELECTOR, 'a > p > strong')[1].text.replace(',', '')) \
                    if page_type == DISCOUNT_HREF else int(
                    prod.find_element(By.CSS_SELECTOR, 'a > p > strong').text.replace(',', ''))

                if page_type == ONE_PLUS_ONE_HREF:  # 할인 페이지일 때는 그냥 가져오면 되지만 plus 행사일 때는 나눠줌
                    discounted_price = round(discounted_price / 2)
                elif page_type == TWO_PLUS_ONE_HREF:
                    discounted_price = round(discounted_price / 3)

                event_type = prod.find_element(By.CSS_SELECTOR, 'a > span').text

                event_item = EventItems(item_name=title, item_price=origin_price,
                                        item_actual_price=discounted_price, depth=0, image_url=img_url,
                                        category=None, cs_brand=cs, event_type=event_type)
                session.add(event_item)
                session.commit()
                event_items.append(event_item)

                print(f'{cs} event_item = {event_item}')

            if page_type == ONE_PLUS_ONE_HREF:
                print(f'{cs} 1+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 1+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
            elif page_type == TWO_PLUS_ONE_HREF:
                print(f'{cs} 2+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 2+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
            else:
                print(f'{cs} 할인 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 할인 행사 제품 개수: {len(event_items)}</b></h3>\n')

            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)

        except NoSuchElementException as noSuchElementException:
            print(noSuchElementException.msg)
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def ministop_gift_event_item_crawling(page_type):  # 미니스톱 덤증정
        # 덤 증정 페이지로 이동
        driver.get(page_type)
        time.sleep(1)

        event_items = []
        dum_event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        scroll_num = 0
        # 스크롤 맨 아래까지 내리기
        last_height = driver.execute_script('return document.body.scrollHeight')
        try:
            while True:
                # scroll down to bottom
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                load_more_button = driver.find_element(By.CSS_SELECTOR,
                                                       'div.inner.wrap.service1 > div.event_add_list > div.pr_btns > a.pr_more')
                # load more page
                if load_more_button is not None:
                    load_more_button.click()
                    scroll_num += 1
                    print(f'ministop(page_type: {page_type}) scrolling: {scroll_num}')
                    time.sleep(1)

                # calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script('return document.body.scrollHeight')
                if new_height == last_height:
                    print('new_height == last_height')
                    print(f'ministop(page_type: {page_type}) 스크롤({scroll_num}) 완료')
                    break
                last_height = new_height
        except NoSuchElementException as noSuchElementException:  # 모두 스크롤이 됐을 때, element 체크하는 method가 없음
            print(f'ministop(page_type: {page_type}) 스크롤({scroll_num}) 완료: {noSuchElementException.msg}')

        # start crawling
        try:
            prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.inner.wrap.service1 > div.event_add_list > ul > li')
            for prod in prod_list:
                title = prod.find_element(By.CSS_SELECTOR, 'a > div.add_left > img').get_attribute('alt')
                img_url = prod.find_element(By.CSS_SELECTOR, 'a > div.add_left > img').get_attribute('src')
                origin_price = int(
                    prod.find_element(By.CSS_SELECTOR, 'a > div.add_left > p > strong').text.replace(',', ''))
                discounted_price = None
                event_type = '덤증정'
                dum_title = prod.find_element(By.CSS_SELECTOR, 'a > div.add_right > img').get_attribute('alt')
                dum_img_url = prod.find_element(By.CSS_SELECTOR, 'a > div.add_right > img').get_attribute('src')
                dum_origin_price = int(
                    prod.find_element(By.CSS_SELECTOR, 'a > div.add_right > p > strong').text.replace(',', ''))

                # 행사 상품 + 덤증정 아이템 같이 저장해야 함
                event_item = EventItems(item_name=title, item_price=origin_price,
                                        item_actual_price=discounted_price, depth=0,
                                        image_url=img_url, category=None, cs_brand=cs, event_type=event_type)
                session.add(event_item)
                session.flush()
                session.refresh(event_item)

                event_item.bundle_id = event_item.event_item_id

                # 덤 증정 상품 정보(depth = 1)
                dum_event_item = EventItems(item_name=dum_title, item_price=dum_origin_price,
                                            item_actual_price=discounted_price, depth=1,
                                            bundle_id=event_item.event_item_id,
                                            image_url=dum_img_url, category=None, cs_brand=cs,
                                            event_type=event_type)
                session.add(dum_event_item)
                session.commit()

                event_items.append(event_item)
                dum_event_items.append(dum_event_item)

                print(f'{cs} event_item = {event_item}')
                print(f'{cs} dum_event_item = {dum_event_item}')

            print(f'{cs} 덤 증정 행사 상품 개수: {len(dum_event_items)}')
            ret_str_list.append(f'\n<h3><b>{cs} 덤 증정 행사 상품 개수: {len(dum_event_items)}</b></h3>\n')
            extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items, dum_event_items=dum_event_items)

        except NoSuchElementException as noSuchElementException:
            print(noSuchElementException.msg)
        except:
            session.rollback()
            raise
        finally:
            session.close()

    ministop_plus_and_discount_event_item_crawling(ONE_PLUS_ONE_HREF)
    ministop_plus_and_discount_event_item_crawling(TWO_PLUS_ONE_HREF)
    ministop_plus_and_discount_event_item_crawling(DISCOUNT_HREF)
    ministop_gift_event_item_crawling(GIFT_HREF)

    ret_str_list.append(
        f'\n<h3><b>============================={cs} End=============================</b></h3>')
    ret_dict[cs] = ''.join(ret_str_list)
    driver.quit()


def emart24_crawling(cs, ret_dict):
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(EMART24_URL)
    print(driver.title)

    ret_str_list = [f'<h1><b><{cs} 행사 상품 목록></b></h3>\n']

    ONE_PLUS_ONE_SCRIPT = 'goTab(\'1n1\');'
    TWO_PLUS_ONE_SCRIPT = 'goTab(\'2n1\');'
    THREE_PLUS_ONE_SCRIPT = 'goTab(\'3n1\');'
    GIFT_HREF = 'goTab(\'X2\');'
    DISCOUNT_SCRIPT = 'goTab(\'SALE\');'

    def emart24_crawling_details(page_type_script):
        # 1+1 | 2+1 | 3+1 | 할인행사 페이지로 이동
        driver.execute_script(page_type_script)
        time.sleep(1)

        event_items = []
        dum_event_items = []

        # Create a session
        Session = sqlalchemy.orm.sessionmaker(bind=models.engine, autoflush=True, autocommit=False)
        session = Session()

        # 몇 페이지까지 있는지 가져오기 (아이템이 없을 때 어떻게 예외 처리를 해야 할지..)
        try:
            go_to_last_page_js_script = driver.find_elements(By.CSS_SELECTOR, 'div.paging > a').pop().get_attribute(
                'href')
            total_page_num = int(re.sub(r'[^0-9]', '', go_to_last_page_js_script))
            print('total_page_num =', total_page_num)

            for i in range(1, total_page_num + 1):
                # start crawling
                prod_list = driver.find_elements(By.CSS_SELECTOR, 'div.eventProduct > div.tabContArea > ul > li')
                for prod in prod_list:
                    title = prod.find_element(By.CSS_SELECTOR, 'div.box > p.productDiv').text
                    img_url = prod.find_element(By.CSS_SELECTOR, 'div.box > p.productImg > img').get_attribute('src')
                    if page_type_script == DISCOUNT_SCRIPT:  # SALE
                        origin_price = int(
                            prod.find_element(By.CSS_SELECTOR, 'div.box > p.price > span > s').text.split(' ')[
                                0].replace(',', ''))
                    else:
                        origin_price = int(
                            prod.find_element(By.CSS_SELECTOR, 'div.box > p.price').text.split(' ')[0].replace(',', ''))

                    if page_type_script == ONE_PLUS_ONE_SCRIPT:  # 실제 가격 구하기
                        discounted_price = round(origin_price / 2)
                    elif page_type_script == TWO_PLUS_ONE_SCRIPT:
                        discounted_price = round(origin_price / 3)
                    elif page_type_script == THREE_PLUS_ONE_SCRIPT:
                        discounted_price = round(origin_price / 4)
                    elif page_type_script == GIFT_HREF:
                        discounted_price = None
                    else:  # SALE (코드가 좀 더럽기는 하네)
                        discounted_price = int(prod.find_element(By.CSS_SELECTOR,
                                                                 'div.box > p.price').text.split(' ')[3].replace(',',
                                                                                                                 ''))

                    if page_type_script == ONE_PLUS_ONE_SCRIPT:  # event_type이 이미지 형태임
                        event_type = '1+1'
                    elif page_type_script == TWO_PLUS_ONE_SCRIPT:
                        event_type = '2+1'
                    elif page_type_script == THREE_PLUS_ONE_SCRIPT:
                        event_type = '3+1'
                    elif page_type_script == GIFT_HREF:
                        event_type = '덤증정'
                    else:
                        event_type = '가격할인'

                    if page_type_script == GIFT_HREF:
                        origin_title = title.split('_')[0]
                        dum_title = title.split('_')[1]

                        event_item = EventItems(item_name=origin_title, item_price=origin_price,
                                                item_actual_price=None,
                                                depth=0, image_url=img_url, category=None,
                                                cs_brand=cs, event_type=event_type)
                        session.add(event_item)
                        session.flush()
                        session.refresh(event_item)

                        event_item.bundle_id = event_item.event_item_id

                        # emart24는 덤 증정 상품 정보 item title밖에 제공 안 함.
                        dum_event_item = EventItems(item_name=dum_title, item_price=None, item_actual_price=None,
                                                    depth=1, bundle_id=event_item.event_item_id,
                                                    image_url=None, category=None, cs_brand=cs, event_type=event_type)
                        session.add(dum_event_item)
                        event_items.append(event_item)
                        dum_event_items.append(dum_event_item)

                        print(f'{cs} event_item = {event_item}')
                        print(f'{cs} dum_event_item = {dum_event_item}')
                    else:
                        event_item = EventItems(item_name=title, item_price=origin_price,
                                                item_actual_price=discounted_price, depth=0, image_url=img_url,
                                                category=None, cs_brand=cs, event_type=event_type)
                        session.add(event_item)
                        event_items.append(event_item)
                        print(f'{cs} event_item = {event_item}')

                    session.commit()

                driver.execute_script(f'goPage(\'{i + 1}\')')
                time.sleep(1)

            if page_type_script == ONE_PLUS_ONE_SCRIPT:
                print(f'{cs} 1+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 1+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
                extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)
            elif page_type_script == TWO_PLUS_ONE_SCRIPT:
                print(f'{cs} 2+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 2+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
                extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)
            elif page_type_script == THREE_PLUS_ONE_SCRIPT:
                print(f'{cs} 3+1 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 3+1 행사 제품 개수: {len(event_items)}</b></h3>\n')
                extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)
            elif page_type_script == GIFT_HREF:
                print(f'{cs} 3+1 행사 제품 개수: {len(dum_event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 덤증정 행사 제품 개수: {len(dum_event_items)}</b></h3>\n')
                extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items,
                                       dum_event_items=dum_event_items)
            else:
                print(f'{cs} 할인 행사 제품 개수: {len(event_items)}')
                ret_str_list.append(f'\n<h3><b>{cs} 할인 행사 제품 개수: {len(event_items)}</b></h3>\n')
                extract_first10_last10(ret_str_list=ret_str_list, event_items=event_items)

        except ValueError as valueError:
            print(f'ValueError: {valueError}')
        except NoSuchElementException as noSuchElementException:
            print(noSuchElementException.msg)
        except:
            session.rollback()
            raise
        finally:
            session.close()

    emart24_crawling_details(ONE_PLUS_ONE_SCRIPT)
    emart24_crawling_details(TWO_PLUS_ONE_SCRIPT)
    emart24_crawling_details(THREE_PLUS_ONE_SCRIPT)
    emart24_crawling_details(DISCOUNT_SCRIPT)
    emart24_crawling_details(GIFT_HREF)

    ret_str_list.append(
        f'<h3><b>============================={cs} End=============================</b></h3>')
    ret_dict[cs] = ''.join(ret_str_list)
    driver.quit()
