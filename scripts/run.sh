#!/bin/sh
function run {
    echo 'Ready to excute:' $@ '...'
    $@
    if [ $? != 0 ];
        then echo 'Fail to excute:' $@;
        return
    fi
    echo $1 'FINISHED.'
}
