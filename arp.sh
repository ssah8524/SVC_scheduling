#!/bin/bash
USERNO=$1
IPPREFIX="192.168.0."
b=1
while [ $b -le $USERNO ];do
    IFACE="$IPPREFIX$b"
    for N in $(arp -n -i ap0 $IFACE | awk '{print $1","$3}' | grep -v "$IFACE" | tail -n +2);do
        IP=$(echo $N | cut -f1 -d',')
        MAC=$(echo $N | cut -f2 -d',')
    done
    let b=$(($b+1))
done

