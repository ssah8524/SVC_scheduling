
#GROUP=node1-1.sb1.orbit-lab.org,node1-2.sb1.orbit-lab.org,node2-1.sb1.orbit-lab.org
GROUP=node1-1.sb4.orbit-lab.org,node1-2.sb4.orbit-lab.org,node1-3.sb4.orbit-lab.org

if [[ -n "$GROUP" ]]  
then  
  omf load -i geni-amirhsho-node-node1-1.sb1.orbit-lab.org-2017-01-12-14-46-26.ndz -t "$GROUP"
else  
  echo "Please set the GROUP variable"
fi  

if [[ -n "$GROUP" ]]  
then  
  omf tell -a on -t "$GROUP"
else  
  echo "Please set the GROUP variable"
fi 
