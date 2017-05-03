### Play back a video

The video files for all users are downloaded into the `user_files` folder on each of the nodes 2 through 9.  We can play back this video and observe the variations in video quality, although we won't be able to see instances of rebuffering. But,

* Video files from a current experiment will overwrite files from previous experiments in `user_files`. If you are playing back video, delete anything in `user_files` before starting the experiment, and save any video that you want to keep in another location.
* Rebuffering only occurs during "live" video play, not when playing back a stored video file.) You will, however, note that some users have a shorter video than others even though they all have a 300-second playback time, because some users spend a substantial portion of that time waiting for video to load.

In order to be able to play back the received video segments, we need to combine different layers into a single video file for every segment, and decode the video. Download the necessary software onto the node and compile it with:

```
apt-get update
apt-get -y install libav-tools

cd ~
git clone -b demo https://github.com/ffund/SVC-Layer-multiplexing-demultiplexing.git multiplex

cd ~/multiplex/SVC_layer_multiplexer/
make

cd ~/multiplex/H264Extension/build/linux/
make decoder

```

This is a one-time setup - you only need to do this once on each node on which you want to create video files.

Now that everything is set up, to create a playable video file out of the segments and layers you have downloaded in an experiment, run,

```
cd /root/SVC_scheduling/user_files/
bash ../mux.sh
```

Then, transfer the video file to your laptop:

<pre>
scp -o "StrictHostKeyChecking no"  -o "ProxyCommand ssh <b>USERNAME</b>@sb4.orbit-lab.org nc %h %p" root@<b>node1-2</b>:/root/SVC_scheduling/user_files/final_output.mp4 video.mp4
</pre>

where

* in place of <b>USERNAME</b>, put the username with which you access the ORBIT testbed,
* in place of <b>node1-2</b>, put the name of the node on which you have created the video file, and
* you may also need to specify a key (with `-i` argument) if you access the ORBIT testbed with a key that is not in the default location.

You should then be able to play back the "video.mp4" file with any standard video player.
