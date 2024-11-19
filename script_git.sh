#!/bin/bash

cd ~/africanpulsartiming.github.io/

git add .

read -p "commit message: " commit
echo $commit

git commit -m "$commit"

git push 

osascript -e 'display notification "pushed to remote" with title "SUCCESS"'

