#!/bin/bash

function make_tunnel {
        LOCALNAME=$1;
        LOCALIP=$2;
        REMOTENAME=$3;
        REMOTEIP=$4;
        REMOTEPUBLICIP=$5;
        REMOTENET=$6;

        TUNNELNAME=$LOCALNAME--$REMOTENAME;

        ip tunnel del $TUNNELNAME || true;
        ip tunnel add $TUNNELNAME mode gre remote $REMOTEPUBLICIP;

        ip link set $TUNNELNAME up;
        ip addr add $LOCALIP dev $TUNNELNAME;
        ip route replace $REMOTEIP dev $TUNNELNAME;
        ip route replace $REMOTENET via $REMOTEIP;
}

make_tunnel bj7 192.168.99.10   ad1             192.168.99.11   122.11.56.108   192.168.168/24
make_tunnel bj7 192.168.99.14   gh-r410-00      192.168.99.15   119.254.92.3    192.168.10/24
