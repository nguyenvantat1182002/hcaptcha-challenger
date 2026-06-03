import queue
import threading
from typing import Callable, Any

class PlaywrightWorker:
    """A thread-isolated, reusable Playwright runner.
    
    This class maintains a single daemon background thread that initializes and holds 
    the Playwright context. It allows executing functions that require Playwright 
    without conflicting with any asyncio event loops in the calling thread.
    
    The thread is a daemon thread, so it won't prevent the program from exiting.
    """
    def __init__(self, cdp_address: str):
        self.cdp_address = cdp_address
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="PlaywrightWorker")
        self.thread.start()
        
        # Wait for initialization to complete
        success, result = self.result_queue.get()
        if not success:
            raise RuntimeError(f"Failed to initialize Playwright worker: {result}")
            
        import atexit
        atexit.register(self.close)

    def _run_loop(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw_context = sync_playwright()
            self._pw = self._pw_context.start()
            self.browser = self._pw.chromium.connect_over_cdp(f"http://{self.cdp_address}")
            self.result_queue.put((True, None))
        except Exception as e:
            self.result_queue.put((False, e))
            return

        while True:
            task = self.task_queue.get()
            if task is None:  # Shutdown signal
                self.task_queue.task_done()
                break
                
            func, args, kwargs = task
            try:
                result = func(self.browser, *args, **kwargs)
                self.result_queue.put((True, result))
            except Exception as e:
                self.result_queue.put((False, e))
            finally:
                self.task_queue.task_done()
                
        try:
            self.browser.close()
            self._pw_context.__exit__(None, None, None)
        except Exception:
            pass

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function synchronously in the Playwright thread.
        
        The function must accept `browser` as its first argument, followed by any args.
        Exceptions raised in the worker thread will be re-raised in the caller's thread.
        """
        self.task_queue.put((func, args, kwargs))
        success, result = self.result_queue.get()
        
        if not success:
            raise result
        return result

    def close(self):
        """Close the Playwright context and shutdown the worker thread."""
        if self.thread.is_alive():
            self.task_queue.put(None)
            self.thread.join(timeout=3.0)
