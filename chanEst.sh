IFACE=ap0
for N in $(arp -n -i $IFACE | awk '{print $1","$3}' | tail -n +2);  do
    IP=$(echo $N | cut -f1 -d',')
    MAC=$(echo $N | cut -f2 -d',')
    sudo iw dev ap0 station get $MAC | awk 'NR==9{print $2}'
done
