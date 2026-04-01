!/bin/csh -f
# source ~/force_env.csh

echo "  Restarting MBS and webmbs..."
~/mncl/bin/kill_screens.csh
resl
~/mncl/bin/check_screens.csh
screen -S mbs -X stuff 'cd ~/sfrs_tof_test/murx/\nmbs -dabc\n\n'
screen -S web -X stuff 'webmbs 8899\n'
screen -S mbs -X stuff '@startup\n'
