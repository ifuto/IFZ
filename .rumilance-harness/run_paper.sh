#!/usr/bin/env bash
cd /tmp/testsrv
rm -f console.in && mkfifo console.in
( while true; do sleep 86400; done ) > console.in &
exec /tmp/jdk21/bin/java -Xmx1000M -Xms256M -Drumilance.harness=true -jar server.jar nogui < console.in
