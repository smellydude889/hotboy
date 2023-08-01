import threading 
def queuify(f):
    def output(q):
        while not q.empty():
            item = q.get()
            try: 
                o = f(item)
            except:
                o = 'fail'
            print(item, o)
    return output

def threadify(f, thread_count, args):
    threads = []
    for _ in range(thread_count):
        t = threading.Thread(target=f, args=(args,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()