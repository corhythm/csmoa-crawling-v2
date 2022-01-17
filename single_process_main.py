import os
import platform
from _datetime import datetime
import multiprocessing
import time

from pytz import timezone

import cs_crawling
from github_utils import get_github_repo, upload_github_issue

try:
    import secret
except ModuleNotFoundError:
    pass

if __name__ == '__main__':
    print('Start Crawling!')
    start_time = time.time()

    ret_dict = {'cu': '', 'gs25': '', 'seven_eleven': '', 'ministop': '', 'emart24': ''}
    
    cs_crawling.seven_eleven_crawling('seven_eleven', ret_dict)
    cs_crawling.cu_crawling('cu', ret_dict)
    cs_crawling.gs25_crawling('gs25', ret_dict)
    #cs_crawling.seven_eleven_crawling('seven_eleven', ret_dict)
    cs_crawling.ministop_crawling('ministop', ret_dict)
    cs_crawling.emart24_crawling('emart24', ret_dict)
    

    if platform.system() != 'Windows':  # 깃허브 이슈에 업로드(깃허브 액션에서 실행될 경우에만 실행)
        access_token = secret.MY_GITHUB_TOKEN if os.path.isfile('secret.py') else os.environ['MY_GITHUB_TOKEN']
        repository_name = 'csmoa-crawling-v2'
        seoul_timezone = timezone('Asia/Seoul')
        today = datetime.now(seoul_timezone).strftime('%Y년 %m월 %d일 %H:%M:%S')

        issue_title = f'(CU, GS25, MINISTOP, SEVEN-ELEVEN, Emart24) 행사상품 알림({today})'
        repository = get_github_repo(access_token, repository_name)
        upload_body = ''.join(ret_dict.values())
        upload_github_issue(repository=repository, title=issue_title, body=upload_body)

    print(ret_dict.values())
    crawling_result_message = f"{time.time() - start_time:.5f} sec / crawling finished"
    print(crawling_result_message)
