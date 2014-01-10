# -*- coding: utf-8 -*-
"""
    cpu_test.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import time
import random
from multiprocessing import Pool
def one_time(nk=(10, 3)):
    n, k = nk
    start_time = time.time()
    c = 0
    coins = [random.random() for i in range(0, n)]
    r = [[None for i in range(0, k)] for j in range(0, n)]
    alloc_time = time.time()
    # initial
    none_of_them = 1
    r[0][0] = 1
    for i in range(1, n):
        c += 1
        r[i][0] = (1 - coins[i]) * r[i-1][0] + coins[i] * none_of_them
        none_of_them *= 1 - coins[i]
    initial_time = time.time()

    # calculate
    for i in range(0, n):
        for j in range(1, k):
            c += 1
            if not r[i][j]:
                if j >= i:
                    r[i][j] = 1
                    continue
                try:
                    r[i][j] = coins[i] * r[i-1][j-1] + (1 - coins[i]) * r[i-1][j]
                except TypeError as e:
                    print e
                    print i, j
                    print r[i]
                    print r[i-1]
                    raise
            else:
                print 'wrong', i, j
    end_time = time.time()
    return {
        'time': {
            'total': end_time - start_time,
            'alloc': alloc_time - start_time,
            'initial': initial_time - alloc_time,
        },
        'results': r,
        'coins': coins,
        'result': r[n-1][k-1],
        'counts': c,
    }


def many_time(many=1000):
    try:
        n = 2000
        k = 100
        for i in range(0, many):
            result = one_time((n, k))
            print "%i\tCounts:%i\tTime:%.4f %.4f %.4f\t%.4f" % (i, result['counts'],
                    result['time']['total'], result['time']['alloc'], result['time']['initial'], 
                    result['result'])
    except KeyboardInterrupt:
        print 'Keyboard Interrupted'
        return None


def multi_process_many_time(total=1000, worker_number=4):
    workers = Pool(worker_number)
    work_results = workers.map_async(many_time, [total / worker_number for i in range(worker_number)])
    workers.close()
    workers.join()
    print 'END: %s' % work_results.successful()

def _main(argv):
    s0 = time.time()
    total = 32
    multi_process_many_time(total, 2)
    #many_time(total)
    s1 = time.time()
    print "TOTAL:%.4f\tAVG:%.4f" % (s1 - s0, (s1 - s0) / total)



if __name__ == '__main__':
    import sys
    _main(sys.argv)
