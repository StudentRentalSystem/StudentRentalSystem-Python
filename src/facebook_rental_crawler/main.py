import sys
import threading
import queue
from crawler import Crawler
from extractor import RentalExtractor
from database import db_instance

def worker(post_queue):
    extractor = RentalExtractor()
    while True:
        post = post_queue.get()
        if post is Crawler.POISON_PILL:
            # 放回 Poison Pill 讓其他 worker 也能停止 (如果有多個 worker)
            post_queue.put(Crawler.POISON_PILL)
            break
            
        try:
            processed_doc = extractor.process_post(post["content"])
            if processed_doc:
                db_instance.insert_post(processed_doc)
        except Exception as e:
            print(f"❌ Error in worker: {e}")
        finally:
            post_queue.task_done()

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <scroll_count>")
        sys.exit(1)

    scroll_count = int(sys.argv[1])
    post_queue = queue.Queue()

    # 啟動 Crawler
    crawler = Crawler(scroll_count, post_queue)
    crawler_thread = threading.Thread(target=crawler.crawl)
    crawler_thread.start()

    # 啟動 Worker 執行緒 (這裡設定數量為 scroll_count / 2，最小為 1)
    worker_count = max(1, scroll_count // 2)
    workers = []
    for _ in range(worker_count):
        t = threading.Thread(target=worker, args=(post_queue,))
        t.start()
        workers.append(t)

    # 等待 Crawler 結束
    crawler_thread.join()
    
    # 等待所有佇列處理完畢
    for t in workers:
        t.join()

    print("🎉 All done!")

if __name__ == "__main__":
    main()