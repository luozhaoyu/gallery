# -*- coding: utf-8 -*-
"""
    queue_simulation.py
    ~~~~~~~~~~~~~~

    simulate queuing theory
"""
import argparse
import random
try:
    import numpy
except ImportError as e:
    print e


def get_random_arrivals(arrival_rate, arrive_type="default"):
    arrive_type = arrive_type.lower()
    if arrive_type == "poisson":
        arrive_times = []
        t = 0
        for i in range(arrival_rate):
            t += random.expovariate(arrival_rate)
            arrive_times.append(t)
    else:
        arrive_times = [random.random() for i in range(arrival_rate)]
    return arrive_times


def run(arrive_times, service_time, worker_number=1):
    arrive_times.sort()
    worker = [0] * worker_number

    total_response_time = 0
    last_check_time = 0
    for i in range(len(arrive_times)):
        worker.sort(reverse=True)
        time_elapsed = arrive_times[i] - last_check_time
        # check each worker from heavist workload to lightest
        for j in range(worker_number):
            if worker[j] - time_elapsed >= 0: # still working
                total_response_time += time_elapsed
                worker[j] -= time_elapsed
            elif worker[j] > 0: # job finished previously
                total_response_time += worker[j]
                worker[j] = 0
            else:
                break
        worker.sort()
        #print arrive_times[i], worker, total_response_time
        # wait until the lightest worker to finish, then attach to this worker
        total_response_time += worker[0]
        worker[0] += service_time

        last_check_time = arrive_times[i]

    # do not forget the mission unfinished
    total_response_time += sum(worker)
    return total_response_time / len(arrive_times)


def _main(argv):
    parser = argparse.ArgumentParser(description="""
        monitor queuing theory
        """)
    parser.add_argument('-a', '--arrival-rate', help='arrival rate per second', type=int, default=100)
    parser.add_argument('-s', '--service-time', help='service time, unit: ms, default: 50 ms', type=float, default=50.0)
    parser.add_argument('-w', '--worker', help='number of workers', type=int, default=1)
    parser.add_argument('-t', '--arrive-type', help='arrive type', default="default")
    parser.add_argument('-r', '--repeat', help='repeat times', default=1, type=int)
    args = parser.parse_args()
    print args
    response_time = []
    for i in range(args.repeat):
        arrive_times = get_random_arrivals(arrival_rate=args.arrival_rate, arrive_type=args.arrive_type)
        response_time.append(run(arrive_times=arrive_times, service_time=args.service_time / 1000, worker_number=args.worker))
    print sum(response_time) / len(response_time)


if __name__ == '__main__':
    import sys
    _main(sys.argv)
