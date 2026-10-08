#!/usr/bin/env bash
cd /tmp/mcref/mcserver
rm -f console.in && mkfifo console.in
( while true; do sleep 86400; done ) > console.in &
exec /tmp/jdk21/bin/java -Xmx1100M -Xms256M -jar fabric-server-launch.jar nogui < console.in
