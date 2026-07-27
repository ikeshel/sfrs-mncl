!/bin/tcsh -f

echo "  Restarting MBS and webmbs..."
~/sfrs-mncl/bin/kill_screens.csh
resl
~/sfrs-mncl/bin/check_screens.csh
screen -S mbs -X stuff 'cd ~/sfrs_tof_test/murx/\nmbs -dabc\n\n'
screen -S web -X stuff 'webmbs 8899\n'
screen -S mbs -X stuff '@startup\n'
