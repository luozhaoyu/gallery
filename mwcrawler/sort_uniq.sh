#!/bin/sh
echo `wc -l $1`
sort -u $1 > t1
sort -k 2 -n -r t1 > t
mv t $1
echo `wc -l $1`
rm -rf t
