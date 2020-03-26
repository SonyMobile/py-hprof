#!/bin/bash

# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

set -ex

find . -name '*.class' | xargs rm
javac Main.java

# generate JVM hprof
rm -f ../tests/java.hprof
java -agentlib:hprof=heap=dump,format=b,doe=n,file=../tests/java.hprof Main &
JPID=$!
sleep 2
kill -QUIT $JPID # this triggers the dump
wait

# TODO: same for dex/ART
dx --dex --output=program.dex $(find . -name '*.class' -a '!' -name Debug.class)
adb push program.dex /data/local/tmp/
adb shell dalvikvm64 -cp /data/local/tmp/program.dex Main /data/local/tmp/android.hprof
adb pull /data/local/tmp/android.hprof ../tests/android.hprof
