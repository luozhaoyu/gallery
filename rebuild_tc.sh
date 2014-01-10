#!/bin/sh
if=$1
if [ ! $if ]
then
    echo "Please input interface name, such as 'eth0'";
    exit;
fi
echo "Rebuilding traffic controlle on $if..."
tc qdisc del dev $if root
tc qdisc add dev $if root handle 1: htb
tc class add dev $if parent 1: classid 1: htb rate 2mbit ceil 2mbit
tc -s qdisc show
tc -s class show dev $if
