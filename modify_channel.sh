
N=8 #number of users
#m=4 #number of groups

##Initialize the attenuations


wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=2\&att=6
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=3\&att=6
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=4\&att=9
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=5\&att=9
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=6\&att=12
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=7\&att=12
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=8\&att=15
wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB=9\&att=15

#wget -qO- "http://internal2dmz.orbit-lab.org:5054/instr/selDevice?switch=1&port=1"
#wget -qO- "http://internal2dmz.orbit-lab.org:5054/instr/selDevice?switch=2&port=1"
#wget -qO- "http://internal2dmz.orbit-lab.org:5054/instr/selDevice?switch=3&port=1"
#wget -qO- "http://internal2dmz.orbit-lab.org:5054/instr/selDevice?switch=4&port=1"


runtime=$((end-start))
while 1; do
    for i in {1..$N}; do
        c=(((RANDOM % 4)+1))
        if[$c -eq 1]; then
            wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB="$i"\&att=6
        fi
        if[$c -eq 2]; then
            wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB="$i"\&att=9
        fi
        if[$c -eq 3]; then
            wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB="$i"\&att=12
        fi
        if[$c -eq 4]; then
            wget -O status http://internal2dmz.orbit-lab.org:5054/instr/set?portA=1\&portB="$i"\&att=15
        fi
    done
    sleep 5
done

