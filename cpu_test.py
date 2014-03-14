# -*- coding: utf-8 -*-
"""
    cpu_test.py
    ~~~~~~~~~~~~~~

    A brief description goes here.
"""
import time
import random
import argparse
from multiprocessing import Pool, current_process


def calc(nk=(10, 3)):
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
    result = {
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
    print "%i\tCounts:%i\tTime:%.4f %.4f %.4f\t%.4f" % (current_process().pid, result['counts'],
            result['time']['total'], result['time']['alloc'], result['time']['initial'], 
            result['result'])
    return result


def many_time(args):
    try:
        for i in range(0, args['many']):
            start_time = time.time()
            try:
                result = args['func'](args['param'])
            except:
                raise
            end_time = time.time()
            if args.get('verbose'):
                print "%i: %.5f" % (current_process().pid, end_time - start_time)
    except KeyboardInterrupt:
        print 'Keyboard Interrupted'
        return None


def sleep(param):
    nap = param['nap']
    last = param['last']
    while last > 0:
        time.sleep(nap)
        print "napped: %.3f" % nap
        calc((2000, 100))
        last -= nap


def multi_process_many_time(total=1000, worker_number=4, task_type='cpu', nap=0.2, last=10):
    workers = Pool(worker_number)
    verbose = False
    if task_type == 'sleep':
        func = sleep
        param = {'nap': nap, 'last': last}
        verbose = True
    else:  # else is assumed as 'cpu'
        func = calc
        param = (2000, 100)

    work_results = workers.map(many_time,
        [{
            'many': total / worker_number,
            'func': func,
            'param': param,
            'verbose': verbose,
            }
            for i in range(worker_number)])
    workers.close()
    workers.join()
    print 'END: %s' % work_results.successful()


def _main(argv):
    parser = argparse.ArgumentParser(description="""
        test cpu multiprocessing ability
        only focus on cpu time consuming, do not perform any statistical tasks""")
    parser.add_argument('-t', '--total', help='total tasks', type=int, default=32)
    parser.add_argument('-w', '--worker', help='worker number', type=int, default=2)
    parser.add_argument('--task-type', help='task type', default='cpu')
    args = parser.parse_args()
    print args
    s0 = time.time()
    multi_process_many_time(args.total, args.worker, task_type=args.task_type)
    s1 = time.time()
    print "TOTAL:%.4f\tAVG:%.4f" % (s1 - s0, (s1 - s0) / args.total)



if __name__ == '__main__':
    import sys
    _main(sys.argv)
