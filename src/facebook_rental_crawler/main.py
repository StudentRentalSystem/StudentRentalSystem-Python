import sys
import threading
import queue
from src.facebook_rental_crawler.extractor import RentalExtractor
from src.facebook_rental_crawler.crawler import Crawler

def worker(post_queue):
    extractor = RentalExtractor()
    while True:
        post = post_queue.get()
        if post is Crawler.POISON_PILL:
            # Put back Poison Pill to let other workers stop (for multiple workers environment)
            post_queue.put(Crawler.POISON_PILL)
            break
            
        try:
            processed_uuid = extractor.process_post_and_insert(post["content"])
            print(processed_uuid)
        except Exception as e:
            print(f"Error in worker: {e}")
        finally:
            post_queue.task_done()


def main():
    """
    To run the crawler, the user must specify the scroll count in arguments.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py <scroll_count>")
        sys.exit(1)

    scroll_count = int(sys.argv[1])
    post_queue = queue.Queue()

    # Start Crawler
    crawler = Crawler(scroll_count, post_queue)
    crawler_thread = threading.Thread(target=crawler.crawl)
    crawler_thread.start()

    # Start Worker threads (Here set count to scroll_count / 2, min 1)
    worker_count = max(1, scroll_count // 2)
    workers = []
    for _ in range(worker_count):
        t = threading.Thread(target=worker, args=(post_queue,))
        t.start()
        workers.append(t)

    # Wait for Crawler to finish
    crawler_thread.join()
    
    # Wait for all queues to be processed
    for t in workers:
        t.join()

    print("Finish Crawling")


if __name__ == "__main__":
    main()