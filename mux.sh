
MUXPATH="/root/multiplex/SVC_layer_multiplexer/Multiplex"
for segment in {00..99}
do 
  layers=$(ls -1 | grep "_$(printf %02d ${segment#0}).svc" | wc -l)
  if [ $layers -eq 1 ]; then
    $MUXPATH layer0"_$(printf %02d "${segment#0}").svc" -n 0
    mv final_output.264 segment-"$(printf %03d ${segment#0})".264
  fi
  if [ $layers -eq 2 ]; then
    $MUXPATH layer0"_$(printf %02d "${segment#0}").svc" -n 1 layer1"_$(printf %02d "${segment#0}").svc"
    mv final_output.264 segment-"$(printf %03d ${segment#0})".264
  fi
  if [ $layers -eq 3 ]; then
    $MUXPATH layer0"_$(printf %02d "${segment#0}").svc" -n 1 layer1"_$(printf %02d "${segment#0}").svc" layer2"_$(printf %02d "${segment#0}").svc"
    mv final_output.264 segment-"$(printf %03d ${segment#0})".264
  fi
done

for segment in {100..300}
do 
  layers=$(ls -1 | grep "_$(printf %02d ${segment#0}).svc" | wc -l)
  if [ $layers -eq 1 ]; then
    $MUXPATH layer0"_$(printf %02d "${segment#0}").svc" -n 0
    mv final_output.264 segment-"$(printf %03d ${segment#0})".264
  fi
  if [ $layers -eq 2 ]; then
    $MUXPATH layer0"_$(printf %02d "${segment#0}").svc" -n 1 layer1"_$(printf %02d "${segment#0}").svc"
    mv final_output.264 segment-"$(printf %03d ${segment#0})".264
  fi
  if [ $layers -eq 3 ]; then
    $MUXPATH layer0"_$(printf %02d "${segment#0}").svc" -n 1 layer1"_$(printf %02d "${segment#0}").svc" layer2"_$(printf %02d "${segment#0}").svc"
    mv final_output.264 segment-"$(printf %03d ${segment#0})".264
  fi
done

