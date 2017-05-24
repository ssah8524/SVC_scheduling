

IFACE=192.168.0.3
for N in $(arp -n -i ap0 $IFACE | awk '{print $1","$3}' | grep -v "$IFACE" | tail -n +2);  do
   IP=$(echo $N | cut -f1 -d',')
   MAC=$(echo $N | cut -f2 -d',')
done
