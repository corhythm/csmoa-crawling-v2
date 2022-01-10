import multiprocessing
import time

import cs_crawling

if __name__ == '__main__':
    start_time = time.time()

    multiprocessing.set_start_method('spawn')
    cu_process = multiprocessing.Process(target=cs_crawling.cu_crawling)
    gs25_process = multiprocessing.Process(target=cs_crawling.gs25_crawling)
    seven_eleven_process = multiprocessing.Process(target=cs_crawling.seven_eleven_crawling)
    ministop_process = multiprocessing.Process(target=cs_crawling.ministop_crawling)
    emart24_process = multiprocessing.Process(target=cs_crawling.emart24_crawling)

    # start processes
    cu_process.start()
    gs25_process.start()
    seven_eleven_process.start()
    ministop_process.start()
    emart24_process.start()

    # join processes
    cu_process.join()
    gs25_process.join()
    seven_eleven_process.join()
    ministop_process.join()
    emart24_process.join()

    crawling_result_message = f"{time.time() - start_time:.5f} sec / crawling finished"
    print(crawling_result_message)

    # cs_crawling.cu_crawling()
    # cs_crawling.gs25_crawling()
    # cs_crawling.seven_eleven_crawling()
    # cs_crawling.ministop_crawling()
    # cs_crawling.emart24_crawling()



