
$UCESB_DIR/empty/empty --help

## Useful parameters
## --allow-errors 
## --data 
## --print 
## --quiet 
## --time-stitch=wr,1000 
## --input-buffer=200Mi 
## --event-sizes 
## --dump=RAW 
## --print-members

##
## Split the imput data 
## with stream
$UCESB_DIR/empty/empty stream://x86l-132 --server=stream:7777

$UCESB_DIR/empty/empty stream://localhost:7777
$UCESB_DIR/empty/empty stream://localhost:7777

## with trans
$UCESB_DIR/empty/empty stream://x86l-132 --server=trans:7777

$UCESB_DIR/empty/empty trans://localhost:7777
$UCESB_DIR/empty/empty trans://localhost:7777

## individual streams
$UCESB_DIR/empty/empty stream://x86l-132 --data --print --quiet
$UCESB_DIR/empty/empty stream://x86l-170 --data --print --quiet
$UCESB_DIR/empty/empty stream://x86l-253 --data --print --quiet



$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --output=- | $UCESB_DIR/empty/empty --data --print --file=-

$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --output=- | ~/software/mrgroot/unpack/exps/superfrs/unpacker --debug --data --print --file=-

$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --output=- | ~/software/mrgroot/unpack/exps/superfrs/unpacker --file=- --debug 

$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --output=- | ~/software/mrgroot/unpack/exps/superfrs/unpacker --file=- --data --print --debug 

$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --output=- | ~/software/mrgroot/unpack/exps/superfrs/unpacker --allow-errors --file=-




## --dump=RAW
$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --event-sizes --output=- | ~/software/mrgroot/unpack/exps/superfrs/unpacker --debug --file=- --data --print --dump=RAW

## --print-members
$UCESB_DIR/empty/empty stream://x86l-157 --quiet --time-stitch=wr,1000 --input-buffer=200Mi --event-sizes --output=- | ~/software/mrgroot/unpack/exps/superfrs/unpacker --debug --file=- --data --print --print-members

