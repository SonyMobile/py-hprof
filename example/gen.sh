#!/bin/bash

set -ex

DATADIR='../testdata'
APROF=$DATADIR/example-android.hprof
JPROF=$DATADIR/example-java.hprof

find . -name '*.class' | xargs rm -f
javac Main.java

# generate JVM hprof
rm -f "$JPROF" "$JPROF.bz2"
java Main &
JAVA_PID=$!
sleep 3
jmap -dump:format=b,file="$JPROF" $JAVA_PID
bzip2 "$JPROF"
kill %1
wait

# generate Android hprof
WDIR='/data/local/tmp'
rm -f "$APROF" "$APROF.bz2"
mkdir -p dexed
d8 --release --output dexed Main.class $(find com -name '*.class')
adb push dexed/classes.dex "$WDIR/example.dex"
adb shell dalvikvm64 -cp "$WDIR/example.dex" Main "$WDIR/ex.hprof"
adb pull "$WDIR/ex.hprof" "$APROF"
bzip2 "$APROF"
